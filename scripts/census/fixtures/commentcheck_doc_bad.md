# Doc fixture: bad (synthetic; one planted failure per check, every bullet must fail)

## Planted

- marker: a sample bullet with no marker.
- name: a sample name that is tracked nowhere. [hypothesis: ram_not_a_tracked_name]
- run: a sample run id that no oracle table holds. [hypothesis: sample_20000101T000000]
- probe: a sample probe id that probes.tsv lacks. [hypothesis: P999]
- path: a sample doc path that does not exist. [hypothesis: docs/no_such_doc.md]
- confirmed: a sample claim with one run and no controlled probe. [confirmed: t2w_pool_20261013T165035]
