# Capital-Chi rate pilot amendment A10: robustness of the positive A9 result

**Date:** 2026-09-22  
**Status:** POST-PRIMARY-RESULT ROBUSTNESS PROTOCOL, FROZEN BEFORE ROBUSTNESS CALCULATION

A9 produced the first positive incremental result. This amendment is explicitly post-result and cannot change the original model or feature set. Its purpose is to try to break the result.

## R1: target-uncertainty Monte Carlo

Use the twelve reported reaction times and their reported uncertainties.

For each of 100,000 deterministic-seed Monte Carlo draws:
1. sample each reaction time from a normal distribution centered on the reported value with the reported uncertainty as sigma;
2. reject/resample nonpositive draws;
3. log-transform the sampled reaction times;
4. repeat the exact A9 leave-one-solvent-out log-linear comparison for viscosity and solvation time;
5. record Delta MSE = MSE(viscosity) - MSE(solvation time).

Report:
- median Delta MSE;
- 2.5th and 97.5th percentiles;
- fraction of draws with Delta MSE > 0.

No predictor uncertainty is invented where the source table does not report it.

## R2: solvent jackknife influence

For each of the twelve solvents:
1. remove that solvent entirely;
2. on the remaining eleven rows, repeat the exact LOO comparison;
3. record Delta MSE.

Report:
- minimum and maximum jackknife Delta MSE;
- number of 11-solvent subsets with Delta MSE > 0;
- identity of the most influential deletion.

## Robustness criterion

A9 is considered robust P1 evidence only if:
- at least 95% of target-uncertainty Monte Carlo draws retain Delta MSE > 0; and
- all or all-but-one solvent-deletion jackknife subsets retain Delta MSE > 0.

Failure does not trigger feature/model changes. It downgrades the result.
