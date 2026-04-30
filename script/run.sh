#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# --- Build the runtime image (only needed once) ---
# docker build -t dataclaw:0.1.0 .

# --- Run all tasks ---
# python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6

# --- Run all tasks with parallelism ---
# python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6 --parallel 4

# --- Run specific tasks ---
# python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6 --suite task_001,task_002

# --- Run a single task file ---
# python dataclaw/eval/run_batch.py --task tasks/task_001_comprehensive_decision_hard_hard001.md --model openrouter/anthropic/claude-sonnet-4.6

# --- Default: run all tasks sequentially ---
python dataclaw/eval/run_batch.py \
  --model "${DEFAULT_MODEL:?Set DEFAULT_MODEL in .env}" \
  --parallel "${DEFAULT_PARALLEL:-1}" \
  "$@"
