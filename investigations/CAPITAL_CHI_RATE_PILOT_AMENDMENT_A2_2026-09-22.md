# Capital-Chi rate pilot amendment A2: frozen Stage-0 and beta-CD P1 tests

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE NUMERIC ASSOCIATION CALCULATION

## A. Stage-0 non-Markovian controlled benchmark

Use the homogeneous-memory empirical expression reported in Brünig, Netz, and Kappler (2022), with:

- beta U0 = 3;
- tau_m / tau_D = 0.01;
- memory grid tau / tau_D = {1e-4, 1e-3, 1e-2, 1e-1, 1, 10};
- all barrier, mass/friction-scale, and potential-geometry quantities held fixed.

Record dimensionless MFPT and reciprocal MFPT as a rate proxy. This is a mechanistic sanity test only, not empirical validation.

## B. beta-cyclodextrin within-family P1 test

### Frozen systems
The seven q4MD-CD beta-cyclodextrin guest systems already present in Barrier-Height/Rate Atlas v0.9.

### Frozen target
For each guest:
[
r_i = ln(k_{obs,i}/k_{native,i}).
]

The native baseline is the q4MD-CD association rate already frozen in the Atlas.

### Frozen incremental Capital-Chi features
Extracted from Tang & Chang and fixed before calculating association with r:

1. **water_release_q4md**: net number of first-shell water molecules released on binding (Delta #, q4MD-CD).
2. **water_entropy_q4md_kcalmol**: q4MD-CD water entropy contribution reported as -T Delta S_water in kcal/mol.
3. **host_entropy_q4md_kcalmol**: q4MD-CD host internal entropy contribution reported as -T Delta S_host in kcal/mol.

These are treated as environment/host reorganization features. They were computed from the simulation architecture and were not fitted to the experimental association rates.

### Frozen analyses
For each feature separately:

1. descriptive Pearson correlation with r;
2. descriptive Spearman rank correlation with r;
3. leave-one-out linear residual prediction r_hat = a + b x;
4. compare LOO mean squared error against the frozen native-baseline residual predictor r_hat = 0.

Report:
[
Delta MSE = MSE_{baseline} - MSE_{CapitalChi-feature}.
]

Positive Delta MSE means the feature adds within-family predictive information; negative means it worsens prediction.

### Restrictions
- No feature may be dropped because it performs poorly.
- No extra beta-CD feature may be added after results are seen without a separately dated amendment.
- No multifeature regression will be promoted from n=7.
- No P2/general rate-prediction claim is allowed from this within-family case series.
