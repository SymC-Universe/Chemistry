# Capital-Chi rate pilot amendment A8: binary-mixture solvent-relaxation test

**Date:** 2026-09-22  
**Status:** FROZEN AFTER SOURCE-TABLE DISCOVERY, BEFORE ANY ASSOCIATION/PREDICTION CALCULATION

## Source system

Christopher A. Rumble, PhD dissertation (Penn State, 2017), Table 6.2, underlying the later publication:

Rumble & Maroncelli, *Solvent controlled intramolecular electron transfer in mixtures of 1-butyl-3-methylimidizolium tetrafluoroborate and acetonitrile*, J. Chem. Phys. 148, 193801 (2018), DOI 10.1063/1.5000727.

The primary test uses only the binary [Im41][BF4]/acetonitrile composition series measured in the same work at approximately 20 C, including the pure-ACN and pure-ionic-liquid endpoints where the table identifies them as "This Work".

## Why this is a strong Capital-Chi test

The binary mixture was selected to vary solvent dynamics strongly while maintaining nearly constant polarity and close-to-ideal mixing.

For the same reacting solute (BPAc+), the source reports:
- bulk viscosity eta;
- independently characterized mean solvation time <tau_solv>;
- independently measured electron-transfer reaction time <tau_rxn>.

The solvation time is an environment-relaxation/conglomeration descriptor and is not reconstructed from the target reaction time.

## Frozen target

Primary target:
[
y = ln 	au_{rxn}.
]

Equivalent rate interpretation is (k_{rxn}=1/	au_{rxn}); model ranking is unchanged by sign reversal in log space.

## Frozen predictors

### M0 bulk proxy
[
x_0 = ln eta.
]

### M1 Capital-Chi environment dynamics
[
x_1 = ln 	au_{solv}.
]

No target-derived friction, fitted transmission coefficient, or reaction-time-derived solvent descriptor is allowed.

## Frozen analyses

For the same complete set of binary-mixture conditions:

1. Pearson correlation with (ln	au_{rxn});
2. Spearman rank correlation;
3. leave-one-composition-out linear prediction:
   [
   ln 	au_{rxn}=a+bln x
   ]
   fit only on the remaining conditions;
4. LOO MSE;
5. LOO mean absolute log error.

Primary contrast:
[
Delta MSE_{solv|visc}=MSE_{lneta}-MSE_{ln	au_{solv}}.
]

Positive values mean the independently measured environment-relaxation descriptor predicts held-out reaction dynamics better than bulk viscosity.

## Sensitivity analysis frozen in advance

Because the fastest-solvent endpoint may approach an intrinsic reaction-time floor noted by the source, repeat the same comparison after excluding **only the pure-ACN endpoint**. This is a preregistered physical sensitivity check, not an outcome-selected exclusion.

Both full-series and endpoint-excluded results must be reported.

## Restrictions

- Do not add mixture composition itself as a predictor after inspecting outcomes.
- Do not fit a nonlinear plateau/floor model in the primary analysis.
- Do not combine neat-solvent literature rows with the primary binary-mixture test.
- Do not use uncertainty weights in the primary comparison; uncertainties are reported descriptively.
- This test can support P1 within-family empirical architecture evidence only.
