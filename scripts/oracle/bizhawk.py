"""BizHawk second oracle: launches EmuHawk 2.11 (GPGX core) on the staged ROM with a Lua probe.

  probe                         locate EmuHawk + one 60-frame run of lua/bizhawk_rammap.lua; exit 0 iff done
  run <lua> [--frames N] [--tag T] [--tsv PATH]
                                one run; JSON lines in .run/oracle/<tag>_<run>.jsonl (run = <tag>_<UTC stamp>);
                                exit 0 iff the script wrote {"ev":"done"}; --tsv merges `run key value` fact rows
                                into PATH (mame.write_facts; a `file:<path>:<size>` value becomes the file's sha1)

Exe: env BIZHAWK (path to EmuHawk.exe), else `bizhawk`/`EmuHawk` on PATH; neither -> exit. Launch (no clicks):
EmuHawk.exe --lua=<abs lua> <staged rom> (ROM staged by mame.stage_rom, SHA-1 checked); the Lua ends with
client.exit(). GPGX asks for the optional Mega-CD BIOS on every cart load and EmuHawk shows a modal "Warning"
box ("Couldn't find firmware ...") that blocks Lua; the watcher here closes that one box (WM_CLOSE) and nothing
else; any other visible dialog is left and the run times out. Env to the Lua: ORACLE_OUT, ORACLE_TRACE (absolute
prefix), ORACLE_FRAMES. Raw output only under .run/oracle/ (ignored). Stdlib only (ctypes for the watcher).
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mame  # noqa: E402

ROOT = mame.ROOT
LUA = mame.LUA
OUT = mame.OUT
TIMEOUT = 280  # one run stays < 285 s
FIRMWARE_WARNING = "Couldn't find firmware"


def exe():
    for c in (os.environ.get("BIZHAWK"), shutil.which("bizhawk"), shutil.which("EmuHawk")):
        if c and os.path.isfile(c):
            return c
    sys.exit("bizhawk: EmuHawk.exe not found (set BIZHAWK to its path, or put it on PATH)")


def _windows(pid):
    """Visible top-level windows of pid -> [(hwnd, title, joined child texts)]."""
    u = ctypes.windll.user32
    proto = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    found = []

    def text(h):
        buf = ctypes.create_unicode_buffer(2048)
        u.GetWindowTextW(h, buf, 2048)
        return buf.value

    def top(h, _):
        p = wt.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u.IsWindowVisible(h):
            kids = []
            u.EnumChildWindows(h, proto(lambda c, _: kids.append(text(c)) or True), 0)
            found.append((h, text(h), " | ".join(k for k in kids if k)))
        return True

    u.EnumWindows(proto(top), 0)
    return found


def launch(lua, env, log):
    """Run EmuHawk until it exits or TIMEOUT; closes only the firmware warning box. Returns rc or None on timeout."""
    p = subprocess.Popen([exe(), "--lua=" + lua, mame.STAGED], cwd=os.path.dirname(exe()), env=env,
                         stdout=log, stderr=subprocess.STDOUT)
    t0 = time.time()
    while p.poll() is None:
        if time.time() - t0 > TIMEOUT:
            p.kill()
            p.wait()
            log.write(f"bizhawk.py: timeout {TIMEOUT}s; dialogs {_windows(p.pid)}\n")
            return None
        for h, title, kids in _windows(p.pid):
            if title == "Warning" and FIRMWARE_WARNING in kids:
                log.write(f"bizhawk.py: closed dialog '{title}': {kids}\n")
                ctypes.windll.user32.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE
        time.sleep(0.25)
    return p.returncode


def run(lua, frames=600, tag=None):
    """One EmuHawk run of a Lua probe; returns (run_id, events list, done flag)."""
    mame.stage_rom()
    lua = mame.lua_path(lua)
    tag = tag or os.path.splitext(os.path.basename(lua))[0]
    os.makedirs(OUT, exist_ok=True)
    while True:  # run ids are unique per second
        run_id = f"{tag}_{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
        jsonl = os.path.join(OUT, run_id + ".jsonl")
        if not os.path.exists(jsonl):
            break
        time.sleep(1)
    env = dict(os.environ, ORACLE_OUT=jsonl.replace("\\", "/"),
               ORACLE_TRACE=os.path.join(OUT, run_id).replace("\\", "/"), ORACLE_FRAMES=str(frames))
    with open(os.path.join(OUT, run_id + ".log"), "w", encoding="utf-8") as log:
        rc = launch(lua, env, log)
        log.write(f"bizhawk.py: rc {rc}\n")
    events = []
    if os.path.isfile(jsonl):
        with open(jsonl, encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
    done = any(e.get("ev") == "done" for e in events)
    return run_id, events, done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    r = sub.add_parser("run")
    r.add_argument("lua")
    r.add_argument("--frames", type=int, default=600)
    r.add_argument("--tag")
    r.add_argument("--tsv")
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        print(f"bizhawk: exe {exe()}")
        run_id, events, done = run("bizhawk_rammap", frames=60, tag="bhprobe")
        print(f"bizhawk: run {run_id} done={done} ({sum(e.get('ev') == 'fact' for e in events)} facts)")
        return 0 if done else 1
    run_id, events, done = run(a.lua, a.frames, a.tag)
    print(f"bizhawk: run {run_id} done={done} -> .run/oracle/{run_id}.jsonl")
    if a.tsv and done:
        rows = mame.fact_rows(run_id, events)
        mame.write_facts(a.tsv, rows)
        for row in rows:
            print("\t".join(row))
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
