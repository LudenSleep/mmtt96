# T4: aggregate slots.lua JSONL runs into config/oracle/slots.tsv (writes per field, slots hit, writers, bp counts).
# Env: any Python 3; input .run/oracle/t4_*.jsonl from scripts/oracle/lua/slots.lua (scenarios: .run/t4/scen.sh challenge|proleague|attract).
# Run: PY scripts/oracle/slots_agg.py <run.jsonl>... > config/oracle/slots.tsv (then re-add the comment header).
import json, sys, collections
CLEAR = {0x000260, 0x01D2B6, 0x01F834, 0x01F854}  # block clears (init / mode setup), excluded
SLOT = [("f00", 0x00), ("f12", 0x12), ("f24", 0x24), ("f36", 0x36), ("f48", 0x48), ("f5A", 0x5A)]
PAIR = [("w00", 0x0), ("w02", 0x2), ("f00_a", 0x4), ("f12_a", 0x6), ("f00_b", 0x8), ("f12_b", 0xA),
        ("f5A_a", 0xC), ("f48_a", 0xE), ("f5A_b", 0x10), ("f48_b", 0x12)]
print("run\tstruct\tfield\toffset\tsize\taddrs\twrites\twriters\tfirst\tlast\tbp153B6\tbp68D2")
for path in sys.argv[1:]:
    run = path.rsplit("/", 1)[-1].replace(".jsonl", "")
    W = collections.defaultdict(lambda: [0, set(), 10**9, 0]); bp = {}
    for l in open(path):
        o = json.loads(l)
        if o["ev"] == "w":
            a, z, pc = o["key"].split("|"); a, z, pc = int(a, 16), int(z), int(pc, 16)
            if pc in CLEAR: continue
            e = W[(a, z)]; e[0] += o["c"]; e[1].add(pc); e[2] = min(e[2], o["f"]); e[3] = max(e[3], o["l"])
        elif o["ev"] == "bp": bp[o["addr"].upper()] = o["c"]
    def row(st, f, off, addrs):
        hits = [(a, z) for (a, z) in W if a in addrs]
        sizes = sorted({z for _, z in hits}) or ["-"]
        n = sum(W[k][0] for k in hits); wr = set().union(*[W[k][1] for k in hits]) if hits else set()
        fi = min([W[k][2] for k in hits], default=0); la = max([W[k][3] for k in hits], default=0)
        print(f"{run}\t{st}\t{f}\t0x{off:X}\t{','.join(map(str,sizes))}\t{len({a for a,_ in hits})}/{len(addrs)}\t{n}\t{len(wr)}\t{fi}\t{la}\t{bp.get('153B6',0)}\t{bp.get('68D2',0)}")
    for f, off in SLOT: row("slot", f, off, {0xFFD032 + off + 2 * s for s in range(9)})
    for f, off in PAIR: row("pairrec", f, off, {0xFFD218 + off})
