# PE1.3.c1 README step 2: working make build
- README.md:22-26: replaced TODO(phase-3) step 2 with: copy dump to Makefile `ROM` path (or `make build ROM=<path>`); `make build` (GNU make, Git bash) splits -> `asm/` (ignored), assembles `build/mmtt96.bin` with clownassembler v1.1.3 from `tools/bin/` (ignored, user-fetched, never in git), `sha1sum -c config/check.retail.sha` -> `build/mmtt96.bin: OK`; `make clean && make build` = clean rebuild; pointer fixed `docs/ops-setup.md` -> `docs/ops/ops-setup-decomp.md`.
- Names confirmed from Makefile:1-43 (ROM var, build/clean targets, check.retail.sha) and ops doc build section.
- Steps 1, 3 untouched. Step is 5 lines, not 2-3 (wrapped at the file's ~120-col width).
- Verified: `python tools/audit_public.py` -> `audit_public: OK`, 0 offenders among 314 paths, exit 0.
