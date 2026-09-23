# Capital-Chi rate pilot amendment A8: DPB solvent-class dynamics test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE FULL-TEXT TABLE EXTRACTION

## Source

Dahl, Biswas, and Maroncelli, *The Photophysics and Dynamics of Diphenylbutadiene in Alkane and Perfluoroalkane Solvents*, J. Phys. Chem. B (2003).

The paper reports nonradiative/isomerization dynamics and independently measured rotational reorientation times across nonpolar solvent series, and discusses solvent-class dependence of microscopic friction.

## Frozen target

Use the source-reported nonradiative rate constant or isomerization rate for DPB, condition matched to the source solvent and temperature.

## Frozen predictors

Primary environment-dynamics predictor:
- independently measured DPB rotational reorientation time.

Control predictor:
- source solvent viscosity where exactly tabulated.

Predeclared architecture label:
- solvent class (alkane vs perfluoroalkane). This label may be used only in a separately reported interaction model because it is defined chemically before target inspection.

## Frozen models

M0: leave-one-condition-out intercept-only prediction of log rate.

M1: log rate ~ log bulk viscosity.

M2: log rate ~ log rotational reorientation time.

M3: log rate ~ log rotational reorientation time + solvent class + log rotational reorientation x solvent class.

M3 is allowed only if each solvent class contains enough exact conditions for leave-one-out fitting; otherwise it remains descriptive.

## Restrictions

- No friction scaling factors fitted to the target rates are used as predictors.
- No class-specific coefficient from the published Kramers fit is imported into the predictor.
- No literature alcohol points are merged into the primary test unless their measurement definitions and temperatures match the present dataset sufficiently for a declared secondary analysis.
- All exact tabulated conditions are retained.
- The target rate cannot be used to define microscopic friction.

## Primary question

Does independently measured microscopic rotational/environment coupling improve held-out prediction of isomerization kinetics beyond bulk viscosity, and does the predeclared solvent class reveal a stable architecture-dependent mapping?

## Promotion ceiling

P1 empirical within-system/solvent-class evidence only. No cross-reaction rate law.
