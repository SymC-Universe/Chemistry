# Na/Cu(001) Computational Checkpoint and Failure Ledger

**Status:** active execution record  
**Established:** 2026-08-03 15:16 America/Chicago  
**Repository:** `SymCUniverse/Chemistry`  
**Branch:** `agent/na-cu001-integration`  
**Primary draft PR:** `#3`  
**Merge state:** intentionally unmerged during computation  
**Scientific object:** one registered Na hopping mechanism on Cu(001)  
**Bridge target:** independent barrier/saddle/prefactor branch for later joined-dynamics comparison with the separately qualified ChemSA evidence branch  

## 1. Record policy

This ledger is the chronological execution record for the computational route. It supplements `COMPUTATIONAL_PROCESS_AMENDMENT_v1.1.md`, `BULK_EXTENSION_AMENDMENT_v1.2.md`, and `REPRODUCIBILITY_GUIDE_INSERT_v1.1.tex`.

Each checkpoint must record:

1. the exact workflow run and commit;
2. the completed job or gate;
3. artifact names and SHA-256 links when available;
4. the frozen numerical criteria applied;
5. PASS, HOLD, MECHANISM_REVISION_REQUIRED, or MECHANICAL_FAILURE;
6. the next permitted dependency;
7. every related GitHub notification email and its disposition.

A job conclusion of `success` is not by itself a scientific PASS. A scientific gate is PASS only when the registered result artifact states PASS and its dependencies and hashes validate.

No failed job may be silently retried. Before a retry, the failure must be classified as one of:

- **MECHANICAL_FAILURE:** transport, syntax, permissions, missing file, runner, or workflow plumbing defect. A focused prospective patch is allowed; scientific criteria cannot change.
- **SCIENTIFIC_HOLD:** the calculation completed sufficiently to show that a frozen scientific criterion was not satisfied. The result is retained. A later extension requires a new prospective protocol, not threshold relaxation.
- **SUPERSEDED_EXPLORATORY_RUN:** an earlier route whose scientific or implementation contract was replaced before current-route admission. It remains in history and is not used as evidence.
- **EXTERNAL_OR_UNRESOLVED:** insufficient evidence to diagnose. No retry or admission is permitted until resolved.

## 2. Frozen checkpoint sequence

| ID | Gate | Required terminal record | Status |
|---|---|---|---|
| C0 | Corrected source, protocols, negative tests, workflow and artifact DAGs | verified source commit and test log | PASS |
| C1 | Original 80 Ry/16^3 bulk holdout against historical matrix | `BULK_CONVERGENCE_RESULT.json` | SCIENTIFIC_HOLD |
| C2 | Audited bulk-extension protocol frozen before results | protocol, runner, tests, workflow linter | PASS |
| C3 | Extension engine and historical-input preparation | pinned QE/UPF artifacts and preflight test log | PASS |
| C4 | Twenty-six six-point extension EOS calculations | 26 raw EOS artifacts and summaries | IN_PROGRESS |
| C5 | Independent 140 Ry/22^3 reference audit against 150 Ry/24^3 and candidate selection | `BULK_CONVERGENCE_RESULT_V0.4.json`; PASS-only handoff | PENDING |
| C6 | Independent v0.4 artifact audit and downstream bridge publication | verified run ID, result/handoff hashes, 46 summaries, bridge tests | PENDING |
| C7 | 64-case ESM `bc1` clean-slab matrix and surface-excess gate | Stage 2 slab result and handoff | PENDING |
| C8 | Electrostatic audit, clean relaxation/SCF reproduction, isolated Na reference | Stages 3-5 PASS artifacts | PENDING |
| C9 | Two-mobility adsorption map and symmetry-equivalent endpoint reproduction | Stages 6-8 PASS or retained mechanism revision | PENDING |
| C10 | 5/7/9 ordinary NEB and CI-NEB for both mobility models | Stages 9-12 PASS artifacts | PENDING |
| C11 | Full-path primary/expanded mobility convergence | Stage 13 PASS artifact | PENDING |
| C12 | Nested mass-weighted Hessians and three-dimensional downhill connectivity | Stages 14-15 PASS artifacts | PENDING |
| C13 | Barrier sensitivity calculations and nonprobabilistic envelope | Stage 16 PASS artifact | PENDING |
| C14 | Tiered barrier, saddle, prefactor, model-rate curve, and Atlas admission | Stages 17-18 PASS artifacts | PENDING |
| C15 | Complete raw/source manifest audit and generated terminal verdict | Stage 19 integration-readiness artifact | PENDING |

## 3. Completed checkpoint details

### C0: corrected implementation and adversarial testing

**Result:** PASS.  
**Published source commit:** `02973538c3effc3fc97f77767205765fae42d413`.  
**Corrected route launch commit:** `1cd76ee2fb425bdb72b43c41c8e46e3e0ffdc94a`.  
**Scope:** corrected bulk joint gate, pinned QE and SSSP provenance, common ESM convention, one-sided mobility models, mechanism-refusal rule, ordinary and CI-NEB separation, mass-weighted active-region Hessians, three-dimensional downhill tests, sensitivity envelope, tiered output, and non-circular artifact graph.  
**Verification:** 23 original unit/adversarial tests plus workflow and artifact contracts passed before launch. Later bulk-extension and v0.4 compatibility tests raise the prepared local total to 33 tests without changing scientific criteria.

### C1: corrected v0.3 bulk decision

**Workflow run:** `30840469734`.  
**Launch commit:** `1cd76ee2fb425bdb72b43c41c8e46e3e0ffdc94a`.  
**Result:** SCIENTIFIC_HOLD.  
**Observed condition:** all twenty historical candidates through 70 Ry/14^3 failed the unchanged `|delta E0| <= 0.001 eV/atom` requirement against the independently executed 80 Ry/16^3 EOS, although lattice constants were broadly converged.  
**Disposition:** retained as a negative convergence result. No candidate selected; all surface and downstream jobs skipped. The threshold was not changed and the reference could not select itself.

### C2: prospective audited bulk extension

**Protocol status:** frozen after C1 and before any extension result.  
**Launch commit:** `ec0e18c86ead22e7062047fdff68e43ead72945f`.  
**Extension workflow:** `Na Cu001 audited bulk convergence extension v1`.  
**Candidates:** 80, 90, 100, 110, 120, 130 Ry crossed with 14^3, 16^3, 18^3, 20^3.  
**Finite reference:** 140 Ry/22^3.  
**Independent audit:** 150 Ry/24^3.  
**Unchanged criteria:** `|delta a0| <= 0.005 A`; `|delta E0| <= 0.001 eV/atom`.  
**Selection:** smallest frozen computational-cost score among eligible joint-pass candidates. Reference and audit are ineligible.

### C3: extension preparation

**Workflow run:** `30843005718`.  
**Result:** PASS.  
**Completed:** historical 20-EOS set verified; pinned QE 7.6 rebuilt; Cu UPF hash verified; extension source and matrix contracts passed; reusable engine and historical-input artifacts uploaded.  
**Permitted next action:** execute exactly the registered 26 EOS cases.

### C4: extension matrix execution

**Workflow run:** `30843005718`.  
**Status at ledger establishment:** 21 of 26 EOS jobs completed successfully; 5 in progress; 0 failed; final gate not yet released.  
**Completed candidate groups:** all 80, 90, 100, and 110 Ry combinations; 120 Ry at 14^3, 16^3, and 18^3; 130 Ry at 14^3 and 16^3.  
**In progress:** 120 Ry/20^3; 130 Ry/18^3; 130 Ry/20^3; 140 Ry/22^3 reference; 150 Ry/24^3 audit.  
**Prohibited interpretation:** no candidate is selected and no bulk PASS exists until C5 finishes and the v0.4 artifacts are independently audited.

## 4. Failure and notification register

| Notification or run | Classification | Root cause / scientific meaning | Resolution or disposition | Closed? |
|---|---|---|---|---|
| Run `30808976656`, legacy complete route; slab matrix failed | SUPERSEDED_EXPLORATORY_RUN | Earlier route reached slab jobs before the corrected electrostatic, geometry, mobility, provenance, and gate architecture was installed | Replaced by corrected V2 route. Outputs are not admissible and are not retried | Yes |
| Install-route runs around commits `3e6093a`, `bd16768`, `a938498`, `ccb0622`, `18ce546` | MECHANICAL_FAILURE | Bootstrap transport/chunk verification and GitHub workflow-write permission limitations during source installation | Source archive was re-chunked and verified; source was installed first; workflow files were installed last through the connector; corrected source commit `02973538...` and launch commit `1cd76ee...` verified | Yes |
| Run `30840469734`, corrected route prepare failed | SCIENTIFIC_HOLD | No historical candidate passed the frozen energy criterion against 80 Ry/16^3 | Retained; prospective v0.4 extension frozen and launched without threshold change | Yes, as HOLD |
| Active extension run `30843005718` | no failure notification as of 2026-08-03 15:16 America/Chicago | 21/26 jobs successful and remaining five computing | Continue monitoring; no intervention permitted absent a classified failure | Open execution |

### Email reconciliation, 2026-08-03 15:16 America/Chicago

Mailbox search covered recent GitHub notifications for `SymCUniverse/Chemistry`, `Na Cu001`, `Na/Cu(001)`, workflows, failures, and cancellations.

- The newest failure email concerns run `30840469734` and matches the retained C1 scientific HOLD.
- Earlier install-route failure emails match the resolved bootstrap and workflow-permission installation failures.
- The earlier legacy slab-failure email matches the superseded exploratory route and is excluded from evidence.
- No failure or cancellation email exists for active extension run `30843005718` at this checkpoint.

## 5. Internal checkpoint rules for remaining execution

### C5 bulk closure

Before declaring PASS:

- require all 26 new summaries and all 156 SCFs;
- require every SCF to have successful return code, convergence marker, final energy, input hash, output hash, and Cu UPF hash;
- require the 140 Ry/22^3 reference to pass both frozen criteria against 150 Ry/24^3;
- require the selected candidate to be an eligible candidate, never the reference or audit;
- independently recompute selection order and deltas from downloaded summaries;
- preserve a HOLD if the reference audit or candidate gate fails.

### C6 downstream bridge

Publish only after independent C5 inspection. The bridge must:

- bind the exact successful extension run ID;
- import and verify the v0.4 result, handoff, 46 summaries, source manifest, and raw manifest;
- reject the v0.3 HOLD and any v0.4 non-PASS;
- rerun all unit, negative, workflow, artifact, and tier tests;
- launch the downstream workflow once, avoiding duplicate expensive runs.

### C7-C15 downstream gates

At each gate:

1. inspect GitHub job status and artifacts;
2. search recent GitHub-notification email for failure/cancellation notices;
3. classify every failure before changing code or rerunning;
4. patch only a demonstrated mechanical defect;
5. never alter a frozen scientific threshold after seeing results;
6. append the run, artifacts, hashes, result, and next dependency to this ledger;
7. retain unexpected minima, alternate paths, disagreement, and absence of admission as scientific outcomes.

## 6. Completion definition

The computational phase is complete only after C15, when Stages 1-18 and all raw/source manifests validate and Stage 19 is generated without self-reference. The final package may end as PASS, HOLD, or mechanism revision. Only a full PASS permits generation of the tiered Barrier-Height/Rate Atlas coordinate. The later ChemSA bridge test remains a separate joined-dynamics stage and cannot retroactively tune this computational route.
