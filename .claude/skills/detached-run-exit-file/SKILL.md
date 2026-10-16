---
name: detached-run-exit-file
description: After run.sh --bg/--wait, read .run/logs/<name>.exit for the exit code; the tail omits it
---

# Detached Run Exit File

Captured 2026-10-12 from phase 1.5/T3 summary gotchas.

## When to use
after any detached run.sh run

## Steps
When: after `bash tools/run.sh --bg <name> -- <cmd>` and `bash tools/run.sh --wait <name> --max <s>`.
The `--wait` tail prints the last lines of `.run/logs/<name>.log`, not the command's exit status.
Read `.run/logs/<name>.exit` (one integer) and record that as the result; a green-looking tail with
a non-zero `.exit` is a failure.
Origin: phase 1.5/T3 summary gotcha.
