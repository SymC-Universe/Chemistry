# Capital-Chi rate pilot amendment A9: modern simultaneous rotation/isomerization test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE ROTATIONAL-TIME TABLE EXTRACTION

## Source

*Photoisomerization Paths of alpha,omega-Diphenylpolyenes: Reaction Rate Dependence on Temperature, Excitation Wavelength, and Deuteration*, J. Am. Chem. Soc. (2024), DOI 10.1021/jacs.4c09134.

The source reports photoisomerization time and rotational time measured simultaneously in the same pump-probe experiment across multiple solvents and temperatures.

## Why this is unusually strong for the pilot

- target kinetic observable and environment-coupling observable are measured in the same experimental run;
- rotational time is not reconstructed from the isomerization time;
- multiple solvents and temperatures provide repeated perturbations;
- the design supports within-solvent and cross-solvent tests;
- no historical OCR alignment is required because the article exposes numeric tables.

## Frozen target

Primary target:
[
y = ln k_{iso} = -ln 	au_{iso}
]
up to an additive constant.

Use the source photoisomerization time (	au_{iso}) exactly as tabulated.

## Frozen Capital-Chi environment feature

Primary predictor:
[
x_R = ln 	au_R
]
using the independently measured rotational time from the same experimental condition.

Rotational time is treated as a measured solute-environment dynamical-coupling descriptor, not as mechanical scalar chi.

## Frozen controls

If exact source viscosity is available condition-matched:
- control predictor (x_eta = ln eta).

Temperature is treated as a declared covariate, not hidden inside Capital Chi.

## Frozen analyses

### A9.1 pooled matched-condition test
For all conditions with exact paired (	au_{iso}) and (	au_R):
- Pearson and Spearman association;
- leave-one-condition-out log-linear prediction;
- compare against intercept-only;
- compare against viscosity-only if exact viscosity is available.

### A9.2 within-solvent temperature trajectories
For every solvent with at least four paired temperatures:
- regress (ln 	au_{iso}) against (ln 	au_R);
- report slope, correlation, and leave-one-temperature-out error.

### A9.3 leave-one-solvent-out generalization
Only if at least four solvent identities have sufficiently complete paired data:
- fit a pooled model on all but one solvent;
- predict the held-out solvent;
- compare rotational-dynamics model against temperature-only and, if available, viscosity-only controls.

## Restrictions

- No fit parameter from the source's own isomerization/rotation model is used as a predictor.
- No solvent is omitted because it weakens the relation.
- Deuterated and structurally distinct solutes are not pooled with the primary solute unless separately declared as secondary perturbation tests.
- Excitation-wavelength variants are not pooled unless they correspond to the same mechanistic branch and are separately labeled.
- No nonlinear model is introduced after seeing the primary log-linear result without a dated amendment.

## Promotion ceiling

A positive result may support P1/P1+ empirical evidence that a directly measured environment-coupling timescale tracks and predicts kinetic changes under matched perturbations.

It still does not establish:
- a scalar Capital-Chi rate coordinate;
- absolute cross-reaction rate prediction;
- P2 cross-family validation.
