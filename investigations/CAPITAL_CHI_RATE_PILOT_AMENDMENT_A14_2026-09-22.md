# Capital-Chi rate pilot amendment A14: prospective A13 gate replication in neat ionic liquids

**Date:** 2026-09-22
**Status:** FROZEN BEFORE PREDICTOR-DECOUPLING CALCULATION AND BEFORE KINETIC COMPARISON

## Source system

BPAc+ intramolecular electron transfer in neat ionic liquids from Li et al. 2011, tabulated with viscosity, independent solvation time, and reaction time in Christopher A. Rumble's 2017 Penn State dissertation, Table 6.2.

The eight frozen conditions are:

| condition | T C | eta (mPa s) | tau_solv (ps) | tau_rxn (ps) |
|---|---:|---:|---:|---:|
| [Im21][Tf2N] | 25 | 35 | 140 | 320 +/- 70 |
| [Im41][PF6] | 25 | 196 | 1000 | 1600 +/- 400 |
| [Im41][PF6] | 70 | 29 | 140 | 240 +/- 70 |
| [N3111][Tf2N] | 25 | 82 | 370 | 1000 +/- 200 |
| [N3111][Tf2N] | 65 | 20 | 70 | 200 +/- 70 |
| [Nip311][Tf2N] | 25 | 113 | 510 | 1100 +/- 200 |
| [Nip311][Tf2N] | 65 | 23 | 90 | 220 +/- 50 |
| [P14666][Tf2N] | 45 | 125 | 2500 | 1600 +/- 200 |

The solvation times and BPAc+ reaction times are distinct measured observables reported by the source lineage. No target-rate-derived environment feature is introduced.

## Stage A14-P: predictor-only gate

Before using tau_rxn:

1. compute
   [
   D_{env|bulk}=1-R^2(ln	au_{solv}simlneta)
   ]
2. compute predictor-only leave-one-condition-out RMSE
   [
   E_{env|bulk}.
   ]
3. checkpoint both values in GitHub.
4. record the qualitative A13 prospective expectation:
   - near-redundant predictor geometry: little/no incremental kinetic gain expected;
   - materially decoupled predictor geometry: environment relaxation has room to add kinetic information.

No numeric threshold is imposed.

## Stage A14-K: kinetic test, permitted only after A14-P is checkpointed

Frozen target:
[
y=ln	au_{rxn}.
]

M0:
[
ln	au_{rxn}=a+blneta.
]

M1:
[
ln	au_{rxn}=a+bln	au_{solv}.
]

Use leave-one-condition-out linear prediction and report:
- Pearson;
- Spearman;
- LOO MSE;
- LOO mean absolute log error;
- Delta MSE = MSE(viscosity) - MSE(solvation).

## Source-structure robustness

Because three ionic-liquid identities contribute paired temperatures, report a secondary **leave-one-liquid-identity-out** prediction comparison if mathematically estimable. [P14666][Tf2N] and [Im21][Tf2N] are singleton identities; each is held out as one condition when its identity is omitted.

The identity-holdout result is required to distinguish temperature interpolation from solvent-identity transfer.

## Restrictions

- No rate calculation before A14-P checkpoint.
- No composition/class features added after outcome inspection.
- No nonlinear model added in primary analysis.
- Same BPAc+ molecule means this is a prospective A13 gate replication, not an independent reaction-family P2 test.
