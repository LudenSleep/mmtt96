# PhaseEnd — Phase 1.7: Campaign: first wave (implements Gen 1.7)
Approved: 2026-10-13 | Closed: 2026-10-13 | Planner: claude-opus-5-5/medium | Tasks: 8 done, 0 superseded

## Milestone
Milestone: census reads 0 undecoded code regions (every `kind code` row of `config/regions.retail.tsv`, verified or inferred, is assembled from instruction source by the default `make build`, or is re-kinded with recorded evidence); the build stays hash-equal after every batch; the first manual wave (6 regions) is named, commented, byte-gated and measured; every code region sits on the campaign ledger with a class, a closeness and a named blocker — verified by: `make clean && make build && make health && "C:/Program Files/Python311/python.exe" scripts/census/ledger.py check && "C:/Program Files/Python311/python.exe" tools/audit_public.py && test -z "$(git ls-files asm build expected)"` (all exit 0; `build/mmtt96.bin: OK`; `health: pairs <n>/<n> agree` with n >= 9 and rungs `asm_leak`, `encmap: forms <m>/<m> mapped` and `ledger` green; `ledger.py check` prints `ledger: code regions <k>/<k> undecoded 0` with k = `kind code` rows counted from the region file; run detached via `bash tools/run.sh --bg gate -- ...` + `bash tools/run.sh --wait gate --max 280` per call, exit code from `.run/logs/gate.exit`)
Verified: make clean && make build && make health && ledger.py check && audit_public.py && test -z "$(git ls-files asm build expected)" && card.py check → build/mmtt96.bin: OK; health exit 0, pairs 9/9 agree, asm_leak 0, encmap 394/394, ledger code regions 252/252 undecoded 0, commentcheck 0 failed, self-test 12/12; ledger check rc 0; audit_public OK; ls-files empty; card 6946/7000

## Tasks
- T1 — campaign ledger and baseline measurements | Done: `scripts/census/ledger.py write|check|report` builds config/campaign/ledger.tsv, one row per code region (252), with closeness, class, blocker; baseline numbers below. | commit: 439b285 | tasks/T1.md | logs/T1.md
- T2 — decrunch oracles keyed by start address | Done: `config/oracle/decrunch.tsv` (368 rows) and `decrunch_natural.tsv` (39 rows) key parents by `parent_start` (col 0, `0x%06X`) instead of positional `r%04d`; all readers resolve by start; region renumbering needs no re-key. | commit: - | tasks/T2.md | logs/T2.md
- T3 — record the source-location decision (D1) | Done: D1 recorded in docs/decisions/source-location.md: option (a), converted source local-only in ignored asm/src, regenerated from tracked sidecars plus the developer's dump; docs/68k-adaptation.md points at it. | commit: - | tasks/T3.md | logs/T3.md
- T4 — default build from instruction source, comment rendering | Done: default `make clean && make build` generates ignored asm/src (246 verified code ids) via `db.py listing --all-code` and builds the retail-matching ROM from instruction source; comments.tsv plate/eol rows render; tracked `.gitattributes` forces LF checkouts. | commit: - | tasks/T4.md | logs/T4.md
- T5 — verdicts for the 6 inferred code and 26 inferred other rows | Done: all 32 inferred rows have an evidence verdict: code_01FA2E promoted to verified code; 31 kept inferred with a ledger class and blocker; inferred code is listed and built from source; `ledger.py check` 0 inferred-without-verdict. | commit: - | tasks/T5.md | logs/T5.md
- T6 — value-logging census for RAM and struct names | Done: `config/oracle/values.tsv` holds a write-value census (30 rows: 15 ram.tsv rows + 15 struct fields, 3 MAME scenarios, control pass each). Name review: no placeholder met the >= 3-consistent-datapoint bar for a meaning name; ram.tsv/structs.tsv unchanged. | commit: - | tasks/T6.md | logs/T6.md
- T7 — manual wave 1: six regions named, commented, measured | Done: the six T1 wave regions (code_010810, code_012EE0, code_01F800, code_03F278, code_00635E, code_041A84) read closeness 0; 110 name rows and 42 comments added; make health 9/9 green; global raw_abs 29994 -> 26553. | commit: - | tasks/T7.md | logs/T7.md
- T8 — harvest, routing, census assertion, docs, milestone | Done: wave-1 harvest swept: every operand target and routine entry has a neutral name; every code row of the ledger has class, closeness, blocker and route; hard-fail health rungs `ledger` and `commentcheck`; milestone gate green. | commit: d83cf87 | tasks/T8.md | logs/T8.md

## Decisions that still bind
- T1 — D1 (developer): converted instruction source lives locally only under ignored asm/ paths, generated from tracked sidecar files plus the developer's own dump (for T3).
- T2 — decrunch oracle TSVs key parents by region start address (`parent_start`), never by positional manifest id.
- T3 — D1 = (a): instruction source never tracked; lives in ignored `asm/src/`, generated from `config/names/*.tsv`, `config/ghidra/comments.tsv`, `config/campaign/ledger.tsv`, routine/signature names plus the local dump (contract: docs/decisions/source-location.md).
- T3 — readability constructs are sidecar rows keyed by address, each with a renderer in the listing path; never hand-edited source (H1).
- T3 — firewall, asm_leak.py, audit_public.py, README unchanged by D1; publishing source would need a project rule superseding G12 at a named commit, never a private exemption.
- T4 — tracked text files are checked out LF regardless of core.autocrlf (`.gitattributes`); readers may keep refusing CR.
- T4 — `make build` builds from asm/src (instruction listings, ignored); `make build SRC=` is the all-data form; a mismatched listing fails the build (no dc.b fallback).
- T6 — a meaning name needs >= 3 consistent datapoints that support that exact meaning; values that merely vary, or a pattern that fits several meanings, keep the neutral name (C0017).
- T7 — every routines.tsv row goes through `signatures.py propagate`, never a hand edit; names lower_snake (fn_<addr6> lower-case hex; NAME_RE refuses upper case).
- T7 — a plate/eol comment is checked against `db.py listing <region>` before commit; claims not shown by the listing are dropped or restated (axes, sortedness, "same as" claims).
- T8 — route rule for code rows: insns < 50 -> `unattended` (comments only, commentcheck-gated); insns >= 50 ->
- T8 — every comment added to config/ghidra/comments.tsv passes `commentcheck.py` (health rung); a new claim form
- D1: instruction source is local-only under ignored `asm/src`, generated from tracked sidecars plus the developer's dump; publishing it needs a project rule superseding G12: contract, `docs/decisions/source-location.md`, guarded by `asm_leak` and `audit_public` (T1, T3).
- Decrunch oracle TSVs key parents by `parent_start`: contract, `docs/ops/ops-tools.md`, `docs/ops/ops-setup-decomp.md` (T2).
- Default `make build` builds from `asm/src` and fails on a mismatched listing; `make build SRC=` is the all-data form; tracked text is LF via `.gitattributes`: contract, card Build line, `docs/ops/ops-setup-decomp.md`, the `srcform` pair (T4, T5).
- A meaning name needs >= 3 consistent datapoints for that exact meaning: technique under rule G62, cookbook C0017 (T6).
- `routines.tsv` is written only by `propagate`/`bulk-neutral`, lower_snake names: contract, `docs/ops/ops-tools.md` names section (closer added the case note) (T7).
- Every comment passes `commentcheck.py`; the route rule (`unattended` < 50 insns, else `developer-review`): contract, `docs/ops/ops-tools.md` ledger/commentcheck sections, health rungs `ledger` and `commentcheck` (T8).
- Next task needs: phase 1.9 waves-2+ plan from T8 (about 27 coder runs of ~1,500 instructions each, comments and meaning names).
- Next task needs: extend `db.py mirror` to regions; a Makefile names-dir variable; refresh older route text and stale `no listing` blocker text on the ledger.
- Next task needs: a value-logging probe aimed at `jcart_38FFFE` (nearest miss of the 3-datapoint bar).
- Next task needs: the card is at 6986 of 7000 chars after this close; any addition must trim elsewhere.

## Rules proposed
- (none)

## Cookbook entries added
C0021 | Draft comments written away from the listing are wrong about half the time | comments,listing,verification,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0022 | Neutral RAM names spill over: name RAM before comments | naming,ram,sweep,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0023 | Readability closeness is mechanical: sweep it by script before manual waves | naming,sweep,routing,wave | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0024 | Code name equal to a region id double-defines the label | naming,build,as,gotcha | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0025 | Sidecar names need renderer support for every addressing form | naming,renderer,68000,listing | 2026-10-13 | 1.7/T7 | T7 summary harvest (T8)
C0026 | CRLF checkouts under core.autocrlf=true: ship .gitattributes eol=lf | git,windows,eol,gotcha | 2026-10-13 | 1.7/T4 | T4 summary gotchas
C0027 | Prove a never-raised exception handler by injecting a 68000 frame in MAME | mame,68000,exception,oracle,verification | 2026-10-13 | 1.7/T5 | T5 summary gotchas
C0028 | Claim checker for prose comments: fixed claim grammar plus planted bad fixture | comments,verification,health,fixture | 2026-10-13 | 1.7/T8 | T8 summary gotchas

## Research
- (none)

## Audit
- seed: no expert runs for phase 1.7
- CLAUDE.md: 983 bytes
- .claude/skills/decrunch-parent-remap/SKILL.md: 953 bytes
- .claude/skills/detached-run-exit-file/SKILL.md: 648 bytes
- .claude/skills/edit-escapes-with-edit-tool/SKILL.md: 725 bytes
- .claude/skills/make-path-detached/SKILL.md: 889 bytes
- .claude/skills/names-edit-mirror/SKILL.md: 630 bytes
- .claude/skills/project-architect/SKILL.md: 13113 bytes
- .claude/skills/propagate-refusal-test/SKILL.md: 731 bytes
- .claude/skills/run-sh-one-step/SKILL.md: 798 bytes
- .claude-state/memory/MEMORY.md: 4262 bytes
- HOW_WE_WORK.md: 7012 bytes
- cookbook/INDEX.md: 4566 bytes
- rules/INDEX.md: 7032 bytes
- audit unavailable: CLI not installed (~/.claude/pa3/pa_ledger.py)

## Agent runs
- (no ledger at ~\.claude\usage-ledger\ledger.sqlite)

## Discussions
- (none)

## Deferred
- from T8: phase 1.8 (publish gate) reads ledger counts above; 1.9 waves use the route column and commentcheck. (unconsumed)

## Changes
- 2026-10-13 router: T1 next -> done
- 2026-10-13 router: T2 next -> done
- 2026-10-13 router: T3 next -> done
- 2026-10-13 router: T4 next -> done
- 2026-10-13 router: T5 next -> done
- 2026-10-13 router: T6 next -> done
- 2026-10-13 router: T7 next -> done
- 2026-10-13 developer: T7 review: wave 1 accepted; T8 harvest sweeps neutral fn_/ram_/rom names and stub-group propagation across all regions before routing; waves 2+ batch comments and meaning names at ~1500 insns per coder run
- 2026-10-13 router: T8 next -> done

## Plain-English Recap
Phase 1.7 ("Campaign") turned the byte-matching rebuild of the game into one assembled from instruction source: every one of the 252 code regions (a "region" is one row of `config/regions.retail.tsv`, a slice of the ROM marked code or data, verified by evidence or inferred) is now listed as 68000 instructions and reassembled by the default `make build`, and the result is still byte-identical to the retail ROM. The developer first decided where that source lives (decision D1, `docs/decisions/source-location.md`): only on the developer's machine, under the ignored `asm/` directory, regenerated from tracked "sidecar" tables (names, comments, ledger) plus the developer's own ROM dump; tracking it in the repository (forbidden by the public-repo rule G12) and a separate repository were both declined. T1 built the campaign ledger (`scripts/census/ledger.py`, `config/campaign/ledger.tsv`), one row per code region with a size stratum (small, medium, large), a closeness score (how many operands still read as raw addresses) and a blocker; at the start the code held 29994 raw absolute operands. T2 keyed the decompression oracle files by each parent's start address instead of a position number that shifted on every inserted row, which retired the hand-remap skill `decrunch-parent-remap`. T4 made the default build regenerate `asm/src` for every listable code region and fail loudly on any mismatch, rendered comments from `config/ghidra/comments.tsv` into the listings, and added `.gitattributes` (line endings forced to LF, because `core.autocrlf=true` on this machine produced CRLF checkouts the table readers refuse).

T5 gave every inferred row a verdict. `code_01FA2E` was promoted to verified code by a controlled experiment: exceptions injected through vectors 25, 26, 27, 29 and 31 entered it and returned with the exact stack pointer 30 times out of 30, a known handler (vector 28) did the same 6 of 6 times, and a vector pointing at padding (vector 2, into `pad_01facc`) behaved like a handler 0 of 3 times; the game never raises these exceptions in normal play. The other 31 inferred rows stay inferred with a named class and blocker (8 lone returns, 4 return stubs, 11 unreached code, 1 unreferenced table, 2 data of inferred code, 1 unread data, 1 vector-target fill, 1 ROM-tail fill, 2 ROM-tail residue). T6 logged the values the game writes to named memory across 3 scenarios with positive controls (`config/oracle/values.tsv`, 30 rows) and renamed nothing, because no placeholder reached the bar of 3 consistent datapoints for one meaning (the nearest miss is `jcart_38FFFE`).

T7, accepted by the developer at review, was the first manual wave: six regions (`code_010810`, `code_012EE0`, `code_01F800`, `code_03F278`, `code_00635E`, `code_041A84`) reached closeness 0 with names and comments. The video-chip helper names rest on the published VDP register map plus the register numbers observed (2, 3, 4, 5, 13); the rest are structural names (`nullsub`, `slotpair4_a`/`_b`, `slot4_fn`). Checking 42 draft comments against the rendered listing found wrong or inexact claims in 23 of them. T8 harvested the wave: cookbook C0021-C0025, a script sweep giving every operand target a neutral name (`config/names/ram.tsv` 82 to 1739 rows), `signatures.py bulk-neutral` (routines 50 to 698 rows, three gates, a planted corrupted target refused), a `route` column on the ledger (comments-only `unattended` below 50 instructions, `developer-review` above) with a hard-fail health rung `ledger`, and `scripts/census/commentcheck.py`, which checks the mechanical claims in comments against the tables (12 of 12 planted wrong claims caught) and is also a health rung. Over the phase raw absolute operands fell from 29994 to 14345, operands still nameable from 16111 to 462, and named operands rose from 1120 to 18411. Its proposed waves-2+ plan for phase 1.9 is about 27 coder runs of roughly 1,500 instructions each, for comments and meaning names.

Milestone evidence (this session, 2026-10-13): `tools/phaseend_index.py verify` ran the plan's chain `make clean && make build && make health && ledger.py check && audit_public.py && test -z "$(git ls-files asm build expected)"` detached through `run.sh` and reported GREEN 1/1, exit 0 (`.run/logs/verify.log`, clause log `.run/logs/verify1.log`): `build/mmtt96.bin: OK` after a clean (`rm -rf build asm/src ...`), `health: pairs 9/9 agree`, `asm_leak: 521 files scanned, 0 runs >= 12`, `encmap: forms 394/394 mapped`, `ledger: code regions 252/252 undecoded 0; inferred 31 without-verdict 0` (252 = `kind code` rows counted from the region file by the closer), `audit_public: OK` 0 offenders among 521 paths, no tracked file under `asm`, `build` or `expected`. `ledger.py report` this session: strata small 123, medium 87, large 37 (verified code rows; T1 read 122 small before `code_01FA2E` was promoted); raw_abs 14345, nameable 462, named_ops 18411.

Push state: the remote-tracking ref `origin/main` reads `87254ed` (HEAD at the start of this close), 0 commits ahead, so it is newer than the `875a802` (1.5 close) named in the closer's brief; the close commits below are local only. The developer pushes; agents never push.
