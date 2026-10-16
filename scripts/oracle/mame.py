"""MAME runtime oracle: launches MAME 0.289 headless on the softlist cart megadriv:microm96 with a Lua probe.

  probe                         -verifysoftlist megadriv (must print "romset megadriv:microm96 is good") + one
                                short boot reading the 64 vectors live (lua/vectors.lua), compared with
                                scripts/extract/rom.parse_vectors; exit 0 iff both
  run <lua> [--frames N] [--tag T] [--tsv PATH] [--secs S]
                                one run; JSON lines in .run/oracle/<tag>_<run>.jsonl (run = <tag>_<UTC stamp>);
                                exit 0 iff the script wrote {"ev":"done"}; --tsv appends boot.lua phase rows
                                (run, phase, first_pcs, entry_after_trap, hit_015918, control_fired, hit_00028C,
                                fired_00028E) to PATH; for a fact probe (lua/rammap.lua) it merges
                                `run key value` rows into PATH instead, rewritten sorted

Launch (settled by T2; no -cart): mame.exe megadriv microm96 -rompath .run/mame/roms -hashpath <mame>/hash
-video none -sound none -nothrottle -skip_gameinfo -seconds_to_run <s> -debug -debugger none -autoboot_script <lua>.
The ROM is copied from disks/ (SHA-1 checked vs config/medium.sha1 line 1) to the softlist name under .run/mame/roms.
MAME_EXE (path to mame.exe) is required; no default. Raw output only under .run/oracle/ (ignored). Stdlib only.
Each run gets -nvram_directory .run/oracle/<run>/nvram, a fresh copy of .run/mame/nvram_seed (cartridge EEPROM).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "extract"))
from rom import parse_vectors  # noqa: E402

LUA = os.path.join(ROOT, "scripts", "oracle", "lua")
OUT = os.path.join(ROOT, ".run", "oracle")
ROMPATH = ".run/mame/roms"
STAGED = os.path.join(ROOT, ROMPATH, "megadriv", "microm96", "m-machines 96mm96mdeddb.u1")
GOOD = "romset megadriv:microm96 is good"
TIMEOUT = 280  # one MAME run stays < 285 s
NVSEED = os.path.join(ROOT, ".run", "mame", "nvram_seed")  # per-run EEPROM seed (ignored)


def mame_exe():
    exe = os.environ.get("MAME_EXE")
    if not exe:
        sys.exit("mame: MAME_EXE is not set (path to mame.exe 0.289)")
    return exe


def hashpath():
    return os.path.join(os.path.dirname(mame_exe()), "hash")


def stage_rom():
    """Copy the disks/ ROM to the softlist file name; refuse on SHA-1 mismatch."""
    with open(os.path.join(ROOT, "config", "medium.sha1"), encoding="utf-8") as f:
        want, name = f.readline().rstrip("\n").split("  ", 1)
    src = os.path.join(ROOT, "disks", name)
    data = open(src, "rb").read()
    got = hashlib.sha1(data).hexdigest()
    if got != want:
        sys.exit(f"mame: ROM SHA-1 {got} != {want} ({name})")
    if not os.path.isfile(STAGED) or hashlib.sha1(open(STAGED, "rb").read()).hexdigest() != want:
        os.makedirs(os.path.dirname(STAGED), exist_ok=True)
        shutil.copyfile(src, STAGED)
    return data


def lua_path(lua):
    if os.path.isfile(lua):
        return os.path.abspath(lua)
    return os.path.join(LUA, lua if lua.endswith(".lua") else lua + ".lua")


def run(lua, frames=60, tag=None, secs=None):
    """One MAME run of a Lua probe; returns (run_id, events list, done flag).
    secs: emulated -seconds_to_run override (a loaded save state restores machine time, so a run from a state
    needs the state's time plus its own frames)."""
    stage_rom()
    lua = lua_path(lua)
    tag = tag or os.path.splitext(os.path.basename(lua))[0]
    os.makedirs(OUT, exist_ok=True)
    while True:  # run ids are unique per second
        run_id = f"{tag}_{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
        jsonl = os.path.join(OUT, run_id + ".jsonl")
        if not os.path.exists(jsonl):
            break
        time.sleep(1)
    env = dict(os.environ, ORACLE_LIB=os.path.join(LUA, "lib.lua").replace("\\", "/"),
               ORACLE_OUT=jsonl.replace("\\", "/"), ORACLE_TRACE=f".run/oracle/{run_id}",
               ORACLE_FRAMES=str(frames))
    secs = secs or 20 + (2 * frames) // 60
    # cartridge EEPROM: each run starts from the same seed copy (NVSEED, first copied from the old shared
    # nvram/ dir), so a kit save or a TT record never leaks into the next run
    nvdir = os.path.join(OUT, run_id, "nvram")
    if os.path.isdir(NVSEED):
        shutil.copytree(NVSEED, nvdir)
    cmd = [mame_exe(), "megadriv", "microm96", "-rompath", ROMPATH, "-hashpath", hashpath(),
           "-nvram_directory", nvdir.replace("\\", "/"),
           "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-seconds_to_run", str(secs),
           "-debug", "-debugger", "none", "-autoboot_script", lua]
    with open(os.path.join(OUT, run_id + ".log"), "w", encoding="utf-8") as log:
        try:
            subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            log.write(f"mame.py: timeout {TIMEOUT}s\n")
    events = []
    if os.path.isfile(jsonl):
        with open(jsonl, encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
    done = any(e.get("ev") == "done" for e in events)
    return run_id, events, done


def boot_rows(run_id, events):
    """boot.lua phase events -> boot.tsv rows (PCs only)."""
    rows = []
    for e in events:
        if e.get("ev") != "phase":
            continue
        hits = dict(zip(e["bp_addrs"], e["bp_hits"]))
        pcs = e["first_pcs"]
        entry = pcs[1] if len(pcs) > 1 and pcs[0] == "000000" else "-"
        rows.append([run_id, e["phase"], ",".join(pcs), entry,
                     *("yes" if hits.get(a, 0) else "no" for a in ("015918", "000100", "00028C", "00028E"))])
    return rows


BOOT_HEADER = ["run", "phase", "first_pcs", "entry_after_trap", "hit_015918", "control_fired", "hit_00028C",
               "fired_00028E"]
FACT_HEADER = ["run", "key", "value"]


def fact_rows(run_id, events):
    """rammap.lua fact events -> rammap.tsv rows, sorted; a `file:<path>:<size>` value becomes the file's sha1."""
    rows = []
    for e in events:
        if e.get("ev") != "fact":
            continue
        value = e["value"]
        if value.startswith("file:"):
            path = os.path.join(ROOT, value[5:].rsplit(":", 1)[0])
            value = hashlib.sha1(open(path, "rb").read()).hexdigest() if os.path.isfile(path) else "none"
        rows.append([run_id, e["key"], value])
    return sorted(rows)


def write_facts(path, rows):
    """Merge fact rows into PATH (header FACT_HEADER), rewritten sorted, LF."""
    old = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            old = [line.rstrip("\n").split("\t") for line in f][1:]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in [FACT_HEADER] + sorted(old + rows):
            f.write("\t".join(row) + "\n")


def probe():
    stage_rom()
    r = subprocess.run([mame_exe(), "-rompath", ROMPATH, "-hashpath", hashpath(), "-verifysoftlist", "megadriv"],
                       cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT)
    good = any(line.strip() == GOOD for line in r.stdout.splitlines())
    print(GOOD if good else f"mame: verifysoftlist did not report '{GOOD}' (rc {r.returncode})")
    run_id, events, done = run("vectors", frames=1, tag="probe")
    live = next((e["v"] for e in events if e.get("ev") == "vectors"), None)
    want = ["%08X" % v for v in parse_vectors(stage_rom())]
    match = done and live == want
    if match:
        print(f"mame: live vectors == rom.parse_vectors (64 longs, reset PC {want[1]}) run {run_id}")
    else:
        print(f"mame: live vectors mismatch or no done (done={done}) run {run_id}")
    return 0 if good and match else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    r = sub.add_parser("run")
    r.add_argument("lua")
    r.add_argument("--frames", type=int, default=60)
    r.add_argument("--tag")
    r.add_argument("--tsv")
    r.add_argument("--secs", type=int, help="emulated seconds cap (default 20 + 2*frames/60); raise for a state load")
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        return probe()
    run_id, events, done = run(a.lua, a.frames, a.tag, a.secs)
    print(f"mame: run {run_id} done={done} -> .run/oracle/{run_id}.jsonl")
    if a.tsv and done and any(e.get("ev") == "fact" for e in events):
        rows = fact_rows(run_id, events)
        write_facts(a.tsv, rows)
        for row in rows:
            print("\t".join(row))
    elif a.tsv and done:
        rows = boot_rows(run_id, events)
        new = not os.path.isfile(a.tsv)
        os.makedirs(os.path.dirname(os.path.abspath(a.tsv)), exist_ok=True)
        with open(a.tsv, "a", encoding="utf-8", newline="\n") as f:
            if new:
                f.write("\t".join(BOOT_HEADER) + "\n")
            for row in rows:
                f.write("\t".join(row) + "\n")
                print("\t".join(row))
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
