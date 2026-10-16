# T6: aggregate values.lua JSONL runs into config/oracle/values.tsv (per ram.tsv row and struct field: writes, value range).
# Env: any Python 3; input .run/oracle/t6_*.jsonl from scripts/oracle/lua/values.lua (scenarios: scripts/oracle/lua/scenarios.lua).
# Run: PY scripts/oracle/values_agg.py <run.jsonl>... [--seq NAME]  (--seq prints a target's change sequences per run; analysis only).
import argparse, collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "config", "oracle", "values.tsv")
HEADER = """# T6 write-value census: every config/names/ram.tsv row (field -) and struct field (struct.field, addr of instance 0).
# Env: MAME 0.289 via scripts/oracle/mame.py run scripts/oracle/lua/values.lua (Lua write taps reinstalled per frame,
#   positive control ram_frame_counter writes in last 100 frames); scenarios scripts/oracle/lua/scenarios.lua.
# Columns: scenarios = runs with writes / runs; writes summed over runs (struct: over instances); distinct = union of
#   per-access values over runs (>= when a run capped at 4096); min/max per access, normalised by tap mask (byte vs word);
#   writers = distinct writer pcs: top 8 by count. Writer pc is cpu PC at the tap and may be ahead of the writing insn.
# Built by: PY scripts/oracle/values_agg.py <run jsonl>..."""


def load(path):
    ev = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    ctrl = [e for e in ev if e["ev"] == "control"]
    if not ctrl or ctrl[0]["result"] != "pass" or not any(e["ev"] == "done" for e in ev):
        sys.exit(f"values_agg: refusing {path}: control not pass or run incomplete")
    return os.path.basename(path).replace(".jsonl", ""), [e for e in ev if e["ev"] == "t"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--seq")
    a = ap.parse_args()
    runs = [load(p) for p in a.runs]
    if a.seq:
        for run, ts in runs:
            for t in ts:
                if a.seq in (t["name"], t["field"]) and "seq" in t:
                    print(f"{run}\t{t['field']}\t{t.get('inst', '-')}\t{t['addr']}\t"
                          + " ".join(f"{f}:{v:X}" for f, v in t["seq"]))
        return 0
    order, agg = [], {}
    for run, ts in runs:
        for t in ts:
            k = (t["name"], t["field"])
            if k not in agg:
                order.append(k)
                agg[k] = dict(addr=t["addr"], size=t["size"], runs=set(), c=0, mn=None, mx=None, dist=set(),
                              nd=0, capped=False, pcs=collections.Counter())
            g = agg[k]
            if t.get("inst", 0) == 0:
                g["addr"] = t["addr"]
            if t["c"]:
                g["runs"].add(run)
                g["c"] += t["c"]
                g["mn"] = t["mn"] if g["mn"] is None else min(g["mn"], t["mn"])
                g["mx"] = t["mx"] if g["mx"] is None else max(g["mx"], t["mx"])
                g["pcs"].update({pc: c for pc, c in t["pcs"]})
                if t.get("dist") is None:
                    g["capped"] = True
                    g["nd"] = max(g["nd"], t["nd"])
                else:
                    g["dist"].update(t["dist"])
    lines = [HEADER, "addr\tfield\tsize\tscenarios\twrites\tdistinct\tmin\tmax\twriters"]
    for k in order:
        g = agg[k]
        nd = max(len(g["dist"]), g["nd"])
        dist = f">={nd}" if g["capped"] else str(nd)
        hx = lambda v: "-" if v is None else f"0x{v:X}"
        top = sorted(g["pcs"].items(), key=lambda x: (-x[1], x[0]))[:8]
        wr = str(len(g["pcs"])) + (":" + ",".join(pc for pc, _ in top) if top else "")
        lines.append(f"0x{g['addr']}\t{k[1]}\t0x{g['size']:X}\t{len(g['runs'])}/{len(runs)}\t{g['c']}\t{dist}\t"
                     f"{hx(g['mn'])}\t{hx(g['mx'])}\t{wr}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"values_agg: {len(order)} rows from {len(runs)} runs -> config/oracle/values.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
