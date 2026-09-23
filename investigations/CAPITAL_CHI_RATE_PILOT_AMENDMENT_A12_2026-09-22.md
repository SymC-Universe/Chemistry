# Capital-Chi rate pilot amendment A12: exploratory solvent-architecture decomposition

**Date:** 2026-09-22  
**Status:** POST-A11 EXPLORATORY; FROZEN BEFORE CALCULATION  
**Promotion:** hypothesis generation only; cannot upgrade A9/A10/A11 evidentiary level.

## Rationale

A11 showed a preregistered mixed result. For tS, adding rotational time to viscosity worsened held-out prediction. For ttD, neither viscosity nor rotational time alone performed well, while the predeclared joint viscosity + rotation model substantially improved held-out prediction.

The source itself discusses systematic solvent effects associated with polarity/dielectric response and molecular-size/shape differences. This exploratory step asks whether those independently tabulated solvent properties help explain the A11 heterogeneity.

## Frozen source features

From the same room-temperature source table:

- bulk viscosity: log(eta);
- measured solute rotational time: log(tau_R);
- static dielectric constant: log(epsilon);
- molar volume: log(V_m).

These quantities are source-tabulated and not derived from target tau_iso.

## Frozen models

Analyze tS and ttD separately.

- B0: intercept only
- B1: log(eta)
- B2: log(eta) + log(tau_R)
- P: log(eta) + log(tau_R) + log(epsilon)
- V: log(eta) + log(tau_R) + log(V_m)
- PV: log(eta) + log(tau_R) + log(epsilon) + log(V_m)

Use leave-one-solvent-out prediction over all complete rows for each model.

## Outputs

For each solute report:
- LOO MSE for every frozen model;
- Delta MSE relative to B1 and B2;
- coefficient signs only as exploratory diagnostics;
- condition number of each design matrix to flag unstable small-sample fits.

## Restrictions

- No additional solvent descriptor may be added after seeing A12 outcomes without a new amendment.
- No nonlinear or interaction terms.
- No solvent-class dummy variables.
- No row exclusion based on leverage or residual.
- The best A12 model is not a new Capital-Chi definition.
- A12 cannot be cited as confirmatory evidence; it can only nominate variables for a future independent preregistered dataset.
