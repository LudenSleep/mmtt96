#!/usr/bin/env python
"""usage_guard.py -- pause work before the Claude five-hour usage window runs out.

  check            go (exit 0) | pause (exit 3) | unknown (exit 0, warns: statusline wrote no fresh data)
  watch            poll every 60 s; on first crossing write .run/PAUSE_NOW, print `PAUSE NN% reset HH:MM`, exit 3
  hook             PreToolUse hook (Agent, Bash): while .run/PAUSE_NOW is live, deny new work (exit 2);
                   commits, status and read-only commands pass; fail-open on any error
  selftest         fake statusline JSON -> temp ledger -> check/watch/hook results
  --pct N          threshold override (default tools/status.py WINDOW_GATE_PCT = 90)

Data: <ledger>/usage_api.json written by tools/usage_statusline.py, read via tools/status.py:_five_hour.
Stdlib only.
"""

import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAUSE_FILE = os.path.join(ROOT, ".run", "PAUSE_NOW")
ALLOW_PREFIXES = ("git commit", "git add", "bash tools/commit_task.sh", "tools/status.py",
                  "tools/usage_guard.py", "git status", "git log", "git diff", "git show")
READ_ONLY = {"ls", "cat", "head", "tail", "grep", "rg", "wc", "pwd", "echo", "date", "type",
             "which", "stat", "file", "du", "df", "tools/outline.py", "tools/card.py"}
PY_RE = re.compile(r'^\s*(?:"[^"]*python[^"]*"|\S*python(?:3)?(?:\.exe)?)\s+(?:-\S+\s+)*', re.I)


def _status():
    sys.path.insert(0, HERE)
    import status  # noqa: E402  tools/status.py: _five_hour, _ledger_dir, WINDOW_GATE_PCT
    return status


def _hhmm(epoch):
    return time.strftime("%H:%M", time.localtime(epoch))


def state(pct_limit):  # -> ("go"|"pause"|"unknown", pct|None, resets|None)
    got = _status()._five_hour(time.time())
    if got is None:
        return "unknown", None, None
    return ("pause" if got[0] >= pct_limit else "go"), got[0], got[1]


def cmd_check(limit):
    kind, pct, resets = state(limit)
    if kind == "unknown":
        sys.stdout.write("unknown: no fresh usage data (statusline has not written %s)\n"
                         % os.path.join(_status()._ledger_dir(), "usage_api.json"))
        return 0
    sys.stdout.write("%s: five-hour window at %d%% (limit %d%%), resets %s\n"
                     % (kind, int(round(pct)), limit, _hhmm(resets)))
    return 3 if kind == "pause" else 0


def watch_step(limit, pause_file):  # -> exit code 3 when paused (file written), else None
    kind, pct, resets = state(limit)
    if kind != "pause":
        return None
    os.makedirs(os.path.dirname(pause_file), exist_ok=True)
    with open(pause_file, "w", encoding="utf-8") as fh:
        fh.write("%d\n%s\n%d%%\n" % (int(resets), _hhmm(resets), int(round(pct))))
    sys.stdout.write("PAUSE %d%% reset %s\n" % (int(round(pct)), _hhmm(resets)))
    sys.stdout.flush()
    return 3


def cmd_watch(limit, interval=60):
    while True:
        rc = watch_step(limit, PAUSE_FILE)
        if rc is not None:
            return rc
        time.sleep(interval)


def _allowed_bash(cmd):
    c = PY_RE.sub("", cmd.strip(), count=1).strip()
    if any(c.startswith(p) or cmd.strip().startswith(p) for p in ALLOW_PREFIXES):
        return True
    if re.search(r"[;&|>]", c.replace("2>&1", "")):   # chains/redirects are not judged read-only
        return False
    first = c.split()[0] if c.split() else ""
    return first in READ_ONLY


def hook(stdin_text, pause_file, now=None):  # -> (exit code, stderr message)
    try:
        if not os.path.exists(pause_file):
            return 0, ""
        with open(pause_file, encoding="utf-8") as fh:
            lines = fh.read().split()
        resets = float(lines[0])
        now = time.time() if now is None else now
        if resets <= now:
            os.remove(pause_file)
            return 0, ""
        data = json.loads(stdin_text) if stdin_text.strip() else {}
        tool = data.get("tool_name", "")
        if tool == "Bash" and _allowed_bash(str((data.get("tool_input") or {}).get("command", ""))):
            return 0, ""
        if tool not in ("Agent", "Task", "Bash"):
            return 0, ""
        return 2, ("usage >= 90%%: committing and pausing until %s; do not start new work"
                   % _hhmm(resets))
    except Exception:
        return 0, ""                     # fail-open


def cmd_hook():
    try:
        text = sys.stdin.read()
    except Exception:
        return 0
    rc, msg = hook(text, PAUSE_FILE)
    if msg:
        sys.stderr.write(msg + "\n")
    return rc


def selftest():
    tmp = os.path.join(ROOT, ".run", "usage_guard_selftest")
    os.makedirs(tmp, exist_ok=True)
    for f in ("usage_api.json", "config.json", "PAUSE_NOW"):
        if os.path.exists(os.path.join(tmp, f)):
            os.remove(os.path.join(tmp, f))
    env = dict(os.environ, PA_LEDGER_DIR=tmp, USAGE_DEBUG_FILE=os.path.join(tmp, "last_input.json"))
    os.environ.update(PA_LEDGER_DIR=tmp)
    py, sl, me = sys.executable, os.path.join(HERE, "usage_statusline.py"), os.path.abspath(__file__)
    reset = int(time.time()) + 3600
    fails = []

    def ok(name, cond, detail=""):
        sys.stdout.write("%s %s %s\n" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    def run(args, inp=""):
        p = subprocess.run(args, input=inp, capture_output=True, text=True, env=env, timeout=60)
        return p.returncode, p.stdout.strip()

    rc, out = run([py, me, "check"])
    ok("missing data -> unknown exit 0", rc == 0 and out.startswith("unknown"), out)
    for pct, want_rc, want in ((50, 0, "go"), (95, 3, "pause")):
        fake = {"rate_limits": {"five_hour": {"used_percentage": pct, "resets_at": reset},
                                "seven_day": {"used_percentage": 20, "resets_at": reset + 86400}}}
        rc, out = run([py, sl], json.dumps(fake))
        ok("statusline %d%%" % pct, rc == 0 and out == "5h %d%% | 7d 20%%" % pct, out)
        rc, out = run([py, me, "check"])
        ok("check %d%% -> %s" % (pct, want), rc == want_rc and out.startswith(want), out)
    rc, out = run([py, sl], json.dumps({"rate_limits": {"five_hour": {"utilization": 0.5,
                                                                      "reset_at": reset * 1000}}}))
    ok("fraction + ms keys", rc == 0 and out == "5h 50% | 7d --", out)
    rc, out = run([py, sl], "not json")
    ok("bad stdin never crashes", rc == 0, out)
    run([py, sl], json.dumps({"rate_limits": {"five_hour": {"used_percentage": 95, "resets_at": reset}}}))
    pf = os.path.join(tmp, "PAUSE_NOW")
    ok("watch step at 95% writes PAUSE_NOW", watch_step(90, pf) == 3 and os.path.exists(pf))
    ok("watch step at --pct 99 -> no pause", watch_step(99, os.path.join(tmp, "nope")) is None)
    agent = json.dumps({"tool_name": "Agent", "tool_input": {"prompt": "x"}})
    bash = lambda c: json.dumps({"tool_name": "Bash", "tool_input": {"command": c}})  # noqa: E731
    ok("hook denies Agent", hook(agent, pf)[0] == 2, hook(agent, pf)[1])
    ok("hook denies build", hook(bash("bash tools/run.sh build -- make"), pf)[0] == 2)
    for c in ("git commit -m x", 'bash tools/commit_task.sh T1 "m" a.py',
              '"C:/Program Files/Python311/python.exe" tools/status.py window-gate', "ls -la", "git status"):
        ok("hook allows %r" % c, hook(bash(c), pf)[0] == 0)
    ok("hook denies chained", hook(bash("ls; make"), pf)[0] == 2)
    ok("hook expired -> allow + remove", hook(agent, pf, now=reset + 1)[0] == 0 and not os.path.exists(pf))
    ok("hook garbage -> allow", hook("{{", pf)[0] == 0)
    sys.stdout.write("selftest: %s\n" % ("PASS" if not fails else "FAIL " + ", ".join(fails)))
    return 0 if not fails else 1


def main(argv):
    limit = None
    if "--pct" in argv:
        i = argv.index("--pct")
        limit = float(argv[i + 1])
        del argv[i:i + 2]
    cmd = argv[0] if argv else "check"
    if cmd == "hook":
        return cmd_hook()
    if limit is None:
        limit = _status().WINDOW_GATE_PCT
    if cmd == "check":
        return cmd_check(limit)
    if cmd == "watch":
        return cmd_watch(limit)
    if cmd == "selftest":
        return selftest()
    sys.stdout.write(__doc__)
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hook":
        try:
            sys.exit(main(sys.argv[1:]))
        except SystemExit:
            raise
        except Exception:
            sys.exit(0)
    sys.exit(main(sys.argv[1:]))
