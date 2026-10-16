# Verification record: the reproducibility contract

A dated snapshot of one contract run: a fresh clone of the committed HEAD, the developer's own dump and the documented
tools, following README.md "Build from your own dump" literally and cold. Only hashes, counts and timings.

## Run of 2026-10-13

- Command: `bash scripts/contract.sh --asl-zip <AS snapshot zip> --dump <own dump>` with `PY` and `GHIDRA_INSTALL_DIR`
  set as README step 2 says; run detached through `tools/run.sh --bg contract`.
- Commit: 2026-10-13T15:09:19+01:00, "T6: Add scripts/contract.sh: cold fresh-clone contract run".
- Clone: `git clone -c core.autocrlf=true` into a dot-free scratch directory outside the repository; cold (no copied
  `ghidra/`, `asm/` or `.run/`).
- Input stamp: `63819e85ed41648c` (first 16 hex of the sha256 over the sha256 sums of `config/regions.retail.tsv`,
  `config/check.retail.sha`, `config/manifest.retail.jsonl`, `config/campaign/ledger.tsv`).
- eol_crlf: 0 (`git ls-files --eol`, files with CRLF in the working tree).
- Timings: clone 1 s, bootstrap 2 s, build 27 s, health 108 s.
- Build: `build/mmtt96.bin: OK`.
- Health: `health: pairs 9/9 agree`.
- Ledger: `ledger.py check`: code regions 252/252, undecoded 0; inferred 31, without-verdict 0.
- No vendor SDK: the kit's with/without-SDK clause does not apply.
- The live oracles (MAME and BizHawk, `make health-live`) are excluded from the contract run; every pair of
  `make health` is offline.
- Result: `contract: OK`.

## Run of 2026-10-16 (phase 1.9 milestone, readable state)

- Command: `bash scripts/contract.sh --dump <own dump>` with `PY` set as README step 2 says (no `--asl-zip`: bootstrap
  fetched the one approved AS asset, sha256-checked before extraction); run detached through `tools/run.sh --bg`.
- Commit: 2026-10-16T12:38:03+01:00, "router: T35 done".
- Clone: `git clone -c core.autocrlf=true` into a dot-free scratch directory outside the repository; cold.
- Input stamp: `4b4527ddcf8f7808` (same recipe as above).
- eol_crlf: 0.
- Timings: clone 1 s, bootstrap 4 s, build 34 s, health 133 s.
- Build: `build/mmtt96.bin: OK`.
- Health: `health: pairs 9/9 agree`.
- Ledger: `ledger.py check`: code regions 252/252, undecoded 0; inferred 31, without-verdict 0.
- Main tree, same commit, the rest of the milestone chain: `ledger.py check --complete` complete 252/252, no-plate 0,
  entries pending 0/715, raw operands 0, neutral names pending 0/2201; `commentcheck.py` 3125 comments, 12545 claims,
  0 failed; `commentcheck.py --doc docs/mechanics.md` 544 bullets, 2365 pointers, 0 failed; `constants.py check` hw
  100/100 symbolic; `audit_public.py` 0 offenders; card 6994/7000.
- Result: `contract: OK`.

Not covered here: the no-ROM CI (`.github/workflows/no-rom.yml`, jobs `audits` and `selftest`) runs on GitHub after a
push; its result is the developer's check (plan 1.8 T7).
