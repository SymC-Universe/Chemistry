# A8 binary-mixture solvent-relaxation test result

**Disposition:** P1 NEGATIVE under the frozen predictive comparison.

The same BPAc+ reacting system was evaluated across ten [Im41][BF4]/ACN composition conditions using independently tabulated bulk viscosity, mean solvation time, and reaction time.

### Full series
- viscosity LOO MSE: 0.0210514
- solvation-time LOO MSE: 0.2524951
- Delta MSE(solv|visc): -0.2314437

### Preregistered sensitivity excluding pure ACN
- viscosity LOO MSE: 0.0198193
- solvation-time LOO MSE: 0.1425294
- Delta MSE(solv|visc): -0.1227101

Both predictors are strongly monotonic with reaction time, but the independently measured environment-relaxation time does not improve held-out log-linear prediction relative to bulk viscosity in this binary-mixture series.

This does not dispute solvent dynamical control. It means this frozen Capital-Chi-style predictor does not add predictive information over viscosity under the preregistered model.

No feature or functional form was changed after seeing the result.
