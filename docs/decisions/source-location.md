# Decision D1 — where the converted instruction source lives

Decided: 2026-10-13, by the developer, at approval of the phase 1.7 plan. Recorded by phase 1.7 task T3.
Status: active. Supersede only by a new dated decision here (and, for any tracked source, a project rule
superseding G12 at a named commit; see "Reversal" below).

## Decision
Option (a). The converted instruction source lives locally only, under ignored `asm/` paths (`asm/src/<id>.asm`),
regenerated from tracked sidecar files (names `config/names/*.tsv`, comments `config/ghidra/comments.tsv`, the
campaign ledger `config/campaign/ledger.tsv`, signatures/routine names) plus the developer's own dump of the game.
The repository never tracks instruction source, in this private phase or after publication.

## Options as offered (plan phase 1.7, ## Rationale)
- (a) Private working tree / rebuild-from-dump: instruction source is generated (`db.py listing` + names + comments
  sidecars) into ignored `asm/src/`; readability lives in tracked sidecars keyed by address (`config/names/*.tsv`,
  `config/ghidra/comments.tsv`, later an operand-expression sidecar for constants); full G12 compliance, the publish
  gate (1.8) is a contract run; cost: hand edits to source text are impossible (H1), every readability construct needs
  a sidecar renderer, readers need their own dump to see code. CHOSEN.
- (b) Track `src/` in this private repo with a dated exemption: violates G12 exactly as written (no private
  exemption); requires relaxing `asm_leak` and the purge set; publishing later needs the DK-53..56 rewrite with host
  purge or a recreated repo, or never publishing source. DECLINED (forbidden outright by G12).
- (c) Hybrid: source in a separate never-published private repository (this repo stays compliant; two repos to sync;
  build points at an external path) or an encrypted archive in git (ciphertext of game code is still game-derived bytes
  in git and needs key management: rejected as worse than both). DECLINED.

## Why (a)
- It is the only reversible option: sidecar-rendered source can be emitted into a tracked `src/` later in one commit if
  a project rule ever supersedes G12 for publication; (b) cannot be undone without a history rewrite.
- G12 (`rules/G12.md`): nothing derived from the game in any tracked or published artifact from the first commit,
  including generated disassembly and any text file that pastes the target's instructions; no private-repository
  exemption (the source project relaxed it while private and paid with a full-history rewrite of about 4,000 commits).

## Consequences (G12, DK-53..58)
- G12 holds unchanged: `config/firewall.txt`, `.gitignore` class 3 (`asm/`, `build/`, `expected/`),
  `tools/audit_public.py` and `scripts/health/asm_leak.py` stay as they are; no relaxation, no allowlist.
- DK-53..58 (`docs/decomp-kernels.md`) forbid nothing new; they are the bill a relaxation would run up, and (a) avoids
  it: no history rewrite to rehearse commit-by-commit with positive assertions (DK-53), no worktrees pinning purged
  history (DK-54), no fetching probe re-importing it (DK-55), no host still serving pre-force-push tips (DK-56; G17: not
  private until the host purged the objects), no broken hash citations (DK-57). DK-58 (outward text is a person's)
  applies to publication unchanged.
- Readability work (names, comments, constants) is expressed only as tracked sidecar rows keyed by address; each new
  construct needs a renderer in the listing path (H1: generated files are never hand-edited).
- Readers of the published project need their own copy of the game to see code; the repo ships tools and sidecars.
- The converted source itself has no version control in git. The sidecars are tracked, so they are versioned; what
  exists only locally is the dump (`disks/`) and ignored caches (`ghidra/` db, `.run/`, `asm/`, `build/`), all
  regenerable from the dump and the tracked files.
- `src/NOTICE.md` assumes publishable source under `src/`, which this project will not have; revisit at the publish
  phase.

## Measured inputs (phase 1.7 T1, 2026-10-13; `scripts/census/ledger.py write` then `report`)
- Ledger rows: 252 code rows (246 verified + 6 inferred).
- Embedded data inside code listings: 0 bytes in 0 runs.
- Absolute operands: raw 29994; nameable 16111; named 1120.
- Strata by instruction count: small (< 50) 122; medium (50-300) 87; large (> 300) 37.
- Full listing wall time: about 11.5 s for 246 regions (regeneration from the dump is cheap enough to run every build).
- Reading: with no embedded data and about 16k nameable operands, readability is sidecar-expressible (names + comments
  + a later operand-expression sidecar); nothing measured needs hand-edited source text.

## What the source pipeline (T4) must provide
- A `make src` target that regenerates `asm/src/` from the dump and the tracked sidecars.
- The default `make build` assembles from instruction source (not the all-data form).
- `config/ghidra/comments.tsv` rendered into the listing.
- No change to the firewall, `asm_leak.py`, `audit_public.py` or README.

## Developer action item (not done by any agent)
- Keep a local backup of the dump (`disks/`) outside the working tree. The sidecars are tracked in git and need no
  extra backup once committed; everything ignored (`asm/`, `build/`, `ghidra/`, `.run/`) is regenerable.
- Commit hand-edited sidecar rows promptly: an uncommitted sidecar edit is the only readability work that can be lost.

## Reversal
Publishing assembly source would need a project rule superseding G12 at a named commit (never a private exemption),
then one commit emitting the rendered source into a tracked `src/`. No history rewrite is needed under (a).
