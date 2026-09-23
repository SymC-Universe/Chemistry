# Capital-Chi rate pilot amendment A7: DPB multi-solvent-class environment test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE NUMERIC TABLE EXTRACTION

## Source system

Dahl, Biswas, and Maroncelli, *The Photophysics and Dynamics of Diphenylbutadiene in Alkane and Perfluoroalkane Solvents*, J. Phys. Chem. B (2003), DOI 10.1021/jp0300703.

The paper reports measured photophysical/nonradiative dynamics and rotational reorientation of trans,trans-diphenylbutadiene (DPB) across nonpolar solvent classes.

## Capital-Chi interpretation

This test asks whether independently measured microscopic environment coupling plus coarse environment class contains rate information not captured by bulk viscosity alone.

No fitted reactive-friction scale factor from the source may be used as a predictor.

## Frozen target

Use the source's measured nonradiative decay/isomerization rate (k_{nr}) (or the exact equivalent rate variable reported in its table) for each solvent condition with a complete predictor set.

## Frozen predictors

### M0 bulk control
- solvent viscosity (eta)

### M1 microscopic dynamics
- measured DPB rotational reorientation time (	au_R)

### M2 architecture
- measured (	au_R)
- solvent-class indicator fixed from chemical identity before outcome inspection:
  - alkane
  - perfluoroalkane

If a third class is present only through literature backfill rather than the same experimental series, it will not enter the primary model.

## Frozen transformations and validation

Use natural-log transforms for positive continuous variables and target.

For each model:
1. leave-one-solvent-out linear prediction of (ln k_{nr});
2. LOO mean squared error;
3. LOO mean absolute log error;
4. Pearson and Spearman descriptive correlations for single continuous predictors.

Primary contrasts:
[
Delta MSE_{micro|bulk}=MSE(M0)-MSE(M1)
]
[
Delta MSE_{arch|bulk}=MSE(M0)-MSE(M2)
]
[
Delta MSE_{arch|micro}=MSE(M1)-MSE(M2)
]

Positive values favor the richer predictor.

## Restrictions

- No source-fitted conversion from rotational friction to reactive friction may be used.
- No class-specific multiplier may be fit outside the ordinary regression coefficients learned within each training fold.
- No additional solvent descriptor may be added after outcome inspection without a dated amendment.
- If sample size is too small for a stable two-class LOO regression, M2 is reported as exploratory only.
- This remains P1 within-family evidence at most.
