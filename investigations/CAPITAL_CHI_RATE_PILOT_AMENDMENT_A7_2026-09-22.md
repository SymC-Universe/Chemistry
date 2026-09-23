# Capital-Chi rate pilot amendment A7: barrier-corrected metallocene solvent-dynamics test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE NUMERICAL REGRESSION/CORRELATION CALCULATION

## Source

McManis, Nielson, Gochev, and Weaver, *Solvent Dynamical Effects in Electron Transfer: Evaluation of Electronic Matrix Coupling Elements for Metallocene Self-Exchange Reactions*, J. Am. Chem. Soc. 1989, 111, 5533-5541, DOI 10.1021/ja00197a004.

A public article copy exposes Tables I-III.

## Why this source is useful

Table II reports, solvent by solvent:

1. the inverse longitudinal solvent relaxation time relative to acetonitrile,
   [
   x_i = 	au_{L,i}^{-1}/	au_{L,ACN}^{-1},
   ]
   derived from independent solvent dielectric properties;

2. the experimental self-exchange rate after correction for solvent-dependent free-energy barrier variation, reported relative to acetonitrile,
   [
   y_i = k'_{ex,i}/k'_{ex,ACN}.
   ]

The barrier correction uses independently measured optical electron-transfer/barrier information. Therefore the remaining solvent dependence is a direct test of dynamical organization after an energetic baseline is removed.

The paper later uses the rate-vs-solvent-dynamics behavior to infer electronic matrix coupling. **Those inferred electronic coupling values are forbidden as predictors here.**

## Capital-Chi interpretation

The longitudinal solvent relaxation coordinate is treated as an independently measured environment/conglomeration dynamical feature. It is not mechanical scalar chi.

This test asks whether a dynamical environment variable explains kinetic variation remaining after an independent barrier correction.

## Frozen sample rule

Use every Table II solvent/couple pair for which both the relative inverse longitudinal relaxation value and the barrier-corrected relative self-exchange rate are explicitly reported.

Primary analysis is performed:
- separately for each redox couple with at least 4 complete solvent pairs;
- and as a pooled descriptive analysis with redox-couple identity retained as a grouping variable.

No couple or solvent is removed because it weakens the relationship.

Values shown in parentheses by the source for relaxation ratios are retained but flagged as source-qualified/non-Debye or approximate; a secondary sensitivity analysis may exclude those flagged values, but the primary table retains them.

## Frozen comparisons

For each eligible redox couple:

### Barrier-only null
After barrier correction and normalization to acetonitrile:
[
hat y_{barrier}=1.
]

### Dynamical architecture model
Fit in log space using leave-one-solvent-out cross-validation:
[
ln y = a+bln x.
]

Report:
- number of complete solvent conditions;
- Pearson correlation of (ln x,ln y);
- Spearman rank correlation;
- leave-one-out MSE of (ln y) for the barrier-only null;
- leave-one-out MSE of the dynamical model;
- (Delta MSE = MSE_{barrier-only}-MSE_{dynamics}).

Positive Delta MSE supports incremental kinetic information in solvent dynamics after barrier correction.

## Additional control

Because each redox couple has its own electronic coupling regime, no common slope is assumed. The pooled analysis is descriptive only unless a hierarchical model can be justified without target-driven tuning.

## Promotion limit

This is a historical reanalysis whose table values were visible before numerical calculation. It is therefore capped at **P1 empirical support** even if strongly positive.

A positive result supports the narrower statement:

> Independently characterized solvent dynamical organization can explain kinetic variation remaining after independent energetic-barrier correction in a matched reaction family.

It does not establish a scalar Capital-Chi coordinate or a generic cross-reaction rate law.
