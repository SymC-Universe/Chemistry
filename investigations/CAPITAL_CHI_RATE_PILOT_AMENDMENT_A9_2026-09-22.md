# Capital-Chi rate pilot amendment A9: diverse neat-solvent electron-transfer test

**Date:** 2026-09-22  
**Status:** FROZEN AFTER SOURCE-TABLE DISCOVERY, BEFORE ASSOCIATION/PREDICTION CALCULATION

## Source system

BPAc+ intramolecular electron-transfer data summarized in Christopher A. Rumble's Penn State dissertation, Table 6.2, from the conventional-solvent measurements attributed there to Horng et al. (1999).

Primary set: the twelve conventional neat solvents listed before the 2018 binary-mixture series:
- acetonitrile
- acetone
- dimethylformamide
- dimethylsulfoxide
- methanol
- formamide
- N-methylformamide
- ethylene glycol
- ethanol
- 1-propanol
- N-methylpropionamide
- 1-butanol

## Research question

Across chemically diverse neat solvents, does independently characterized solvent relaxation predict the same reacting molecule's electron-transfer time better than bulk viscosity?

Unlike A8, this set is intentionally heterogeneous enough that viscosity and solvent relaxation need not be collinear.

## Frozen target

[
y=ln	au_{rxn}.
]

## Frozen predictors

### M0 bulk proxy
[
x_0=lneta.
]

### M1 Capital-Chi environment dynamics
[
x_1=ln	au_{solv}.
]

## Frozen analyses

For the twelve complete rows:
1. Pearson correlation with log reaction time;
2. Spearman correlation;
3. leave-one-solvent-out linear prediction in log space;
4. LOO MSE;
5. LOO mean absolute log error.

Primary contrast:
[
Delta MSE_{solv|visc}=MSE_{lneta}-MSE_{ln	au_{solv}}.
]

Positive values favor the independently measured solvent-relaxation descriptor.

## Frozen robustness check

Repeat the same comparison after excluding **acetonitrile only**, because the source literature identifies a fastest-solvent intrinsic reaction-time floor. Both results must be reported.

## Restrictions

- No protic/aprotic class indicator is added in the primary analysis.
- No nonlinear floor model is fitted in the primary analysis.
- No binary-mixture rows are pooled into this test.
- No outcome-weighted feature selection.
- P1 within-reaction-family evidence is the maximum promotion.
