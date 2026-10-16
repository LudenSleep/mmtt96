"""Runtime PC coverage of the 68000 (maincpu) under MAME: boot, attract and a scripted race (lua/coverage.lua).

  --run <boot|attract|race>     one scenario run from cold boot, as chunks of <= CHUNK frames (separate MAME calls
                                chained by save states, each < 280 s); unique PCs + insn lengths kept in
                                .run/oracle/cov/<run>.pcs (run = cov_<scenario>_<UTC stamp>); chunk files deleted
  --write                       merge every kept .run/oracle/cov/*.pcs into config/oracle/coverage.tsv; trace PCs in
                                the vector table (< 0x100: PC 0 is a reset trace artifact) are dropped
  --check [--tsv PATH] [--regions PATH]
                                exit 0 iff the tsv (default config/oracle/coverage.tsv) is well-formed and lists >= 3
                                distinct runs covering boot, attract and race, and no executed byte lies in a non-code
                                row of the regions TSV (default config/regions.retail.tsv); else exit 1 naming the fault
  --report [--tsv PATH]         counts only: executed bytes (tsv rows) and insn starts (kept .pcs runs) per ROM range,
                                row count, lowest/highest executed ROM PC

coverage.tsv: `start<TAB>end<TAB>runs`, hex, end exclusive (= end of the last executed insn: PC + length from the
debugger `dasm` listing), runs = ';'-joined run ids executing every insn start in the row. Rows sorted and
non-overlapping; contiguous executed bytes merge into one row while the run set is the same (adjacent rows differ in
runs). ROM only (PC < 0x400000); RAM PCs are counted in the --write printout, not listed. Stdlib only.
"""
import argparse
import glob
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mame  # noqa: E402

ROOT = mame.ROOT
COV = os.path.join(ROOT, ".run", "oracle", "cov")
TSV = os.path.join(ROOT, "config", "oracle", "coverage.tsv")
REGIONS = os.path.join(ROOT, "config", "regions.retail.tsv")
HEADER = ["start", "end", "runs"]
ROM_END = 0x400000
VEC_END = 0x100  # vector table: longwords, never executed; a trace PC below this is an artifact
CHUNK = 900  # frames per MAME call; tracing runs at ~13 frames/s on menus, ~6 in a race
SCENARIOS = ("boot", "attract", "race")
RUN_RE = re.compile(r"^cov_(boot|attract|race)_\d{8}T\d{6}$")
_MENU = [1000, 1200, 1400, 1700, 2000, 2300, 2950]  # Start presses: title, mode, driver, name, track, ready
SCENARIO = {
    # cold boot to the title menu (menu visible from ~frame 900)
    "boot": dict(frames=1000, input="", snaps="1000"),
    # attract: title menu, then the demo race (starts ~frame 2400), run ~15 s into it
    "attract": dict(frames=3300, input="", snaps="900,2700,3300"),
    # 1 Player > Challenge > driver > name > track > ready; race starts ~frame 3060, accelerate (P1 B) held 9 s
    "race": dict(frames=3600, input=" ".join(f"{f}:P1 Start:5" for f in _MENU) + " 3060:P1 B:540 3300:P1 Left:20",
                 snaps="1200,1400,2160,2880,3300,3600"),
}


def run_scenario(name):
    sc = SCENARIO[name]
    run_id = f"cov_{name}_{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}"
    os.makedirs(COV, exist_ok=True)
    pcs = {}
    start, k, load = 0, 0, None
    while start < sc["frames"]:
        end = min(start + CHUNK, sc["frames"])
        save = f"{run_id}_s{end}" if end < sc["frames"] else None
        env = {"ORACLE_FROM": str(start), "ORACLE_INPUT": sc["input"], "ORACLE_SNAPS": sc["snaps"]}
        for key, val in (("ORACLE_LOAD", load), ("ORACLE_SAVE", save)):
            if val:
                env[key] = val
            else:
                os.environ.pop(key, None)
        os.environ.update(env)
        t0 = time.time()
        chunk, events, done = mame.run("coverage", frames=end, tag=f"{run_id}_c{k}")
        cover = next((e for e in events if e.get("ev") == "cover"), {})
        errors = [e.get("msg") for e in events if e.get("ev") == "error"]
        print(f"coverage: {chunk} frames {start}..{end} done={done} pcs={cover.get('pcs')} "
              f"unknown_len={cover.get('unknown_len')} {time.time() - t0:.0f}s", flush=True)
        if errors or not done or cover.get("unknown_len", 1):
            print(f"coverage: chunk failed ({errors or 'no done / unknown lengths'}); see .run/oracle/{chunk}.log", flush=True)
            return 1
        part = os.path.join(mame.OUT, chunk + ".pcs")
        with open(part, encoding="utf-8") as f:
            for line in f:
                pc, ln = line.split()
                pcs[int(pc, 16)] = int(ln, 16)
        os.remove(part)
        if load:
            os.remove(os.path.join(mame.OUT, "megadriv", load + ".sta"))  # MAME adds the driver dir
        load, start, k = save, end, k + 1
    out = os.path.join(COV, run_id + ".pcs")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for pc in sorted(pcs):
            f.write(f"{pc:06X}\t{pcs[pc]:X}\n")
    print(f"coverage: run {run_id} {len(pcs)} unique PCs -> {os.path.relpath(out, ROOT)}", flush=True)
    return 0


def load_runs():
    runs = {}
    for path in sorted(glob.glob(os.path.join(COV, "cov_*.pcs"))):
        run_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            runs[run_id] = {int(a, 16): int(b, 16) for a, b in (line.split() for line in f if line.strip())
                            if int(a, 16) >= VEC_END}
    return runs


def merge(runs):
    """Elementary intervals over all runs' [pc, pc+len) (ROM only) -> rows (start, end, sorted run ids)."""
    cover = {}  # byte address -> set of runs whose executed insns span it
    for run_id, pcs in runs.items():
        for pc, ln in pcs.items():
            if pc < ROM_END:
                for a in range(pc, pc + ln):
                    cover.setdefault(a, set()).add(run_id)
    rows = []
    for a in sorted(cover):
        key = ";".join(sorted(cover[a]))
        if rows and rows[-1][1] == a and rows[-1][2] == key:
            rows[-1][1] = a + 1
        else:
            rows.append([a, a + 1, key])
    return rows


def write():
    runs = load_runs()
    rows = merge(runs)
    os.makedirs(os.path.dirname(TSV), exist_ok=True)
    with open(TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(HEADER) + "\n")
        for s, e, key in rows:
            f.write(f"{s:06X}\t{e:06X}\t{key}\n")
    union = set().union(*(set(p) for p in runs.values())) if runs else set()
    ram = sum(1 for pc in union if pc >= ROM_END)
    print(f"coverage: {len(runs)} runs, {len(union)} unique PCs ({ram} outside ROM, not listed), "
          f"{len(rows)} rows -> {os.path.relpath(TSV, ROOT)}")
    return 0


def agreement(rows, regions=REGIONS):
    """Faults: executed bytes (rows of (start, end)) inside a non-code row of the regions TSV."""
    with open(regions, encoding="utf-8") as f:
        regs = [(int(c[0], 16), int(c[1], 16), c[2], c[3]) for c in (ln.split("	") for ln in f.read().splitlines()[1:])
                if len(c) == 6]
    faults = []
    for rs, re_, kind, name in regs:
        if kind == "code":
            continue
        hit = sum(max(0, min(e, re_) - max(s, rs)) for s, e in rows)
        if hit:
            faults.append(f"{os.path.relpath(regions, ROOT)}: {kind} row {name} 0x{rs:06X}-0x{re_:06X} has {hit} "
                          f"executed bytes")
    return faults


def check(path=TSV, regions=REGIONS):
    """Faults of a coverage.tsv (empty list = well-formed with >= 3 runs over all scenarios, agreeing with regions)."""
    if not os.path.isfile(path):
        return [f"{path}: missing"]
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    if not lines or lines[0].split("\t") != HEADER:
        return [f"{path}:1: header is not {'/'.join(HEADER)}"]
    faults, runs, prev, spans = [], set(), None, []
    for i, line in enumerate(lines[1:], 2):
        cols = line.split("\t")
        if len(cols) != 3:
            faults.append(f"{path}:{i}: {len(cols)} columns")
            continue
        try:
            s, e = int(cols[0], 16), int(cols[1], 16)
        except ValueError:
            faults.append(f"{path}:{i}: start/end not hex")
            continue
        ids = cols[2].split(";")
        bad = [r for r in ids if not RUN_RE.match(r)]
        if bad or ids != sorted(set(ids)):
            faults.append(f"{path}:{i}: run ids malformed or unsorted")
        if s >= e or e > ROM_END:
            faults.append(f"{path}:{i}: bad range")
        if prev:
            if s < prev[1]:
                faults.append(f"{path}:{i}: unsorted or overlaps previous row")
            elif s == prev[1] and cols[2] == prev[2]:
                faults.append(f"{path}:{i}: contiguous with previous row and same runs (not merged)")
        prev = (s, e, cols[2])
        spans.append((s, e))
        runs.update(ids)
    if prev is None:
        faults.append(f"{path}: no rows")
    if len(runs) < 3:
        faults.append(f"{path}: {len(runs)} distinct runs (< 3)")
    missing = [sc for sc in SCENARIOS if not any(r.startswith(f"cov_{sc}_") for r in runs)]
    if missing:
        faults.append(f"{path}: no run for scenario(s) {', '.join(missing)}")
    return faults + agreement(spans, regions)


REPORT_RANGES = [(0x0002EA, 0x01597A), (0x016DE6, 0x01FACC), (0x01FACC, 0x020000), (0x020000, 0x0477BA),
                 (0x0477BA, ROM_END)]


def report(path=TSV):
    with open(path, encoding="utf-8") as f:
        rows = [(int(c[0], 16), int(c[1], 16)) for c in (line.split("	") for line in f.read().splitlines()[1:])]
    starts = sorted({pc for pcs in load_runs().values() for pc in pcs if pc < ROM_END})
    for lo, hi in REPORT_RANGES:
        nbytes = sum(max(0, min(e, hi) - max(s, lo)) for s, e in rows)
        nstart = sum(1 for pc in starts if lo <= pc < hi)
        print(f"coverage: {lo:06X}-{hi:06X} executed_bytes={nbytes} insn_starts={nstart}")
    print(f"coverage: rows={len(rows)} lowest_pc={rows[0][0]:06X} highest_pc={starts[-1]:06X} "
          f"highest_end={rows[-1][1]:06X}" if rows else "coverage: rows=0")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", choices=SCENARIOS)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--report", action="store_true")
    ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--regions", default=REGIONS)
    a = ap.parse_args(argv)
    if a.run:
        return run_scenario(a.run)
    if a.write:
        return write()
    if a.report:
        return report(a.tsv)
    faults = check(a.tsv, a.regions)
    for fault in faults[:20]:
        print(f"coverage: {fault}")
    if not faults:
        print(f"coverage: {os.path.relpath(a.tsv, ROOT)} ok")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
