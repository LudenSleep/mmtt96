<!-- decomp-architect: the rows appended to docs/ops-setup.md at Step 8, inside a marked section. The generation-time
     placeholders are written as literal TODO(phase-N) lines when their phase has not happened yet, so the leftover
     placeholder audit stays clean; the phase that produces the value replaces the TODO. -->

## Decomp environment (decomp-architect, Phase 0.5 — installed 2026-10-11)

Line endings (phase 1.7 T4): tracked `.gitattributes` sets `* text=auto eol=lf`; the TSV readers (db.py) refuse CR, and `core.autocrlf=true` without it checked out CRLF. Revert an LF-strict file from a backup copy or re-checkout after `.gitattributes` exists.

### Version pins (decomp)

| Component | Version | Notes / why pinned |
|---|---|---|
| Toolchain | Macroassembler AS V1.42 Bld 313 (`asw` + `p2bin`, `tools/bin/asl/`); no compiler, no linker | the game is hand-written 68000 assembly; the byte gate (`make build`) is the pin's evidence |
| The splitter / disassembler and its config | `scripts/build/split.py` (stdlib, all-data `dc.b` splitter; phase 1.3) | version = this repo; input `config/regions.retail.tsv` |
| The build assembler (phase 1.4, T3) | Macroassembler AS V1.42 Bld 313 (`tools/bin/asl/asw.exe` + `p2bin.exe`, GPL-2.0+; snapshot asset `asl-windows-x86_64-v1.4.2.20261012-run38215198548.zip` from github.com/flamewing/asl-releases); zip + extract ignored, sha256 tracked: `cd tools/bin && sha256sum -c asl.zip.sha256` (verify before extracting) | Make (cwd `asm/`): `asw -q -xx -n -U -i . main.asm` then `p2bin main.p ../build/mmtt96.bin` (range deduced, flat). Header `cpu 68000`/`supmode on`/`padding off`/`org 0`. Assert: `if * <> $XXXXXX` / `error "<id>: end mismatch"` / `endif` → rc 2, no `.p`, no bin. Keeps `cmp #,Dn` vs `cmpi` as written; no auto moveq/addq; explicit `.s/.w/.l` honoured; bare `0(An)` shrinks to `(An)`, write `0.w(An)`. Encoding detail: `docs/encoding-map.md` |
| The all-data baseline assembler (phase 1.3, T1; retired from the build in 1.4 T3) | clownassembler v1.1.3 `tools/bin/clownassembler_asm68k.exe` (131,072 B, AGPL-3.0-or-later, asm68k-compatible; https://github.com/Clownacy/clownassembler/releases/download/v1.1.3/clownassembler_asm68k.exe); exe ignored, sha256 tracked: `cd tools/bin && sha256sum -c clownassembler_asm68k.exe.sha256` (R1.3-001, R1.3-002) | command: `clownassembler_asm68k.exe //p <src.asm>,<out.bin>` (`/p` = flat binary, no header, no padding past the last byte; from Git bash/make write `//p` or set `MSYS_NO_PATHCONV=1`, else `/p` is rewritten to a path and the run fails rc=1). Boundary assert (end exclusive): `if * <> $XXXXXX` / `inform 3,"<msg>"` / `endc` → rc=1, no output file; `fail` and `error` are not directives (syntax error), `inform 0/1` only warn rc=0. No usage text (`/?` unrecognised). 1 MiB `dc.b` source: 0.35 s single file, 3.9 s as 1255 includes, byte-identical. One short region cascades an assert error into every later region; the first `On line` names the culprit. Encoding (phase 1.4 T1): no switches; nothing is optimised by default (unsuffixed Bcc/BSR/BRA = .w, unsuffixed abs and lea/pea/jmp/jsr label = abs.l, `move.l #` never moveq, `add/sub #,Dn` = addi/subi); short forms only by explicit `Bcc.s`, `(x).w` with RAM as `$FFFFxxxx`, `label(pc)`, `moveq`, `addq/subq`; `/o oz+` (0(An)→(An)) is the only optimiser; ae+ default pads dc.w at odd address; `@` = local label; `include` resolves against the process cwd only (run from source root); `align` not a directive (use `cnop`) |
| The disassembler database | Ghidra 12.1.4 headless (`support/analyzeHeadless.bat`; zip `ghidra_12.1.4_PUBLIC_20260921.zip`, 569,649,598 B, published sha256 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db` from the GitHub release API, phase 1.8 T3; manual install, `GHIDRA_INSTALL_DIR`), Java 21 (Temurin 21.0.12 if none on PATH); no MCP | the static oracle; tracked as the TEXT export `config/ghidra/*.tsv`, rebuilt and round-tripped by `scripts/ghidra/db.py` |
| The emulator and its scripting bridge | MAME 0.289 (env `MAME_EXE` = path to `mame.exe`, required, no default), softlist launch `megadriv microm96` (slot rom_mm96 = J-Cart+EEPROM, no `-cart`), Lua `-autoboot_script` with `-debug -debugger none` | the runtime oracle; driven by `scripts/oracle/mame.py` |
| Second 68000 disassembler (phase 1.5, T1) | Capstone 5.0.9 (`pip install --require-hashes -r requirements-python.txt`: win_amd64 + manylinux x86_64 sha256s, phase 1.8 T3; was `pip install --user`, wheel `capstone-5.0.9-py3-none-win_amd64.whl`, sha256 `732cedbbb56d42e723f14d7af6387f1454194a820b4b96b56d1e53f865ef85d0`, verified against PyPI JSON; BSD-3); `capstone.__version__` reports 5.0.7, `pip show` 5.0.9 (report R1.5-001) | the boundary oracle's independent decoder; used by `scripts/oracle/boundaries.py` |

### The game and the medium

- **Title / platform / serial:** Micro Machines Turbo Tournament 96 · Sega Mega Drive / Genesis (Motorola 68000 main CPU, Z80 sound CPU) · Europe v1.1 (J-Cart), Codemasters; header serial 00000000-00; ROM SHA-1 e8ff759679a0df2b3f9ece37ef686f248d3cf37b
- **The main executable on the medium:** `Micro Machines Turbo Tournament 96 (Europe) (v1.1) (J-Cart).md` (its hash is the first per-binary contract, Phase 3)
- **Container layout:** one flat 1 MiB cartridge ROM, no filesystem; J-Cart with two extra controller ports; coarse map in `config/regions.retail.tsv` (Phase 1.1): vectors, header, Z80 boot stub + raw sound driver (0x01597A-0x016DE6), 368 Amiga Imploder "IMP!" blobs tiling 0x0477BA-0x0FFB1A (one format, name `imp`; decoder `scripts/extract/decode_imp.py`; `decoded` manifest rows stay `status: inferred` until the Phase 1.2 emulator cross-check promotes them), 2 padding runs; the 68000 program (code vs data) stays `unknown` until the Phase 1.2 disassembler segments it (R1.1-002, R1.1-003)
- **SDK / compiler-era evidence:** none gathered yet (the ROM header is generic); Phase 2 records the hardware-library and sound-driver evidence
- **The dump (machine-local, never committed):** `<path>` (your own dump dir) — copied once onto a fast local filesystem under `disks/`
  (ignored); the extractor reads it, nothing builds against it.

### Build / extract / verify (decomp)

- **Bootstrap (phase 1.8 T3):** `bash scripts/bootstrap.sh [--asl-zip PATH] [--dump PATH]` (Git bash or Linux) checks Python 3.11 at `PY` + capstone 5.0.9 (prints the pip line, never runs it), Java 21, Ghidra 12.1.4 (`GHIDRA_INSTALL_DIR`, required; version from `Ghidra/application.properties`), GNU make; installs AS into ignored `tools/bin/asl/` from `--asl-zip` or by downloading the one approved asset (developer decision D1, 2026-10-13; nothing else is downloaded), sha256-checked against `tools/bin/asl.zip.sha256` before extraction (mismatch: refused, partial file removed, nothing extracted); `--dump` is SHA-1-checked against `config/medium.sha1` and copied to `disks/` under `ROM_DEFAULT`. A missing item prints its source URL and expected hash; exit 0 iff all present. Idempotent. Env `MMTT96_BIN_DIR` (AS target dir) and `MMTT96_ASL_URL` exist for the controls only.

```
# extract the medium and verify against the committed manifest
"$PY" scripts/extract/manifest.py           # writes config/manifest.retail.jsonl + extracted/retail/{raw,decoded}/
"$PY" scripts/extract/manifest.py --check   # exit 0 identical, 1 differs
"$PY" tools/audit_public.py                 # exit 0 = no tracked file matches a manifest hash
# the clean fleet verification — every binary from clean → extract → build, exit code read
make clean && make build    # green = exit 0 + `build/mmtt96.bin: OK`; needs Ghidra + Java (make src)
make src                    # asm/src only: db.py listing --all-code (all verified code), self-checked, ~12 s
make build SRC=             # all-data baseline: every region as dc.b, no asm/src, no Ghidra/Java
make build SRC=<dir>        # region sources from <dir> (no make src)
make build PY=<python> NAMES=<dir>  # PY must import capstone (parse-time check names PY); NAMES default config/names
```

- **Environment of a clone:** `PY=` (Python 3.11 + capstone; default `python3` if it runs, else `python`; override with `PY=`;
  a Python without capstone fails at parse time),
  `GHIDRA_INSTALL_DIR` (Ghidra 12.1.4), `JAVA_HOME` or java on PATH (else `MMTT96_JDK_PARENT`), `MMTT96_GHIDRA_PROJ`
  when the clone path has an element starting with `.` (Ghidra refuses it; db.py names the variable),
  `MMTT96_NAMES` for `ledger.py` when `NAMES` is not the default. Use a junction, not `subst` (split.py `relpath`
  across drives); never `rm -rf` a junction (it follows into the target). `.run/ghidra/seeds.tsv` is generated by
  `census.py` (health pair `census`); `commentcheck.py --self-test` needs no dump.

- **Source regions:** default `SRC=asm/src` is generated by `make src` (`asm/src/.stamp`; prereqs ROM, regions TSV,
  `config/ghidra/*.tsv`, `config/names/*.tsv`, `db.py`, `Mmtt96Listing.java`, `split.py`): `db.py listing --all-code`
  lists every `kind=code status=verified` region (log `.run/src/listing.log`); any self-check failure removes
  `asm/src`, prints `make: db.py listing failed (<ids>)` and exits 1 (no dc.b fallback); success writes
  `asm/.srclist`. Ghidra 12.1.4 + Java 21 are therefore needed by `make build`; a missing Ghidra is a one-line
  `db: no Ghidra at ...` error. split builds each `<SRC>/<id>.asm` through the region wrapper, whose `assert_end`
  fails the build if the encoded size drifts; the file set is tracked in `asm/.srclist` (adding/removing a file
  re-splits). `asm/src` is local-only and ignored (G12, decision D1); `make clean` removes it.

- **The gate:** a binary is green only when its hash check inside `make build` passes; a match is verified from a CLEAN
  rebuild, never incremental; the executable is gated only by a clean rebuild; a build is verified by its exit code.
  The contract is `config/check.retail.sha` (`sha1sum -c` inside `make build`); `make expected` copies the green
  binary to `expected/mmtt96.bin` (ignored).

- **Health chain:** `make health` (`mk/health.mk`, ~1 min) runs `db.py probe` first (a Ghidra failure stops it), then 9 differential pairs (`scripts/health/pairs.py`), the
  `asm_leak.py` firewall rung and a summary: one `pair <name>: agree|DISAGREE` each + `health: pairs <a>/<n> agree`,
  exit 0 iff all agree; report `.run/mmtt96-health/report.txt`, child logs `.run/mmtt96-health/logs/`. Pair 2 forces
  `make src` and leaves `asm/src` + the default tree in instruction form at exit. Controls: `pairs.py <pair> --plant` and `asm_leak.py --plant` must exit 1.
  `make health-live` = `check_maps.py --live` (MAME/BizHawk; run detached).

### The oracles (decomp)

- **Disassembler database (headless, no MCP):** Ghidra 12.1.4 driven by `PY scripts/ghidra/db.py
  {probe|rebuild|export|roundtrip}` (own GhidraScripts `scripts/ghidra/Mmtt96Apply.java` / `Mmtt96Export.java`, no
  pyghidra). `db.py probe` (exit 0 + version) is the one cheap call before any reverse-engineering task. Projects live
  only under `ghidra/` (ignored; `ghidra/mmtt96` from `rebuild`); the tracked record is `config/ghidra/*.tsv`, and
  `roundtrip` proves it rebuilds byte-identically. kind=label symbols apply after auto-analysis (last postScript;
  docs/ops/ops-tools.md ghidra_db). Blocks: ROM 0x000000-0x0FFFFF, Z80 0xA00000-0xA0FFFF, IO
  0xA10000-0xA1FFFF, VDP 0xC00000-0xC0001F, RAM 0xFF0000-0xFFFFFF, JCART 0x380000-0x3FFFFF (J-Cart range unverified).
  `db.py listing <id>...|--all-code [--out asm/src]` (`Mmtt96Listing.java`, read-only): region -> AS `<out>/<id>.asm`
  (explicit short forms, `L_xxxxxx` locals, zero d16 as `0.w(An)`, `comments.tsv` plate/eol as `;` comments), self-checked by asw+p2bin with split's AS
  header in `.run/ghidra/listing/as/` vs ROM; ignored dirs only.
  `analyzeHeadless.bat` breaks on `(` in arguments, so the ROM is imported from an ignored copy `.run/ghidra/mmtt96.md`.
  Region classification: `PY scripts/ghidra/classify.py seeds` (vector targets, known entries, decruncher call sites,
  coverage row starts -> `.run/ghidra/seeds.tsv`), `db.py analyse` (`ghidra/mmtt96_seed` + `Mmtt96Seed.java` ->
  `.run/ghidra/seed/`), `classify.py merge` (rewrites the gap rows of `config/regions.retail.tsv`, mirrors
  `config/ghidra/`; `config/oracle/decrunch*.tsv` key parents by `parent_start`, no re-key); then `manifest.py` and `db.py roundtrip`.
  Status rule: `verified` code = executed (coverage) or call/jump/flow-reachable from a verified unit (vectors alone do
  not verify); `verified` data = referenced only as data, never executed. Export holds owned symbols only.
- **Emulator bridge:** `PY scripts/oracle/mame.py probe` (`-verifysoftlist megadriv` must print `romset
  megadriv:microm96 is good` + live vectors == `rom.parse_vectors`) and `run <lua> [--frames N] [--tag T] [--tsv P]`
  (JSONL `.run/oracle/<run>.jsonl`, exit 0 iff `done`). The ROM is copied (SHA-1 checked) to
  `.run/mame/roms/megadriv/microm96/`. Launch: `mame.exe megadriv microm96 -rompath .run/mame/roms -hashpath
  <mame>/hash -video none -sound none -nothrottle -skip_gameinfo -seconds_to_run <s> -debug -debugger none
  -autoboot_script <lua>`. Lua: trace via `debugger:command("trace <f>,maincpu,noloop")` (~15 MB/40 frames: trace
  one frame, bps after); bp action `printf` with a fixed text read from `debugger.consolelog` (m68000 `pc` reads
  insn+2 at a hit); `soft_reset()` re-runs the autoboot script while old callbacks persist (guard with a global).
  Claims: `config/maps/*.tsv`, datapoints `config/oracle/boot.tsv`, checked by `scripts/oracle/check_maps.py
  [--live]`. A live-memory finding is verified only with three or more consistent datapoints or a controlled
  before/after diff. Coverage: `PY scripts/oracle/coverage.py --run <scenario>` traces in 900-frame chunks chained by
  save states (~6-13 frames/s; run detached via `tools/run.sh --bg`), keeps unique PCs in `.run/oracle/cov/*.pcs`;
  `--write` merges them into `config/oracle/coverage.tsv` (PCs < 0x100 dropped), `--check` gates it (plus no executed
  byte in a non-code row of `config/regions.retail.tsv`), `--report` prints range counts.
  Decruncher cross-check: `PY scripts/oracle/decrunch.py --all [--write]` drives 0x035416 (A0 = blob, A1 = dest; out
  D1 = size, D0 = -1 ok) in MAME for all 368 blobs vs the offline decode -> `config/oracle/decrunch.tsv`; `--natural
  [--tsv]` captures in-game calls -> `decrunch_natural.tsv`; `manifest.py --decrunch` promotes decoded rows from it.
- **Second emulator (BizHawk 2.11, GPGX core):** `PY scripts/oracle/bizhawk.py {probe|run <lua> [--frames N] [--tag T]
  [--tsv P]}`. Exe: env `BIZHAWK`, else `bizhawk`/`EmuHawk` on PATH (set `BIZHAWK` when EmuHawk is not on PATH; no other default).
  Launch (headless-ish: a window opens, no clicks): `EmuHawk.exe --lua=<abs lua> <staged rom>` (same staged ROM as
  mame.py), the Lua sets `client.speedmode(6400)` + `client.invisibleemulation(true)` (600 frames ~4 s) and ends with
  `client.exit()`. GPGX asks for the optional Mega-CD BIOS on every cart load (and again on `reboot_core`): EmuHawk shows
  a modal "Warning" box ("Couldn't find firmware GEN+CD_BIOS_EU") that blocks the Lua; bizhawk.py closes exactly that box
  (WM_CLOSE), any other dialog times the run out. Registers `M68K PC`, `M68K SP`; domains `68K RAM` (0 = 0xFF0000),
  `Z80 RAM`, `M68K BUS`, `MD CART`. Gotcha: the Lua starts after frame 1 (framecount 1), so callbacks registered at start
  miss boot; `client.reboot_core()` (hard reset, framecount 0, the script survives) drops callbacks registered before
  it: reset first, then register `event.onmemoryexecute`/`onmemoryexecuteany` (M68K BUS). The exec-any callback first
  reports 000000 (reset trap), like MAME's trace. Probe: `lua/bizhawk_rammap.lua` (entry_after_trap,
  z80_sha1_after_upload, frame_counter); datapoints `config/oracle/bizhawk.tsv` (`run key value`), run ids in the
  `second` column of `config/maps/*.tsv`.
- **Second-oracle rule:** a claim with a non-empty `second` needs >= 3 BizHawk runs agreeing with its `expect`
  (`check_maps.py`, `--live` re-runs bizhawk_rammap once). If BizHawk and MAME disagree on a claim, nobody relabels the
  claim or edits `expect`: the task returns `blocked` with both outputs.
- **MCP decision:** none adopted (pyghidra-mcp is beta, GhidraMCP needs the GUI, no emulator MCP exists); revisit at
  phase 1.7 or when a stable headless MCP for Ghidra 12.x or an emulator exists and cuts agent context vs the scripts.

### Git posture (decomp)

- **Visibility:** developed privately through Phase 1.9, public since publication (2026-10) — the ROM firewall applies
  either way (`config/firewall.txt`, `tools/audit_public.py`, the CI workflow).
- Never `git clean -x` in a working clone (the game-derived data is ignored-but-present); the backup of the
  reverse-engineering work is the tracked text export + the checksum files, not the ignored directories.

### Tooling inventory (decomp)

| Tool | Location | Purpose |
|---|---|---|
| `tools/audit_public.py` | `tools/` | the ROM audit (purge paths, the derived hash set, the size cap, the pasted-disassembly check); the first-push gate and the CI job; its sources are `config/firewall.txt` |
| `make build\|clean\|expected\|split\|src` | `Makefile` | `src`: `db.py listing --all-code` -> ignored `asm/src` (default `SRC`; needs Ghidra + Java; failure removes it, exit 1); split ROM -> `asm/`, assemble -> `build/mmtt96.bin`, hash check against `config/check.retail.sha`; `expected` copies to `expected/`; vars `PY ROM ASM REGIONS` overridable; an absent dump refuses (`make build ROM=...` exit 2) |
| `scripts/build/split.py` | `scripts/build/` | stdlib all-data splitter: ROM + `config/regions.retail.tsv` -> `asm/` `dc.b` sources with boundary asserts; prints `regions N/N files N bytes N/N`; refuses (exit 2) on a missing or mismatched dump |
| `scripts/extract/manifest.py` (+ `rom.py`, `decode_imp.py`) | `scripts/extract/` | stdlib extractor: reads `disks/` ROM (SHA-1 checked), partitions it per `config/regions.retail.tsv`, writes `config/manifest.retail.jsonl` (the audit's required hash source) and raw/decoded blobs to `extracted/retail/` (ignored); refuses (exit 2) on SHA mismatch, overlap, out-of-range, empty region or decode mismatch |

### The three dictionaries (the kit master copy — consulted, never copied into this repository)

| Corpus | Where | How to use it |
|---|---|---|
| The tool dictionary — the source project's tools, verbatim, by ladder phase, keyed by the need each answers | `<kit master copy>/decomp-architect/corpus/tools/INDEX.md` (installed summary: `docs/tools-manifest.md`) | before designing or debugging a tool, grep the index by the need; the matching file is the jumping-off point, its Adapt column the list of what differs here |
| The inherited knowledge base — the cookbook, its symptom index and the codegen map, verbatim | `<kit master copy>/decomp-architect/corpus/cookbook/` (installed front page: `docs/knowledge-corpus.md`) | same compiler family: look the symptom up, apply, re-prove on your bytes; another compiler: read the same pass in your compiler's source and find your own lever |
| The inherited record — the source project's distilled records (the how-to, the decision log, the accelerators, the retrospective, the story, the playbook, the effort doctrine, the readability charter) and every phase-end, verbatim | `<kit master copy>/decomp-architect/corpus/record/` (installed front page: `docs/inherited-record.md`) | when a rule or kernel cites a source, open it here; the digest first, a phase-end on demand, the how-to in order |
| Kit master copy location | the developer's machine only; not published (the installed front pages above are) | — |
