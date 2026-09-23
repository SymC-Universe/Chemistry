# Capital-Chi rate pilot amendment A6: no-fit non-Markovian electron-transfer architecture test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE SUPPLEMENTARY TARGET/PREDICTION TABLE EXTRACTION

## Source system

Angulo et al., *How good is the generalized Langevin equation to describe the dynamics of photo-induced electron transfer in fluid solution?* J. Chem. Phys. (2017), DOI 10.1063/1.4990044.

The reacting system is PeDMA photo-induced intramolecular electron transfer across a solvent series. The paper determines the free-energy surface from stationary spectroscopy and independently calibrates solvent non-Markovian friction using the dynamics of nonreacting Coumarin 153. The authors state that no fitting parameters enter the GLE simulations of the reacting system.

## Capital-Chi interpretation

This test does **not** scalarize capital Chi.

For this system, the relevant Capital-Chi architecture is the independently established relationship among:

1. the reacting-system free-energy surface from stationary spectroscopy;
2. solvent-specific non-Markovian friction/memory measured with an external probe;
3. inertial/dynamical propagation through that environment;
4. the resulting reacting-system relaxation/electron-transfer dynamics.

The target reacting-system time trace or characteristic reaction time is not used to define these inputs.

## Frozen primary comparison

Where exact supplementary numerical data permit, compare the source's two no-fit dynamical predictions against the measured characteristic reaction time (	au_{1/e}):

- **Full architecture:** generalized Langevin equation (GLE), retaining inertial and non-Markovian memory structure.
- **Compressed comparator:** generalized Smoluchowski equation (GSE), the paper's simpler overdamped/harmonic reduction.

The primary error metric is absolute log error:

[
e_i = left|lnleft(rac{	au_{pred,i}}{	au_{obs,i}}ight)ight|.
]

Across all conditions with exact independently tabulated target and model values, report:
- mean absolute log error;
- median absolute log error;
- paired per-condition error difference (e_{GSE}-e_{GLE});
- number of conditions favoring GLE, favoring GSE, or tied within reported precision.

Primary question:

[
	ext{Does retaining the independently measured non-Markovian/inertial architecture improve no-fit prediction relative to the compressed comparator?}
]

## Frozen secondary comparisons

If the supplement supplies complete groups, report the same error metrics separately for the source-defined solvent groups without redefining groups after seeing outcomes:
- pure aprotic solvents;
- DMSO/benzyl-acetate mixtures;
- DMSO/glycerol isodielectric mixtures.

No threshold based on observed prediction error may be used to create a favorable subset.

## Restrictions

- No model parameter may be refit to the PeDMA target dynamics.
- No digitized value will be treated as exact if a tabulated source value exists or can be retrieved.
- If exact model predictions are available only graphically and cannot be recovered reproducibly, the comparison remains qualitative/P0-Q and is not promoted.
- The GSE is not described as "no Capital Chi"; it is a deliberately compressed dynamical architecture. The test asks whether the **richer independently measured architecture** adds predictive value.
- A positive result is at most **P1 empirical architecture evidence within this reaction system**, not a general Capital-Chi rate law.
- A null/negative result is retained without changing the Capital-Chi definition.

## Promotion target

A successful result would support:

> Independently measured whole-system dynamical architecture can improve no-fit prediction of reacting-system kinetics relative to a compressed dynamical reduction.

It would **not** establish:
- a scalar Capital-Chi rate coordinate;
- cross-family rate prediction;
- a replacement for native reaction-rate theory.
