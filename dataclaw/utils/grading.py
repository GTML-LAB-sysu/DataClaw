"""
LLM Judge grading engine for per-task container mode.

Runs the judge agent inside the same container where the task executed,
reusing the already-running OpenClaw gateway.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dataclaw.utils.docker_utils import (
    TMP_WORKSPACE,
    collect_transcript,
    detect_transcript_errors,
    resolve_qualified_model,
)

logger = logging.getLogger(__name__)

DEFAULT_JUDGE_MODEL = os.environ.get(
    "JUDGE_MODEL", "openrouter/anthropic/claude-opus-4.5"
)
MAX_JUDGE_PARSE_ATTEMPTS = 5
JUDGE_TIMEOUT_SECONDS = 180


@dataclass
class GradeResult:
    task_id: str
    score: float
    max_score: float
    grading_type: str
    breakdown: Dict[str, float]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "score": self.score,
            "max_score": self.max_score,
            "grading_type": self.grading_type,
            "breakdown": self.breakdown,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def grade_task(
    *,
    container_id: str,
    task_id: str,
    task_prompt: str,
    expected_behavior: str,
    grading_criteria: List[str],
    llm_judge_rubric: Optional[str],
    agent_transcript_path: Path,
    output_dir: Path,
    judge_model: str = DEFAULT_JUDGE_MODEL,
) -> GradeResult:
    """Grade a task using the LLM judge inside the task's container."""
    final_text = _final_assistant_text(agent_transcript_path)
    rubric = llm_judge_rubric or _format_grading_criteria(grading_criteria)
    base_prompt = _build_judge_prompt(task_prompt, expected_behavior, final_text, rubric)

    # Create judge agent inside the container
    qualified_judge = resolve_qualified_model(container_id, judge_model)
    agent_create = subprocess.run(
        ["docker", "exec", container_id, "openclaw", "agents", "add", "judge",
         "--model", qualified_judge, "--non-interactive",
         "--workspace", "/root/.openclaw/workspace"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if agent_create.returncode != 0:
        logger.warning(
            "[%s] Judge agent creation failed (exit=%s): %s",
            task_id, agent_create.returncode,
            (agent_create.stderr or agent_create.stdout or "").strip()[:500],
        )

    parsed: Dict[str, Any] = {"scores": {}, "total": None, "notes": ""}
    last_err: Optional[str] = None
    success = False

    for attempt in range(1, MAX_JUDGE_PARSE_ATTEMPTS + 1):
        if attempt > 1:
            # Clear previous judge sessions before retry
            subprocess.run(
                ["docker", "exec", container_id, "/bin/bash", "-c",
                 "rm -rf /root/.openclaw/agents/judge/sessions/*"],
                capture_output=True, text=True, encoding="utf-8",
            )

        # Enhance prompt only when the previous failure was a format issue
        if attempt > 1 and last_err and last_err.startswith("format"):
            prompt = (
                base_prompt
                + "\n\n---\nYour previous reply was not a valid scoring JSON with a numeric "
                "`total`. Reply with ONLY a single JSON object, no markdown fences, no other "
                "text, exactly this shape:\n"
                '{"scores": {"criterion_name": 0.0}, "total": 0.0, "notes": "brief justification"}\n'
            )
        else:
            prompt = base_prompt

        # L1: runtime (subprocess / timeout)
        try:
            _run_judge_in_container(container_id, prompt)
        except RuntimeError as exc:
            last_err = f"runtime: {exc}"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue

        transcript_path = collect_transcript(container_id, output_dir, agent_id="judge")

        # L2: transcript validity
        if not transcript_path.exists():
            last_err = "transcript: file missing"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue

        tr_err = detect_transcript_errors(transcript_path)
        if tr_err:
            last_err = f"transcript: {tr_err}"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue

        try:
            final_text = _final_assistant_text(transcript_path)
        except OSError as exc:
            last_err = f"transcript: read failed: {exc}"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue
        if not final_text:
            last_err = "transcript: empty assistant response"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue

        # L3: format (required fields present)
        try:
            raw_parsed = _parse_judge_response_from_file(transcript_path)
        except OSError as exc:
            last_err = f"transcript: read failed: {exc}"
            logger.warning("[%s] Judge attempt %d/%d failed — %s",
                           task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)
            continue
        parsed = _normalize_judge_response(raw_parsed)

        if _has_total_field(parsed):
            logger.info("[%s] Judge returned valid score on attempt %d", task_id, attempt)
            success = True
            break

        last_err = "format: missing or non-numeric total field"
        logger.warning("[%s] Judge attempt %d/%d failed — %s",
                       task_id, attempt, MAX_JUDGE_PARSE_ATTEMPTS, last_err)

    if not success:
        raise RuntimeError(
            f"Judge failed after {MAX_JUDGE_PARSE_ATTEMPTS} attempts: {last_err}"
        )

    breakdown = parsed.get("scores", {})
    total = parsed.get("total")
    notes = parsed.get("notes", "")

    return GradeResult(
        task_id=task_id,
        score=float(total) if total is not None else 0.0,
        max_score=1.0,
        grading_type="llm_judge",
        breakdown=_normalize_score_dict(breakdown),
        notes=str(notes) if notes is not None else "",
    )


# ---------------------------------------------------------------------------
# Container interaction
# ---------------------------------------------------------------------------

def _run_judge_in_container(container_id: str, message: str) -> None:
    """Send a message to the judge agent inside the container.

    Uses docker cp + file read to bypass Windows command-line length limits.
    Raises RuntimeError on docker cp failure, judge subprocess non-zero exit,
    or timeout — so callers can detect and retry.
    """
    fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(message)

        cp_result = subprocess.run(
            ["docker", "cp", tmp_path,
             f"{container_id}:/tmp/judge_prompt.txt"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if cp_result.returncode != 0:
            raise RuntimeError(
                f"docker cp failed (exit={cp_result.returncode}): "
                f"{(cp_result.stderr or '').strip()[:300]}"
            )

        bash_cmd = (
            f"prompt=$(cat /tmp/judge_prompt.txt) && "
            f"cd {TMP_WORKSPACE} && "
            f"openclaw agent --agent judge --session-id judge_chat "
            f"--message \"$prompt\""
        )
        try:
            result = subprocess.run(
                ["docker", "exec", container_id, "/bin/bash", "-c", bash_cmd],
                capture_output=True, text=True, encoding="utf-8",
                timeout=JUDGE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"judge timed out after {JUDGE_TIMEOUT_SECONDS}s"
            ) from exc

        if result.returncode != 0:
            stderr_snippet = (result.stderr or result.stdout or "").strip()[:300]
            raise RuntimeError(
                f"judge subprocess exit={result.returncode}: {stderr_snippet}"
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Transcript parsing
# ---------------------------------------------------------------------------

def _final_assistant_text(transcript_path: Path) -> str:
    """Extract text from the most recent assistant message that contains
    text content.

    Agents (especially tool-heavy ones) may have their last message be a
    pure toolCall with no text — particularly when interrupted mid-call by
    a timeout. In that case, fall back to the most recent assistant
    message that actually has text content so the judge still sees the
    agent's reasoning.
    """
    if not transcript_path.exists():
        return ""

    last_text_message: Optional[Dict[str, Any]] = None
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
        msg = entry.get("message", {})
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", []) or []
        has_text = any(
            isinstance(item, dict)
            and item.get("type") == "text"
            and item.get("text")
            for item in content
        )
        if has_text:
            last_text_message = msg

    if last_text_message is None:
        return ""

    parts: List[str] = []
    for item in last_text_message.get("content", []) or []:
        if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
            parts.append(item["text"])
    return "\n".join(parts).strip()


def _parse_judge_response_from_file(transcript_path: Path) -> Dict[str, Any]:
    """Parse the judge's JSON response from transcript JSONL."""
    if not transcript_path.exists():
        return {}

    content_chunks: List[str] = []
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
        msg = entry.get("message", {})
        if msg.get("role") != "assistant":
            continue
        for item in msg.get("content", []):
            if item.get("type") == "text":
                content_chunks.append(item.get("text", ""))

    raw_text = "\n".join(content_chunks).strip()
    if not raw_text:
        return {}

    return _parse_json_from_text(raw_text)


def _parse_json_from_text(raw_text: str) -> Dict[str, Any]:
    """Extract a JSON object from free-form text."""
    # Try code blocks first
    code_block_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
    if code_block_match:
        try:
            parsed = json.loads(code_block_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Find balanced-brace JSON candidates
    json_candidates: List[str] = []
    brace_depth = 0
    current_json: List[str] = []
    for char in raw_text:
        if char == "{":
            if brace_depth == 0:
                current_json = []
            brace_depth += 1
        if brace_depth > 0:
            current_json.append(char)
        if char == "}":
            brace_depth -= 1
            if brace_depth == 0 and current_json:
                json_candidates.append("".join(current_json))

    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "scores" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # Fallback: regex for "total: 0.XX"
    score_pattern = re.search(
        r"(?:total|overall|final)\s*(?:score)?[:\s]*(0\.\d+|1\.0+)",
        raw_text,
        re.IGNORECASE,
    )
    if score_pattern:
        try:
            total = float(score_pattern.group(1))
            if 0.0 <= total <= 1.0:
                return {"scores": {}, "total": total, "notes": "Score extracted from prose"}
        except ValueError:
            pass

    logger.warning("Failed to parse judge JSON response")
    return {}


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _has_total_field(normalized: Dict[str, Any]) -> bool:
    """Format check: total field exists and is a numeric value (range not enforced)."""
    if not isinstance(normalized, dict):
        return False
    total = normalized.get("total")
    if total is None:
        return False
    try:
        t = float(total)
    except (TypeError, ValueError):
        return False
    if t != t:  # NaN
        return False
    return True


def _normalize_judge_response(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize judge response to {scores, total, notes}."""
    result: Dict[str, Any] = {"scores": {}, "total": None, "notes": ""}

    if "scores" in parsed:
        scores_data = parsed["scores"]
        if isinstance(scores_data, dict):
            for key, value in scores_data.items():
                if isinstance(value, dict) and "score" in value:
                    try:
                        result["scores"][key] = float(value["score"])
                    except (TypeError, ValueError):
                        pass
                elif isinstance(value, (int, float)):
                    result["scores"][key] = value
    elif "criteria_scores" in parsed:
        criteria = parsed["criteria_scores"]
        if isinstance(criteria, dict):
            for key, value in criteria.items():
                if isinstance(value, dict) and "score" in value:
                    result["scores"][key] = value["score"]
                elif isinstance(value, (int, float)):
                    result["scores"][key] = value

    if "total" in parsed and parsed["total"] is not None:
        try:
            result["total"] = float(parsed["total"])
        except (TypeError, ValueError):
            pass
    elif "score" in parsed and isinstance(parsed["score"], (int, float)):
        result["total"] = float(parsed["score"])
    elif "overall_score" in parsed and isinstance(parsed["overall_score"], (int, float)):
        result["total"] = float(parsed["overall_score"])
    elif result["scores"]:
        values = [v for v in result["scores"].values() if isinstance(v, (int, float))]
        if values:
            result["total"] = sum(values) / len(values)

    if "notes" in parsed:
        result["notes"] = str(parsed["notes"])
    elif "justification" in parsed:
        result["notes"] = str(parsed["justification"])
    elif "reasoning" in parsed:
        result["notes"] = str(parsed["reasoning"])

    return result


def _normalize_score_dict(scores: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key, value in scores.items():
        try:
            normalized[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return normalized


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def _format_grading_criteria(criteria: List[str]) -> str:
    if not criteria:
        return ""
    return "\n".join(f"- {c}" for c in criteria)


def _build_judge_prompt(
    task_prompt: str,
    expected_behavior: str,
    agent_final_text: str,
    rubric: str,
) -> str:
    return (
        "You are a grading function. Your ONLY job is to output a single JSON object.\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT use any tools (no Read, Write, exec, or any other tool calls)\n"
        "- Do NOT create files or run commands\n"
        "- Do NOT write any prose, explanation, or commentary outside the JSON\n"
        "- Respond with ONLY a JSON object — nothing else\n\n"
        "Be a strict evaluator. Judge the final assistant message against the task and rubric.\n\n"
        "## Task\n"
        f"{task_prompt}\n\n"
        "## Expected Behavior\n"
        f"{expected_behavior}\n\n"
        "## Agent final answer\n"
        f"{agent_final_text}\n\n"
        "## Grading Rubric\n"
        f"{rubric}\n\n"
        "Score each criterion from 0.0 to 1.0.\n\n"
        "Respond with ONLY this JSON structure (no markdown, no code fences, no extra text):\n"
        '{"scores": {"criterion_name": 0.0}, "total": 0.0, "notes": "brief justification"}'
    )
