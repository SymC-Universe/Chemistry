# Capital-Chi A6 disposition: Angulo et al. no-fit ET architecture

**Date:** 2026-09-22  
**Parent:** Amendment A6  
**Disposition:** **P0-Q POSITIVE ARCHITECTURE DEMONSTRATION; P1 QUANTITATIVE PROMOTION BLOCKED BY SOURCE FORMAT**

## What is established

The source independently determines the two principal ingredients of the reacting-system dynamics:

1. the PeDMA free-energy surface from stationary spectroscopy;
2. the solvent-specific non-Markovian friction/memory from time-resolved measurements on nonreacting Coumarin 153.

The resulting GLE simulations contain no fitted parameters from the PeDMA target dynamics. The source compares the full GLE with the simpler GSE and reports that the GSE characteristic times deviate more strongly from experiment, with the difference increasing as the relaxation becomes slower. The source also reports that a memoryless overdamped Smoluchowski calculation fails to reproduce the observations in the tested fast/slow solvent pair.

The Supplement independently tabulates:
- C153 multiexponential solvent-relaxation parameters (Table S2);
- the derived time-dependent friction parameters used in the GLE (Table S3).

## Why this is not promoted to the preregistered P1 metric

The exact PeDMA observed, GLE-predicted, and GSE-predicted characteristic times (	au_{1/e}) are shown in Supplementary Figure S7 but are not tabulated numerically.

Amendment A6 explicitly prohibited treating graphically estimated values as exact when reproducible numeric recovery is unavailable.

Therefore:
- the qualitative architecture comparison is retained;
- no mean/median absolute log-error calculation is claimed;
- no plot-by-eye digitization is used to manufacture a quantitative positive result.

## Scientific interpretation

This source supports the **architecture/model-selection interpretation** of Capital Chi:

> independently measured free-energy geometry plus independently measured environmental memory/friction can predict reacting-system dynamics without fitting the target dynamics, and retaining richer dynamical architecture can outperform a compressed reduction.

It does **not** establish:
- a scalar Capital-Chi rate coordinate;
- a cross-family rate predictor;
- a new rate law.

A P1 quantitative reanalysis remains possible only if exact Figure S7 source data or a reproducible calibrated numerical extraction becomes available.
