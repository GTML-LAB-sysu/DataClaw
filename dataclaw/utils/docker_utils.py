"""
Container lifecycle management for per-task Docker isolation.

Each benchmark task runs in its own Docker container. The host-side orchestrator
(dataclaw/eval/run_batch.py) uses these helpers to start, configure, drive, and tear down
containers via the Docker CLI.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
logger = logging.getLogger(__name__)

DOCKER_IMAGE = os.environ.get("DOCKER_IMAGE", "dataclaw:0.1.0")
TMP_WORKSPACE = os.environ.get("TMP_WORKSPACE", "/tmp_workspace")
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "3333"))
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENCLAW_CUSTOM_BASE_URL = os.environ.get("OPENCLAW_CUSTOM_BASE_URL", "")
OPENCLAW_CUSTOM_API_KEY = os.environ.get("OPENCLAW_CUSTOM_API_KEY", "")
OPENCLAW_CUSTOM_MODEL_ID = os.environ.get("OPENCLAW_CUSTOM_MODEL_ID", "")
JUDGE_CUSTOM_BASE_URL = os.environ.get("JUDGE_CUSTOM_BASE_URL", "")
JUDGE_CUSTOM_API_KEY = os.environ.get("JUDGE_CUSTOM_API_KEY", "")
JUDGE_CUSTOM_MODEL_ID = os.environ.get("JUDGE_CUSTOM_MODEL_ID", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

OPENCLAW_MODEL_CONTEXT_WINDOW = int(os.environ.get("OPENCLAW_MODEL_CONTEXT_WINDOW", "128000"))
OPENCLAW_MODEL_MAX_TOKENS = int(os.environ.get("OPENCLAW_MODEL_MAX_TOKENS", "16384"))
OPENCLAW_MODEL_COST_INPUT = float(os.environ.get("OPENCLAW_MODEL_COST_INPUT", "0"))
OPENCLAW_MODEL_COST_OUTPUT = float(os.environ.get("OPENCLAW_MODEL_COST_OUTPUT", "0"))
OPENCLAW_MODEL_COST_CACHE_READ = float(os.environ.get("OPENCLAW_MODEL_COST_CACHE_READ", "0"))
OPENCLAW_MODEL_COST_CACHE_WRITE = float(os.environ.get("OPENCLAW_MODEL_COST_CACHE_WRITE", "0"))

JUDGE_MODEL_CONTEXT_WINDOW = int(os.environ.get("JUDGE_MODEL_CONTEXT_WINDOW", "128000"))
JUDGE_MODEL_MAX_TOKENS = int(os.environ.get("JUDGE_MODEL_MAX_TOKENS", "16384"))
JUDGE_MODEL_COST_INPUT = float(os.environ.get("JUDGE_MODEL_COST_INPUT", "0"))
JUDGE_MODEL_COST_OUTPUT = float(os.environ.get("JUDGE_MODEL_COST_OUTPUT", "0"))
JUDGE_MODEL_COST_CACHE_READ = float(os.environ.get("JUDGE_MODEL_COST_CACHE_READ", "0"))
JUDGE_MODEL_COST_CACHE_WRITE = float(os.environ.get("JUDGE_MODEL_COST_CACHE_WRITE", "0"))


def remove_container(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, encoding="utf-8")


def start_container(task_id: str, extra_env: Optional[Dict[str, str]] = None) -> None:
    """Start a detached container for one task."""
    env_args: List[str] = []

    proxy_http = os.environ.get("HTTP_PROXY_INNER", "")
    proxy_https = os.environ.get("HTTPS_PROXY_INNER", "")
    if proxy_http or proxy_https:
        env_args += [
            "-e", f"http_proxy={proxy_http}",
            "-e", f"https_proxy={proxy_https}",
            "-e", f"HTTP_PROXY={proxy_http}",
            "-e", f"HTTPS_PROXY={proxy_https}",
        ]

    for key, value in (extra_env or {}).items():
        env_args += ["-e", f"{key}={value}"]

    cmd = [
        "docker", "run", "-d",
        "--name", task_id,
        *env_args,
        DOCKER_IMAGE,
        "/bin/bash", "-c", "tail -f /dev/null",
    ]
    logger.info("[%s] Starting container (image=%s)", task_id, DOCKER_IMAGE)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"Container startup failed:\n{r.stderr}")
    logger.info("[%s] Container started: %s", task_id, r.stdout.strip()[:12])


def setup_workspace(
    task_id: str,
    workspace_files: List[Dict[str, str]],
    assets_dir: Path,
) -> None:
    """Copy task workspace files into the container's /tmp_workspace."""
    subprocess.run(
        ["docker", "exec", task_id, "mkdir", "-p", TMP_WORKSPACE],
        capture_output=True, text=True, encoding="utf-8",
    )

    with tempfile.TemporaryDirectory() as staging:
        staging_path = Path(staging)
        for file_spec in workspace_files:
            source = assets_dir / file_spec["source"]
            dest_rel = file_spec["dest"]
            dest_local = staging_path / dest_rel
            dest_local.parent.mkdir(parents=True, exist_ok=True)
            if not source.exists():
                logger.error("[%s] Workspace file not found: %s", task_id, source)
                raise FileNotFoundError(f"Workspace file not found: {source}")
            shutil.copy2(str(source), str(dest_local))

        r = subprocess.run(
            ["docker", "cp", f"{staging}/.", f"{task_id}:{TMP_WORKSPACE}/"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if r.returncode != 0:
            raise RuntimeError(f"Workspace copy failed:\n{r.stderr}")
    logger.info("[%s] Workspace files injected (%d files)", task_id, len(workspace_files))

    # Symlink OpenClaw workspace to TMP_WORKSPACE so tools can access files
    subprocess.run(
        ["docker", "exec", task_id, "/bin/bash", "-c",
         f"rm -rf /root/.openclaw/workspace && ln -s {TMP_WORKSPACE} /root/.openclaw/workspace"],
        capture_output=True, text=True, encoding="utf-8",
    )


def onboard_openclaw(task_id: str) -> None:
    """Run openclaw onboard inside the container with configured auth."""
    onboard_args = [
        "--non-interactive",
        "--accept-risk",
        "--skip-health",
        "--workspace", "/root/.openclaw/workspace",
        "--gateway-bind", "loopback",
        "--gateway-port", str(GATEWAY_PORT),
    ]

    if OPENCLAW_CUSTOM_BASE_URL:
        if not OPENCLAW_CUSTOM_API_KEY:
            raise ValueError(
                "OPENCLAW_CUSTOM_API_KEY is required when OPENCLAW_CUSTOM_BASE_URL is set"
            )
        onboard_args += [
            "--auth-choice", "custom-api-key",
            "--custom-base-url", OPENCLAW_CUSTOM_BASE_URL,
            "--custom-api-key", OPENCLAW_CUSTOM_API_KEY,
            "--custom-model-id", OPENCLAW_CUSTOM_MODEL_ID or DEFAULT_MODEL,
        ]
    elif OPENROUTER_API_KEY:
        onboard_args += ["--openrouter-api-key", OPENROUTER_API_KEY]

    if OPENAI_API_KEY:
        onboard_args += ["--openai-api-key", OPENAI_API_KEY]
    if ANTHROPIC_API_KEY:
        onboard_args += ["--anthropic-api-key", ANTHROPIC_API_KEY]
    if GEMINI_API_KEY:
        onboard_args += ["--gemini-api-key", GEMINI_API_KEY]

    cmd = ["docker", "exec", task_id, "openclaw", "onboard", *onboard_args]
    logger.info("[%s] Running openclaw onboard", task_id)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"OpenClaw onboard failed:\n{r.stderr}")
    logger.info("[%s] Onboard complete", task_id)

    _patch_streaming_usage_compat(task_id)
    _patch_main_model_capabilities(task_id)
    _patch_brave_web_search(task_id)


def _patch_main_model_capabilities(task_id: str) -> None:
    """Patch contextWindow, maxTokens, and cost for the main (agent) model.

    OpenClaw onboard assigns conservative defaults for unknown custom providers.
    This overwrites them with values from the OPENCLAW_MODEL_* environment variables.
    """
    config = _read_openclaw_config(task_id)
    if not config:
        return
    patched = False
    for _pname, pinfo in config.get("models", {}).get("providers", {}).items():
        for model in pinfo.get("models", []):
            model["contextWindow"] = OPENCLAW_MODEL_CONTEXT_WINDOW
            model["maxTokens"] = OPENCLAW_MODEL_MAX_TOKENS
            model["cost"] = {
                "input": OPENCLAW_MODEL_COST_INPUT,
                "output": OPENCLAW_MODEL_COST_OUTPUT,
                "cacheRead": OPENCLAW_MODEL_COST_CACHE_READ,
                "cacheWrite": OPENCLAW_MODEL_COST_CACHE_WRITE,
            }
            patched = True
    if patched:
        _write_openclaw_config(task_id, config)
        logger.info(
            "[%s] Patched main model capabilities (contextWindow=%d, maxTokens=%d)",
            task_id, OPENCLAW_MODEL_CONTEXT_WINDOW, OPENCLAW_MODEL_MAX_TOKENS,
        )


def _patch_brave_web_search(task_id: str) -> None:
    """Enable Brave as ``web_search`` provider when ``BRAVE_API_KEY`` is set.

    Matches OpenClaw canonical config:
    https://docs.openclaw.ai/tools/brave-search
    """
    api_key = (BRAVE_API_KEY or "").strip()
    if not api_key:
        return
    config = _read_openclaw_config(task_id)
    if not config:
        logger.warning("[%s] Cannot read openclaw.json; skip Brave web_search patch", task_id)
        return

    plugins = config.setdefault("plugins", {})
    entries = plugins.setdefault("entries", {})
    brave_entry = entries.setdefault("brave", {})
    brave_entry["enabled"] = True
    brave_cfg = brave_entry.setdefault("config", {})
    brave_cfg.setdefault("webSearch", {})["apiKey"] = api_key

    tools = config.setdefault("tools", {})
    web = tools.setdefault("web", {})
    search = web.setdefault("search", {})
    search["provider"] = "brave"
    search["maxResults"] = int(os.environ.get("BRAVE_WEB_SEARCH_MAX_RESULTS", "5"))
    search["timeoutSeconds"] = int(os.environ.get("BRAVE_WEB_SEARCH_TIMEOUT_SECONDS", "30"))

    _write_openclaw_config(task_id, config)
    logger.info("[%s] Patched OpenClaw config: web_search provider=brave", task_id)


def _patch_streaming_usage_compat(task_id: str) -> None:
    """Ensure all custom-provider models have ``compat.supportsUsageInStreaming: true``.

    OpenClaw defaults this flag to ``false`` for unrecognised providers, which
    prevents ``stream_options: {include_usage: true}`` from being sent in API
    requests, resulting in zero-value token usage in transcripts.
    """
    config = _read_openclaw_config(task_id)
    if not config:
        return
    patched = False
    for _pname, pinfo in config.get("models", {}).get("providers", {}).items():
        for model in pinfo.get("models", []):
            compat = model.get("compat")
            if compat is None:
                model["compat"] = {"supportsUsageInStreaming": True}
                patched = True
            elif not compat.get("supportsUsageInStreaming"):
                compat["supportsUsageInStreaming"] = True
                patched = True
    if patched:
        _write_openclaw_config(task_id, config)
        logger.info("[%s] Patched compat.supportsUsageInStreaming for custom providers", task_id)


def start_gateway(task_id: str, log_path: Path) -> subprocess.Popen:
    """Start the OpenClaw gateway in the background inside the container."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")

    gateway_cmd = f"openclaw gateway run --bind loopback --port {GATEWAY_PORT}"
    exports: List[str] = []
    if OPENROUTER_API_KEY:
        exports.append(f"export OPENROUTER_API_KEY='{OPENROUTER_API_KEY}'")
    brave = (BRAVE_API_KEY or "").strip()
    if brave:
        exports.append(f"export BRAVE_API_KEY='{brave}'")
    if exports:
        gateway_cmd = " && ".join(exports) + " && " + gateway_cmd

    proc = subprocess.Popen(
        ["docker", "exec", task_id, "/bin/bash", "-c", gateway_cmd],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )
    proc._log_file = log_file  # type: ignore[attr-defined]
    logger.info("[%s] Gateway starting (PID=%s)", task_id, proc.pid)

    time.sleep(2)
    return proc


def _read_openclaw_config(task_id: str) -> Dict[str, Any]:
    """Read and parse openclaw.json from the container."""
    r = subprocess.run(
        ["docker", "exec", task_id, "cat", "/root/.openclaw/openclaw.json"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def _write_openclaw_config(task_id: str, config: Dict[str, Any]) -> None:
    """Write openclaw.json back into the container via docker cp."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8",
    ) as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        tmp_path = f.name
    try:
        subprocess.run(
            ["docker", "cp", tmp_path, f"{task_id}:/root/.openclaw/openclaw.json"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        )
    finally:
        os.unlink(tmp_path)


def register_custom_provider(
    task_id: str, base_url: str, api_key: str, model_id: str,
) -> None:
    """Register an additional custom model provider in the container."""
    config = _read_openclaw_config(task_id)
    if not config:
        raise RuntimeError("Cannot read openclaw.json from container")

    from urllib.parse import urlparse
    hostname = urlparse(base_url).hostname or ""
    slug = f"custom-{hostname.replace('.', '-')}"

    providers = config.setdefault("models", {}).setdefault("providers", {})
    if slug not in providers:
        providers[slug] = {
            "baseUrl": base_url,
            "apiKey": api_key,
            "api": "openai-completions",
            "models": [],
        }
    existing_ids = {m["id"] for m in providers[slug].get("models", [])}
    if model_id not in existing_ids:
        providers[slug]["models"].append({
            "id": model_id,
            "name": f"{model_id} (Custom Provider)",
            "reasoning": False,
            "input": ["text"],
            "cost": {
                "input": JUDGE_MODEL_COST_INPUT,
                "output": JUDGE_MODEL_COST_OUTPUT,
                "cacheRead": JUDGE_MODEL_COST_CACHE_READ,
                "cacheWrite": JUDGE_MODEL_COST_CACHE_WRITE,
            },
            "compat": {"supportsUsageInStreaming": True},
            "contextWindow": JUDGE_MODEL_CONTEXT_WINDOW,
            "maxTokens": JUDGE_MODEL_MAX_TOKENS,
        })

    _write_openclaw_config(task_id, config)
    logger.info("[%s] Registered custom provider: %s/%s", task_id, slug, model_id)


def resolve_qualified_model(task_id: str, model: str) -> str:
    """Resolve a bare model name to its fully-qualified provider/model form
    by reading the live openclaw.json inside the container."""
    if "/" in model:
        return model
    config = _read_openclaw_config(task_id)
    if not config:
        logger.warning("[%s] Cannot read openclaw.json, using bare model name: %s",
                       task_id, model)
        return model
    providers = config.get("models", {}).get("providers", {})
    for provider_name, provider_info in providers.items():
        for m in provider_info.get("models", []):
            if m.get("id") == model:
                return f"{provider_name}/{model}"
    return model


def set_model(task_id: str, model: str) -> None:
    """Set the active model inside the container."""
    qualified = resolve_qualified_model(task_id, model)
    r = subprocess.run(
        ["docker", "exec", task_id, "/bin/bash", "-c",
         f"openclaw models set '{qualified}'"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(f"Model setup failed:\n{r.stderr}")
    logger.info("[%s] Model set: %s", task_id, qualified)


def create_agent(task_id: str, agent_id: str, model: str) -> None:
    """Create an OpenClaw agent inside the container."""
    r = subprocess.run(
        ["docker", "exec", task_id, "openclaw", "agents", "add", agent_id,
         "--model", model, "--non-interactive",
         "--workspace", "/root/.openclaw/workspace"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r.returncode != 0:
        logger.warning("[%s] Agent creation returned %s: %s", task_id, r.returncode, r.stderr)


def run_agent_message(
    task_id: str,
    message: str,
    timeout_seconds: float,
    log_path: Path,
    agent_id: str = "main",
) -> subprocess.Popen:
    """Send a message to an agent inside the container (background).

    Uses docker cp + file read to bypass Windows command-line length limits.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("w", encoding="utf-8")

    fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(message)

    subprocess.run(
        ["docker", "cp", tmp_path,
         f"{task_id}:/tmp/agent_prompt.txt"],
        capture_output=True, text=True, encoding="utf-8",
    )
    os.unlink(tmp_path)

    bash_cmd = (
        f"prompt=$(cat /tmp/agent_prompt.txt) && "
        f"cd {TMP_WORKSPACE} && "
        f"openclaw agent --agent {agent_id} --session-id chat "
        f"--timeout {int(timeout_seconds)} --message \"$prompt\""
    )

    proc = subprocess.Popen(
        ["docker", "exec", task_id, "/bin/bash", "-c", bash_cmd],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )
    proc._log_file = log_file  # type: ignore[attr-defined]
    logger.info("[%s] Agent message sent (PID=%s, timeout=%ds)", task_id, proc.pid, int(timeout_seconds))
    return proc


def run_judge_message(
    task_id: str,
    message: str,
    timeout_seconds: float = 180,
    judge_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the LLM judge inside the container synchronously. Returns transcript entries."""
    if judge_model:
        subprocess.run(
            ["docker", "exec", task_id, "openclaw", "agents", "add", "judge",
             "--model", judge_model, "--non-interactive",
             "--workspace", "/root/.openclaw/workspace"],
            capture_output=True, text=True, encoding="utf-8",
        )

    fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(message)

        cp_result = subprocess.run(
            ["docker", "cp", tmp_path,
             f"{task_id}:/tmp/judge_prompt.txt"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if cp_result.returncode != 0:
            return {
                "stdout": "",
                "stderr": f"docker cp failed: {cp_result.stderr}",
                "exit_code": -1,
                "timed_out": False,
            }

        bash_cmd = (
            f"prompt=$(cat /tmp/judge_prompt.txt) && "
            f"cd {TMP_WORKSPACE} && "
            f"openclaw agent --agent judge --session-id judge_chat "
            f"--message \"$prompt\""
        )

        r = subprocess.run(
            ["docker", "exec", task_id, "/bin/bash", "-c", bash_cmd],
            capture_output=True, text=True, encoding="utf-8",
            timeout=timeout_seconds,
        )
        return {
            "stdout": r.stdout,
            "stderr": r.stderr,
            "exit_code": r.returncode,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Judge timed out",
            "exit_code": -1,
            "timed_out": True,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def collect_transcript(task_id: str, output_dir: Path, agent_id: str = "main", output_filename: str = "") -> Path:
    """Copy the agent transcript from the container to the host."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_filename:
        filename = output_filename
    else:
        filename = "chat.jsonl" if agent_id == "main" else f"{agent_id}_chat.jsonl"
    transcript_host = output_dir / filename

    transcript_container = f"/root/.openclaw/agents/{agent_id}/sessions/chat.jsonl"
    r = subprocess.run(
        ["docker", "cp", f"{task_id}:{transcript_container}", str(transcript_host)],
        capture_output=True, text=True, encoding="utf-8",
    )

    if r.returncode != 0:
        # Try to find transcript within the specific agent's directory only
        agent_dir = f"/root/.openclaw/agents/{agent_id}"
        find_cmd = f"find {agent_dir} -name '*.jsonl' -type f 2>/dev/null | head -5"
        find_r = subprocess.run(
            ["docker", "exec", task_id, "/bin/bash", "-c", find_cmd],
            capture_output=True, text=True, encoding="utf-8",
        )
        if find_r.stdout.strip():
            first_jsonl = find_r.stdout.strip().splitlines()[0]
            r2 = subprocess.run(
                ["docker", "cp", f"{task_id}:{first_jsonl}", str(transcript_host)],
                capture_output=True, text=True, encoding="utf-8",
            )
            if r2.returncode == 0:
                logger.info("[%s] Transcript found via fallback: %s", task_id, first_jsonl)
                return transcript_host

        logger.warning("[%s] Transcript not found for agent '%s': %s",
                       task_id, agent_id, r.stderr.strip())

    return transcript_host


def collect_output(task_id: str, output_dir: Path) -> None:
    """Collect all task output files from the container.

    Note: workspace and OpenClaw session data are NOT collected because they
    consist entirely of static input files (database/, md files) or duplicates
    of files already saved at the output_dir level (chat.jsonl, judge_chat.jsonl).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("[%s] Task output collected to %s", task_id, output_dir)


def close_proc_log(proc: subprocess.Popen) -> None:
    """Close the log file handle created by run_agent_message / start_gateway."""
    log_file = getattr(proc, "_log_file", None)
    if log_file and not log_file.closed:
        log_file.close()


def detect_transcript_errors(transcript_path: Path) -> Optional[str]:
    """Check an OpenClaw transcript for API / provider errors.

    OpenClaw reports errors as assistant messages with stopReason="error"
    and an errorMessage field containing the details (e.g. 429, 504, etc.).
    This is the framework's own structured error reporting — no guessing.

    Returns an error description string if errors found, else None.
    """
    if not transcript_path or not transcript_path.exists():
        return None
    try:
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    error_messages: List[str] = []
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
        if msg.get("role") == "assistant" and msg.get("stopReason") == "error":
            em = msg.get("errorMessage", "unknown error")
            # Keep first line only (some errors contain full HTML pages)
            first_line = em.split("\n", 1)[0].strip()[:200]
            error_messages.append(first_line)

    if error_messages:
        sample = error_messages[0]
        return f"API error ({len(error_messages)} occurrence(s)): {sample}"
    return None


def extract_usage_from_jsonl(jsonl_path: Path) -> Dict[str, Any]:
    """Sum token usage and cost from all assistant messages in a transcript JSONL."""
    totals: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "request_count": 0,
    }
    if not jsonl_path.exists():
        return totals
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
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
        totals["request_count"] += 1
        usage = msg.get("usage", {})
        totals["input_tokens"] += usage.get("input", 0)
        totals["output_tokens"] += usage.get("output", 0)
        totals["cache_read_tokens"] += usage.get("cacheRead", 0)
        totals["cache_write_tokens"] += usage.get("cacheWrite", 0)
        totals["total_tokens"] += usage.get("totalTokens", 0)
        cost = usage.get("cost", {})
        totals["cost_usd"] += cost.get("total", 0.0)
    totals["cost_usd"] = round(totals["cost_usd"], 6)
    return totals
