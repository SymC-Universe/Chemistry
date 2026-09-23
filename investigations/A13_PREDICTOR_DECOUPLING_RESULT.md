# A13 predictor-decoupling descriptive result

**Status:** EXPLORATORY POST-RESULT PATTERN ONLY

The metric was frozen in Amendment A13 after the A8-A12 kinetic results and therefore cannot retrospectively validate those results.

For each dataset:
[
D_{env|bulk}=1-R^2(ln	au_{env}simlneta)
]

and
[
E_{env|bulk}=mathrm{RMSE}_{LOO}(ln	au_{env}-widehat{ln	au_{env}}(lneta)).
]

| Dataset | n | R2(env~bulk) | D=1-R2 | predictor-only LOO RMSE E | already-frozen kinetic Delta MSE |
|---|---:|---:|---:|---:|---:|
| A8 BPAc+ binary mixture | 10 | 0.971627 | 0.028373 | 0.494490 | -0.231444 |
| A9 BPAc+ diverse neat solvents | 12 | 0.485076 | 0.514924 | 1.438836 | +0.376046 |
| A11 proton-transfer protic solvents | 5 | 0.506607 | 0.493393 | 1.873921 | +1.921782 |

## Descriptive interpretation

The only completed dataset in which the environment timescale is nearly redundant with bulk viscosity (A8) is also the dataset in which the environment descriptor fails to improve held-out kinetic prediction.

The two completed datasets with substantial predictor-only decoupling (A9 and A11) both show positive kinetic improvement from the independent environment timescale.

With only three datasets and a hypothesis generated after their outcomes, this is **not evidence for a threshold or law**. It motivates a prospective gate for future datasets:

1. quantify environment-vs-bulk predictor decoupling before examining the reaction-rate comparison;
2. retain that preregistered decoupling status;
3. then execute the frozen kinetic comparison;
4. test whether future datasets reproduce the pattern.

No threshold is estimated from these three cases.
