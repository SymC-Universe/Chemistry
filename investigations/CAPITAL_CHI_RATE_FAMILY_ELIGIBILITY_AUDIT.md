# Capital-Chi rate pilot: family eligibility audit

Atlas families audited: **26**

## Disposition counts

- `P0D_partial`: 1
- `P1_negative_frozen_features`: 1
- `blocked_by_baseline_identifiability`: 3
- `high_quality_but_no_incremental_X`: 1
- `ineligible_current`: 4
- `ineligible_for_primary_rate_test`: 3
- `ineligible_incremental_current`: 1
- `ineligible_no_observed_rate`: 2
- `no_need_for_correction`: 1
- `regime_only`: 9

## Family audit

| Family | n | Grades | Baseline / overlap | Capital-Chi feature status | Disposition |
|---|---:|---|---|---|---|
| FAM-4OT-ENZYME-PROTON-TRANSFER | 1 | B:1 | baseline_embedded_and_source_independence_limited | multistep/tunneling embedded | **ineligible_current** |
| FAM-5-HEXENYL-RADICAL-CYCLIZATION | 1 | B:1 | baseline_model_spread_dominates | TS geometry/dispersion/solvation mostly method architecture | **blocked_by_baseline_identifiability** |
| FAM-AQ-DIELS-ALDER | 4 | B:4 | partial_incremental_candidate | initial-state solvation/hydrophobic descriptors | **P0D_partial** |
| FAM-AQ-FE2-FE3-ELECTRON-EXCHANGE | 1 | B:1 | baseline_embedded | Markov eigenmode/Hab/reorganization embedded | **regime_only** |
| FAM-AQ-HALOMETHANE-SN2 | 2 | B:1;C:1 | baseline_embedded | hydrodynamic friction is embedded | **regime_only** |
| FAM-AQ-THIOLATE-DISULFIDE-SN2 | 1 | C:1 | baseline_embedded | hydrodynamic friction is embedded | **ineligible_no_observed_rate** |
| FAM-BETA-CD-HOST-GUEST-ASSOCIATION | 7 | B:7 | tested_incremental | water/host reorganization independent | **P1_negative_frozen_features** |
| FAM-ETHOXYHETEROCYCLE-ETHYLENE-ELIMINATION | 3 | C:3 | source_scale_conflict | unresolved | **ineligible_current** |
| FAM-FORMATE-METAL110-DEHYDROGENATION | 6 | C:6 | grade_C_reconstructed_series | surface material organization possible | **ineligible_for_primary_rate_test** |
| FAM-GAS-CH3NC-ISOMERIZATION | 3 | A:3 | baseline_embedded_or_missing | none_identified | **high_quality_but_no_incremental_X** |
| FAM-GAS-CYCLOBUTANE-RING-OPENING | 3 | A:3 | baseline_embedded | multistep network embedded | **regime_only** |
| FAM-GAS-DIELS-ALDER-BUTADIENE-ETHENE | 1 | B:1 | baseline/target_scope_problem | unresolved | **ineligible_current** |
| FAM-GAS-H-ABSTRACTION-ETHANE | 1 | A:1 | baseline_embedded | tunneling/path degeneracy embedded | **regime_only** |
| FAM-GAS-H-ABSTRACTION-METHANE | 1 | A:1 | baseline_embedded | tunneling/path degeneracy embedded | **regime_only** |
| FAM-GAS-H2-OH-ABSTRACTION | 1 | A:1 | baseline_embedded | tunneling/path degeneracy embedded | **regime_only** |
| FAM-GAS-H3-EXCHANGE | 5 | A:2;C:3 | method_benchmark_scope | same-PES exact/instanton structure | **ineligible_current** |
| FAM-LICO2-LITHIUM-LATTICE-DIFFUSION | 1 | C:1 | proxy_scope_grade_C | lattice transport organization possible | **ineligible_for_primary_rate_test** |
| FAM-LPS-SOLID-ELECTROLYTE-DIFFUSION | 4 | C:4 | proxy_scope_grade_C | collective transport organization possible | **ineligible_for_primary_rate_test** |
| FAM-MORPHINONE-REDUCTASE-HYDRIDE-TRANSFER | 4 | B:4 | baseline_embedded | recrossing/tunneling/preorganization mostly native | **regime_only** |
| FAM-OH-HO2-RADICAL-TERMINATION | 1 | B:1 | baseline_model_spread_dominates | PES topology/TS frequencies/master equation | **blocked_by_baseline_identifiability** |
| FAM-PD-PCY3-PHBR-OXIDATIVE-ADDITION | 1 | B:1 | baseline_envelope_contains_observation | speciation/pathway organization independent in part | **blocked_by_baseline_identifiability** |
| FAM-PORPHYCENE-DOUBLE-PROTON-TRANSFER | 2 | B:2 | baseline_embedded | channel competition/tunneling embedded | **regime_only** |
| FAM-POV-PCET-CROSS-REACTIONS | 2 | B:2 | baseline_calibrated | cross-relation architecture embedded | **ineligible_incremental_current** |
| FAM-PT332-HYDROGEN-OXIDATION | 1 | C:1 | no_point_rate_closure | surface mechanism | **ineligible_no_observed_rate** |
| FAM-QTTFQ-INTRAMOLECULAR-ELECTRON-TRANSFER | 3 | B:3 | baseline_embedded_or_overlap_unresolved | solvent dynamics encoded by explicit simulation | **regime_only** |
| FAM-SO2PLUS-CO-OXYGEN-ATOM-TRANSFER | 1 | B:1 | baseline_model_spread_dominates_for_tiny_residual | ISC/capture architecture embedded | **no_need_for_correction** |

## Interpretation

This matrix is an eligibility audit, not a rate-prediction result. It applies the preregistered target-leakage firewall, Amendment A1 baseline-overlap rule, and Amendment A4 native-baseline identifiability gate.

The main result of the audit is that the frozen Atlas is excellent for testing barrier/rate closure but was not built as a Capital-Chi dataset. In most families, the obvious dynamical architecture is already embedded in the native rate calculation, the empirical target is not sufficiently independent, or native-model sensitivity is too large to diagnose an omitted architectural correction.

The one completed incremental within-family test is beta-cyclodextrin. Its three preregistered independent environment-reorganization features were negative against the stricter leave-one-out intercept-only calibration control.

Aqueous Diels-Alder remains a partial P0-D lead, but only two rows have directly audited raw experimental rates and the strongest transition-state solvent-transfer quantities are themselves rate-derived and therefore forbidden as predictors.
