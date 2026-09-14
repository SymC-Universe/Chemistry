# CO/Cu(111) L15-L17 site-depth restart and production reproducibility record v0.1

Date opened: 2026-09-06
Repository: `SymC-Universe/Chemistry`
Branch: `agent/na-cu001-integration`

## Purpose

This record preserves the order of operations by which the frozen CO/Cu(111) L15-vs-L17 site-depth diagnostic moved from a mechanically infeasible standard-runner path to a qualified exact-restart paid-runner path and then into production. It is an operations/provenance record. It does not modify, retune, or reinterpret the frozen scientific contract.

The governing protocol remains `systems/co_cu111/SYSTEM2_PBE_L15_L17_SITE_DEPTH_DIAGNOSTIC_v0.2.json`. The production runner remains `systems/co_cu111/pbe_l15_l17_site_depth_diagnostic_v2.py`.

## Frozen scientific contract retained throughout

- System: CO/Cu(111)
- Slab depths: L15 and L17
- Matched sites: top, bridge, fcc_hollow, hcp_hollow
- Supercell: 2x2
- k mesh: 8
- Nominal coverage: 0.25 ML
- Slab-depth sensitivity gate: 0.005 eV/CO
- Checkpoint semantics: `QE_CLEAN_MAX_SECONDS_EXACT_RESTART`
- QE `max_seconds` per segment: 16200 s
- Maximum SCF segments: 6
- Original L17 clean-surface failure remains preserved
- `absolute_clean_surface_pass_claimed = false`
- `low_coverage_4x4_sufficiency_claimed = false`
- No automatic L19 dispatch

## Order of operations

### 1. Standard-runner production attempt established a mechanical resource hold

The v0.2 site-depth diagnostic had already demonstrated that its standard GitHub-hosted runner path could fail before a scientific energy result. This was treated as a mechanical/resource failure, not a scientific L15/L17 result. The frozen v0.2 protocol preserves that distinction and preserves the prior L17 scientific HOLD.

### 2. Exact-restart qualification was run before relying on paid-runner production

Qualification workflow:

- Workflow: `.github/workflows/co-cu111-l15-l17-restart-qualification-v1.yml`
- Run ID: `34019612490`
- Head commit: `070552d7bb87bd4f0a329ac171ed242c64c1ca47`
- Qualification case: real frozen `L15/top`, not a toy SCF
- Paid runner label: `ubuntu-latest-m`
- Observed memory in qualification segment 2: about 62.8 GiB

The qualification first verified the frozen protocol, immutable source evidence, source hashes, engine hash manifest, and original L17 HOLD before starting paid compute.

### 3. Qualification segment 1 started the real L15/top SCF from scratch and stopped only at an admissible QE checkpoint

Job ID: `101449652301`

Recorded state:

- depth: `L15`
- site: `top`
- segment: `1`
- status: `CHECKPOINT`
- restart mode: `from_scratch`
- SCF converged: `false`
- scientific settings changed: `false`
- elapsed SCF time: `17037.83187842369 s`
- protocol SHA-256: `eb9ad034cc7b514e797ccc3b9790f797e337634419ba65d03edab16fa9292772`
- checkpoint-manifest SHA-256: `c87f29e950ecda3c93019ebc79a1b4f932108fff520d182a1f3a4386a4aa877c`
- raw-input SHA-256: `544f38c026b4791ca14c537afe9738392c212a76f9477efc0fffcf7a5172466a`
- raw-output SHA-256: `c3426b248c002c5eefbe8d047f0263a3dca2fd001e8fb83d72ace1ccd02e392c`

Preserved artifact:

- name: `co-cu111-l15-l17-restart-qualification-seg01-v1`
- artifact ID: `9989239836`
- size: `9032821275` bytes
- artifact ZIP digest: `sha256:a58e09018960dee2d48d99f5a874bab14ecb20a917b4bce01d76bda96b395bf9`

### 4. Qualification segment 2 first verified segment 1, then exercised the exact restart path

Job ID: `101486021651`

Before continuation the job downloaded the preserved segment-1 artifact, verified the artifact digest, and required:

- admissible prior status
- exact `L15/top` identity
- prior segment number `1`
- `QE_CLEAN_MAX_SECONDS_EXACT_RESTART` checkpoint semantics
- a clean `max_seconds` stop when checkpointed
- a nonempty checkpoint-manifest hash

The job printed `PRIOR_STATE_VERIFIED_CHECKPOINT` before invoking the continuation.

It then invoked the same frozen SCF runner with `--segment 2 --prior-root prior`. The resulting state recorded:

- depth: `L15`
- site: `top`
- segment: `2`
- status: `CHECKPOINT`
- restart mode: `restart`
- SCF converged: `false`
- scientific settings changed: `false`
- elapsed SCF time: `16221.079166412354 s`
- protocol SHA-256: `eb9ad034cc7b514e797ccc3b9790f797e337634419ba65d03edab16fa9292772`
- checkpoint-manifest SHA-256: `4b2eac5e26ff545d6bd01104eb7fdb0be3a84e19aac71810932995e3498a56a0`
- raw-input SHA-256: `a2bae7f60a3d73bc32066263cfe61a327081526277281273f05d50508f55d0a3`
- raw-output SHA-256: `58adba680bcd85820bcbcc74eb900d843548e9a24e4f1c46398d43037efb5304`

The post-run proof required that `restart_mode == restart`, that the generated QE input explicitly contained restart mode `restart`, that no wrapper timeout occurred, and that the original L17 HOLD/firewall remained intact. It then printed `EXACT_QE_RESTART_QUALIFIED`.

Preserved artifact:

- name: `co-cu111-l15-l17-restart-qualification-seg02-v1`
- artifact ID: `9993508118`
- size: `9089744204` bytes
- artifact ZIP digest: `sha256:08b6764dc39bcd099cd12e242deda32bb0256bd712e3951e487186e3bd68598f`

The qualification therefore established a real, hash-traceable checkpoint lineage. It did **not** claim an L15 scientific energy because the SCF remained checkpointed rather than converged.

### 5. Qualification code and production code were checked for identity before reuse

Between qualification commit `070552d7bb87bd4f0a329ac171ed242c64c1ca47` and the production runner-routing commit `f9ba88edee6490013999b0d6d7cc312a5ce8a9db`:

- protocol Git blob SHA: `08020c8172e140a5ea41a1e2446c1b265197d1a8`
- runner Git blob SHA: `54316e0c1153ac5e2af70db60e7c3b59716cbe1f`

Thus the reusable L15/top qualification checkpoint was generated by the same frozen protocol and same SCF state-machine implementation used by production. The production workflow additionally checks the raw protocol SHA stored inside the imported state before accepting reuse.

### 6. First paid production launch exposed an orchestration inefficiency and was stopped early

Initial paid production run:

- Run ID: `34048251571`
- Head commit: `f9ba88edee6490013999b0d6d7cc312a5ce8a9db`

That workflow correctly routed the eight matched cases to the qualified paid-runner class, but it initially started `L15/top` from scratch instead of consuming the already-qualified L15/top checkpoint. This was identified as unnecessary recomputation rather than a scientific issue.

The run was cancelled early. It is retained in provenance as a cancelled orchestration attempt and must not be interpreted as a scientific L15/L17 result.

### 7. Production was rewired to reuse the qualification checkpoints with fail-closed provenance checks

Corrective commit:

- commit: `e1df5fd5b92f3ebbd274ccb453ea83647ffb9ac6`
- message: `Reuse qualified L15 top checkpoint in production diagnostic`

Replacement production run:

- Run ID: `34048806316`
- run number: `3`

The corrected workflow is configured so that:

1. L15/top segment 1 is imported from qualification run `34019612490` rather than recomputed.
2. The imported segment-1 state must match L15/top/segment-1, the current frozen protocol SHA, exact-restart checkpoint semantics, and the original L17 scientific firewall.
3. L15/top segment 2 is likewise imported from qualification run `34019612490` rather than recomputed.
4. The imported segment-2 state must match L15/top/segment-2 and the same provenance/firewall requirements.
5. Production L15/top can then continue from segment 3 through the ordinary tested state machine.
6. The other seven matched L15/L17-site cases begin from scratch because no equivalent previously qualified scientific checkpoints exist for them.

### 8. Production segment-1 checkpoint reuse was then verified live rather than assumed

Replacement-run job `101528646242`, `L15/top segment 1 of 6`, reached the reuse path after the replacement preflight passed.

Observed production behavior:

- `Reuse qualified L15 top segment 1`: `success`
- `Verify reused qualified L15 top segment 1`: `success`
- `Install unchanged QE runtime dependencies`: `skipped`
- production input-artifact download for a fresh SCF: `skipped`
- `Start frozen 2x2 K8 matched-depth SCF`: `skipped`
- upload of the verified production-carried state: started after the provenance verification

Therefore the production workflow did not merely contain checkpoint-reuse code; it demonstrably selected that code path and avoided re-running the already-qualified L15/top segment-1 QE calculation. Segment-2 import remains separately subject to its own verification when the workflow reaches that stage. Only after that succeeds may production L15/top continue at segment 3.

## How the tests were used

Tests were not treated as a substitute for the real restart qualification. They were used as a firewall before production and were then complemented by the real two-segment L15/top restart exercise.

In replacement production preflight, job `101528619053`, the workflow ran:

1. Python byte-compilation of the v1 runner, v2 runner, and v2 test file.
2. The v2 runner self-test, which returned `SELF_TEST_PASS`.
3. The dedicated v2 unit test suite, which returned 9/9 tests `OK`.
4. Explicit frozen-contract assertions after the test suite.
5. Immutable source and L17 result hash verification.
6. Stage-A engine and pseudopotential hash-manifest verification.

The nine passing v2 tests were:

- `test_checkpoint_manifest_detects_mutation`: verifies that checkpoint evidence is fail-closed against file mutation.
- `test_exact_restart_control_fields`: verifies the exact-restart QE control construction.
- `test_frozen_v02_contract`: verifies the v0.2 scientific/resource contract remains frozen.
- `test_matched_geometry_atom_counts_and_common_vacuum`: verifies the matched geometry construction used for L15/L17 comparison.
- `test_rejects_l17_reclassification`: verifies the diagnostic cannot rewrite the original L17 failure into a pass.
- `test_rejects_return_to_4x4_under_v02_claim`: prevents silently claiming the mechanically infeasible 4x4 observable under the 2x2 diagnostic.
- `test_rejects_threshold_retuning`: prevents post-outcome sensitivity-threshold changes.
- `test_resource_hold_is_preserved`: preserves the historical mechanical resource-hold provenance.
- `test_sufficiency_classifier_pass_and_fail`: exercises both sides of the final diagnostic classification rule.

The test suite completed with `Ran 9 tests` and `OK`, followed by the explicit `V0_2_RESOURCE_ADAPTATION_FIREWALL_VERIFIED` assertion block. The same preflight then reverified the L15 and L17 source identities, the original L17 HOLD, the Stage-A engine, and all three pseudopotentials before production work was admitted.

This gives two distinct layers of evidence:

- **software tests** verify that the state machine, firewalls, geometry rules, thresholds, and checkpoint-integrity logic behave as specified;
- **the real qualification calculation** verifies that an actual QE L15/top checkpoint survives artifact transfer and resumes with exact QE restart semantics on the selected paid runner.

The live production segment-1 reuse adds a third link: the production workflow actually consumed and verified the qualified checkpoint instead of silently recomputing it.

None of these layers is represented as proving the eventual L15-vs-L17 scientific result. That result remains pending the completed eight-case diagnostic and final adjudication.

## Meter-conscious execution rule

Larger GitHub-hosted runners are treated as metered compute. Cost control is therefore based on avoiding unnecessary paid runner-minutes, not on changing scientific settings.

For this L15-L17 diagnostic the operational priority is:

1. If a valid compatible COMPLETE state exists, carry it forward without QE recomputation.
2. If a valid compatible CHECKPOINT exists, resume from the newest verified checkpoint.
3. Never restart an entire case from scratch merely because a later mechanical segment failed if a verified prior checkpoint survives.
4. Never run overlapping paid production copies of the same frozen case.
5. Do not repeat a demonstrated broken paid-runner path unchanged.
6. Do not add a seventh segment or an L19 scientific rung under the current frozen v0.2 contract.
7. Treat `max-parallel` as a wall-clock control, not as a claim of reduced total metered minutes.
8. Preserve each paid job's start/end time, case identity, segment number, terminal state, and artifact lineage so paid runner-minutes can be reconstructed from GitHub job metadata.
9. The currently active replacement run `34048806316` is authorized to continue as needed to complete the frozen diagnostic.
10. If recovery from a future mechanical failure would require discarding valid checkpoints or materially duplicating many paid runner-hours, escalate the cost consequence before launching a broad paid recomputation. Narrow checkpoint-preserving mechanical recovery remains authorized.

GitHub's workflow timing endpoint currently reports `billable ... total_ms: 0` for the larger-runner qualification even though the run demonstrably occupied larger runners. That endpoint is therefore not used as the authoritative larger-runner cost meter here. Meter reconstruction uses each larger-runner job's actual start/end timestamps and GitHub's billing dashboard remains authoritative for dollar charges.

The qualification run's total workflow duration was approximately 34,016,000 ms. For scientific-compute accounting, the two real L15/top QE segments recorded 17037.83 s and 16221.08 s of SCF elapsed time respectively. These are preserved so reuse savings can be distinguished from fresh paid compute.

The user's account-level spend observed outside this repository is not encoded here as a reproducibility datum. This record tracks reproducible compute lineage and paid-runner use, while GitHub billing remains the authoritative source for dollar charges.

## Scientific status after first live production reuse verification

- Exact QE restart: mechanically QUALIFIED on a real L15/top case.
- L15/top after qualification segment 2: CHECKPOINT, not scientifically converged.
- Replacement production preflight: PASS.
- Production reuse of L15/top qualification segment 1: VERIFIED PASS.
- Production reuse of L15/top qualification segment 2: PENDING its workflow stage.
- L15/bridge production segment 1: real SCF in progress when this update was recorded.
- Eight-case L15-vs-L17 scientific adjudication: PENDING.
- Original L17 clean-surface scientific HOLD: PRESERVED.
- No L19 authorization: PRESERVED.

This file should be updated after production segment-2 checkpoint-import verification, after each terminal eight-case state is available, and after final adjudication so the final reproducibility guide can reconstruct the complete sequence without relying on conversational history.