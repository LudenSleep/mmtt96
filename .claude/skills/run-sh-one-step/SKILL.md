---
name: run-sh-one-step
description: Run each step as its own tools/run.sh call; bash -c chains through run.sh can trip the rm guard
---

# One run.sh call per step

Captured 2026-10-12 from phase 1.2 T5 summary (workflow gotcha).

## When to use
a multi-command sequence must go through tools/run.sh

## Steps
- Give each command its own `bash tools/run.sh <name> -- <cmd>` call (one log per step in `.run/logs/`).
- Do not wrap a `&&` chain in `bash -c "..."` inside run.sh: the command guard can read it as a destructive (`rm`) pattern and deny it (phase 1.2 T5).
- If a chain is unavoidable (a milestone clause list), keep it free of `rm`-like tokens and record any denial as a `harness:` gotcha.
- Long steps: `run.sh --bg <name> -- <cmd>` then `run.sh --wait <name> --max <s>` in one call.
