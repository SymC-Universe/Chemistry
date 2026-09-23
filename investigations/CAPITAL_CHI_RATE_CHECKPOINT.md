# Capital-Chi Modal Investigation Checkpoint

**Branch:** `agent/capital-chi-rate-pilot-20260922`  
**Current conceptual baseline:** modal reset A16 + `CAPITAL_CHI_MODAL_DEFINITION_v0.1_2026-09-22.md`  
**Manuscript:** private and not stored in this public Chemistry repository.

## Canonical distinction

- scalar `chi_i`: scalar coordinate attached to one licensed mode/carrier/subspace.
- capital `Chi`: modal/vector architecture itself.
- system/environment/conglomerate variables: separate embedding layer. They may perturb or condition modal Chi but are not automatically capital Chi.

Canonical modal record:
[
Chi=(Lambda,V_R,V_L,A_{s->V},P,K_V,U_V).
]

This instantiates the frozen Chemistry Stability Arc reporting contract:
`G,s,V,C,R,U`.

## Evidence status

### Direct modal mechanisms

**A17 Duschinsky modal-basis benchmark**
- same scalar frequency spectrum;
- mixed-mode displacement K=0;
- fixed solvent reorganization, temperature and energy gap;
- only Duschinsky basis matrix J(theta) changes;
- Franck-Condon distribution and rate proxy change strongly.
- source literature reports ~4-order inverted-region rate changes for the full model while reorganization peak remains fixed.

**A18 reactive-normal-mode benchmark**
- same bare barrier curvature;
- same bath frequency spectrum;
- same total scalar coupling norm S=1;
- only coupling-vector orientation across modes changes;
- unstable collective eigenvector and Grote-Hynes transmission change.
- kappa_GH: 0.6248 -> 0.9531 from phi=0 -> 90 deg.

### Empirical modal evidence

**A19 deuterated methane / Pt(111)**
- experiment supplies state-resolved sticking coefficients;
- independent DFT/SVP calculation supplies reactant-mode projections onto transition-state reaction-coordinate vectors;
- more strongly projected modes are more reactive within CH3D and CH2D2;
- bond-selective modal projection matrix distinguishes C-H and C-D channels.

Supporting gas-phase literature:
- CH3D + Cl: near-isoenergetic symmetric and antisymmetric C-H stretch preparation gives ~7x difference in H-abstraction enhancement.

### Prior A9-A15 work

Preserved but **demoted to environment/embedding precursor evidence**. These results do not directly validate capital Chi because they do not contain the required modal/vector carrier structure.

Do not resume from A9-A15 unless explicitly studying how an external perturbation reorganizes modal Chi.

## Current executable target

Build an **additive Capital-Chi modal reporting adapter** around ChemSA Release 38 without changing the frozen core engine.

The frozen inheritance contract states the engine already preserves:
- authoritative spectrum;
- indexed right eigenvectors;
- left/right response bases;
- mode geometry;
- conditioning/refusal state;
- separate mechanical modal factors.

The reporting gap is persistence/assembly of these into an explicit scalar-to-carrier modal record.

## Adapter requirements

The adapter must:
1. consume an already-built `BalancedSpectrum` and `SystemSummary`;
2. consume `ModeGeometry` records from the same `spectrum_id`;
3. emit indexed poles/eigenvalues and right/left modal bases;
4. preserve mechanical `chi_i` separately from spectral `pole_angle_rho`;
5. explicitly assign each licensed mechanical `chi_i` to its mass-normalized mechanical modal vector/subspace;
6. optionally accept declared physical coordinate vectors and report their mass-metric participation/projection;
7. report degeneracy, conditioning, unresolved/refusal state;
8. support modal correspondence between two conditions using overlap matrices, with correspondence rule frozen before target inspection;
9. never scalarize capital Chi by default;
10. require no modification of the frozen Release 38 core.

## Exact next action after interruption

Open this checkpoint, then inspect/continue:
- `chemsa_v3.py`: `BalancedSpectrum`, `MechanicalModeRecord`, `scalar_reduction_valid`, modal factor construction;
- `biorthogonal_response.py`: `ModeGeometry`, `all_mode_geometries_from_spectrum`;
- additive adapter + regression tests on the investigation branch.

First validation targets:
- ordinary proportional two-mode system with two distinct chi_i values;
- degenerate stiffness block requiring modal basis rotation;
- non-proportional system where mechanical chi must remain refused;
- A18-style saddle/modal projection record;
- correspondence under a known orthogonal mode rotation.

## Promotion gate after adapter

Do not alter the manuscript from this investigation yet.

The next scientific promotion requires:
1. adapter QA passes;
2. one real chemical system exposes the native modal basis needed to construct Chi;
3. modal Chi adds explanatory/predictive information beyond barrier/native energetics and local scalar chi_i;
4. no target-driven mode selection.

## Privacy rule

`SymC-Universe/Chemistry` is public. Do not commit current manuscript .tex/.pdf/submission-ready source here.


## 2026-09-23 modal execution closure

The modal correction is now implemented and empirically/theoretically exercised.

Completed after the modal reset:
- A17 Duschinsky modal-basis mechanism;
- A18 reactive collective-mode transmission mechanism;
- A19 Pt(111) empirical partial modal record;
- A20 CH3OH/Cu(111) multichannel projection matrix;
- A21 CH3D+Cl path-dependent modal evidence;
- modal data contract v0.1;
- additive path-aware modal adapter, 117 targeted tests passed;
- first prospective native molecular modal-output record for HCN<->HNC;
- same-method HCN/HNC minima, first-order saddle, independent frequency validation, and IRC endpoint closure;
- reproducible mass-metric endpoint-to-TS carrier/subspace correspondence committed.

Current consolidated status:
`investigations/CAPITAL_CHI_MODAL_STATUS_2026-09-23.md`
commit `8d5273c6a2b35e4e9a47c72aab31b83ee7150a98`.

### Exact resume target

Do NOT resume the old environment-variable Capital-Chi regressions.

Resume only from the independent kinetic-validation gate:

1. choose a reaction/system with independent kinetics and multiple states/conditions;
2. freeze its modal construction before inspecting target variation;
3. obtain/generate the native modal record;
4. compare native barrier/scalar baseline versus modal Chi increment under holdout;
5. include lowercase chi_i only if its damping/lifetime reduction is independently licensed.

No further feature mining on A17-A21 or HCN/HNC is allowed to manufacture P2.
