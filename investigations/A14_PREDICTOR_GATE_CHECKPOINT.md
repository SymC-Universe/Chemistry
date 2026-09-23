# A14-P predictor-only checkpoint

**Status:** COMPLETED BEFORE KINETIC CALCULATION

Frozen eight-condition neat-ionic-liquid predictor set:

[
R^2(ln	au_{solv}simlneta)=0.8541614
]

[
D_{env|bulk}=1-R^2=0.1458386
]

Predictor-only leave-one-condition-out RMSE:

[
E_{env|bulk}=0.6076846
]

Pearson correlation between log viscosity and log solvation time:

[
r=0.9242085
]

## Prospective A13 expectation recorded before tau_rxn modeling

The environment timescale is **not nearly redundant** with viscosity to the degree observed in A8 (D=0.028), but it is substantially less decoupled than the prior A9/A11 positive examples (D about 0.5).

Therefore the preregistered qualitative expectation is:

- some incremental kinetic value from tau_solv is physically possible;
- any improvement is expected to be smaller/less decisive than A9 or A11;
- a null result remains plausible because predictor redundancy is still substantial.

No reaction-time model has been calculated at this checkpoint.
