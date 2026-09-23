# A14 prospective predictor-decoupling replication result

**Disposition:** KINETIC NEGATIVE; A13 decoupling-alone gate falsified as a sufficient predictor

The A14-P predictor-only checkpoint was committed before any reaction-time model was calculated:

- R2(log tau_solv ~ log eta) = 0.8541614
- D = 0.1458386
- predictor-only LOO RMSE = 0.6076846

The prospectively recorded expectation was modest: some incremental value from tau_solv was possible, but a null remained plausible.

## Condition-wise leave-one-out kinetic comparison

### Bulk viscosity
- Pearson r = 0.984912
- Spearman rho = 0.994030
- full-data slope = 1.03887
- LOO MSE = **0.0449042**
- LOO MAE(log) = **0.1669243**

### Independent solvation time
- Pearson r = 0.946160
- Spearman rho = 0.976190
- LOO MSE = **0.1888763**
- LOO MAE(log) = **0.3169327**

Primary contrast:
[
Delta MSE_{solv|visc}=0.0449042-0.1888763=-0.1439721
]

Bulk viscosity predicts held-out reaction time better.

## Leave-one-ionic-liquid-identity-out robustness

Three ionic liquids contribute temperature pairs; two identities are singletons. Entire identities were held out together.

- viscosity identity-holdout MSE = **0.0441117**
- solvation-time identity-holdout MSE = **0.1849930**
- Delta MSE = **-0.1408813**

The negative result therefore is not an artifact of placing two temperatures of the same liquid on opposite sides of the validation split.

## Interpretation

A13's predictor-decoupling metric is **not sufficient** to predict whether the richer environment timescale will improve kinetic prediction.

In this ionic-liquid regime, reaction dynamics show an apparent finite/intrinsic limit relative to the slowest solvation environments, while bulk viscosity remains an excellent empirical predictor over the frozen conditions.

No floor/saturation model is introduced post hoc. Such a model may be preregistered for a future mechanistic study, but cannot rescue A14.

The emerging rate-regime problem therefore requires at least one additional architectural question beyond bulk-vs-environment predictor redundancy, plausibly whether the reaction is in a solvent-controlled versus intrinsic/nonadiabatic saturation regime. That hypothesis is not tested by A14 itself.
