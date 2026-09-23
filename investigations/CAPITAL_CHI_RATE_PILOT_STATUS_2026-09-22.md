# Capital-Chi rate pilot: execution status

**Date:** 2026-09-22
**Branch:** `agent/capital-chi-rate-pilot-20260922`

## Frozen controls

The investigation is governed by the preregistration plus Amendments A1-A5. No positive feature is allowed to be selected after target inspection.

## Results to date

### Stage 0 controlled non-Markovian benchmark

With barrier shape, beta U0, inertial time and ordinary friction scale fixed, changing the memory time in the Brünig-Netz-Kappler homogeneous-memory model changes the reciprocal MFPT rate proxy by roughly a factor of 65 across the frozen scan. This supports the mechanistic premise that memory/system organization can alter barrier-crossing kinetics even when a local Markovian descriptor is unchanged.

This is a controlled-model sanity check only and is not empirical validation of Capital Chi.

### Empirical P1 test 1: beta-cyclodextrin

Three preregistered independent environment-reorganization features were tested against q4MD-CD association-rate residuals:

- number of waters released on binding;
- water entropy contribution;
- host entropy contribution.

All three improved over the raw uncalibrated native prediction because the family contains a systematic offset. After Amendment A3 added the necessary leave-one-out intercept-only family calibration, all three features worsened held-out error:

- water release: Delta MSE(Chi|cal) = -0.13016;
- water entropy: -0.08589;
- host entropy: -0.12014.

Disposition: **P1 negative for the three frozen features.**

### Empirical P1 test 2: S-DPB matched n-alkane solvent series

The frozen test compared bulk viscosity with independently measured S-DPB rotational reorientation time as a microscopic environment-coupling descriptor. Target is the source isomerization/nonradiative rate calculated from fluorescence lifetime using the source fixed radiative rate.

Both predictors are strongly monotonic with rate, but the microscopic descriptor did not improve leave-one-solvent-out prediction:

- viscosity LOO MSE = 0.00300564;
- rotational-reorientation LOO MSE = 0.00421440;
- Delta MSE(micro|bulk) = -0.00120876.

Disposition: **P1 negative under the preregistered non-leaky log-linear comparison.**

The published nonlinear Kramers-Hubbard fit is not counted as a Capital-Chi win because it optimizes dynamical parameters against the rate data, which the pilot firewall excludes from the primary predictive test.

## Atlas eligibility audit

All 26 Barrier-Height/Rate Atlas families have been triaged.

Current counts:
- 9 regime-only because the relevant architecture is already embedded in the native rate;
- 3 blocked by native-baseline identifiability/model spread;
- 1 completed P1 negative family;
- 1 P0-D partial lead;
- remaining families ineligible under current evidence/source/proxy rules or have no need for residual correction.

The Atlas therefore cannot by itself support a P2 Capital-Chi rate-prediction claim without a new matched dataset designed for this question.

## Current interpretation

Two statements are supported at different levels:

1. **Mechanistic support:** whole-system memory/coupling architecture can matter strongly for rates. Established non-Markovian rate theory and the frozen Stage-0 benchmark support this.
2. **Predictive support for Capital Chi:** not established. The two clean empirical incremental tests executed so far are null/negative.

The investigation remains open for an independently matched dataset in which dynamical architecture is measured separately from both the native barrier model and target rate.
