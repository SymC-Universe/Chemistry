# Checkpoint C6 preflight: complete V3 computational contract

**Status:** PASS, prospective and non-executable  
**Bulk v0.4 result known at workflow freeze:** no  
**Surface computation launched:** no  

## Verification run

- workflow: `Na Cu001 v0.4 downstream bridge tests`
- Actions run: `30851502637`
- job: `bridge-contract`
- conclusion: success
- temporary PR: `#14`
- PR disposition: closed unmerged
- artifact: `na-cu001-v04-bridge-and-v3-preflight`
- artifact digest: `sha256:a9e32ae2cfd418b38ef942cb949a5b4c6ef59ae871b19428245b537a332f1f42`

## Generated workflow

- generated filename: `na-cu001-computational-route-v3.yml`
- generated size: 20,134 bytes
- generated SHA-256: `250d0d16189777590b5851a5eff81016761202356bca174acaea65308484bf52`
- job count: 20
- Hessian matrix count: 108
- installation state: not installed under `.github/workflows`
- launch rule: install the exact verified bytes only after the live v0.4 decision and real artifact bundle independently pass

## Contracts verified

1. ten bridge and surface-entrypoint adversarial tests;
2. Python compilation of bridge, wrapper, builder, validator, and linter source;
3. shell syntax of `run_computational_stage_v3.sh`;
4. exact JSON/YAML parsing of the generated workflow;
5. 20-job workflow DAG and registered matrix cardinalities;
6. 19-stage artifact DAG with one validator-generated terminal artifact;
7. no terminal self-reference;
8. Stage 1 defined as the audited v0.4 bulk bridge;
9. required v0.4 result, handoff, protocol, upstream artifact-digest record, checkpoint ledger, and guide records;
10. commit-specific non-cancelling concurrency and separated raw-artifact collection.

## Source hashes recorded by the runner

The uploaded `V3_PREFLIGHT_SOURCE.sha256` records the generated workflow and all direct V3 bridge, entrypoint, stage-harness, plan, validator, and linter source. The generated workflow itself is not a live workflow and cannot dispatch any Quantum ESPRESSO job.

This preflight authorizes installation only after Checkpoint C5 is an independently verified PASS. A bulk HOLD leaves the workflow uninstalled and the surface route closed.
