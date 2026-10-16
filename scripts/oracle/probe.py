"""1.9 T2 controlled RAM probe: a BASE and a VARIANT run from one save state; reports the RAM words whose per-frame
series diverge (what a given input or value affects).

  run --state S --frames N [--input I] [--var-input I] [--var-poke P] [--what TEXT] [--kind controlled|census] [--write]
      I = drive.lua SCEN_INPUT "frame:field:hold ..." (the variant uses --var-input when given, else --input);
      P = SCEN_POKES "frame:addr:bytes:value ..." (hex addr/value), applied to the variant only.
      Each run: scripts/oracle/lua/probe.lua (drive.lua + the whole work RAM FF0000-FFFFFF after every frame to
      .run/oracle/<run>_ram.bin). Divergent words (first frame, frames diverged) -> .run/oracle/<probe>_diverge.tsv;
      --write appends one row to config/oracle/probes.tsv (addresses, frames and counts only);
      --control identical marks a no-variant control row (pass iff 0 words diverge).
  --self-test [--write]
      controls, all must pass (exit 0): a fresh state (attract, frame 600 -> probe_selftest); writers.lua from it:
      ram_frame_counter FFC220 written every frame (positive), ROM header 000100 never (negative); an identical base/variant
      pair diverges nowhere (negative); a poke of FFC220 at frame 10 diverges at FFC220 (positive).
      Rows -> .run/oracle/probes_selftest.tsv (--write: also config/oracle/probes.tsv).
States: .run/states/megadriv/<S>.sta (scripts/oracle/lua/scenarios.lua saves; docs/ops/ops-tools.md "scenarios").
Runs from a state use mame.py --secs 900 (a state restores machine time); each run has its own EEPROM copy.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import mame  # noqa: E402
import writers_agg  # noqa: E402

ORACLE = os.path.join(ROOT, ".run", "oracle")
OUT = os.path.join(ROOT, "config", "oracle", "probes.tsv")
SELF = os.path.join(ORACLE, "probes_selftest.tsv")
COLS = ["probe_id", "run", "control", "kind", "scen", "what", "result"]
HEADER = """# 1.9 T2 probe results: controlled RAM probes (base vs variant from one save state) and their controls.
# Env: MAME 0.289 via scripts/oracle/probe.py (scripts/oracle/lua/probe.lua, writers.lua over drive.lua).
# run = base+variant run ids (or the writers run); control = which control the row is (- for a probe);
# kind = controlled|census; scen = save state; result = pass|fail for controls, else divergent RAM words:
#   count, then addr@first-frame x frames-diverged (earliest first, top 24). Full lists stay in .run/oracle/.
# Built by: PY scripts/oracle/probe.py run ... --write | --self-test --write"""
RAM, WORDS = 0x10000, 0x8000
SEL = ("SCEN", "SCEN_LOAD", "SCEN_INPUT", "SCEN_POKES", "SCEN_SAVE", "SCEN_SNAPS", "SCEN_PEEK", "WATCH")


def mame_run(lua, frames, tag, **env):
    """One mame.py run with drive.lua env vars set (others of SEL cleared); returns run id; exits on no done."""
    old = {k: os.environ.pop(k, None) for k in SEL}
    os.environ.update({k: v for k, v in env.items() if v})
    try:
        run_id, events, done = mame.run(lua, frames, tag, secs=900)
    finally:
        for k in SEL:
            os.environ.pop(k, None)
            if old[k] is not None:
                os.environ[k] = old[k]
    if not done or any(e.get("ev") == "error" for e in events):
        sys.exit(f"probe: run {run_id} incomplete or input error (see .run/oracle/{run_id}.log)")
    return run_id


def series_run(state, frames, tag, inputs="", pokes=""):
    return mame_run("probe", frames, tag, SCEN="probe", SCEN_LOAD=state, SCEN_INPUT=inputs, SCEN_POKES=pokes)


def diverge(base, var, frames):
    """{word addr: [first frame, frames diverged]} over frames 1..frames of two _ram.bin series."""
    out = {}
    with open(os.path.join(ORACLE, base + "_ram.bin"), "rb") as fa, open(os.path.join(ORACLE, var + "_ram.bin"), "rb") as fb:
        for fr in range(1, frames + 1):
            x, y = fa.read(RAM), fb.read(RAM)
            if len(x) < RAM or len(y) < RAM:
                sys.exit(f"probe: series shorter than {frames} frames ({base}, {var})")
            if x == y:
                continue
            mx, my = memoryview(x).cast("H"), memoryview(y).cast("H")
            for blk in range(0, WORDS, 256):
                if x[2 * blk:2 * blk + 512] == y[2 * blk:2 * blk + 512]:
                    continue
                for i in range(blk, blk + 256):
                    if mx[i] != my[i]:
                        r = out.setdefault(0xFF0000 + 2 * i, [fr, 0])
                        r[1] += 1
    return out


def summary(d, top=24):
    if not d:
        return "0 words"
    order = sorted(d.items(), key=lambda x: (x[1][0], x[0]))
    return f"{len(d)} words; " + ",".join(f"{a:06X}@{f}x{n}" for a, (f, n) in order[:top])


def write_rows(path, rows):
    """Append rows to PATH (header when new); probe ids P<nnn> allocated per file in order."""
    new = not os.path.isfile(path)
    n = 0
    if not new:
        n = sum(1 for l in open(path, encoding="utf-8") if l.startswith("P"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        if new:
            f.write(HEADER + "\n" + "\t".join(COLS) + "\n")
        for r in rows:
            n += 1
            f.write("\t".join([f"P{n:03d}"] + r) + "\n")


def probe(a):
    base = series_run(a.state, a.frames, "t2p_base", a.input)
    var = series_run(a.state, a.frames, "t2p_var", a.var_input or a.input, a.var_poke)
    d = diverge(base, var, a.frames)
    with open(os.path.join(ORACLE, f"{var}_diverge.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("addr\tfirst\tframes\n")
        for addr, (fr, n) in sorted(d.items()):
            f.write(f"{addr:06X}\t{fr}\t{n}\n")
    what = a.what or f"input {a.var_input or a.input or '-'}; poke {a.var_poke or '-'}"
    verdict = ("pass " if not d else "fail ") if a.control == "identical" else ""
    row = [f"{base}+{var}", a.control, a.kind, a.state, what, verdict + summary(d)]
    print("probe: " + "\t".join(row))
    print(f"probe: full list .run/oracle/{var}_diverge.tsv")
    if a.write:
        write_rows(OUT, [row])
    return 0


def self_test(a):
    st = "probe_selftest"
    mk = mame_run("drive", 620, "t2st_state", SCEN="attract", SCEN_SAVE=f"600:{st}")
    print(f"probe: state {st} from {mk}")
    w = mame_run("writers", 300, "t2st_writers", SCEN="probe", SCEN_LOAD=st)
    ok, detail, pos_ok, neg_ok = writers_agg.controls(w, pos_from=2)  # from a state: every recorded frame
    pos, neg = detail.split("; ")
    b1 = series_run(st, 300, "t2st_base")
    b2 = series_run(st, 300, "t2st_same")
    same = diverge(b1, b2, 300)
    pk = series_run(st, 300, "t2st_poke", pokes="10:FFC220:2:1234")
    poked = diverge(b1, pk, 300)
    res = [
        [w, "writers-positive", "controlled", st, "ram_frame_counter FFC220 written every frame", ("pass " if pos_ok else "fail ") + pos],
        [w, "writers-negative", "controlled", st, "ROM header 000100 never written", ("pass " if neg_ok else "fail ") + neg],
        [f"{b1}+{b2}", "identical", "controlled", st, "identical base/variant pair (no input, no poke)",
         ("pass " if not same else "fail ") + summary(same)],
        [f"{b1}+{pk}", "poke-positive", "controlled", st, "poke 10:FFC220:2:1234 (variant only)",
         ("pass " if 0xFFC220 in poked else "fail ") + summary(poked, 8)],
    ]
    for r in res:
        print("probe: " + "\t".join(r))
    write_rows(SELF, res)
    if a.write:
        write_rows(OUT, res)
    good = all(r[-1].startswith("pass") for r in res)
    print(f"probe: self-test {'PASS' if good else 'FAIL'} ({sum(r[-1].startswith('pass') for r in res)}/4 controls)")
    return 0 if good else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", nargs="?", choices=["run"])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--state")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--input", default="")
    ap.add_argument("--var-input", default="")
    ap.add_argument("--var-poke", default="")
    ap.add_argument("--what")
    ap.add_argument("--kind", choices=["controlled", "census"], default="controlled")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--control", default="-", help="identical: a no-variant control row (pass iff 0 words)")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test(a)
    if a.cmd != "run" or not a.state:
        ap.error("need --self-test or: run --state S ...")
    return probe(a)


if __name__ == "__main__":
    sys.exit(main())
