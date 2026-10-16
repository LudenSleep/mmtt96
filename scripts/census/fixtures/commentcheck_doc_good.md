# Doc fixture: good (synthetic; commentcheck.py --self-test)

Prose before any section heading is not a claim.
- A bullet before the first `## ` heading is not checked.

## Section one

- A sample widget turns blue on each tick. [confirmed: P001]
- A sample counter steps once per frame. [confirmed: t2w_challenge_20261013T165019, t2w_h2h_20261013T165027, t2w_pool_20261013T165035]
- The sample pair agrees. [hypothesis: t2st_base_20261013T165121+t2st_same_20261013T165123]
- A sample open question. [hypothesis]

### Sub-section

- Sample pointers of every name kind. [hypothesis: header, ram_frame_counter, vdp_init_regs, slot, slot.x, vdp_no_scaling]
  - An indented sample bullet with a doc path. [hypothesis: docs/ops/ops-tools.md:1, config/oracle/probes.tsv]

```
- a bullet inside a code fence is not checked
```
