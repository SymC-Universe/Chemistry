# Capital-Chi rate pilot amendment A9A: temperature-confounding control

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE A9 NUMERIC CALCULATION

## Rationale

The matched 2024 tS dataset varies solvent temperature from 283-323 K. Both rotational time and isomerization time are temperature dependent. Therefore a raw pooled association between tau_R and tau_iso cannot by itself establish incremental environment-dynamics information.

## Added decisive models

Use all exact paired tS conditions for the undeuterated solute only.

Target:
[
y=-ln 	au_{iso}.
]

Predictors:
- (z = 1/T) as the temperature-only control;
- (x = ln 	au_R) as the measured environment-coupling descriptor.

For leave-one-condition-out and leave-one-solvent-out validation compare:

- **T0:** intercept only;
- **T1:** (y=a+b/T);
- **X1:** (y=a+cln	au_R);
- **TX:** (y=a+b/T+cln	au_R).

Primary incremental test:
[
Delta MSE_{X|T}=MSE(T1)-MSE(TX).
]

Positive values mean rotational/environment dynamics adds predictive information beyond temperature.

Secondary comparison:
[
MSE(T1)-MSE(X1)
]
tests whether the measured dynamical descriptor alone is more useful than temperature alone.

## Cross-solvent gate

The strongest A9 result is leave-one-solvent-out. Entire solvent identities must be held out so that temperature trajectories from a held-out solvent do not leak into training.

## Restrictions

- D2-ac is excluded from the primary set because it is a deuterated solute.
- No solvent-specific intercepts are used in leave-one-solvent-out prediction.
- No nonlinear terms are added after outcome inspection.
- No fit parameters from the source authors' kinetic model enter these predictors.
