# Chemistry project state — 16 September 2026

**Status:** current superseding source-of-record state pointer for active Chemistry work  
**Supersedes:** `CHEMISTRY_PROJECT_STATE_2026-09-14.md` for current execution state and the H/Ru(0001) fixed-grid layer gate  
**Governing program baseline:** SymC General Operations Manual v0.8.0  
**Source-of-record branch:** `agent/na-cu001-integration`  
**Prior source-of-record head:** `2191b75196c71b83b92b5a787f54a6018dd31933`

This record does not rewrite historical results or `governance/IMPLEMENTATION_STATUS_v1.1.json`. The v1.1 registry remains the deployment-capability record from 14 September 2026. Live execution state is read from GitHub Actions and is recorded here only as a dated snapshot.

## 1. Scientific state changes since 14 September

### System 3 — H/Ru(0001)

The prior `CLEAN_SURFACE_NUMERICAL_HOLD` has been superseded **only at the fixed-grid layer-convergence gate** by a valid prospective extension and recovered adjudication.

Frozen extension protocol:

`systems/h_ru0001/SYSTEM3_CLEAN_RU0001_LAYER_EXTENSION_L15_L19_v0.1.json`

Computed extension run:

- GitHub Actions run: `35060420908`
- branch: `bridge/h-ru0001-l15-l19-20260916`
- valid new fixed-grid cases: L15, L17, L19
- no scientific setting, geometry, threshold, kinetic input, evidence-firewall rule, or acceptance rule changed

The original adjudication job failed mechanically because the source-ladder parser selected only records tagged `first_stage_requested == "layers"`. The frozen source contract included L7, but the source run had correctly reused the already-selected L7 slab from its earlier k-mesh/vacuum stage instead of recomputing it in the later layer stage. The exact selected-condition L7 record was present in the source artifact and reproduced the frozen declared L7-to-L13 delta.

A mechanical-only record-routing correction recovered that already-existing selected L7 source record. No numerical case was recomputed. Adjudication-only recovery run `35080334319` then completed successfully on the preserved source and L15/L17/L19 artifacts.

Recovered adjudication:

- status: `PASS_FIXED_GRID_LAYER_ASYMPTOTIC_REGIME`
- selected lowest passing non-terminal suffix layer: **L17**
- terminal reference: **L19**
- frozen tolerance: **0.001 eV per surface atom**
- L17 -> L19 absolute difference: **0.000307420632452704 eV per surface atom**
- next eligible gate: `H_RU0001_CLEAN_SURFACE_RELAXATION_AND_REPRODUCTION`
- automatic adsorption progression: **not allowed**
- automatic further layer extension: **not allowed**

The complete preserved layer ladder in the successful adjudication is:

| layers | surface excess (eV / surface atom) | origin |
|---:|---:|---|
| 5 | 1.0987778170992897 | source run |
| 7 | 1.0929096816544188 | source selected baseline |
| 9 | 1.0954157142714394 | source run |
| 11 | 1.0895499598245806 | source run |
| 13 | 1.0926721942851145 | source run |
| 15 | 1.092107489992486 | extension |
| 17 | 1.091078831559571 | extension |
| 19 | 1.0907714109271183 | extension |

This PASS does not imply adsorption, kinetics, reaction-rate, chi, capital-Chi, or cross-system closure.

### System 2 — CO/Cu(111)

Scientific disposition remains `NUMERICAL_HOLD_EXTENSION_AUDIT` until the currently authorized L19 exact-restart convergence extension is completed and adjudicated. The existence of a running workflow does not itself supersede the HOLD.

### Barrier-Height/Rate Atlas

Barrier-Height/Rate Atlas v0.9 remains `CLOSED_REPRODUCIBLE_V0.9`, immutable except for explicitly additive future work. Nothing in the H/Ru or CO/Cu bridge work modifies the v0.9 Atlas.

## 2. Execution-state snapshot at capture

At this state capture:

- CO/Cu(111) L19 exact QE restart convergence run `35059010039` is **RUNNING** on branch `bridge/co-cu111-l19-20260916`;
- its frozen-contract/preflight job has passed and the exact-restart segment is active;
- H/Ru(0001) L15/L17/L19 computation is complete;
- H/Ru adjudication-only recovery run `35080334319` is complete and successful;
- no H/Ru numerical rerun is scientifically required by the successful adjudication;
- no paid/larger runner is authorized or used.

Deployment capability remains distinct from execution state. `governance/IMPLEMENTATION_STATUS_v1.1.json` remains historical evidence of qualified/wired capabilities; its 14 September `IDLE` execution snapshot is not a claim about the live 16 September Actions state.

## 3. Mechanical recovery record

The H/Ru adjudication correction changed only source-record routing so that the exact pre-existing selected L7 baseline could be included in the prospectively frozen `[5,7,9,11,13]` source ladder. It did not change:

- any computed energy;
- the PBE method;
- cutoffs;
- k mesh;
- vacuum;
- geometry;
- bulk reference;
- layer set;
- 0.001 eV/surface-atom threshold;
- suffix decision rule;
- evidence firewall;
- interpretation.

The superseded H/Ru v1 computation workflow has been retired from automatic push execution after it was accidentally retriggered by the mechanical parser/test correction. That accidental run failed before numerical computation at its already-known missing-SSSP extraction step; the actual layer-case step was skipped. Future use of that v1 route is explicitly refused.

## 4. Next operational boundaries

1. Do not advance H/Ru directly to adsorption. The successful fixed-grid layer gate makes only the named clean-surface relaxation/reproduction gate eligible.
2. Do not rerun L15/L17/L19 merely because the original combined workflow concluded `failure`; all three numerical cases completed successfully and the only failing step was the mechanically defective adjudicator, which has now been recovered without recomputation.
3. Do not change CO/Cu state until run `35059010039` produces an exact output/adjudication record.
4. Continue to read live Actions state separately from deployment qualification.
5. Keep Barrier-Height/Rate Atlas v0.9 immutable.
6. Standard free GitHub-hosted runners only unless a new explicit dollar authorization is provided.
