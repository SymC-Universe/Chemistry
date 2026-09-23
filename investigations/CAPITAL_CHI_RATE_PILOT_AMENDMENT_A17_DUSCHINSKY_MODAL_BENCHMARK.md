# A17: Duschinsky modal-basis rate benchmark

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE LOCAL REPRODUCTION CALCULATION

## External source benchmark

Sando et al., *Large Electron Transfer Rate Effects from the Duschinsky Mixing of Vibrations*, J. Phys. Chem. A 2001, DOI 10.1021/JP004229C.

The cleanest modal contrast is the nontotally symmetric-mode example in Section III.C / Figure 10.

### Fixed scalar ingredients

- mixed-mode frequencies: 400 and 1800 cm^-1;
- displacement of both mixed modes: K = 0;
- therefore mixed-mode contribution to vibrational reorganization energy: 0;
- electronic coupling: H_ab = 250 cm^-1;
- solvent reorganization energy: lambda_s = 3000 cm^-1;
- total vibrational reorganization from the other displaced modes: 2209.7 cm^-1;
- corresponding total reorganization peak location remains fixed;
- same initial/final frequency spectrum.

### Varied object

Only the Duschinsky modal transformation changes:

[
Q' = J(\theta)Q+K
]

with

[
J(\theta)=
\begin{pmatrix}
\cos\theta & \sin\theta\\
-\sin\theta & \cos\theta
\end{pmatrix}
]

for source angles 0, 5, 10, 20, 30, 45, 60 degrees.

For the mixed nontotally symmetric modes K=0.

### Source result

The source reports large inverted-region rate enhancement with modal rotation while the reorganization-energy peak position remains fixed. Around E00 = 20000 cm^-1, Figure 10 shows an approximately four-order-of-magnitude change from the unmixed to strongly mixed case.

Exact plotted rates are not tabulated and are not treated as exact numerical observations in this project.

## Capital-Chi interpretation

For this controlled benchmark:

- scalar frequency set is unchanged;
- scalar displacement/reorganization contribution of the mixed modes is unchanged at zero;
- scalar solvent and electronic-coupling inputs are unchanged;
- Capital Chi changes because the **modal basis/correspondence matrix J changes**.

Thus this is a direct literature example of:

[
\text{same scalar inventory} + \text{different modal }\Chi
\rightarrow
\text{different kinetic response}.
]

## Local reproducible benchmark

Build a minimal two-mode harmonic model using:
- frequencies 400 and 1800 cm^-1;
- zero displacement;
- same frequencies in initial and final states;
- Duschinsky rotation J(theta);
- fixed solvent Gaussian broadening with lambda_s = 3000 cm^-1;
- initial vibrational ground state;
- fixed temperature declared prospectively;
- fixed energy gap chosen prospectively in the inverted region.

Compute multidimensional Franck-Condon overlaps numerically and evaluate a golden-rule rate proxy using the same modal basis at all angles.

### Purpose

The local benchmark is **not an exact reproduction** of Figure 10 because it omits the paper's additional unchanged displaced modes.

Its purpose is narrower:

> verify computationally that rotating the modal basis alone, with the scalar frequency/displacement inventory fixed, changes the kinetic Franck-Condon weighting.

## Frozen local settings

- frequency unit: 400 cm^-1;
- omega1 = 400 cm^-1;
- omega2 = 1800 cm^-1;
- K = (0,0);
- theta = {0,5,10,20,30,45,60} degrees;
- T = 78 K;
- lambda_s = 3000 cm^-1;
- E00 = 12000 cm^-1;
- final basis truncation: increase until summed Franck-Condon probability and rate ratio are numerically converged under a separately reported convergence audit;
- no parameter is tuned to reproduce the source figure.

## Promotion limit

A17 can establish a controlled modal mechanism and external-literature consistency.

It cannot by itself establish an empirical chemical rate predictor or cross-system Capital-Chi law.
