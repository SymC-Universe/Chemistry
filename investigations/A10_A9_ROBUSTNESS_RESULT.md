# A10 robustness result for A9

**Final A9 disposition:** ROBUST P1 WITHIN-FAMILY EMPIRICAL EVIDENCE

## R1 target-uncertainty Monte Carlo

Frozen protocol: 100,000 draws, deterministic seed 20260922, reaction-time uncertainties propagated; viscosity and solvation predictors held fixed.

Delta MSE is defined as:
[
MSE_{viscosity}-MSE_{solvation}.
]

Results:
- 2.5th percentile: **0.1947821**
- median: **0.3772299**
- 97.5th percentile: **0.7418556**
- fraction of draws with Delta MSE > 0: **0.99999**

Thus the positive predictive contrast survives the reported target uncertainties.

## R2 solvent-deletion jackknife

All 12 leave-one-solvent-deleted datasets retained positive Delta MSE.

Range:
- minimum: **0.2201203** (delete 1-butanol)
- maximum: **0.4890612** (delete methanol)
- positive subsets: **12/12**

Per-solvent deletion:
- acetonitrile: 0.3222959
- acetone: 0.4356938
- dimethylformamide: 0.4184193
- dimethylsulfoxide: 0.3766314
- methanol: 0.4890612
- formamide: 0.3637526
- N-methylformamide: 0.4289557
- ethylene glycol: 0.4562582
- ethanol: 0.3875417
- 1-propanol: 0.3100259
- N-methylpropionamide: 0.3951659
- 1-butanol: 0.2201203

## Interpretation

For this BPAc+ conventional-solvent family, an independently measured whole-environment relaxation time predicts held-out reaction dynamics more accurately than bulk viscosity under the frozen log-linear model.

This supports an incremental kinetic role for a Capital-Chi-type environment-organization descriptor **within this reaction family**.

It does not establish:
- a scalar capital-Chi rate coordinate;
- a cross-family rate law;
- superiority over all native rate theories;
- P2 evidence.

No feature or model was changed after the positive A9 result.
