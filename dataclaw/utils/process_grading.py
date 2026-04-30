"""
Process-oriented grading metrics for DataClaw.

Provides fine-grained evaluation of agent execution trajectories
beyond outcome-only scoring.

Metrics implemented:
- Execution Efficiency: S_gold / S_agent
- Goal Progress Rate (GPR): LLM-Judge-based milestone evaluation
"""

from __future__ import annotations

import json
import logging
import math
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUMERIC_REL_TOL = 0.01      # 1% relative tolerance for candidate extraction
NUMERIC_ABS_TOL = 1e-6      # absolute tolerance for values near zero
SNIPPET_CONTEXT_CHARS = 300  # ~100 tokens context window around matches
SHORT_RESULT_TOKEN_THRESHOLD = 1000  # tool results <= this are included whole
HIGH_FREQ_THRESHOLD = 5             # value occurrences above this trigger key-proximity filter
MAX_SNIPPETS_WHEN_HIGH_FREQ = 5      # max snippets to randomly sample when high-freq filtered
CHARS_PER_TOKEN = 3                  # rough chars-per-token estimate for token counting
ARG_MAX_BYTES = 2 * 1024 * 1024     # Linux ARG_MAX ~2MB — prompt size guard before subprocess


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def _is_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float))


def _numbers_match(expected: float, actual: float) -> bool:
    if math.isnan(expected) or math.isnan(actual):
        return False
    if expected == actual:
        return True
    if abs(expected) < NUMERIC_ABS_TOL:
        return abs(actual - expected) < NUMERIC_ABS_TOL
    return abs(actual - expected) / abs(expected) <= NUMERIC_REL_TOL


# ---------------------------------------------------------------------------
# Trajectory parsing
# ---------------------------------------------------------------------------

@dataclass
class AgentStep:
    """A single agent step, corresponding to one assistant turn."""
    index: int
    tool_calls: List[Dict[str, Any]]
    text: str
    tool_results: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None

    @property
    def has_tool_call(self) -> bool:
        return len(self.tool_calls) > 0

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_calls)

    @property
    def full_text(self) -> str:
        parts = []
        if self.text:
            parts.append(self.text)
        parts.extend(self.tool_results)
        return "\n".join(parts)


def parse_trajectory(transcript_path: Path) -> List[AgentStep]:
    """Parse chat.jsonl into a list of AgentSteps.

    Each assistant message is one step. Tool results following an
    assistant turn are attached to that step.
    """
    if not transcript_path.exists():
        logger.warning("Transcript not found: %s", transcript_path)
        return []

    messages: List[Dict[str, Any]] = []
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "message":
            continue
        messages.append(entry)

    steps: List[AgentStep] = []
    current_step: Optional[AgentStep] = None
    step_index = 0

    for entry in messages:
        msg = entry.get("message", {})
        role = msg.get("role", "")

        if role == "assistant":
            content = msg.get("content", []) or []
            text_parts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []

            for item in content:
                if item.get("type") == "text" and item.get("text"):
                    text_parts.append(item["text"])
                elif item.get("type") == "toolCall":
                    tool_calls.append({
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "arguments": item.get("arguments", {}),
                    })

            step_index += 1
            current_step = AgentStep(
                index=step_index,
                tool_calls=tool_calls,
                text="\n".join(text_parts).strip(),
                timestamp=msg.get("timestamp") or entry.get("timestamp"),
            )
            steps.append(current_step)

        elif role == "toolResult" and current_step is not None:
            content = msg.get("content", []) or []
            for item in content:
                if item.get("type") == "text" and item.get("text"):
                    current_step.tool_results.append(item["text"])

        else:
            current_step = None

    return steps


# ---------------------------------------------------------------------------
# Execution Efficiency
# ---------------------------------------------------------------------------

@dataclass
class EfficiencyResult:
    s_agent: int
    s_gold: int
    efficiency: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "s_agent": self.s_agent,
            "s_gold": self.s_gold,
            "efficiency": self.efficiency,
        }


def compute_efficiency(steps: List[AgentStep], s_gold: int) -> EfficiencyResult:
    """Compute Execution Efficiency = S_gold / S_agent."""
    s_agent = len(steps)
    if s_agent == 0:
        return EfficiencyResult(s_agent=0, s_gold=s_gold, efficiency=None)
    return EfficiencyResult(
        s_agent=s_agent,
        s_gold=s_gold,
        efficiency=round(s_gold / s_agent, 4),
    )


# ---------------------------------------------------------------------------
# GPR: Candidate snippet extraction
# ---------------------------------------------------------------------------

@dataclass
class CandidateSnippet:
    """A context snippet from a tool result containing milestone candidate values."""
    snippet: str
    milestone_matches: List[Tuple[str, float, float]]  # (key, expected, matched)
    tool_result_index: int


def _extract_candidates_for_step(
    step: AgentStep,
    numeric_milestones: Dict[str, float],
    context_chars: int = SNIPPET_CONTEXT_CHARS,
) -> List[CandidateSnippet]:
    """Extract context snippets around numeric milestone matches in tool results.

    Short tool results (≤ SHORT_RESULT_TOKEN_THRESHOLD tokens) are included whole.

    For long tool results, windows are extracted per milestone.  If a milestone
    value appears more than HIGH_FREQ_THRESHOLD times (likely a raw data column),
    only snippets that contain at least one component of the milestone key name
    are kept, and at most MAX_SNIPPETS_WHEN_HIGH_FREQ are randomly sampled.
    If none survive the key-proximity filter, the milestone is skipped for that
    tool result entirely.
    """
    snippets: List[CandidateSnippet] = []

    for tr_idx, tr_text in enumerate(step.tool_results):
        approx_tokens = len(tr_text) // CHARS_PER_TOKEN

        if approx_tokens <= SHORT_RESULT_TOKEN_THRESHOLD:
            # Short result: include whole text, annotate with all matching milestones
            matched: List[Tuple[str, float, float]] = []
            seen_keys: set = set()
            for num_match in re.finditer(r'-?\d+(?:\.\d+)?', tr_text):
                try:
                    num_val = float(num_match.group())
                except ValueError:
                    continue
                for key, expected in numeric_milestones.items():
                    if key not in seen_keys and _numbers_match(expected, num_val):
                        matched.append((key, expected, num_val))
                        seen_keys.add(key)
            if matched:
                snippets.append(CandidateSnippet(
                    snippet=tr_text,
                    milestone_matches=matched,
                    tool_result_index=tr_idx,
                ))
            continue

        # Long result: per-milestone window extraction + frequency-based filtering
        for key, expected in numeric_milestones.items():
            # Collect all positions where this milestone value appears
            match_positions: List[Tuple[int, int, float]] = []
            for num_match in re.finditer(r'-?\d+(?:\.\d+)?', tr_text):
                try:
                    num_val = float(num_match.group())
                except ValueError:
                    continue
                if _numbers_match(expected, num_val):
                    match_positions.append((num_match.start(), num_match.end(), num_val))

            if not match_positions:
                continue

            value_freq = len(match_positions)

            # Build and merge overlapping windows
            raw_windows = [
                (max(0, start - context_chars), min(len(tr_text), end + context_chars), val)
                for start, end, val in match_positions
            ]
            raw_windows.sort()
            cur_start, cur_end, cur_val = raw_windows[0]
            merged_windows: List[Tuple[int, int, float]] = []
            for start, end, val in raw_windows[1:]:
                if start <= cur_end:
                    cur_end = max(cur_end, end)
                else:
                    merged_windows.append((cur_start, cur_end, cur_val))
                    cur_start, cur_end, cur_val = start, end, val
            merged_windows.append((cur_start, cur_end, cur_val))

            candidate_texts: List[Tuple[str, float]] = [
                (tr_text[s:e], v) for s, e, v in merged_windows
            ]

            if value_freq > HIGH_FREQ_THRESHOLD:
                # High-frequency value: require key component in snippet
                key_parts = [p.lower() for p in key.split('_') if p]
                filtered = [
                    (s, v) for s, v in candidate_texts
                    if any(part in s.lower() for part in key_parts)
                ]
                if not filtered:
                    continue  # no reliable evidence for this milestone in this tool result
                candidate_texts = random.sample(
                    filtered, min(MAX_SNIPPETS_WHEN_HIGH_FREQ, len(filtered))
                )

            for snippet_text, matched_val in candidate_texts:
                snippets.append(CandidateSnippet(
                    snippet=snippet_text,
                    milestone_matches=[(key, expected, matched_val)],
                    tool_result_index=tr_idx,
                ))

    return snippets


# ---------------------------------------------------------------------------
# GPR: Judge prompt construction
# ---------------------------------------------------------------------------

def build_gpr_judge_prompt(
    steps: List[AgentStep],
    milestones: Dict[str, Any],
    gold_steps: List[str],
    final_answer_correct: bool,
) -> str:
    """Build the LLM Judge prompt for GPR milestone evaluation.

    Constructs the prompt with:
    1. Gold reference steps and milestones
    2. Final answer correctness status
    3. Agent trajectory with assistant text + candidate snippets

    If the assembled prompt exceeds ARG_MAX_BYTES, falls back to a text-only
    trajectory (no tool-result snippets) to stay within the Linux ARG_MAX limit.
    """
    # --- Format gold steps ---
    steps_formatted = "\n".join(
        f"{i + 1}. {s}" for i, s in enumerate(gold_steps)
    )

    # --- Format milestones ---
    milestone_lines = []
    for i, (key, value) in enumerate(milestones.items()):
        milestone_lines.append(f"M{i + 1}. {key}: {value}")
    milestones_formatted = "\n".join(milestone_lines)

    # --- Extract numeric milestones for candidate search ---
    numeric_milestones = {
        k: float(v) for k, v in milestones.items() if _is_numeric(v)
    }

    # --- Final answer status ---
    final_answer_status = (
        "The agent's final answer is CORRECT."
        if final_answer_correct
        else "The agent's final answer is INCORRECT."
    )

    # --- Inner helpers ---
    def _format_trajectory(include_candidates: bool) -> str:
        parts: List[str] = []
        for step in steps:
            lines: List[str] = [f"### Step {step.index}"]

            if step.text:
                lines.append(f"Assistant: {step.text}")
            else:
                lines.append("Assistant: (no text)")

            if include_candidates:
                candidates = _extract_candidates_for_step(step, numeric_milestones)
                if candidates:
                    for c in candidates:
                        keys_str = ", ".join(
                            f"{k}≈{matched}" for k, _exp, matched in c.milestone_matches
                        )
                        lines.append(f"[Candidate: {keys_str}]")
                        lines.append(c.snippet)
                elif step.tool_results:
                    lines.append("(tool executed, no milestone candidates detected)")
            else:
                if step.tool_results:
                    lines.append("(tool executed, results omitted — prompt size limit)")

            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    def _assemble(trajectory: str) -> str:
        return f"""\
You are a milestone evaluator for an AI agent benchmark. Your task is to determine \
which milestones an agent achieved during its execution trajectory.

## Reference Solution Path

The following ordered steps describe the gold-standard approach to solving this task. \
Milestones are key intermediate results that should be produced along this path.

### Gold Steps (in order)
{steps_formatted}

### Milestones to Evaluate
{milestones_formatted}

## Agent Execution Trajectory

Below is a reconstruction of the agent's work, organized by step (assistant turn). \
For each step, "Assistant" is the agent's own text output. "Candidate" sections are \
excerpts from tool execution outputs where milestone-relevant values were detected \
by numeric matching. These candidates may or may not be true milestone achievements — \
you must verify the semantic context.

{trajectory}

## Evaluation Rules

1. **Direct evidence**: A milestone is achieved if the trajectory clearly shows the \
agent computed or obtained the expected value (or a value within 1% relative error) \
in the CORRECT semantic context. A number appearing in an unrelated context \
(e.g., a value for Province A matching a milestone defined for Province B) does NOT count.

2. **Temporal coupling inference**: Milestones follow a logical dependency chain as \
defined in the Gold Steps. If a downstream milestone is correctly achieved, its \
upstream dependencies can be inferred as achieved — even if they were not explicitly \
output. For example, if the agent correctly computed "ratio = A/B", then milestones \
for computing A and B can be inferred as achieved.

3. **Chain-break identification**: If the final answer is INCORRECT, identify the \
earliest milestone in the logical chain that was NOT achieved — this is the \
"break point" where the agent's reasoning diverged from the correct path.

4. **Different-but-valid paths**: The agent may use a different method than the gold \
steps. Judge milestone achievement based on whether the agent obtained the correct \
intermediate values, regardless of method.

## Output Format

Respond with ONLY a JSON object. No markdown fences, no extra text.

{{"milestones": [{{"key": "milestone key", "achieved": true, "evidence_type": "direct", "first_step": 4, "reason": "brief justification"}}, ...], "break_point": null, "chain_summary": "one-sentence summary"}}

Where:
- "achieved": true or false
- "evidence_type": "direct" (found in trajectory), "inferred" (implied by downstream achievement), or "final_answer" (implied by correct final answer)
- "first_step": the agent Step number where this milestone was first achieved (integer), or null if not achieved. For "inferred" milestones, use the step of the downstream milestone that implies it. For "final_answer" milestones, use the step of the agent's final answer.
- "break_point": null if all achieved, otherwise 0-based index of first unachieved milestone
- "chain_summary": where and why the chain broke, or "All milestones achieved" if none broke"""

    # --- Assemble with candidates; fall back to text-only if prompt is too large ---
    prompt = _assemble(_format_trajectory(include_candidates=True))
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes > ARG_MAX_BYTES:
        logger.warning(
            "GPR judge prompt is %d bytes, exceeds ARG_MAX (%d bytes); "
            "falling back to text-only trajectory",
            prompt_bytes, ARG_MAX_BYTES,
        )
        prompt = _assemble(_format_trajectory(include_candidates=False))

    return prompt


# ---------------------------------------------------------------------------
# GPR: Judge response parsing
# ---------------------------------------------------------------------------

@dataclass
class MilestoneResult:
    """Evaluation result for a single milestone."""
    key: str
    expected: Any
    achieved: bool
    evidence_type: str = ""   # "direct" | "inferred" | "final_answer"
    reason: str = ""
    first_step: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "key": self.key,
            "expected": self.expected,
            "achieved": self.achieved,
            "evidence_type": self.evidence_type,
            "reason": self.reason,
        }
        if self.first_step is not None:
            d["first_step"] = self.first_step
        return d


@dataclass
class GPRResult:
    """Result of the Goal Progress Rate metric."""
    gpr: float
    milestones_total: int
    milestones_achieved: int
    break_point: Optional[int]
    chain_summary: str
    details: List[MilestoneResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gpr": self.gpr,
            "milestones_total": self.milestones_total,
            "milestones_achieved": self.milestones_achieved,
            "break_point": self.break_point,
            "chain_summary": self.chain_summary,
            "details": [d.to_dict() for d in self.details],
        }


def _parse_json_from_text(raw_text: str) -> Dict[str, Any]:
    """Extract a JSON object from free-form text (handles markdown fences, etc.)."""
    # Try code blocks first
    code_block = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_text, re.DOTALL)
    if code_block:
        try:
            parsed = json.loads(code_block.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Find balanced-brace JSON candidates
    candidates: List[str] = []
    depth = 0
    current: List[str] = []
    for char in raw_text:
        if char == "{":
            if depth == 0:
                current = []
            depth += 1
        if depth > 0:
            current.append(char)
        if char == "}":
            depth -= 1
            if depth == 0 and current:
                candidates.append("".join(current))

    # Prefer the one with "milestones" key
    for c in reversed(candidates):
        try:
            parsed = json.loads(c)
            if isinstance(parsed, dict) and "milestones" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    # Fallback: any valid dict
    for c in reversed(candidates):
        try:
            parsed = json.loads(c)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    return {}


def parse_gpr_judge_response(
    raw_text: str,
    milestones: Dict[str, Any],
) -> GPRResult:
    """Parse the LLM Judge response into a GPRResult.

    If parsing fails, returns a GPRResult with all milestones marked unachieved.
    """
    milestone_keys = list(milestones.keys())
    n = len(milestone_keys)

    if not raw_text.strip():
        logger.warning("Empty judge response for GPR")
        return _fallback_gpr_result(milestones)

    parsed = _parse_json_from_text(raw_text)
    if not parsed or "milestones" not in parsed:
        logger.warning("Failed to parse GPR judge response")
        return _fallback_gpr_result(milestones)

    judge_milestones = parsed["milestones"]
    if not isinstance(judge_milestones, list):
        logger.warning("Judge 'milestones' is not a list")
        return _fallback_gpr_result(milestones)

    # Build a lookup from judge response by key
    judge_lookup: Dict[str, Dict[str, Any]] = {}
    for item in judge_milestones:
        if isinstance(item, dict) and "key" in item:
            judge_lookup[item["key"]] = item

    # Match judge results to our milestones (by key or by position)
    details: List[MilestoneResult] = []
    for i, key in enumerate(milestone_keys):
        expected = milestones[key]

        # Try key-based match first, then positional fallback
        judge_item = judge_lookup.get(key)
        if judge_item is None and i < len(judge_milestones):
            judge_item = judge_milestones[i]

        if judge_item and isinstance(judge_item, dict):
            achieved = bool(judge_item.get("achieved", False))
            evidence_type = str(judge_item.get("evidence_type", ""))
            reason = str(judge_item.get("reason", ""))
            raw_step = judge_item.get("first_step")
            try:
                first_step = int(raw_step) if raw_step is not None else None
            except (TypeError, ValueError):
                first_step = None
        else:
            achieved = False
            evidence_type = ""
            reason = "Not found in judge response"
            first_step = None

        details.append(MilestoneResult(
            key=key,
            expected=expected,
            achieved=achieved,
            evidence_type=evidence_type,
            reason=reason,
            first_step=first_step,
        ))

    achieved_count = sum(1 for d in details if d.achieved)
    gpr = achieved_count / n if n > 0 else 0.0

    break_point = parsed.get("break_point")
    if break_point is not None:
        try:
            break_point = int(break_point)
        except (TypeError, ValueError):
            break_point = None
    chain_summary = str(parsed.get("chain_summary", ""))

    return GPRResult(
        gpr=round(gpr, 4),
        milestones_total=n,
        milestones_achieved=achieved_count,
        break_point=break_point,
        chain_summary=chain_summary,
        details=details,
    )


def _fallback_gpr_result(milestones: Dict[str, Any]) -> GPRResult:
    """Return a GPRResult with all milestones marked as unachieved."""
    details = [
        MilestoneResult(
            key=key,
            expected=value,
            achieved=False,
            reason="Judge response could not be parsed",
        )
        for key, value in milestones.items()
    ]
    return GPRResult(
        gpr=0.0,
        milestones_total=len(milestones),
        milestones_achieved=0,
        break_point=0,
        chain_summary="Judge response could not be parsed",
        details=details,
    )


# ---------------------------------------------------------------------------
# Temporal Goal Progress Rate (TGPR) and Temporal Progress Efficiency (TPE)
# ---------------------------------------------------------------------------

DEFAULT_GAMMA = 0.9  # exponential decay factor


@dataclass
class TGPRResult:
    """Result of the Temporal Goal Progress Rate (TGPR) and Temporal Progress
    Efficiency (TPE) metrics. Both share the same per-milestone decay table;
    TGPR normalises by total milestones, TPE by achieved milestones (eval.tex)."""
    tgpr: float
    tpe: float
    gpr: float
    gamma: float
    s_gold: int
    milestones_total: int
    milestones_achieved: int
    details: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tgpr": self.tgpr,
            "tpe": self.tpe,
            "gpr": self.gpr,
            "gamma": self.gamma,
            "s_gold": self.s_gold,
            "milestones_total": self.milestones_total,
            "milestones_achieved": self.milestones_achieved,
            "details": self.details,
        }


def compute_tgpr(
    gpr_result: GPRResult,
    s_gold: int,
    gamma: float = DEFAULT_GAMMA,
) -> TGPRResult:
    """Compute Temporal Goal Progress Rate (TGPR) and Temporal Progress
    Efficiency (TPE).

    TGPR = (1/n_total)    * sum_i  I(m_i) * gamma^max(t_i - S_gold, 0)
    TPE  = (1/n_achieved) * sum_i  I(m_i) * gamma^max(t_i - S_gold, 0)
                                                   (per eval.tex)

    Uses S_gold (total gold-path steps) as a global baseline:
    - If the agent achieves a milestone within S_gold steps, no penalty.
    - If it takes more than S_gold steps, exponential decay kicks in.

    For unachieved milestones, the contribution is 0.
    Raises ValueError when the Judge marks a milestone achieved but
    omits first_step — TPE has no defensible fallback for that case
    (a decay=1 default would silently inflate the score).

    TPE differs from TGPR only by the denominator: it averages decay over
    *achieved* milestones, isolating timing from coverage. TPE = 0 when no
    milestones were achieved.
    """
    n = gpr_result.milestones_total
    if n == 0:
        return TGPRResult(
            tgpr=0.0, tpe=0.0, gpr=0.0, gamma=gamma, s_gold=s_gold,
            milestones_total=0, milestones_achieved=0, details=[],
        )

    details: List[Dict[str, Any]] = []
    tgpr_sum = 0.0
    decay_sum = 0.0
    achieved_count = 0

    for milestone in gpr_result.details:
        entry: Dict[str, Any] = {
            "key": milestone.key,
            "achieved": milestone.achieved,
            "t_agent": milestone.first_step,
            "s_gold": s_gold,
            "delay": None,
            "decay": None,
            "contribution": 0.0,
        }

        if milestone.achieved and milestone.first_step is not None:
            delay = max(milestone.first_step - s_gold, 0)
            decay = gamma ** delay
            contribution = (1.0 / n) * decay
            entry["delay"] = delay
            entry["decay"] = round(decay, 6)
            entry["contribution"] = round(contribution, 6)
            tgpr_sum += contribution
            decay_sum += decay
            achieved_count += 1
        elif milestone.achieved and milestone.first_step is None:
            raise ValueError(
                f"Milestone {milestone.key!r} marked achieved but the judge "
                "did not report first_step; refusing to compute TPE/TGPR "
                "with a fabricated decay value."
            )

        details.append(entry)

    tpe_value = decay_sum / achieved_count if achieved_count > 0 else 0.0

    return TGPRResult(
        tgpr=round(tgpr_sum, 4),
        tpe=round(tpe_value, 4),
        gpr=gpr_result.gpr,
        gamma=gamma,
        s_gold=s_gold,
        milestones_total=n,
        milestones_achieved=achieved_count,
        details=details,
    )
