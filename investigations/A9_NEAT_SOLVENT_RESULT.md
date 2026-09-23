# A9 diverse neat-solvent electron-transfer test result

**Disposition before robustness:** POSITIVE P1 CANDIDATE

Across the twelve frozen conventional neat solvents:

- viscosity LOO MSE = 0.5592193
- independently measured solvation-time LOO MSE = 0.1831733
- Delta MSE(solv|visc) = +0.3760460

Descriptive correlations:
- viscosity vs log reaction time: Pearson r = 0.7923; Spearman rho = 0.8246
- solvation time vs log reaction time: Pearson r = 0.9332; Spearman rho = 0.9561

Preregistered ACN-exclusion sensitivity:
- viscosity LOO MSE = 0.5332967
- solvation-time LOO MSE = 0.2110008
- Delta MSE(solv|visc) = +0.3222959

The positive contrast therefore survives the preregistered fastest-solvent sensitivity check.

## Predictor independence

The solvation-time predictor is not reconstructed from the BPAc+ target reaction times.

The conventional-solvent solvation dynamics were previously measured with the nonreacting Coumarin 153 probe (Horng, Gardecki, Papazyan & Maroncelli, 1995, DOI 10.1021/j100048a004). The BPAc+ electron-transfer times were measured in a separate later study (Horng, Dahl, Jones & Maroncelli, 1999, DOI 10.1016/S0009-2614(99)01258-0), whose abstract explicitly compares the reaction times to the previously measured Coumarin-153 solvation times.

This satisfies the pilot's target-leakage firewall at the measurement level.

Promotion remains contingent on the post-result robustness protocol frozen in Amendment A10.
