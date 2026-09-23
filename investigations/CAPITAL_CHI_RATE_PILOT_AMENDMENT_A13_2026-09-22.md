# Capital-Chi rate pilot amendment A13: predictor-decoupling gate

**Date:** 2026-09-22
**Status:** EXPLORATORY POST-RESULT HYPOTHESIS, FROZEN BEFORE CALCULATION

## Motivation

Completed datasets show three distinct outcomes:

- A8: binary-mixture BPAc+ series, environment relaxation does not outperform viscosity.
- A9: diverse neat-solvent BPAc+ series, environment relaxation strongly outperforms viscosity.
- A11: protic-solvent proton-transfer series, environment relaxation strongly outperforms viscosity.
- A12: simple ground-state Markovian barrier crossing is already captured by bulk viscosity and does not require a richer environment coordinate.

This pattern suggests a prospective architecture gate:

> A richer environment-relaxation descriptor should not be expected to add kinetic information when it is nearly redundant with the bulk proxy. Its potential incremental value begins when microscopic/environmental dynamics decouple from bulk viscosity.

This hypothesis is explicitly generated after A8-A12 and is **not confirmatory evidence** from those datasets.

## Predictor-only decoupling metric

For any dataset with paired positive bulk viscosity eta and independent environment timescale tau_env, define:

1. log variables:
   [
   u_i=lneta_i,qquad v_i=ln	au_{env,i}.
   ]

2. Fit the predictor-only relation:
   [
   v=a+bu.
   ]

3. Define:
   [
   D_{env|bulk}=1-R^2(vsim u).
   ]

This metric uses no reaction-rate target.

Interpretation:
- D near 0: environment timescale is largely redundant with viscosity.
- larger D: environment dynamics contain structure not captured by viscosity.

Also record a scale-sensitive predictor-only leave-one-out RMSE:
[
E_{env|bulk}=mathrm{RMSE}_{LOO}(v-hat v(u)).
]

## Retrospective descriptive check

Compute D and E for A8, A9, and A11 only. Compare them descriptively with the already-frozen kinetic improvement:

[
Delta MSE_{kin}=MSE_{viscosity}-MSE_{environment}.
]

With only three datasets, no inferential correlation or threshold is claimed.

## Prospective rule for future datasets

For every future dataset:
1. compute predictor-only D and E **before** fitting reaction kinetics;
2. record whether the environment descriptor is redundant or decoupled;
3. then run the preregistered kinetic comparison;
4. do not adjust the decoupling metric based on the rate outcome.

No universal threshold is defined from A8-A11. A threshold, if ever used, must be fixed from a larger predictor-only corpus or external physical theory.
