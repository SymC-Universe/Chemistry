# Capital-Chi rate pilot amendment A11: room-temperature cross-solvent panel

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE TABLE-1 NUMERIC EXTRACTION

## Source

Dobryakov et al., JACS 2024, DOI 10.1021/jacs.4c09134.

## Motivation

A9/A10 vary temperature and solvent. Table 1 provides a broad room-temperature solvent panel, allowing a test in which temperature is effectively fixed and solvent/environment organization is the dominant perturbation.

## Frozen primary solutes

Analyze tS and ttD separately. Do not pool them.

## Frozen target and predictors

Target:
[
y=-ln	au_{iso}.
]

Primary Capital-Chi environment feature:
[
x_R=ln	au_R.
]

Control:
[
x_eta=lneta
]
using the source room-temperature viscosity.

## Frozen analyses

For each solute independently, using every Table-1 solvent with complete exact (	au_R), (	au_{iso}), and viscosity:

- Pearson and Spearman association;
- leave-one-solvent-out linear prediction for:
  - intercept only;
  - viscosity only;
  - rotational time only;
  - viscosity + rotational time.

Primary incremental quantities:
[
Delta MSE_{R|eta}=MSE(eta)-MSE(eta+	au_R)
]
and
[
MSE(eta)-MSE(	au_R).
]

## Predeclared subgroup diagnostics

Report errors by the source's own solvent classes without using them to exclude rows:
- n-alkanes;
- iso/cyclic/perfluoro class;
- polar solvents.

No class-specific fit coefficients are introduced in the primary model.

## Restrictions

- No row is omitted because it is an outlier.
- Temperature differences of 20 C for tS versus 21 C for ttD are intrinsic to the source and solutes are analyzed separately.
- No nonlinear terms or solvent-specific intercepts are added after inspection.
- This test is cross-solvent P1 evidence only.
