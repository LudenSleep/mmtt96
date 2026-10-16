# Usage guard

Stops new work before the Claude five-hour usage window runs out, so a task is committed rather than cut off mid-edit.

## What it does

- `tools/usage_statusline.py` is a Claude Code status line command. Each time Claude Code refreshes the status line it
  passes a JSON description of the session on standard input, including the rate-limit windows. The script saves the
  five-hour and seven-day percentages and reset times to `%USERPROFILE%/.claude/usage-ledger/usage_api.json` (the file
  `tools/status.py window-gate` already reads), keeps a copy of the raw input in `.run/usage_last_input.json`, and shows
  `5h NN% | 7d NN%` as the status line.
- `tools/usage_guard.py check` prints `go`, `pause` (exit code 3, at 90% or more) or `unknown` (no fresh data; exit 0
  with a warning). `--pct N` changes the threshold.
- `tools/usage_guard.py watch` checks every minute. The first time the five-hour window reaches the threshold it writes
  `.run/PAUSE_NOW` (reset time inside), prints one line `PAUSE NN% reset HH:MM` and exits with code 3. It can run as a
  Monitor command so the session is told the moment the limit nears, not only between tasks.
- `tools/usage_guard.py hook` is a PreToolUse hook. While `.run/PAUSE_NOW` exists and its reset time is in the future,
  it refuses Agent spawns and Bash commands with the message "usage >= 90%: committing and pausing until HH:MM; do not
  start new work". Commits (`git commit`, `git add`, `bash tools/commit_task.sh`), `tools/status.py`, and simple
  read-only commands still run. Once the reset time passes it deletes `.run/PAUSE_NOW` and allows everything. Any error
  inside the hook allows the call.
- `tools/usage_guard.py selftest` checks all of the above against a scratch ledger in `.run/usage_guard_selftest/`.

## How to enable

Add these two keys to `.claude/settings.json`, keeping every existing key:

```json
"statusLine": {"type": "command",
               "command": "\"C:/Program Files/Python311/python.exe\" tools/usage_statusline.py"},
"hooks": {"PreToolUse": [{"matcher": "Agent|Bash",
                          "hooks": [{"type": "command",
                                     "command": "\"C:/Program Files/Python311/python.exe\" tools/usage_guard.py hook"}]}]}
```

Restart Claude Code, let the status line refresh once, then run
`"C:/Program Files/Python311/python.exe" tools/usage_guard.py check`.

## Limits

- It sees only the five-hour and seven-day windows. It cannot read a monthly spend limit or any other billing cap.
- The input field names (`rate_limits.five_hour.used_percentage`, `resets_at` in epoch seconds) are assumed. The script
  accepts several spellings, but after the first refresh confirm the real names in `.run/usage_last_input.json`. If the
  status line shows `5h -- | 7d --`, the names did not match and nothing is being saved.
- A value between 0 and 1 is read as a fraction only under the `utilization` or `used` keys; percent-named keys are
  always read as 0 to 100.
- Data older than 30 minutes (twice the ledger's `poll_min`, default 15) counts as stale, so the guard reports `unknown`
  and does not pause if the status line stops refreshing.
- The hook's read-only list is short and deliberately strict: a command chained with `;`, `&`, `|` or a redirect is
  refused while paused unless it starts with one of the commit or status prefixes.
