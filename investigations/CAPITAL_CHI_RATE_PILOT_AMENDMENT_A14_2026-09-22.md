# Capital-Chi rate pilot amendment A14: 50-solvent apolar-motor counter-test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE CALCULATION

## Source

Lubbe et al., *Solvent effects on the thermal isomerization of a rotary molecular motor*, PCCP 2016, DOI 10.1039/C6CP03571J.

The version-of-record repository PDF reports exact room-temperature ln(rate), ln(viscosity), molecular weight, and source-defined solvent group for 50 solvents/mixtures.

## Purpose

A14 is an independent empirical **counter-test** of relational environment modeling.

The molecular motor is deliberately apolar and changes little in polarization during thermal helix inversion. Therefore the dielectric/polar architecture nominated post hoc by A12 for ttD should not be assumed to help this system.

## Frozen target and predictors

Target:
- source Table-1 ln(k) at 20 C.

Primary control:
- source Table-1 ln(eta).

Additional independently tabulated structural/environment descriptor:
- ln(molecular weight).

Source-defined solvent group is retained only for diagnostics and group holdout, not as a fitted dummy variable in the primary model.

## Frozen models

- M0: intercept only
- M1: ln(k) ~ ln(eta)
- M2: ln(k) ~ ln(eta) + ln(MW)

Validation:
1. leave-one-solvent-out across all complete Table-1 rows;
2. leave-one-source-defined-solvent-group-out if group membership can be reconstructed unambiguously from the article.

Primary incremental statistic:
[
Delta MSE_{MW|eta}=MSE(M1)-MSE(M2).
]

## Interpretation

Positive Delta MSE means molecular-size/environment information adds to viscosity in this apolar motor.

Null/negative Delta MSE is an important counterexample showing that adding more environmental architecture is not automatically beneficial.

## Restrictions

- No solvent polarity/dielectric predictor is added unless exact values are independently extracted and preregistered before calculation.
- No group-specific intercepts or slopes.
- No row exclusions.
- Source-derived activation parameters are not predictors because many are calculated from the same kinetics.
- A14 remains P1 cross-source evidence, not P2 Capital-Chi validation.
