# Chemistry project state — 17 September 2026

**Status:** current superseding source-of-record state pointer for active Chemistry work  
**Supersedes:** `CHEMISTRY_PROJECT_STATE_2026-09-16.md` for current execution state and downstream H/Ru(0001) gate disposition  
**Governing program baseline:** SymC General Operations Manual v0.8.0  
**Source-of-record branch:** `agent/na-cu001-integration`

This record does not rewrite historical results or `governance/IMPLEMENTATION_STATUS_v1.1.json`. The v1.1 registry remains historical deployment-capability evidence from 14 September 2026. Live execution state is read separately from GitHub Actions.

## 1. System 3 — H/Ru(0001)

### Fixed-grid depth

The valid prospective fixed-grid extension remains:

- status: `PASS_FIXED_GRID_LAYER_ASYMPTOTIC_REGIME`
- selected lowest passing non-terminal suffix: **L17**
- terminal reference: **L19**
- frozen tolerance: **0.001 eV per surface atom**
- L17 -> L19 absolute difference: **0.000307420632452704 eV per surface atom**

No layer result is changed by this state update.

### Clean-surface relaxation/reproduction

The accepted L17 clean surface was subsequently relaxed and independently reproduced on branch `bridge/h-ru0001-relax-pass-20260917`.

Valid result:

- status: `CLEAN_SURFACE_RELAX_PASS`
- readiness: `SURFACE_READY`
- maximum movable force: **0.0005723 eV/angstrom**
- frozen force threshold: **0.02 eV/angstrom**
- fresh-SCF reproduction absolute energy difference: **1.22e-8 eV**
- frozen reproduction tolerance: **0.001 eV**

This supersedes the prior statement that clean-surface relaxation/reproduction was merely the next eligible gate.

### Shared H pseudopotential qualification

Prospectively frozen shared-H qualification run **35295414137** completed with a genuine frozen-gate HOLD:

- status: `SHARED_H_PSEUDOPOTENTIAL_HOLD`
- candidate: `H.nc.pbe.z_1.oncvpsp4.sg15.v0.upf`
- candidate MD5: `39a7d154f04d65093d603a437119a874`
- candidate SHA-256: `6f339df39b8556f1f648bb2c292728ce709a6bc93aa3878d9ab23142a5f01d34`
- exact QE runtime SHA-256: `2b1ede22d276b1d4dab3e31212f306e88ae57e00f33ce6b532b849493a457855`
- frozen bases: 70/280 Ry and 80/320 Ry
- frozen H2 final-force ceiling: **0.005 eV/angstrom**
- H2 maximum final force at 70/280: **0.018395216198306058 eV/angstrom**
- H2 maximum final force at 80/320: **0.01871737545104524 eV/angstrom**
- atomic-H records returned code 0 but did not satisfy the frozen completion parser, so both atomic energies are null
- consequently `all_complete=false`, `force_pass=false`, bond-difference and binding-energy-difference crosschecks are unresolved/null
- result artifact: `system3-shared-h-pseudopotential-qualification-v1`, artifact ID **10527449397**

The two H2 force values alone exceed the prospectively frozen force ceiling. The HOLD therefore may not be rescued by treating the atomic-H completion issue as a mechanical parsing defect, by changing the 0.005 eV/angstrom threshold, by using downstream H/Ru agreement, or by retuning the protocol after outcome inspection.

This HOLD qualifies neither H/Ru adsorption accuracy nor any barrier, rate, dissipation, chi, capital-Chi, or site-ordering claim.

### Adsorption Stage A

Adsorption Stage-A run **35295894752** completed with workflow conclusion `failure` because its entry gate correctly observed that run 35295414137 did not finish with `SHARED_H_PSEUDOPOTENTIAL_PASS`.

No Stage-A adsorption matrix case ran. Therefore:

- no Stage-A adsorption scientific result exists;
- no Stage-A scientific HOLD is inferred;
- `STAGE_A_SELECTION_PASS` was not obtained;
- downstream Stage B is not scientifically authorized.

A CI hygiene defect allowed the Stage-A selector to execute after the matrix was skipped. That behavior is not scientific evidence. The bridge workflow was mechanically patched at commit `947154ee16348332b0ccd8ae4ec3fd692501a624` so selection cannot run when the Stage-A matrix is skipped or cancelled. The current failed Stage-A run is not rerun because the upstream H qualification remains a genuine HOLD.

### Adsorption Stage B

Stage-B run **35295941060** did not execute any Stage-B adsorption case.

Its wait step had a mechanical GitHub-output formatting defect: diagnostic polling text was redirected into `$GITHUB_OUTPUT`. The later always-run adjudicator then saw zero Stage-B case artifacts and emitted `ADSORPTION_SITE_NUMERICAL_HOLD / missing_stage_b_cases`. That record is **invalid as a scientific HOLD** because Stage B never ran and Stage A never passed.

The bridge workflow was mechanically repaired at commit `4d204c96c48eef16f7ff7774908457fa19445ea4` to:

1. write only the valid `stage_a_run_id` key to `$GITHUB_OUTPUT` after exact Stage-A workflow success; and
2. suppress Stage-B adjudication when the Stage-B matrix is skipped or cancelled.

No Stage-B rerun is authorized while `SHARED_H_PSEUDOPOTENTIAL_HOLD` remains the upstream disposition.

### Current System 3 boundary

The valid H/Ru chain is therefore:

`fixed-grid depth PASS (L17) -> clean-surface relaxation/reproduction PASS -> shared-H pseudopotential qualification HOLD`

Adsorption Stage A and Stage B are blocked upstream. The H qualification HOLD is preserved as scientific/numerical evidence and must not be reclassified as a mechanical failure.

## 2. System 2 — CO/Cu(111)

Scientific disposition remains `NUMERICAL_HOLD_EXTENSION_AUDIT` until an actual L19 scientific adjudication supersedes it.

Checkpoint-preserving recovery run **35112369188** on branch `bridge/co-cu111-l19-20260916` remains active under the unchanged frozen L19 protocol.

Completed successfully in the recovery chain:

- recovered relax segment 2 from the last verified segment-1 checkpoint;
- relax segments 3, 4, 5, and 6;
- SCF segments 1, 2, and 3.

At this state capture, **SCF segment 4 is in progress**. No final L19 adjudication has yet been reached.

No scientific file, method, geometry, threshold, acceptance rule, evidence firewall, or interpretation has changed.

## 3. System 1 — Na/Cu(001)

C9 remains mechanically blocked pending a verified environment with **at least 32 GB memory**. It must not be forced onto standard/approximately 8 GB hardware by changing the frozen physical or numerical problem. No such compute environment is authorized by this state update.

## 4. Barrier-Height/Rate Atlas

Barrier-Height/Rate Atlas v0.9 remains `CLOSED_REPRODUCIBLE_V0.9` and immutable except for explicitly additive future work. None of the H/Ru or CO/Cu activity modifies the frozen Atlas.

## 5. Execution-state snapshot

At this state capture:

- H pseudopotential qualification run 35295414137: **COMPLETED / SHARED_H_PSEUDOPOTENTIAL_HOLD**;
- H/Ru Stage-A run 35295894752: **COMPLETED / blocked by upstream H HOLD; no adsorption cases executed**;
- H/Ru Stage-B run 35295941060: **COMPLETED/CANCELLED; no adsorption cases executed; missing-case adjudication is invalid as scientific evidence**;
- CO/Cu(111) recovery run 35112369188: **RUNNING**, SCF segment 4 active;
- queued GitHub Actions runs at capture: **0**;
- no paid/larger runner is authorized or used.

Deployment capability remains distinct from execution state. `governance/IMPLEMENTATION_STATUS_v1.1.json` remains historical deployment evidence and its 14 September execution snapshot is not a live-state claim.

## 6. Operational boundaries

1. Preserve `SHARED_H_PSEUDOPOTENTIAL_HOLD`; do not rerun or relax its frozen criteria as mechanical recovery.
2. Do not start or rerun H/Ru Stage A or Stage B unless a new prospective scientific decision legitimately supersedes the shared-H HOLD.
3. Treat the Stage-B `missing_stage_b_cases` adjudication from run 35295941060 as invalid/superseded CI output, not as a physical adsorption HOLD.
4. Keep the Stage-A and Stage-B mechanical gating fixes, but do not use those fixes to bypass the shared-H gate.
5. Continue CO/Cu checkpoint-preserving recovery without changing frozen science; retain `NUMERICAL_HOLD_EXTENSION_AUDIT` until final L19 adjudication.
6. Keep Na/Cu C9 on mechanical resource HOLD until a verified >=32 GB environment exists.
7. Keep Barrier-Height/Rate Atlas v0.9 immutable.
8. Use standard free GitHub-hosted runners only unless a new explicit dollar authorization is provided.
