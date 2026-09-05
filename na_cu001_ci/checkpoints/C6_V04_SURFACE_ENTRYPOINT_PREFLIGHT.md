# Checkpoint C6 preflight: versioned v0.4 surface entrypoints

**Status:** PASS, prospective preflight only  
**Bulk v0.4 result known at source freeze:** no  
**V2 physics engines modified:** no  

## Versioned source

- `na_cu001_ci/slab_runner_v3.py`
  - commit `a4c671d39f815dacbb94720bb974d911266b5520`
  - substitutes only the v0.4 bulk loader before delegating slab cases and analysis to `slab_runner_v2.py`;
  - requires the PASS bridge, result, handoff, reference audit, 46 EOS summaries, and 276 SCF inventory.
- `na_cu001_ci/closure_engine_v3.py`
  - commit `62eaea7bd3de2e1b3c6e22b29737f2ad952bfc3a`
  - replaces only `slab-handoff` and `resolve-na`, the two commands that directly consume the bulk handoff;
  - delegates adsorption, endpoints, ordinary NEB, CI-NEB, mobility, Hessians, connectivity, sensitivity, barrier, and Atlas admission to unchanged V2 functions.
- `na_cu001_ci/test_v04_surface_entrypoints_v1.py`
  - commit `bab4e9d91f7dba938fdf58a8186d47ac301f2755`.

## Isolated verification

- workflow: `Na Cu001 v0.4 downstream bridge tests`
- run: `30850655226`
- job: `bridge-contract`
- conclusion: success
- combined adversarial tests: 10/10
- artifact: `na-cu001-v04-bridge-test-record`
- artifact digest: `sha256:5d67fe0adf82fbdb1abcca1c277be17355c265b0246db2076124516569f0bffc`
- temporary trigger PR: `#13`
- PR disposition: closed unmerged

## Additional refusal behavior verified

1. valid bridge/result/handoff bundle is accepted;
2. slab handoff records direct v0.4 result, handoff, and bridge provenance;
3. failed independent reference audit is rejected;
4. incomplete 276-SCF inventory is rejected;
5. post-verification result mutation is rejected by hash disagreement.

This checkpoint authorizes no slab computation by itself. Surface execution remains blocked until the live v0.4 bulk decision is PASS and the real artifact bundle passes the frozen verifier.
