"""Firewall rung (G12): scan text files for runs of AS-style 68000 instruction lines.

  asm_leak.py [paths...]     default: every `git ls-files` path
  asm_leak.py --plant        write the synthetic fixture .run/mmtt96-health/plant/leak_fixture.asm, scan it (exit 1)

An instruction line = optional `label:`, then tab/space indent, a 68000 mnemonic with optional .b/.w/.l/.s, then
operands (one token, no inner blanks) or nothing, optional `; comment`. A label-only line neither counts nor breaks a
run. Exit 1 iff some file has a run >= RUN_CAP lines; prints path, line range and run length only, never the text.
Binary files (NUL in the first 8 KiB) are skipped. Stdlib only.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE = os.path.join(ROOT, ".run", "mmtt96-health", "plant", "leak_fixture.asm")
RUN_CAP = 12  # contiguous instruction lines that make a tracked text file an offender

CC = "(?:t|f|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le|hs|lo)"
MNEMONICS = (
    "move|movea|moveq|movem|movep|lea|pea|exg|swap|ext|clr|tst|tas|not|neg|negx|"
    "add|adda|addi|addq|addx|sub|suba|subi|subq|subx|and|andi|or|ori|eor|eori|"
    "cmp|cmpa|cmpi|cmpm|btst|bset|bclr|bchg|lsl|lsr|asl|asr|rol|ror|roxl|roxr|"
    "mulu|muls|divu|divs|abcd|sbcd|nbcd|chk|link|unlk|trap|trapv|stop|reset|illegal|"
    "nop|rts|rte|rtr|jmp|jsr|bra|bsr|b" + CC + "|db" + CC + "|s" + CC)
INSN = re.compile(r"^(?:[A-Za-z_.][\w.]*:)?[ \t]+(?:" + MNEMONICS + r")(?:\.[bwls])?"
                  r"(?:[ \t]+[^\s;]+)?[ \t]*(?:;.*)?$", re.IGNORECASE)
LABEL = re.compile(r"^[A-Za-z_.][\w.]*:[ \t]*$")

# Synthetic, not game code: a made-up counting loop in AS syntax, long enough to trip RUN_CAP.
FIXTURE_TEXT = "".join("\t%s\n" % l for l in (
    "moveq\t#0,d0", "moveq\t#15,d1", "lea\tbuf(pc),a0", "clr.w\td2") + tuple(
    "addq.w\t#1,d%d" % (i % 3) for i in range(6)) + (
    "move.w\td0,(a0)+", "tst.w\td2", "bne.s\tdone", "dbf\td1,loop", "rts"))


def tracked():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, stdout=subprocess.PIPE, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def runs(path):
    """[(first line, last line, length)] of instruction runs >= RUN_CAP in one file (1-based lines)."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return []
    if b"\0" in data[:8192]:
        return []
    found, n, first, last = [], 0, 0, 0
    for i, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
        if INSN.match(line):
            if n == 0:
                first = i
            n, last = n + 1, i
        elif LABEL.match(line):
            continue
        else:
            if n >= RUN_CAP:
                found.append((first, last, n))
            n = 0
    if n >= RUN_CAP:
        found.append((first, last, n))
    return found


def main(argv):
    if argv == ["--plant"]:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        with open(FIXTURE, "w", encoding="utf-8", newline="\n") as f:
            f.write(FIXTURE_TEXT)
        argv = [FIXTURE]
    paths = argv or tracked()
    bad = 0
    for p in paths:
        for first, last, n in runs(os.path.join(ROOT, p) if not os.path.isabs(p) else p):
            print("asm_leak: %s:%d-%d run %d >= %d" % (p.replace("\\", "/"), first, last, n, RUN_CAP))
            bad += 1
    print("asm_leak: %d files scanned, %d runs >= %d" % (len(paths), bad, RUN_CAP))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
