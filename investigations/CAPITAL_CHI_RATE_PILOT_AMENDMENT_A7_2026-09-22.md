# Capital-Chi rate pilot amendment A7: metallocene solvent-relaxation test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE FULL TABLE EXTRACTION / MODEL CALCULATION

## Source

McManis, Nielson, Gochev, and Weaver, *Solvent Dynamical Effects in Electron Transfer: Evaluation of Electronic Matrix Coupling Elements for Metallocene Self-Exchange Reactions*, J. Am. Chem. Soc. 1989, 111, 5533-5541. DOI: 10.1021/ja00197a004.

Journal identity is independently verified. A freely accessible published copy exposes the numerical tables.

## Why this dataset is eligible

The source reports:
- self-exchange rate constants for six metallocene redox couples in up to 15 solvents;
- solvent longitudinal relaxation times / inverse relaxation frequencies;
- independently determined barrier corrections from optical electron-transfer measurements;
- barrier-corrected rate constants across solvents.

The solvent-relaxation descriptor is not reconstructed from the target self-exchange rate.

## Capital-Chi interpretation

The candidate Capital-Chi environment feature is **solvent longitudinal dynamical relaxation**, represented by (	au_L^{-1}) or its source-normalized equivalent.

This is a system/environment dynamical descriptor. It is not mechanical scalar chi.

## Frozen primary test

Use the source's **barrier-corrected self-exchange rate** (k'_{ex}) where available, because this removes solvent-dependent barrier-height variation using an independent optical measurement.

For each redox couple with at least five complete Debye-solvent pairs:

1. regress (ln k'_{ex}) against (ln 	au_L^{-1});
2. report Pearson and Spearman associations;
3. perform leave-one-solvent-out linear prediction;
4. compare against an intercept-only leave-one-out model.

Primary incremental quantity:

[
Delta MSE = MSE_{intercept} - MSE_{	au_L}.
]

Positive Delta MSE supports within-couple incremental kinetic information from solvent dynamical organization after barrier correction.

## Secondary test

Use the source's uncorrected (k_{ex}) and compare whether the barrier-corrected relation to solvent dynamics is cleaner than the uncorrected relation. This tests the architecture concept that energetic/path and dynamical-environment information should be separated rather than collapsed.

## Strict exclusions

- Electronic coupling (H_{12}) values inferred by fitting the (k'_{ex}-	au_L^{-1}) dependence are excluded as predictors.
- Effective solvent relaxation times inferred from target kinetics in non-Debye solvents are excluded from the primary test.
- Primary analysis is restricted to source-identified Debye solvents with independently characterized solvent relaxation.
- No solvent or redox couple may be dropped based on whether it improves the result.
- No global cross-couple model is promoted from these data unless separately preregistered.

## Promotion ceiling

A positive result is P1 within-family/cross-solvent evidence that independently measured environmental dynamics carries kinetic information after independent barrier correction. It does not establish a cross-reaction Capital-Chi rate law or a scalarized Capital Chi.
