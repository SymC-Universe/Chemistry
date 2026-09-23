# Capital-Chi rate pilot amendment A15: true external holdout of the A9 solvent-dynamics model

**Date:** 2026-09-22
**Status:** FROZEN BEFORE HOLDOUT PREDICTION CALCULATION

## Purpose

A9 produced robust within-family P1 evidence that independently measured solvent relaxation predicts BPAc+ reaction time better than bulk viscosity across twelve conventional neat solvents.

The same source table contains two additional conventional neat-solvent conditions that were not included in the frozen A9 training/validation set:

| solvent | eta (cP) | tau_solv (ps) | tau_rxn (ps) |
|---|---:|---:|---:|
| 1-pentanol | 3.51 | 103 | 183 +/- 18.3 |
| 1-decanol | 11.0 | 259 | 486 +/- 48.6 |

These two rows are now reserved as a **true external holdout**.

## Frozen training set

Use exactly the original twelve A9 conventional-solvent rows and no others.

Fit once on all 12 A9 rows:

### M0 bulk model
[
ln	au_{rxn}=a_0+b_0lneta
]

### M1 environment model
[
ln	au_{rxn}=a_1+b_1ln	au_{solv}
]

No refitting is permitted after holdout outcomes are evaluated.

## Frozen holdout calculation

For each of the two external solvents:
1. generate M0 and M1 predictions from the 12-row fitted coefficients;
2. calculate signed log error
   [
   e=ln(	au_{pred}/	au_{obs});
   ]
3. calculate squared log error and absolute log error.

Aggregate across the two holdouts:
- mean squared log error;
- mean absolute log error.

Primary contrast:
[
Delta MSE_{external}=MSE_{viscosity}-MSE_{solvation}.
]

Positive values favor the environment-relaxation model.

## Uncertainty sensitivity

Using the reported 10% target uncertainties, propagate only target uncertainty with 100,000 deterministic-seed draws while holding the already-fitted A9 model coefficients fixed.

Report the fraction of draws with:
[
Delta MSE_{external}>0.
]

## Restrictions

- No A9 training row may be changed.
- The two holdouts may not be used to refit coefficients.
- No nonlinear floor, alcohol indicator, or additional feature may be added.
- This remains validation of the A9 within-family model, not a new reaction-family P2 result.
- The holdout values were discovered before this amendment, but no model coefficients, predictions, residuals, or comparison metrics were calculated before the amendment was frozen.
