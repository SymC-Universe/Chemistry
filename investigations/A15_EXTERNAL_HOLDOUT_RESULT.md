# A15 true external holdout result for the A9 BPAc+ conventional-solvent model

**Disposition:** STRONG EXTERNAL WITHIN-FAMILY VALIDATION OF A9

The original twelve A9 conventional-solvent rows were used once to fit the frozen models. Two additional conventional neat-solvent rows discovered later were held out completely from fitting and cross-validation.

## Frozen A9 model coefficients

Bulk-viscosity model:
[
ln	au_{rxn}=2.81474715+0.77629155lneta
]

Solvation-dynamics model:
[
ln	au_{rxn}=2.16237590+0.59923956ln	au_{solv}
]

## External holdout predictions

| Solvent | observed tau_rxn (ps) | viscosity prediction (ps) | solvation prediction (ps) | squared log error, viscosity | squared log error, solvation |
|---|---:|---:|---:|---:|---:|
| 1-pentanol | 183.0 | 44.2330 | 139.762 | 2.01644 | 0.07279 |
| 1-decanol | 486.0 | 107.3627 | 242.803 | 2.28009 | 0.48158 |

Aggregate:
- viscosity mean squared log error = **2.1482645**
- solvation mean squared log error = **0.2771870**
- Delta MSE(external) = **+1.8710780**

Mean absolute log error:
- viscosity = **1.465005**
- solvation = **0.481879**

## Target-uncertainty sensitivity

100,000 deterministic-seed draws were generated using the reported 10% target uncertainties while the A9 coefficients remained fixed.

Delta MSE(external) distribution:
- 2.5th percentile = **+1.565163**
- median = **+1.866115**
- 97.5th percentile = **+2.126286**
- fraction Delta MSE > 0 = **1.000000**

## Interpretation

The independently measured solvent-relaxation model retains a large predictive advantage on two solvent conditions that were not used in A9 fitting, leave-one-out validation, feature choice, or robustness analysis.

This materially strengthens A9 as **within-family empirical evidence** that environment-relaxation dynamics carry kinetic information not captured by bulk viscosity for BPAc+ in conventional neat solvents.

It remains within one reacting molecule/family and therefore does not by itself establish P2 cross-family Capital-Chi rate prediction.
