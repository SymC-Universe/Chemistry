# Capital-Chi Modal Investigation Status

**Date:** 2026-09-23  
**Current baseline:** modal definition v0.1 + modal data contract v0.1  
**Core distinction:** lowercase chi is scalar; capital Chi is modal/vector architecture.

## Corrected object

[
\chi_i = \text{licensed scalar coordinate attached to carrier }i
]

[
\Chi = (\Lambda,V_R,V_L,A_{s\to V},P,K_V,U_V)
]

with fields included only when licensed.

Bulk environment, barriers, memory, substrate and whole-system variables remain separate embedding layers unless they are explicitly represented through their effect on the modal architecture.

## Rate question

The valid question is:

> Does modal Capital Chi carry kinetic information beyond native energetics/barriers and any licensed local scalar chi_i?

Not:

> Can a larger scalar called Capital Chi predict rate?

## Modal evidence stack

### A17 Duschinsky rotation
Controlled external-literature + local benchmark.

Same scalar mixed-mode frequencies and zero displacement; different Duschinsky basis rotation. Kinetic Franck-Condon weighting changes strongly. External full model reports ~4-order inverted-region rate changes.

### A18 reactive collective mode
Controlled benchmark.

Same bare barrier, same bath spectrum and same total scalar coupling norm. Redistributing coupling across modes changes the unstable collective eigenvector and Grote-Hynes transmission from 0.6248 to 0.9531.

### A19 CH3D/CH2D2 on Pt(111)
Empirical partial modal record.

State-resolved sticking changes track independently calculated mode-to-reaction-coordinate projections. Exact partial projection matrix stored.

### A20 CH3OH on Cu(111)
Multichannel partial modal record.

Exact 5x3 stretch-mode/TS reaction-coordinate projection matrix. Row maxima identify selectively promoted bond-scission channel for 5/5 carriers. Several preparations within 92 cm^-1 of scalar excitation energy have strongly different efficacy and branching.

A single projection scalar does not fully predict efficacy; the matrix plus native energetics is the informative object.

### A21 CH3D + Cl
Independent gas-phase modal-path evidence.

Near-isoenergetic symmetric/antisymmetric C-H stretch preparation produces ~7x different enhancement. Ab initio tracking shows different mode localization/evolution along the reaction path.

## Additive ChemSA modal adapter

Files:
- `investigations/capital_chi_modal.py`
- `investigations/test_capital_chi_modal.py`

Current Git blob identities:
- adapter: `25d76871d360fcc6c704f9fd5cfa538cc7ec12c1`
- tests: `b9c6d1120fbb364884325f7bf8dfb11dc82cbd7f`

Targeted QA: **117 passed** against frozen ChemSA Release 38.

Capabilities:
- preserves pole-angle rho and mechanical chi separately;
- assigns licensed chi_i to explicit mechanical carriers;
- preserves spectral/reaction subspace geometry when chi refuses;
- treats exact degeneracy as a subspace, not arbitrary vectors;
- supports declared physical-coordinate projection;
- supports basis-invariant cross-condition/path subspace correspondence by principal angles;
- never scalarizes Capital Chi by default.

## First native real-molecule record: HCN <-> HNC

Private Rowan folder:
`4459e358-6eec-4a64-a964-0f08addfcc8b`

All calculations use AIMNet2 `aimnet2_wb97md3`.

### R0 minima
HCN and HNC independently optimized and frequency checked. Both are stable minima with complete normal-mode displacement vectors.

### R1/R2 saddle
Double-ended search returns bent Cs candidate.
Independent fixed-geometry validation gives exactly one imaginary frequency:

[
-2006.267,\;2268.267,\;3420.307\;cm^{-1}.
]

### R3 connectivity
30-step forward and backward IRC with optimized endpoints:
- forward -> HCN fingerprint;
- reverse -> HNC fingerprint.

Reaction path therefore closes HCN -> TS -> HNC.

### Native modal correspondence

Declared atom mapping H,C,N.
Endpoint structures mass-centred and proper mass-weighted Kabsch aligned to TS.
Degenerate endpoint bends treated as two-dimensional subspaces.

Carrier weights onto TS modes:

| endpoint carrier | TS unstable | TS stable 2268 | TS stable 3420 |
|---|---:|---:|---:|
| HCN bend subspace | 0.09984 | 0.03908 | 0.74963 |
| HCN CN stretch | 0.13276 | 0.86109 | 0.00353 |
| HCN CH stretch | 0.71163 | 0.08760 | 0.05119 |
| HNC bend subspace | 0.12362 | 0.04726 | 0.66514 |
| HNC CN stretch | 0.14918 | 0.84395 | 0.00186 |
| HNC NH stretch | 0.68675 | 0.09365 | 0.05699 |

The unstable reaction direction is therefore dominated by the terminal X-H stretch carrier from either side.

### Lowercase chi status

Unavailable. This electronic-structure calculation supplies no independently licensed mode-resolved damping/lifetime.

No chi is manufactured.

Capital Chi remains available through modal geometry.

## Current maturity

- controlled modal mechanism: P1+
- source-level empirical modal evidence: P0-Q/P1 depending source
- native molecular modal-output pipeline: P0-Q closed for HCN/HNC
- independent-source held-out modal rate prediction: **not yet P2**

## Current hard scientific gate

To promote Capital Chi as an incremental rate predictor, obtain a system or family with:

1. full or partial quantitative modal object frozen independently of kinetics;
2. native barrier/energetic baseline;
3. observed or independently generated kinetic outcome;
4. multiple states/conditions/systems enabling holdout;
5. no target-driven mode selection;
6. comparison against scalar controls, including chi_i where actually licensed.

The completed literature search found no turnkey dataset satisfying all six simultaneously.

The next strongest routes are:
- reconstruct modal objects from open reaction/Hessian archives and attach independent kinetics;
- prospectively generate native modal records for reactions with existing independent mode-specific kinetic measurements.

## Manuscript

Do not add this investigation to the current ChemSA manuscript merely because the modal result is interesting.

Promotion requires a separate manuscript-level decision after independent kinetic validation.

The current working manuscript remains private and absent from the public Chemistry repo.
