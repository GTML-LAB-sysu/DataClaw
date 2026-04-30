#!/usr/bin/env python3
"""Generate DataClaw/EIP-style benchmark tasks from QA JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def _discover_database_files(project_root: Path) -> list[dict[str, str]]:
    database_root = project_root / "assets" / "database"
    files: list[dict[str, str]] = []
    for path in sorted(database_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(database_root).as_posix()
        files.append({"source": f"database/{rel}", "dest": f"database/{rel}"})
    return files


def _answer_repr(answer: Any) -> str:
    return json.dumps(answer, ensure_ascii=False)


def _validate_payload(payload: dict[str, Any], qa_file: Path) -> None:
    required = ("id", "question", "guidelines", "answer")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"{qa_file} missing required keys: {', '.join(missing)}")
    if not isinstance(payload["question"], str) or not payload["question"].strip():
        raise ValueError(f"{qa_file} has invalid question")
    if not isinstance(payload["guidelines"], str) or not payload["guidelines"].strip():
        raise ValueError(f"{qa_file} has invalid guidelines")


def _mk_rubric(answer: Any, guidelines: str) -> str:
    answer_json = _answer_repr(answer)
    if isinstance(answer, list):
        n = len(answer)
        return f"""### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`{answer_json}`

Scoring rules:
- The gold answer is a list with N={n} parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_{n - 1}` each as 0 or 1.
- Return `total = (sum(part_i)) / {n}` exactly.
- If the model output is missing or cannot be parsed into {n} comparable parts, score all parts 0.
"""

    return f"""### Criterion 1: Single-answer Correctness (Weight: 100%)

Gold answer JSON:
`{answer_json}`

Scoring rules:
- Judge semantic equivalence between the model final answer and the gold answer.
- Return `scores` with one key `match` as 1 or 0.
- Return `total` as 1.0 if equivalent, otherwise 0.0.
"""


def _build_task_markdown(
    *,
    task_id: str,
    task_name: str,
    category: str,
    item_id: str,
    question: str,
    guidelines: str,
    answer: Any,
    timeout_seconds: int,
    workspace_files: list[dict[str, str]],
) -> str:
    ws_json = json.dumps(workspace_files, ensure_ascii=False, indent=2)
    rubric = _mk_rubric(answer, guidelines)
    expected = (
        "Agent should read the provided `database/` files, compute the result, and return the final answer. "
        "The final answer must follow the required output format."
    )
    criteria = (
        "- [ ] Final answer semantically matches the gold `answer`.\n"
        "- [ ] Output format follows `guidelines`."
    )
    data_sources = (
        "You may use files under `./database/` and web search."
        if category == "international_comparison"
        else "Only use files under `./database/`."
    )
    gold_file = f"qa_gold/{category}/{item_id}.json"
    return f"""---
id: {task_id}
name: {task_name}
category: {category}
grading_type: llm_judge
timeout_seconds: {timeout_seconds}
gold_file: {gold_file}
workspace_files: {ws_json}
---

## Prompt

{question}

Output guidelines:
{guidelines}

{data_sources}

## Expected Behavior

{expected}

## Grading Criteria

{criteria}

## LLM Judge Rubric

{rubric}
"""


def build(project_root: Path) -> int:
    qa_root = project_root / "assets" / "qa_raw"
    gold_root = project_root / "assets" / "qa_gold"
    tasks_root = project_root / "tasks"

    gold_root.mkdir(parents=True, exist_ok=True)
    tasks_root.mkdir(parents=True, exist_ok=True)

    for stale in tasks_root.glob("task_*.md"):
        stale.unlink()

    workspace_files = _discover_database_files(project_root)
    if not workspace_files:
        raise RuntimeError("No files found under assets/database")
    qa_files = sorted(qa_root.rglob("*_result.json"))
    if not qa_files:
        raise RuntimeError(f"No QA files found in {qa_root}")

    for idx, qa_file in enumerate(qa_files, start=1):
        payload = json.loads(qa_file.read_text(encoding="utf-8"))
        _validate_payload(payload, qa_file)
        category = str(payload.get("metadata", {}).get("category", qa_file.parent.name))
        level = str(payload.get("metadata", {}).get("level", "unknown"))
        item_id = str(payload.get("id", qa_file.stem.replace("_result", "")))
        question = str(payload.get("question", "")).strip()
        guidelines = str(payload.get("guidelines", "")).strip()
        answer = payload.get("answer")
        task_id = f"task_{idx:03d}_{_slug(category)}_{_slug(level)}_{_slug(item_id)}"
        task_name = f"{category}-{level}-{item_id}"

        gold_dir = gold_root / category
        gold_dir.mkdir(parents=True, exist_ok=True)
        gold_payload = {
            "id": item_id,
            "question": question,
            "guidelines": guidelines,
            "answer": answer,
            "metadata": payload.get("metadata", {}),
            "steps": payload.get("steps", []),
            "steps_num": payload.get("steps_num", 0),
            "milestone": payload.get("milestone", {}),
        }
        (gold_dir / f"{item_id}.json").write_text(
            json.dumps(gold_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        task_md = _build_task_markdown(
            task_id=task_id,
            task_name=task_name,
            category=category,
            item_id=item_id,
            question=question,
            guidelines=guidelines,
            answer=answer,
            timeout_seconds=1200,
            workspace_files=workspace_files,
        )
        (tasks_root / f"{task_id}.md").write_text(task_md, encoding="utf-8")

    return len(qa_files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EIP OpenClaw benchmark tasks")
    parser.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Project root path",
    )
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    count = build(project_root)
    print(f"Generated {count} tasks.")


if __name__ == "__main__":
    main()
