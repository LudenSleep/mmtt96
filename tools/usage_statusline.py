#!/usr/bin/env python
"""usage_statusline.py -- Claude Code statusLine command that caches the rate-limit windows.

Reads the statusline JSON on stdin; writes <ledger>/usage_api.json in the schema
tools/status.py:_five_hour reads ({ts, windows: {five_hour: {pct, resets_at}, seven_day: {...}}});
copies the raw stdin to .run/usage_last_input.json (field-name debugging); prints `5h NN% | 7d NN%`.
Ledger dir: $PA_LEDGER_DIR, else %USERPROFILE%/.claude/usage-ledger. Stdlib only; never crashes; exit 0.
"""

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCT_KEYS = ("used_percentage", "used_percent", "pct", "percent", "utilization", "used")
FRACTION_KEYS = ("utilization", "used")      # may be 0-1; percent-named keys are taken as 0-100
RESET_KEYS =("resets_at", "reset_at", "resets", "reset_time", "resetsAt", "resetAt")
WINDOWS = {"five_hour": ("five_hour", "fiveHour", "5h", "five_hour_window"),
           "seven_day": ("seven_day", "sevenDay", "7d", "seven_day_window")}


def ledger_dir():  # same rule as tools/status.py:_ledger_dir
    env = os.environ.get("PA_LEDGER_DIR")
    if env:
        return env
    h = os.environ.get("USERPROFILE") if os.name == "nt" else None
    return os.path.join(os.path.abspath(h or os.path.expanduser("~")), ".claude", "usage-ledger")


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().rstrip("%"))
    except ValueError:
        return None


def _first(d, keys):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def parse_window(w):  # -> {"pct": 0-100, "resets_at": epoch|ISO} or None
    if not isinstance(w, dict):
        return None
    key = next((k for k in PCT_KEYS if w.get(k) is not None), None)
    pct = _num(w.get(key)) if key else None
    if pct is None:
        return None
    if 0 <= pct <= 1 and key in FRACTION_KEYS:
        pct *= 100.0                    # 0-1 fraction; *percent* keys are always 0-100
    reset = _first(w, RESET_KEYS)
    rn = _num(reset)
    if rn is not None:
        reset = rn / 1000.0 if rn > 1e11 else rn    # epoch ms -> s
    return {"pct": round(pct, 2), "resets_at": reset}


def extract(data):  # -> {"five_hour": {...}, "seven_day": {...}} (only those found)
    rl = None
    if isinstance(data, dict):
        rl = _first(data, ("rate_limits", "rateLimits", "usage_limits", "rate_limit"))
        if not isinstance(rl, dict):
            rl = data
    out = {}
    for name, keys in WINDOWS.items():
        w = parse_window(_first(rl, keys)) if isinstance(rl, dict) else None
        if w:
            out[name] = w
    return out


def write_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)
    os.replace(tmp, path)


def main():
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:
        pass
    try:
        dbg = os.environ.get("USAGE_DEBUG_FILE") or os.path.join(ROOT, ".run", "usage_last_input.json")
        os.makedirs(os.path.dirname(dbg), exist_ok=True)
        with open(dbg, "w", encoding="utf-8") as fh:
            fh.write(raw)
    except Exception:
        pass
    wins = {}
    try:
        wins = extract(json.loads(raw)) if raw.strip() else {}
    except Exception:
        wins = {}
    try:
        if wins:
            write_atomic(os.path.join(ledger_dir(), "usage_api.json"),
                         {"ts": time.time(), "source": "tools/usage_statusline.py", "windows": wins})
    except Exception:
        pass
    parts = []
    for name, label in (("five_hour", "5h"), ("seven_day", "7d")):
        w = wins.get(name)
        parts.append("%s %s" % (label, "%d%%" % int(round(w["pct"])) if w else "--"))
    try:
        sys.stdout.write(" | ".join(parts) + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
