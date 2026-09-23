# Capital-Chi rate pilot amendment A15: motor-specific diffusion reproduction benchmark

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE CALCULATION  
**Epistemic status:** source-result reproduction, not blinded confirmation.

## Source

Lubbe et al., PCCP 2016, DOI 10.1039/C6CP03571J.

The source reports that the diffusion coefficient of motor 1, measured by DOSY-NMR in selected solvents, correlates more strongly with the thermal helix-inversion rate than viscosity on the same restricted dataset.

## Purpose

Reproduce that statement using predictive rather than correlation-only scoring.

This tests a bounded Capital-Chi idea:

> a solute-specific environment-coupling observable can carry kinetic information beyond a bulk solvent property.

## Frozen matched subset

Use every Table-2 solvent for which an exact motor-1 diffusion coefficient D is unambiguously printed and for which Table 1 supplies exact ln(k) and ln(eta).

No row is added by digitizing Fig. 2g.

## Frozen models

Target:
- Table-1 ln(k).

Predictors:
- M0: intercept only
- M1: Table-1 ln(eta)
- M2: ln(D), using source DOSY-NMR motor diffusion
- M3: ln(eta) + ln(D)

Validation:
- leave-one-solvent-out across the exact matched subset.

Report:
- LOO MSE;
- Pearson/Spearman associations;
- design conditioning.

## Restrictions

- Because the source already reports the qualitative ranking, A15 cannot be counted as new confirmatory evidence.
- D is not converted to a fitted reactive friction.
- No missing D values are estimated.
- No solvent is excluded based on residual.
