# Encoding map (phase 1.4 T3; coverage phase 1.6 T5)

How the original encodings of Micro Machines Turbo Tournament 96 map onto assembler behaviour, which assembler the
build pins and why, and whether the code is hand-written or compiler output. Prose and tables only: no bytes, no
instruction listings, no game addresses beyond region ids. Operand forms use Motorola notation (`<ea>`, `Dn`, `An`,
`#imm`, `d16`, `d8`).

## Pinned assembler and flags

- Assembler: Macroassembler AS V1.42 Bld 313 (`asw` + `p2bin` from the same snapshot; pin and sha256 in
  `docs/ops/ops-setup-decomp.md`, "Version pins").
- `asw` flags: `-q -xx -n -U -i .`. None of them changes an encoding: `-q` silent, `-xx` extended error messages,
  `-n` error numbers in messages, `-U` case-sensitive symbols, `-i .` include path.
- Source header (written by `scripts/build/split.py`): `cpu 68000`, `supmode on` (allows the SR forms),
  `padding off` (no implicit alignment bytes), then `org 0`.
- `p2bin` with no options: address range deduced from the object, flat image.
- Region end assert: `if * <> $end` / `error "<id>: end mismatch"` / `endif` stops the build (rc 2, no image).
- AS has no global optimisation switches comparable to asm68k `/o`: it emits what the source says, except class E.

## Why AS replaced clownassembler for the build

clownassembler (asm68k-compatible, the phase 1.3 all-data baseline) rewrites CMP, ADD, SUB, AND and OR with a
literal source to the immediate instruction form (CMPI, ADDI, ...) unconditionally; only the warning is switchable,
and its CMP operand table has no literal-source form at all (R1.4-002). The game uses the `<ea>,Dn` form of CMP with
an immediate source at 1254 sites across the verified code (byte/word/long 345/898/11), so no clownassembler source,
suffix, `/o` switch or `opt` directive can reproduce them (switch probe: ow op os omq oaq osq an c w ws v d oz, all
identical). The lever ladder (suffix, `/o` switch, `opt` directive, converter fix) ended without a lever, which
triggered the developer-approved fallback: AS keeps the form the source names. With converter fixes for classes B-D
and the class E form, all 194 verified code regions assemble back to the original under AS (listing self-check
194/194). A hybrid build (clownassembler for most, AS for class A regions) was rejected: two dialects and include
chains for one class AS handles by default.

## Disagreement classes

Every disagreement found across the 194 verified code regions (same-size, aligned; no size drift anywhere).

| Class | Original form | clownassembler v1.1.3 | AS V1.42 default | Forcing / fix | Kind |
|---|---|---|---|---|---|
| A | CMP `<ea>,Dn` with an immediate `<ea>` (never CMPI to a data register; CMPI only to memory) | always CMPI; no lever (R1.4-002) | `cmp #imm,Dn` keeps the `<ea>,Dn` form; `cmpi` gives CMPI | write the mnemonic the original used; no flag needed | assembler |
| A' | ADDI/SUBI/ANDI/ORI to `Dn` are the immediate forms in the original | I-form (matches) | `add/and #imm,Dn` gives the `<ea>` form; `addi/andi/subi/ori` give the I-form | write the explicit I mnemonic (the listing does) | assembler (no disagreement once spelled) |
| B | MOVEM with a `(d16,PC)` source | encodes correctly | encodes correctly | converter: PC base is the instruction address + 4 (mask word first) | converter |
| C | ORI/ANDI/EORI to CCR or SR | assembler error (destination missing) | same | converter: restore the `ccr`/`sr` operand the Ghidra listing drops; AS needs `supmode on` for SR | converter |
| D | `(d8,PC,Xn)` | out-of-range error (wrong target) | same | converter: use the target Ghidra prints as is | converter |
| E | `(d16,An)` with a zero displacement (regions code_007EF4, code_035890, code_03EEA2, code_03F278) | not isolated (those regions also carried class A) | shrinks to `(An)` ("useless displacement") | size the displacement: `0.w(An)`; `db.py listing` writes this form | assembler |

A zero `(d16,PC)` needs nothing: the 68000 has no PC form without a displacement, so AS keeps the word.

## Trap set: agreements

Forms where the original and AS agree once the size is spelled out (the listing always spells it):

| Trap | AS behaviour |
|---|---|
| Short / word branches | explicit `.s` / `.w` honoured |
| Absolute short / long | explicit `.w` / `.l` honoured |
| MOVEQ and quick forms (ADDQ/SUBQ) | emitted only when written; no automatic MOVEQ/ADDQ substitution |
| LEA / PEA | as written; PEA does not occur in the verified code |
| PC-relative `(d16,PC)` | as written |
| Jump tables | assemble as written (code_010BA0) |

## Gate regions (milestone probe set)

Five verified code regions, each fully MAME-covered (coverage 1.00, at least 3 runs), switched to instruction source
under AS; `make clean && make build` reports `split: src 5 regions` and `build/mmtt96.bin: OK`; the all-data build
(`make build SRC=`) stays OK.

| Region | Traps covered |
|---|---|
| code_0139B0 | short and word branches, absolute short and long, LEA, MOVEQ, quick, immediate forms, calls |
| code_01F800 | short and word branches, absolute long, LEA, MOVEQ, quick, immediate forms, calls |
| code_010BA0 | jump table, PC-relative, LEA, absolute short |
| z80_upload_driver | short and word branches, absolute long, LEA, calls |
| vdp_dma | short branch, absolute long, immediate forms |

Not in the gate: class A, because no verified region containing it is fully covered (best 0.99, code_0429E2); its AS
behaviour is proven by the synthetic probe and by the 194/194 listing self-check. Data-in-code: none in the gate
regions. PEA: absent from the verified code.

## Hand-written or compiler-generated

Verdict: hand-written 68000 assembly. No compiler phases are needed (kit phases 4 and 7 stay out) unless later
evidence contradicts this.

Evidence classes, counted over all 194 verified code regions:

| Evidence class | Compiler signature | Observed |
|---|---|---|
| Frame setup and teardown | LINK/UNLK pairs | none |
| Frame-local access | negative displacements off the frame register | none |
| Caller stack cleanup | stack adjust after calls | none |
| Argument pushes | PEA | none |
| Position independence | heavy PC-relative addressing | 6 instructions only |
| Immediate loads | compilers pick MOVEQ automatically | MOVE of a small immediate to `Dn` is kept long where written |
| Compare form | one canonical compare form | CMP vs CMPI chosen by destination, an assembler rule applied by hand-written source |

## Coverage (forms)

Every encoding form of the verified code, one row each; the health rung `scripts/census/encodings.py` fails on a
form absent from this table or with a stale count. Form = `<mnemonic>[.<size>]:<operand modes>` (conditions
collapsed to `bcc`/`dbcc`/`scc`; branches carry `.s`/`.w` and no operand).

<!-- encmap:begin -->
Denominators: 247 verified code regions, 38509 instructions (Capstone sweep, boundaries.py skip rules). Evidence = the first verified region (address order) holding the form, i.e. assembled back to the original under AS by the srcform health pair; class A-E forms also cite their synthetic probe (P16T5-A, P16T5-A2, P16T5-B, P16T5-C, P16T5-D, P16T5-E; log T5.c1). Generated by `scripts/census/encodings.py --write-map`; never hand-edited.

| Form | Count | Evidence |
|---|---|---|
| `add.b:absw,dn` | 1 | code_012FF6 |
| `add.b:dn,absw` | 1 | code_010EE2 |
| `add.b:dn,d16an` | 3 | code_00A6C2 |
| `add.b:dn,dn` | 30 | code_00266E |
| `add.b:dn,ind` | 1 | code_010EE2 |
| `add.b:postinc,dn` | 2 | code_0002FA |
| `add.l:dn,absw` | 18 | code_0068D2 |
| `add.l:dn,dn` | 10 | code_001978 |
| `add.l:postinc,dn` | 1 | code_03D56A |
| `add.w:absl,dn` | 6 | code_01005A |
| `add.w:absw,dn` | 240 | code_00266E |
| `add.w:an,dn` | 5 | code_005BBA |
| `add.w:d16an,dn` | 9 | code_00B25C |
| `add.w:d8anxn,dn` | 26 | code_00589A |
| `add.w:dn,absl` | 2 | code_010EE2 |
| `add.w:dn,absw` | 89 | code_00143C |
| `add.w:dn,d16an` | 4 | code_00C998 |
| `add.w:dn,d8anxn` | 1 | code_000A8C |
| `add.w:dn,dn` | 271 | init |
| `add.w:dn,ind` | 7 | code_00266E |
| `add.w:dn,postinc` | 1 | code_00C998 |
| `add.w:ind,dn` | 5 | code_017444 |
| `add.w:postinc,dn` | 12 | code_004D34 |
| `adda.l:an,an` | 1 | imp_decrunch_core |
| `adda.l:dn,an` | 25 | code_001978 |
| `adda.l:postinc,an` | 2 | imp_decrunch_core |
| `adda.w:absw,an` | 3 | code_01005A |
| `adda.w:d8anxn,an` | 1 | code_017728 |
| `adda.w:dn,an` | 66 | code_001978 |
| `addi.b:imm,absl` | 1 | code_00A6C2 |
| `addi.b:imm,absw` | 11 | code_0015C0 |
| `addi.b:imm,d16an` | 10 | code_009CBA |
| `addi.b:imm,dn` | 68 | P16T5-A2; code_00266E |
| `addi.l:imm,absw` | 8 | code_001978 |
| `addi.l:imm,dn` | 7 | P16T5-A2; code_0012B4 |
| `addi.w:imm,absw` | 40 | code_00266E |
| `addi.w:imm,dn` | 509 | P16T5-A2; code_00102E |
| `addi.w:imm,ind` | 1 | code_00C998 |
| `addq.b:imm,absl` | 1 | code_00A6C2 |
| `addq.b:imm,absw` | 15 | code_0002FA |
| `addq.b:imm,d16an` | 17 | code_00BE02 |
| `addq.b:imm,d8anxn` | 1 | code_006286 |
| `addq.b:imm,dn` | 114 | code_001978 |
| `addq.b:imm,ind` | 10 | code_009CBA |
| `addq.l:imm,absw` | 4 | code_01F96A |
| `addq.l:imm,an` | 9 | code_00A6C2 |
| `addq.l:imm,dn` | 1 | code_007BA4 |
| `addq.w:imm,absl` | 9 | code_00855A |
| `addq.w:imm,absw` | 261 | code_0002FA |
| `addq.w:imm,an` | 170 | code_0002FA |
| `addq.w:imm,d16an` | 10 | code_005BBA |
| `addq.w:imm,d8anxn` | 7 | code_0002FA |
| `addq.w:imm,dn` | 431 | code_0002FA |
| `addq.w:imm,ind` | 14 | code_00A6C2 |
| `addq.w:imm,postinc` | 1 | code_00C998 |
| `addx.b:dn,dn` | 17 | imp_decrunch_core |
| `addx.l:dn,dn` | 1 | imp_decrunch_core |
| `addx.w:dn,dn` | 1 | imp_decrunch_core |
| `and.b:absl,dn` | 1 | code_012FF6 |
| `and.b:absw,dn` | 34 | code_00143C |
| `and.b:dn,dn` | 7 | code_00266E |
| `and.l:dn,dn` | 5 | code_0068D2 |
| `and.w:dn,dn` | 8 | code_0132FC |
| `andi.b:imm,absw` | 25 | code_00266E |
| `andi.b:imm,d16an` | 3 | code_009CBA |
| `andi.b:imm,dn` | 171 | P16T5-A2; init |
| `andi.l:imm,dn` | 6 | P16T5-A2; code_001978 |
| `andi.w:imm,absw` | 42 | code_00266E |
| `andi.w:imm,d16an` | 3 | code_01ACFC |
| `andi.w:imm,dn` | 728 | P16T5-A2; code_0002FA |
| `andi.w:imm,ind` | 3 | code_012FF6 |
| `asl.b:imm,dn` | 3 | code_010EE2 |
| `asl.l:imm,dn` | 14 | code_013BD6 |
| `asl.w:imm,dn` | 76 | code_000A8C |
| `asr.b:imm,dn` | 1 | code_00A6C2 |
| `asr.w:imm,dn` | 23 | code_009CBA |
| `bcc.s:none` | 4844 | init |
| `bcc.w:none` | 916 | code_0002FA |
| `bchg.b:imm,dn` | 1 | code_007AB4 |
| `bclr.b:dn,dn` | 1 | code_0054E4 |
| `bclr.b:imm,dn` | 16 | code_0054E4 |
| `bra.s:none` | 747 | init |
| `bra.w:none` | 439 | code_0002FA |
| `bset.b:dn,dn` | 1 | code_0054E4 |
| `bset.b:imm,dn` | 13 | code_0054E4 |
| `bsr.s:none` | 58 | code_0015C0 |
| `bsr.w:none` | 1550 | code_0002FA |
| `btst.b:imm,absl` | 3 | code_016DE6 |
| `btst.b:imm,dn` | 32 | code_0002FA |
| `btst.b:imm,ind` | 5 | code_0054E4 |
| `btst.l:dn,ind` | 1 | init |
| `clr.b:absl` | 4 | code_007790 |
| `clr.b:absw` | 23 | code_0045CE |
| `clr.b:d8anxn` | 1 | code_00C998 |
| `clr.b:dn` | 46 | code_005426 |
| `clr.b:postinc` | 7 | code_0002FA |
| `clr.l:absw` | 14 | code_00266E |
| `clr.l:dn` | 101 | code_0012B4 |
| `clr.l:postinc` | 4 | code_01062E |
| `clr.w:absl` | 29 | code_001978 |
| `clr.w:absw` | 889 | code_0002FA |
| `clr.w:d16an` | 6 | code_005BBA |
| `clr.w:d8anxn` | 3 | code_000A8C |
| `clr.w:dn` | 392 | code_0002FA |
| `clr.w:ind` | 5 | code_009B82 |
| `clr.w:postinc` | 7 | code_004D34 |
| `cmp.b:absl,dn` | 8 | code_03DE0A |
| `cmp.b:absw,dn` | 7 | code_00266E |
| `cmp.b:d8anxn,dn` | 1 | code_00F0C2 |
| `cmp.b:dn,dn` | 12 | code_000FCE |
| `cmp.b:imm,dn` | 360 | P16T5-A; code_0002FA |
| `cmp.b:ind,dn` | 2 | code_0108C2 |
| `cmp.b:postinc,dn` | 3 | code_010EE2 |
| `cmp.l:absw,dn` | 12 | code_00855A |
| `cmp.l:dn,dn` | 2 | code_040A18 |
| `cmp.l:imm,dn` | 11 | P16T5-A; code_0015C0 |
| `cmp.l:ind,dn` | 1 | code_00855A |
| `cmp.w:absl,dn` | 18 | code_01008C |
| `cmp.w:absw,dn` | 257 | code_0002FA |
| `cmp.w:d16an,dn` | 14 | code_00266E |
| `cmp.w:d8anxn,dn` | 10 | code_00C998 |
| `cmp.w:dn,dn` | 133 | code_0002FA |
| `cmp.w:imm,dn` | 1166 | P16T5-A; code_0002FA |
| `cmp.w:ind,dn` | 11 | code_00C998 |
| `cmp.w:postinc,dn` | 6 | code_0045CE |
| `cmpa.l:an,an` | 2 | imp_decrunch_core |
| `cmpi.b:imm,absl` | 3 | data_01A4C8 |
| `cmpi.b:imm,absw` | 41 | code_0002FA |
| `cmpi.b:imm,d16an` | 7 | code_009CBA |
| `cmpi.b:imm,d8anxn` | 1 | code_00FC54 |
| `cmpi.b:imm,ind` | 7 | code_00266E |
| `cmpi.b:imm,postinc` | 2 | code_00BC1A |
| `cmpi.b:imm,predec` | 3 | code_00BE02 |
| `cmpi.l:imm,absw` | 7 | code_0002FA |
| `cmpi.l:imm,ind` | 2 | imp_decrunch |
| `cmpi.w:imm,absl` | 35 | code_00143C |
| `cmpi.w:imm,absw` | 1294 | code_0002FA |
| `cmpi.w:imm,d16an` | 6 | code_005BBA |
| `cmpi.w:imm,d8anxn` | 9 | code_000A8C |
| `cmpi.w:imm,ind` | 29 | code_00266E |
| `cmpi.w:imm,postinc` | 3 | code_0068D2 |
| `cmpm.b:an,an` | 4 | code_00C998 |
| `dbcc.w:dn` | 490 | init |
| `divu.w:dn,dn` | 21 | code_00B25C |
| `divu.w:imm,dn` | 14 | code_0129DE |
| `eor.b:dn,dn` | 3 | code_007B66 |
| `eor.l:dn,dn` | 1 | code_001978 |
| `eor.w:dn,dn` | 33 | code_001978 |
| `eori.b:imm,dn` | 3 | code_00266E |
| `jmp:absl` | 125 | code_001978 |
| `jmp:absw` | 10 | code_00266E |
| `jmp:ind` | 4 | code_016E0E |
| `jsr:absl` | 1133 | code_0002FA |
| `jsr:absw` | 120 | code_00266E |
| `jsr:ind` | 1 | code_01F96A |
| `lea.l:absl,an` | 1434 | code_0002FA |
| `lea.l:absw,an` | 337 | code_0002FA |
| `lea.l:d16an,an` | 99 | code_001978 |
| `lea.l:d16pc,an` | 2 | init |
| `lea.l:d8anxn,an` | 34 | code_000D14 |
| `lsl.b:imm,dn` | 9 | code_001978 |
| `lsl.l:dn,dn` | 1 | code_03F450 |
| `lsl.l:imm,dn` | 2 | code_040A18 |
| `lsl.w:imm,dn` | 292 | code_0002FA |
| `lsr.b:imm,dn` | 14 | code_001978 |
| `lsr.l:dn,dn` | 1 | code_03F450 |
| `lsr.l:imm,dn` | 25 | code_001978 |
| `lsr.w:absw` | 4 | data_018BAE |
| `lsr.w:imm,dn` | 359 | code_0002FA |
| `move.b:absl,absl` | 6 | code_007790 |
| `move.b:absl,dn` | 18 | code_001978 |
| `move.b:absl,postinc` | 1 | code_006286 |
| `move.b:absw,absw` | 120 | code_0015C0 |
| `move.b:absw,d8anxn` | 2 | code_006286 |
| `move.b:absw,dn` | 246 | code_0002FA |
| `move.b:absw,ind` | 1 | code_013BD6 |
| `move.b:d16an,absw` | 4 | code_0090EE |
| `move.b:d16an,dn` | 41 | init |
| `move.b:d16an,postinc` | 1 | code_0002FA |
| `move.b:d8anxn,absw` | 12 | code_006190 |
| `move.b:d8anxn,d8anxn` | 1 | code_006190 |
| `move.b:d8anxn,dn` | 133 | code_0002FA |
| `move.b:d8anxn,postinc` | 2 | code_00A6C2 |
| `move.b:d8pcxn,dn` | 2 | P16T5-D; imp_decrunch_core |
| `move.b:dn,absl` | 10 | code_010EE2 |
| `move.b:dn,absw` | 106 | code_0002FA |
| `move.b:dn,d16an` | 68 | code_001978 |
| `move.b:dn,d8anxn` | 36 | code_000FCE |
| `move.b:dn,dn` | 33 | code_00266E |
| `move.b:dn,ind` | 50 | code_001978 |
| `move.b:dn,postinc` | 53 | code_00266E |
| `move.b:imm,absl` | 7 | code_0002FA |
| `move.b:imm,absw` | 81 | code_0002FA |
| `move.b:imm,d16an` | 77 | code_001978 |
| `move.b:imm,d8anxn` | 2 | code_00266E |
| `move.b:imm,dn` | 192 | code_0002FA |
| `move.b:imm,ind` | 19 | code_00266E |
| `move.b:imm,postinc` | 128 | code_0002FA |
| `move.b:ind,absw` | 1 | code_006286 |
| `move.b:ind,dn` | 46 | code_001978 |
| `move.b:ind,postinc` | 6 | code_0002FA |
| `move.b:postinc,absw` | 1 | code_006286 |
| `move.b:postinc,d16an` | 12 | init |
| `move.b:postinc,dn` | 76 | init |
| `move.b:postinc,ind` | 1 | code_017444 |
| `move.b:postinc,postinc` | 66 | init |
| `move.b:predec,dn` | 16 | code_00C84C |
| `move.b:predec,predec` | 2 | imp_decrunch_core |
| `move.l:absl,absl` | 8 | code_041A84 |
| `move.l:absw,absw` | 33 | code_0068D2 |
| `move.l:absw,dn` | 93 | code_0068D2 |
| `move.l:an,absl` | 4 | code_001978 |
| `move.l:an,absw` | 46 | code_0002FA |
| `move.l:an,predec` | 37 | code_0002FA |
| `move.l:d16an,absl` | 2 | code_001978 |
| `move.l:d16an,d16an` | 1 | code_00C998 |
| `move.l:d16an,dn` | 22 | code_001978 |
| `move.l:d8anxn,absl` | 1 | code_01CE34 |
| `move.l:d8anxn,absw` | 9 | code_00102E |
| `move.l:d8anxn,dn` | 12 | code_00C8E8 |
| `move.l:dn,absw` | 59 | code_0012B4 |
| `move.l:dn,d16an` | 20 | code_001978 |
| `move.l:dn,dn` | 22 | code_00FC54 |
| `move.l:dn,ind` | 39 | init |
| `move.l:dn,postinc` | 45 | code_001978 |
| `move.l:dn,predec` | 13 | init |
| `move.l:imm,absl` | 8 | code_001978 |
| `move.l:imm,absw` | 29 | code_0002FA |
| `move.l:imm,d16an` | 4 | init |
| `move.l:imm,dn` | 9 | code_0002FA |
| `move.l:imm,ind` | 1 | code_001978 |
| `move.l:ind,dn` | 15 | code_0015C0 |
| `move.l:ind,ind` | 1 | code_00855A |
| `move.l:postinc,dn` | 23 | code_001978 |
| `move.l:postinc,ind` | 56 | init |
| `move.l:postinc,postinc` | 5 | code_0002FA |
| `move.l:postinc,predec` | 3 | imp_decrunch_core |
| `move.l:predec,dn` | 1 | code_03F278 |
| `move.l:predec,ind` | 8 | code_03F278 |
| `move.w:absl,absl` | 1 | code_010E24 |
| `move.w:absl,absw` | 36 | code_004D34 |
| `move.w:absl,dn` | 125 | code_00143C |
| `move.w:absl,ind` | 1 | code_00EA9C |
| `move.w:absw,absl` | 6 | code_004D34 |
| `move.w:absw,absw` | 702 | code_0002FA |
| `move.w:absw,d16an0` | 1 | P16T5-E; code_03F278 |
| `move.w:absw,d8anxn` | 2 | code_00C998 |
| `move.w:absw,dn` | 2064 | code_0002FA |
| `move.w:absw,ind` | 8 | code_0012B4 |
| `move.w:absw,postinc` | 4 | code_0012B4 |
| `move.w:absw,predec` | 2 | code_03573C |
| `move.w:an,dn` | 6 | code_0139B0 |
| `move.w:d16an,absw` | 10 | code_001978 |
| `move.w:d16an,d16an` | 2 | code_03F278 |
| `move.w:d16an,dn` | 151 | code_0002FA |
| `move.w:d16an,ind` | 11 | code_00C998 |
| `move.w:d16an0,d16an` | 2 | P16T5-E; code_03F278 |
| `move.w:d16an0,d16an0` | 1 | P16T5-E; code_03F278 |
| `move.w:d16an0,dn` | 7 | P16T5-E; code_007EF4 |
| `move.w:d8anxn,absl` | 17 | code_00A6C2 |
| `move.w:d8anxn,absw` | 16 | code_000D14 |
| `move.w:d8anxn,d16an` | 1 | code_00A6C2 |
| `move.w:d8anxn,d8anxn` | 2 | code_00C998 |
| `move.w:d8anxn,dn` | 236 | code_000A8C |
| `move.w:d8anxn,ind` | 2 | code_0068D2 |
| `move.w:d8anxn,postinc` | 12 | code_00102E |
| `move.w:dn,absl` | 18 | code_001978 |
| `move.w:dn,absw` | 1065 | code_0002FA |
| `move.w:dn,d16an` | 144 | code_00266E |
| `move.w:dn,d8anxn` | 7 | code_00124C |
| `move.w:dn,dn` | 440 | code_0002FA |
| `move.w:dn,ind` | 101 | init |
| `move.w:dn,postinc` | 71 | code_00102E |
| `move.w:dn,predec` | 74 | code_0002FA |
| `move.w:imm,absl` | 49 | code_00102E |
| `move.w:imm,absw` | 1609 | code_0002FA |
| `move.w:imm,d16an` | 98 | code_001978 |
| `move.w:imm,d8anxn` | 9 | code_00803C |
| `move.w:imm,dn` | 1797 | code_0002FA |
| `move.w:imm,ind` | 40 | code_007790 |
| `move.w:imm,postinc` | 28 | code_000D14 |
| `move.w:imm,sr` | 3 | init |
| `move.w:ind,absw` | 6 | code_013BD6 |
| `move.w:ind,dn` | 96 | init |
| `move.w:ind,ind` | 3 | code_00C998 |
| `move.w:ind,postinc` | 1 | code_00EA9C |
| `move.w:postinc,absw` | 43 | code_001978 |
| `move.w:postinc,d16an` | 2 | code_00C998 |
| `move.w:postinc,dn` | 199 | code_0002FA |
| `move.w:postinc,ind` | 9 | code_00C998 |
| `move.w:postinc,postinc` | 28 | code_001978 |
| `move.w:predec,predec` | 2 | code_00C998 |
| `move:an,usp` | 1 | init |
| `movea.l:absl,an` | 10 | code_0090EE |
| `movea.l:absw,an` | 48 | code_0002FA |
| `movea.l:an,an` | 45 | code_00A6C2 |
| `movea.l:d16an,an` | 2 | code_03F278 |
| `movea.l:d16an0,an` | 1 | P16T5-E; code_03F278 |
| `movea.l:d8anxn,an` | 17 | code_001978 |
| `movea.l:dn,an` | 14 | init |
| `movea.l:ind,an` | 2 | code_001978 |
| `movea.l:postinc,an` | 38 | code_0002FA |
| `movea.w:absw,an` | 2 | code_00C998 |
| `movea.w:an,an` | 2 | code_00EA9C |
| `movea.w:d8anxn,an` | 2 | imp_decrunch_core |
| `movea.w:dn,an` | 5 | code_03EEA2 |
| `movea.w:imm,an` | 1 | code_03EEA2 |
| `movem.l:d16pc,reglist` | 2 | P16T5-B; code_0002FA |
| `movem.l:ind,reglist` | 1 | init |
| `movem.l:postinc,reglist` | 81 | init |
| `movem.l:reglist,predec` | 79 | code_001978 |
| `movem.w:postinc,reglist` | 102 | init |
| `movem.w:reglist,predec` | 92 | code_001978 |
| `moveq:imm,dn` | 459 | init |
| `mulu.w:absw,dn` | 36 | code_001978 |
| `mulu.w:dn,dn` | 31 | code_001978 |
| `mulu.w:imm,dn` | 85 | code_0002FA |
| `neg.l:dn` | 17 | code_0068D2 |
| `neg.w:absw` | 2 | code_00741A |
| `neg.w:dn` | 23 | code_00741A |
| `nop:none` | 36 | code_0002FA |
| `not.b:dn` | 3 | code_007790 |
| `or.b:dn,absw` | 4 | code_000FCE |
| `or.b:dn,dn` | 15 | code_001978 |
| `or.l:dn,dn` | 8 | code_001978 |
| `or.w:absl,dn` | 1 | code_041526 |
| `or.w:absw,dn` | 2 | code_001978 |
| `or.w:dn,d16an` | 1 | code_0053BE |
| `or.w:dn,dn` | 39 | code_0002FA |
| `ori.b:imm,absw` | 7 | code_00124C |
| `ori.b:imm,ccr` | 1 | P16T5-C; code_007AB4 |
| `ori.b:imm,dn` | 27 | P16T5-A2; code_0045CE |
| `ori.w:imm,dn` | 89 | P16T5-A2; code_00266E |
| `rol.b:imm,dn` | 2 | code_007B66 |
| `rol.w:imm,dn` | 20 | code_007790 |
| `ror.b:imm,dn` | 1 | code_007B66 |
| `ror.l:imm,dn` | 1 | code_00B25C |
| `ror.w:imm,dn` | 2 | code_03EEA2 |
| `roxl.b:imm,dn` | 19 | code_0002FA |
| `roxl.l:imm,dn` | 1 | code_013BD6 |
| `roxl.w:imm,dn` | 4 | code_010EE2 |
| `roxr.l:imm,dn` | 16 | code_001978 |
| `rte:none` | 7 | code_01F964 |
| `rts:none` | 917 | code_000A8C |
| `scc.b:absw` | 1 | code_0002FA |
| `scc.b:ind` | 3 | code_007790 |
| `sub.b:absw,dn` | 6 | code_010EE2 |
| `sub.b:dn,absw` | 1 | code_00BE02 |
| `sub.b:dn,dn` | 6 | code_00266E |
| `sub.l:an,dn` | 3 | code_01CE34 |
| `sub.l:dn,absw` | 8 | code_0068D2 |
| `sub.w:absw,dn` | 210 | code_00266E |
| `sub.w:d16an,dn` | 7 | code_00B25C |
| `sub.w:dn,absw` | 4 | code_00FC54 |
| `sub.w:dn,d16an` | 2 | code_01B936 |
| `sub.w:dn,dn` | 181 | code_00266E |
| `sub.w:ind,dn` | 4 | code_00B25C |
| `suba.l:absw,an` | 2 | code_03DE0A |
| `suba.l:imm,an` | 1 | code_0002FA |
| `suba.w:absw,an` | 2 | code_03E8C4 |
| `suba.w:an,an` | 1 | code_03EEA2 |
| `subi.b:imm,dn` | 37 | P16T5-A2; code_000FCE |
| `subi.w:imm,absw` | 17 | code_00266E |
| `subi.w:imm,d16an` | 2 | code_00A6C2 |
| `subi.w:imm,dn` | 278 | P16T5-A2; code_00102E |
| `subq.b:imm,absw` | 9 | code_006286 |
| `subq.b:imm,d16an` | 3 | code_00BE02 |
| `subq.b:imm,dn` | 16 | code_007B66 |
| `subq.b:imm,ind` | 1 | code_010EE2 |
| `subq.l:imm,an` | 3 | code_005BBA |
| `subq.l:imm,dn` | 4 | code_01CE34 |
| `subq.w:imm,absl` | 13 | code_00855A |
| `subq.w:imm,absw` | 133 | code_000D14 |
| `subq.w:imm,an` | 8 | code_00266E |
| `subq.w:imm,d16an` | 6 | code_005BBA |
| `subq.w:imm,d8anxn` | 4 | code_00C998 |
| `subq.w:imm,dn` | 267 | code_0002FA |
| `subq.w:imm,ind` | 6 | code_0129DE |
| `swap:dn` | 15 | code_00855A |
| `tst.b:absw` | 41 | code_0045CE |
| `tst.b:d8anxn` | 2 | code_00C998 |
| `tst.b:dn` | 29 | code_009CBA |
| `tst.b:ind` | 1 | code_010EE2 |
| `tst.b:postinc` | 2 | code_00A6C2 |
| `tst.l:absl` | 1 | init |
| `tst.l:dn` | 9 | imp_decrunch_core |
| `tst.l:postinc` | 1 | imp_decrunch_core |
| `tst.w:absl` | 25 | init |
| `tst.w:absw` | 936 | code_0002FA |
| `tst.w:d16an` | 10 | code_005BBA |
| `tst.w:d8anxn` | 9 | code_00C998 |
| `tst.w:dn` | 89 | code_0002FA |
| `tst.w:ind` | 22 | code_0045CE |
| `tst.w:postinc` | 4 | code_00A6C2 |
<!-- encmap:end -->
