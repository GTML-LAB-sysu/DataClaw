"""
DataClaw — Host-side benchmark orchestrator.

Runs each task in an isolated Docker container. The host manages container
lifecycle, workspace injection, agent execution, LLM-judge grading, and
result collection.

Usage:
    python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6
    python dataclaw/eval/run_batch.py --model ... --suite task_001,task_002
    python dataclaw/eval/run_batch.py --model ... --parallel 4
    python dataclaw/eval/run_batch.py --task tasks/task_001_xxx.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dataclaw.lib_tasks import Task, TaskLoader
from dataclaw.utils.docker_utils import (
    JUDGE_CUSTOM_API_KEY,
    JUDGE_CUSTOM_BASE_URL,
    JUDGE_CUSTOM_MODEL_ID,
    close_proc_log,
    collect_output,
    collect_transcript,
    detect_transcript_errors,
    extract_usage_from_jsonl,
    onboard_openclaw,
    register_custom_provider,
    remove_container,
    set_model,
    setup_workspace,
    start_container,
    start_gateway,
)
from dataclaw.utils.grading import GradeResult, grade_task, _run_judge_in_container
from dataclaw.utils.process_grading import (
    parse_trajectory,
    compute_efficiency,
    build_gpr_judge_prompt,
    parse_gpr_judge_response,
    compute_tgpr,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = ROOT_DIR / os.environ.get("TASKS_SUBDIR", "tasks")
ASSETS_DIR = ROOT_DIR / "assets"
OUTPUT_DIR = ROOT_DIR / os.environ.get("OUTPUT_SUBDIR", "output")

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "")
DEFAULT_PARALLEL = int(os.environ.get("DEFAULT_PARALLEL", "1"))
DEFAULT_JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openrouter/anthropic/claude-opus-4.5")
TIMEOUT_MULTIPLIER = float(os.environ.get("BENCHMARK_TIMEOUT_MULTIPLIER", "1.0"))
BENCHMARK_RUNS = int(os.environ.get("BENCHMARK_RUNS", "1"))
TMP_WORKSPACE = os.environ.get("TMP_WORKSPACE", "/tmp_workspace")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify_model(model_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9.\-_]", "_", model_id.rsplit("/", 1)[-1])


def _get_git_version() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, encoding="utf-8", timeout=2, check=False, cwd=ROOT_DIR,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""


def _validate_openrouter_model(model_id: str) -> bool:
    """Basic check that the model exists on OpenRouter (skippable)."""
    if os.environ.get("DATACLAW_SKIP_OPENROUTER_MODEL_VALIDATION", "").strip().lower() in (
        "1", "true", "yes",
    ):
        return True
    if os.environ.get("OPENCLAW_CUSTOM_BASE_URL", "").strip():
        return True

    bare = model_id
    if bare.startswith("openrouter/"):
        bare = bare[len("openrouter/"):]
    if bare.startswith("bailian/") or "/" not in bare:
        return True
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set, skipping model validation")
        return True

    from urllib import error, request as urlreq
    encoded = bare.replace("/", "%2F")
    url = f"https://openrouter.ai/api/v1/models/{encoded}"
    req = urlreq.Request(url, headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/GTMLLab/DataClaw",
        "X-Title": "DataClaw",
    }, method="GET")
    try:
        with urlreq.urlopen(req, timeout=10):
            return True
    except error.HTTPError as exc:
        if exc.code == 404:
            logger.error("Model '%s' not found on OpenRouter", bare)
            return False
        return True
    except (error.URLError, OSError):
        return True


# ---------------------------------------------------------------------------
# Progress file helpers (for --resume support)
# ---------------------------------------------------------------------------

_progress_lock = threading.Lock()


def _progress_path(model_slug: str) -> Path:
    return OUTPUT_DIR / f"progress_{model_slug}.json"


def _load_progress(path: Path) -> Optional[Dict[str, Any]]:
    """Load progress file, returning the parsed dict or None."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read progress file %s: %s", path, exc)
        return None


def _save_progress(
    path: Path,
    model: str,
    suite: str,
    runs: int,
    completed: List[Dict[str, Any]],
) -> None:
    """Atomically write progress file (temp file + os.replace)."""
    data = {
        "model": model,
        "suite": suite,
        "runs": runs,
        "completed": completed,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(str(tmp_path), str(path))


# ---------------------------------------------------------------------------
# Process grading helpers
# ---------------------------------------------------------------------------

PROCESS_JUDGE_TIMEOUT_SECONDS = 180


def _load_gold_process_data(task: Task) -> Optional[Dict[str, Any]]:
    """Load gold process fields (steps, milestone, steps_num) from qa_gold."""
    gold_file = task.frontmatter.get("gold_file", "")
    if not gold_file:
        return None
    gold_path = ASSETS_DIR / gold_file
    if not gold_path.exists():
        logger.warning("Gold file not found: %s", gold_path)
        return None
    try:
        data = json.loads(gold_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read gold file %s: %s", gold_path, exc)
        return None
    if not data.get("milestone") or not data.get("steps"):
        return None
    return data


GPR_MAX_ATTEMPTS = 5


def _extract_assistant_text(transcript_path: Path) -> str:
    """Concatenate all assistant text content from a transcript JSONL.

    Returns empty string on missing file or read error (callers treat
    empty result as an L2 failure).
    """
    if not transcript_path.exists():
        return ""
    try:
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    out = ""
    for line in text.splitlines():
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
        for item in msg.get("content", []) or []:
            if isinstance(item, dict) and item.get("type") == "text":
                out += item.get("text", "") or ""
    return out


def _run_process_grading(
    *,
    container_id: str,
    task_id: str,
    transcript_path: Path,
    gold_data: Dict[str, Any],
    outcome_score: float,
    output_dir: Path,
) -> Dict[str, Any]:
    """Run process grading conditional on outcome score.

    Full-score tasks (score >= 1.0) get only Efficiency. Incorrect tasks
    (score < 1.0) get only GPR (via LLM Judge, with GPR_MAX_ATTEMPTS retries
    across three layers: runtime / transcript / parse), TGPR and TPE.
    Raises RuntimeError if the GPR judge fails every attempt.
    """
    milestones = gold_data.get("milestone", {})
    gold_steps = gold_data.get("steps", [])
    steps_num = gold_data.get("steps_num", len(gold_steps))

    if outcome_score >= 1.0:
        # --- Full score: Efficiency only ---
        steps = parse_trajectory(transcript_path)
        eff = compute_efficiency(steps, steps_num)
        process_scores: Dict[str, Any] = {"efficiency": eff.to_dict()}
        (output_dir / "process_score.json").write_text(
            json.dumps(process_scores, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info(
            "[%s] Process: efficiency=%.2f (full score, GPR/TGPR/TPE skipped)",
            task_id,
            eff.efficiency if eff.efficiency is not None else 0.0,
        )
        return process_scores

    # --- Incorrect: GPR + TGPR + TPE only ---
    steps = parse_trajectory(transcript_path)
    gpr_prompt = build_gpr_judge_prompt(
        steps=steps,
        milestones=milestones,
        gold_steps=gold_steps,
        final_answer_correct=False,
    )

    gpr_result = None
    last_err: Optional[str] = None

    for attempt in range(1, GPR_MAX_ATTEMPTS + 1):
        # Clear previous judge sessions before each attempt
        subprocess.run(
            ["docker", "exec", container_id, "/bin/bash", "-c",
             "rm -rf /root/.openclaw/agents/judge/sessions/*"],
            capture_output=True, text=True, encoding="utf-8",
        )

        # L1: runtime
        try:
            _run_judge_in_container(container_id, gpr_prompt)
        except RuntimeError as exc:
            last_err = f"runtime: {exc}"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        gpr_transcript = collect_transcript(
            container_id, output_dir, agent_id="judge",
            output_filename="judge_process_chat.jsonl",
        )

        # L2: transcript validity
        if not gpr_transcript.exists():
            last_err = "transcript: file missing"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        tr_err = detect_transcript_errors(gpr_transcript)
        if tr_err:
            last_err = f"transcript: {tr_err}"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        gpr_raw_text = _extract_assistant_text(gpr_transcript)
        if not gpr_raw_text.strip():
            last_err = "transcript: empty assistant response"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        # L3: format — parse_gpr_judge_response falls back to a sentinel
        # GPRResult when required fields are missing; detect it explicitly.
        try:
            parsed_gpr = parse_gpr_judge_response(gpr_raw_text, milestones)
        except Exception as exc:
            last_err = f"format: parse failed: {exc}"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        if "could not be parsed" in (parsed_gpr.chain_summary or ""):
            last_err = "format: judge response missing required fields (milestones)"
            logger.warning("[%s] GPR attempt %d/%d failed — %s",
                           task_id, attempt, GPR_MAX_ATTEMPTS, last_err)
            continue

        gpr_result = parsed_gpr
        logger.info("[%s] GPR judge succeeded on attempt %d", task_id, attempt)
        break

    if gpr_result is None:
        raise RuntimeError(
            f"GPR judge failed after {GPR_MAX_ATTEMPTS} attempts: {last_err}"
        )

    tgpr_result = compute_tgpr(gpr_result, s_gold=steps_num)

    process_scores = {
        "gpr": gpr_result.to_dict(),
        "tgpr": tgpr_result.to_dict(),
    }
    (output_dir / "process_score.json").write_text(
        json.dumps(process_scores, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(
        "[%s] Process: GPR=%.2f, TGPR=%.2f, TPE=%.2f (incorrect, efficiency skipped)",
        task_id,
        gpr_result.gpr,
        tgpr_result.tgpr,
        tgpr_result.tpe,
    )
    return process_scores


# ---------------------------------------------------------------------------
# Single-task execution
# ---------------------------------------------------------------------------

def run_single_task(
    task: Task,
    model: str,
    judge_model: str,
    timeout_multiplier: float,
) -> Dict[str, Any]:
    """Execute a single task in an isolated container. Thread-safe."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_id = uuid.uuid4().hex[:6]
    short_model = _slugify_model(model)
    suffix = f"{short_model}_{timestamp}_{run_id}"
    container_id = f"{task.task_id}_{suffix}"

    # Truncate container name to Docker's 128-char limit
    if len(container_id) > 128:
        container_id = container_id[:128]

    output_dir = OUTPUT_DIR / task.task_id / suffix
    output_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "task_id": task.task_id,
        "model": model,
        "scores": {},
        "grade": None,
        "process_grade": None,
        "usage": {},
        "error": None,
        "elapsed_time": 0.0,
    }
    errors: List[str] = []

    gateway_proc = None
    agent_proc = None
    timeout_seconds = task.timeout_seconds * timeout_multiplier
    start_time = time.perf_counter()

    try:
        # 1. Start container
        start_container(container_id)

        # 2. Inject workspace files
        if task.workspace_files:
            setup_workspace(container_id, task.workspace_files, ASSETS_DIR)

        # 3. Onboard OpenClaw
        onboard_openclaw(container_id)

        # 3.5 Register judge provider if using a separate endpoint
        if JUDGE_CUSTOM_BASE_URL and JUDGE_CUSTOM_API_KEY:
            register_custom_provider(
                container_id,
                JUDGE_CUSTOM_BASE_URL,
                JUDGE_CUSTOM_API_KEY,
                JUDGE_CUSTOM_MODEL_ID or judge_model,
            )

        # 4. Start gateway
        gateway_proc = start_gateway(container_id, output_dir / "gateway.log")

        # 5. Set model
        set_model(container_id, model)

        # 6. Run agent — use docker cp to bypass Windows cmd-line limit
        fd, tmp_path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(task.prompt)
        subprocess.run(
            ["docker", "cp", tmp_path,
             f"{container_id}:/tmp/agent_prompt.txt"],
            capture_output=True, text=True, encoding="utf-8",
        )
        os.unlink(tmp_path)

        agent_bash = (
            f"prompt=$(cat /tmp/agent_prompt.txt) && "
            f"cd {TMP_WORKSPACE} && "
            f"openclaw agent --session-id chat "
            f"--timeout {int(timeout_seconds)} --message \"$prompt\""
        )

        log_file = (output_dir / "agent.log").open("w", encoding="utf-8")
        agent_proc = subprocess.Popen(
            ["docker", "exec", container_id, "/bin/bash", "-c", agent_bash],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
        agent_proc._log_file = log_file  # type: ignore[attr-defined]

        logger.info("[%s] Agent running (timeout=%ds)", container_id, int(timeout_seconds))
        try:
            agent_proc.wait(timeout=timeout_seconds)
            elapsed = time.perf_counter() - start_time
            logger.info("[%s] Agent finished (%.1fs, exit=%s)",
                        container_id, elapsed, agent_proc.returncode)
        except subprocess.TimeoutExpired:
            elapsed = timeout_seconds
            logger.info("[%s] Agent timed out", container_id)
            agent_proc.kill()
            agent_proc.wait()

        # 7. Collect transcript and compute usage
        transcript_path = collect_transcript(container_id, output_dir)
        usage = extract_usage_from_jsonl(transcript_path)
        usage["elapsed_time"] = round(time.perf_counter() - start_time, 2)
        result["usage"] = usage
        (output_dir / "usage.json").write_text(
            json.dumps(usage, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 7.5 Check for API errors in transcript BEFORE grading
        transcript_err = detect_transcript_errors(transcript_path)
        if transcript_err:
            logger.warning("[%s] %s — skipping judge", container_id, transcript_err)
            errors.append(transcript_err)
        else:
            # 8. LLM Judge grading
            grade = None
            try:
                grade = grade_task(
                    container_id=container_id,
                    task_id=task.task_id,
                    task_prompt=task.prompt,
                    expected_behavior=task.expected_behavior,
                    grading_criteria=task.grading_criteria,
                    llm_judge_rubric=task.llm_judge_rubric,
                    agent_transcript_path=transcript_path,
                    output_dir=output_dir,
                    judge_model=judge_model,
                )
                result["grade"] = grade.to_dict()
                result["scores"] = grade.breakdown
                score_path = output_dir / "score.json"
                score_path.write_text(
                    json.dumps(grade.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
                )
                logger.info("[%s] Grade: %.2f/%.2f", container_id, grade.score, grade.max_score)
            except Exception as exc:
                logger.error("[%s] Grading failed: %s", container_id, exc)
                errors.append(f"Grading failed: {exc}")

            # 8.5 Process grading — only if step 8 succeeded
            if not errors:
                try:
                    gold_data = _load_gold_process_data(task)
                    if gold_data is not None:
                        outcome_score = grade.score if grade else 0.0
                        process_scores = _run_process_grading(
                            container_id=container_id,
                            task_id=task.task_id,
                            transcript_path=transcript_path,
                            gold_data=gold_data,
                            outcome_score=outcome_score,
                            output_dir=output_dir,
                        )
                        result["process_grade"] = process_scores
                    else:
                        logger.info("[%s] No process annotations, skipping process grading", container_id)
                except Exception as exc:
                    logger.error("[%s] Process grading failed: %s", container_id, exc)
                    errors.append(f"Process grading failed: {exc}")

        # 9. Collect task output (always attempt — preserve artifacts for debugging)
        try:
            collect_output(container_id, output_dir)
        except Exception as exc:
            logger.warning("[%s] Output collection failed: %s", container_id, exc)
            errors.append(f"Output collection failed: {exc}")

    except Exception as exc:
        logger.error("[%s] Execution error: %s", container_id, exc)
        errors.append(f"Execution error: {exc}")

    finally:
        result["elapsed_time"] = round(time.perf_counter() - start_time, 2)
        if errors:
            result["error"] = "; ".join(errors)

        if gateway_proc is not None:
            try:
                gateway_proc.terminate()
            except Exception:
                pass
        for proc in [gateway_proc, agent_proc]:
            if proc is not None:
                try:
                    close_proc_log(proc)
                except Exception:
                    pass

        remove_container(container_id)
        logger.info("[%s] Container cleaned up", container_id)

    return result


# ---------------------------------------------------------------------------
# Summary & reporting
# ---------------------------------------------------------------------------

def _print_summary(results: List[Dict[str, Any]], model_name: str) -> None:
    print(f"\n{'#' * 60}")
    print(f"  Summary Report — {model_name}")
    print(f"{'#' * 60}")

    scored = 0
    total_score = 0.0
    for r in results:
        grade = r.get("grade")
        if r.get("error") or not grade:
            print(f"  X {r['task_id']}: {r.get('error', 'no grade')}")
            continue
        scored += 1
        total_score += grade.get("score", 0.0)
        pct = grade["score"] / grade["max_score"] * 100 if grade["max_score"] > 0 else 0
        print(f"  + {r['task_id']}: {grade['score']:.2f}/{grade['max_score']:.2f} ({pct:.0f}%)")

    error_count = sum(1 for r in results if r.get("error"))
    if scored:
        avg = total_score / scored
        print(f"\n  Scored: {scored}/{len(results)}  Average: {avg:.4f}")
        if error_count:
            print(f"  Errors: {error_count} task(s) skipped due to API errors")
    else:
        print("\n  No tasks scored successfully")
        if error_count:
            print(f"  Errors: {error_count} task(s) skipped due to API errors")

    valid = [r for r in results if not r.get("error")]
    total_out_tok = sum(r.get("usage", {}).get("output_tokens", 0) or 0 for r in valid)
    total_cost = sum(r.get("usage", {}).get("cost_usd", 0.0) or 0.0 for r in valid)
    print(f"  Total output tokens: {total_out_tok}  Total cost: ${total_cost:.4f}")

    # Process metrics summary — exclude error tasks
    proc = [
        r["process_grade"] for r in results
        if r.get("process_grade") and not r.get("error")
    ]
    if proc:
        eff_vals = [p["efficiency"]["efficiency"] for p in proc if p.get("efficiency", {}).get("efficiency") is not None]
        gpr_vals = [p["gpr"]["gpr"] for p in proc if "gpr" in p]
        tgpr_vals = [p["tgpr"]["tgpr"] for p in proc if "tgpr" in p]
        # TPE is added to the same TGPRResult dict; older runs may lack the key.
        tpe_vals = [p["tgpr"]["tpe"] for p in proc if "tgpr" in p and "tpe" in p["tgpr"]]
        print(f"\n  Process metrics ({len(proc)} tasks):")
        if eff_vals:
            print(f"    Avg Efficiency: {sum(eff_vals)/len(eff_vals):.4f}")
        if gpr_vals:
            print(f"    Avg GPR:        {sum(gpr_vals)/len(gpr_vals):.4f}")
        if tgpr_vals:
            print(f"    Avg TGPR:       {sum(tgpr_vals)/len(tgpr_vals):.4f}")
        if tpe_vals:
            print(f"    Avg TPE:        {sum(tpe_vals)/len(tpe_vals):.4f}")

    print("#" * 60)

    # Errored tasks — listed together for easy review
    errored = [r for r in results if r.get("error")]
    if errored:
        print(f"\n{'#' * 60}")
        print(f"  Errored Tasks ({len(errored)})")
        print(f"{'#' * 60}")
        for r in errored:
            print(f"  X {r['task_id']}: {r.get('error')}")
        print()
        print("  -> Run with --resume to retry these tasks")
        print("#" * 60)


def _write_global_summary(
    results: List[Dict[str, Any]],
    model: str,
    model_slug: str,
    suite: str,
    runs_per_task: int,
    task_objects: Optional[List[Task]] = None,
) -> Path:
    task_meta_map: Dict[str, Dict[str, Any]] = {}
    if task_objects:
        for t in task_objects:
            task_meta_map[t.task_id] = t.frontmatter

    aggregate: Dict[str, Any] = {
        "model": model,
        "benchmark_version": _get_git_version(),
        "timestamp": time.time(),
        "suite": suite,
        "runs_per_task": runs_per_task,
        "tasks": [],
    }

    agg_total_tokens = 0
    agg_total_cost = 0.0
    agg_total_requests = 0

    for r in results:
        grade = r.get("grade")
        usage = r.get("usage", {})
        score = grade.get("score", 0.0) if grade else 0.0
        elapsed = r.get("elapsed_time", 0.0)

        # Only count tokens/cost/requests from non-error tasks
        if not r.get("error"):
            agg_total_tokens += usage.get("total_tokens", 0) or 0
            agg_total_cost += usage.get("cost_usd", 0.0) or 0.0
            agg_total_requests += usage.get("request_count", 0) or 0

        entry: Dict[str, Any] = {
            "task_id": r["task_id"],
            "frontmatter": task_meta_map.get(r["task_id"], {}),
            "grade": grade,
            "process_grade": r.get("process_grade"),
            "grading": {"mean": score},
            "usage": usage,
            "error": r.get("error"),
            "elapsed_time": elapsed,
            "execution_time": elapsed,
        }
        aggregate["tasks"].append(entry)

    # Compute global score — exclude error tasks
    valid_results = [r for r in results if not r.get("error")]
    error_count = sum(1 for r in results if r.get("error"))
    grades = [r["grade"] for r in valid_results if r.get("grade")]
    if grades:
        total_score = sum(g["score"] for g in grades)
        max_score = sum(g["max_score"] for g in grades)
        overall = round(total_score / max_score, 4) if max_score > 0 else 0.0
        aggregate["overall_score"] = overall
        aggregate["total_score"] = total_score
        aggregate["max_score"] = max_score
    else:
        overall = 0.0
        aggregate["overall_score"] = 0
    aggregate["error_count"] = error_count
    aggregate["evaluated_count"] = len(results) - error_count

    aggregate["efficiency"] = {
        "total_tokens": agg_total_tokens,
        "total_cost_usd": round(agg_total_cost, 6),
        "total_requests": agg_total_requests,
    }

    # Aggregate process metrics — exclude error tasks
    process_results = [
        r["process_grade"] for r in results
        if r.get("process_grade") is not None and not r.get("error")
    ]
    if process_results:
        eff_values = [
            p["efficiency"]["efficiency"]
            for p in process_results
            if p.get("efficiency", {}).get("efficiency") is not None
        ]
        gpr_values = [p["gpr"]["gpr"] for p in process_results if "gpr" in p]
        tgpr_values = [p["tgpr"]["tgpr"] for p in process_results if "tgpr" in p]
        aggregate["process_metrics"] = {
            "tasks_with_process": len(process_results),
            "avg_efficiency": round(sum(eff_values) / len(eff_values), 4) if eff_values else None,
            "avg_gpr": round(sum(gpr_values) / len(gpr_values), 4) if gpr_values else None,
            "avg_tgpr": round(sum(tgpr_values) / len(tgpr_values), 4) if tgpr_values else None,
        }

    summary_path = OUTPUT_DIR / f"summary_{model_slug}.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary_path


# ---------------------------------------------------------------------------
# CLI & main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="DataClaw — per-task container benchmark orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tasks
  python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6

  # Run specific tasks
  python dataclaw/eval/run_batch.py --model ... --suite task_001,task_002

  # Run with parallelism
  python dataclaw/eval/run_batch.py --model ... --parallel 4

  # Run a single task file
  python dataclaw/eval/run_batch.py --task tasks/task_001_xxx.md

  # Resume an interrupted run
  python dataclaw/eval/run_batch.py --model ... --suite all --resume
""",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--task", "-t", help="Path to a single task.md file")
    mode.add_argument(
        "--suite", "-s",
        default="all",
        help='Tasks to run: "all" or comma-separated task IDs (default: all)',
    )

    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Model identifier (default: {DEFAULT_MODEL or 'from .env'})",
    )
    parser.add_argument(
        "--judge",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model identifier (default: {DEFAULT_JUDGE_MODEL})",
    )
    parser.add_argument(
        "--parallel", "-p",
        type=int,
        default=DEFAULT_PARALLEL,
        metavar="N",
        help=f"Number of parallel containers (default: {DEFAULT_PARALLEL})",
    )
    parser.add_argument(
        "--timeout-multiplier",
        type=float,
        default=TIMEOUT_MULTIPLIER,
        help=f"Scale all task timeouts (default: {TIMEOUT_MULTIPLIER})",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=BENCHMARK_RUNS,
        help=f"Number of runs per task (default: {BENCHMARK_RUNS})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last interrupted run (skip completed tasks)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if not args.model:
        logger.error("--model is required (or set DEFAULT_MODEL in .env)")
        sys.exit(1)

    # Validate model
    if not _validate_openrouter_model(args.model):
        sys.exit(1)

    logger.info("DataClaw — per-task container benchmark")
    logger.info("Model: %s | Judge: %s | Parallel: %d", args.model, args.judge, args.parallel)

    # Load tasks
    if args.task:
        task_file = Path(args.task)
        if not task_file.exists():
            logger.error("File not found: %s", task_file)
            sys.exit(1)
        loader = TaskLoader(task_file.parent)
        task = loader.load_task(task_file)
        tasks = [task]
        suite_label = task.task_id
    else:
        if not TASKS_DIR.exists():
            logger.error("Tasks directory not found: %s", TASKS_DIR)
            sys.exit(1)
        loader = TaskLoader(TASKS_DIR)
        all_tasks = loader.load_all_tasks()
        if args.suite == "all":
            tasks = all_tasks
            suite_label = "all"
        else:
            requested = {tid.strip() for tid in args.suite.split(",") if tid.strip()}
            known = {t.task_id for t in all_tasks}
            unknown = requested - known
            if unknown:
                logger.error("Unknown task IDs: %s", ", ".join(sorted(unknown)))
                sys.exit(1)
            tasks = [t for t in all_tasks if t.task_id in requested]
            suite_label = args.suite

    if not tasks:
        logger.error("No tasks to run")
        sys.exit(1)

    logger.info("Tasks: %d | Runs per task: %d", len(tasks), args.runs)

    # Execute
    all_results: List[Dict[str, Any]] = []
    model_slug = _slugify_model(args.model)
    prog_path = _progress_path(model_slug)

    # --resume: load previous progress and validate parameters
    completed_keys: set = set()
    progress_entries: List[Dict[str, Any]] = []

    if args.resume:
        prog_data = _load_progress(prog_path)
        if prog_data is not None:
            mismatches = []
            if prog_data.get("model") != args.model:
                mismatches.append(
                    f"model (progress={prog_data.get('model')}, current={args.model})"
                )
            if prog_data.get("suite") != suite_label:
                mismatches.append(
                    f"suite (progress={prog_data.get('suite')}, current={suite_label})"
                )
            if prog_data.get("runs") != args.runs:
                mismatches.append(
                    f"runs (progress={prog_data.get('runs')}, current={args.runs})"
                )
            if mismatches:
                logger.error(
                    "Resume failed: parameter mismatch — %s. "
                    "Use the same parameters as the original run, or remove %s to start fresh.",
                    "; ".join(mismatches), prog_path,
                )
                sys.exit(1)

            for entry in prog_data.get("completed", []):
                completed_keys.add((entry["task_id"], entry["run_index"]))
                all_results.append(entry["result"])
                progress_entries.append(entry)
            logger.info("Resuming: %d tasks already completed", len(completed_keys))
        else:
            logger.warning(
                "No progress file found for model '%s', starting from scratch",
                args.model,
            )

    for run_index in range(args.runs):
        if args.runs > 1:
            logger.info("=== Run %d/%d ===", run_index + 1, args.runs)

        pending_tasks = [
            t for t in tasks if (t.task_id, run_index) not in completed_keys
        ]
        if not pending_tasks:
            logger.info("All tasks in run %d already completed, skipping", run_index + 1)
            continue
        if completed_keys:
            skipped = len(tasks) - len(pending_tasks)
            if skipped:
                logger.info(
                    "Skipping %d completed task(s), running %d remaining",
                    skipped, len(pending_tasks),
                )

        if args.parallel <= 1:
            for i, task in enumerate(pending_tasks, 1):
                logger.info("--- Task %d/%d: %s ---", i, len(pending_tasks), task.task_id)
                result = run_single_task(
                    task, args.model, args.judge, args.timeout_multiplier,
                )
                all_results.append(result)
                if result.get("error"):
                    logger.warning(
                        "[%s] Skipping progress save (error: %s) — will retry on resume",
                        task.task_id, result["error"],
                    )
                else:
                    with _progress_lock:
                        progress_entries.append({
                            "task_id": task.task_id,
                            "run_index": run_index,
                            "result": result,
                        })
                        _save_progress(
                            prog_path, args.model, suite_label, args.runs,
                            progress_entries,
                        )
        else:
            with ThreadPoolExecutor(max_workers=args.parallel) as pool:
                futures = {
                    pool.submit(
                        run_single_task,
                        task, args.model, args.judge, args.timeout_multiplier,
                    ): (task.task_id, run_index)
                    for task in pending_tasks
                }
                for future in as_completed(futures):
                    tid, ridx = futures[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        logger.error("[%s] Thread exception: %s", tid, exc)
                        result = {
                            "task_id": tid,
                            "model": args.model,
                            "scores": {},
                            "grade": None,
                            "process_grade": None,
                            "usage": {},
                            "error": str(exc),
                            "elapsed_time": 0.0,
                        }
                    all_results.append(result)
                    if result.get("error"):
                        logger.warning(
                            "[%s] Skipping progress save (error: %s) — will retry on resume",
                            tid, result["error"],
                        )
                    else:
                        with _progress_lock:
                            progress_entries.append({
                                "task_id": tid,
                                "run_index": ridx,
                                "result": result,
                            })
                            _save_progress(
                                prog_path, args.model, suite_label, args.runs,
                                progress_entries,
                            )

    # Summary
    _print_summary(all_results, args.model)
    summary_path = _write_global_summary(
        all_results, args.model, model_slug, suite_label, args.runs,
        task_objects=tasks,
    )
    logger.info("Summary written to: %s", summary_path)

    # Clean up progress file only if all tasks succeeded (no errors).
    # If there are errors, keep progress so --resume can retry just the
    # errored tasks without re-running the ones that already succeeded.
    error_count = sum(1 for r in all_results if r.get("error"))
    if error_count == 0:
        try:
            prog_path.unlink(missing_ok=True)
        except OSError:
            pass
    else:
        logger.info(
            "%d task(s) had errors — progress file kept for --resume",
            error_count,
        )


if __name__ == "__main__":
    main()
