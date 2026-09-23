# Amendment A16: Modal reset of Capital Chi

**Date:** 2026-09-22  
**Status:** FROZEN CONCEPTUAL CORRECTION BEFORE ANY MODAL-RATE CALCULATION  
**Branch:** `agent/capital-chi-rate-pilot-20260922`

## 1. Correction

The investigation drifted from the SymC definition of capital Chi.

Scalar chi already serves the local scalar role:

[
\chi_i = \text{licensed scalar stability coordinate for mode } i
]

when the native model permits such a reduction.

Capital Chi is **not** a larger scalar and is **not** a bag of environmental variables. Capital Chi is the modal/vector stability architecture carried by the native generator.

The corrected hierarchy is:

[
\text{native generator}
\rightarrow
\text{modal/carrier structure}
\rightarrow
\chi_i \text{ where licensed}
\rightarrow
\text{modal coupling/organization}
\rightarrow
\Chi
\rightarrow
\text{realized response}.
]

## 2. Modal Capital-Chi object under test

For chemistry, capital Chi is provisionally represented as a structured modal object:

[
\Chi_{modal}
=
\{
V_R, V_L, \Lambda,
P,
C_{modal},
\kappa,
G_{transient},
\mathcal S,
\Delta\mathcal M,
\chi_i
\}
]

only where each term is licensed by the native model.

Candidate components:

- right eigenvectors / mode vectors;
- left eigenvectors where non-normal or biorthogonal structure matters;
- modal eigenvalues/poles;
- mode-resolved scalar chi_i where licensed;
- participation factors / projections of the reaction coordinate onto modes;
- off-diagonal modal coupling;
- mode mixing / subspace rotation under perturbation;
- spectral gaps and slow-mode separation;
- conditioning / non-normality diagnostics;
- transient amplification where relevant;
- stable/unstable subspace geometry;
- redistribution of damping/decay among modes;
- persistence or loss of mode identity;
- pathway-relevant collective modes and their couplings.

No requirement is imposed that these collapse to one number.

## 3. Rate question after correction

The corrected question is **not**:

> Do environmental variables grouped under Capital Chi predict rate?

It is:

> Does independently reconstructed modal architecture carry kinetic information beyond barrier energetics and local scalar chi_i?

Primary hierarchy:

- **M0:** native barrier / native rate baseline;
- **M1:** M0 + local scalar chi_i, where licensed;
- **M2:** M0 + modal Capital-Chi architecture;
- **M3:** M0 + local chi_i + modal Capital-Chi architecture.

Primary outcome remains held-out rate error or native-model residual, but the predictor must now be modal.

## 4. Required modal contrasts

The investigation must seek systems enabling at least one of:

1. **same/similar local chi, different modal Chi**
   - tests what modal organization adds beyond the scalar coordinate;

2. **same/similar barrier, different modal Chi**
   - tests whether mode structure alters kinetics at fixed energetic barrier;

3. **perturbation trajectory**
   - track how modal vectors/subspaces and chi_i reorganize while rate changes;

4. **mode-removal or coupling intervention**
   - alter one mode/coupling in a native model and test whether the kinetic outcome changes;

5. **reactive-mode participation**
   - test whether projection/participation of the reactive coordinate onto the coupled modal basis predicts transmission, recrossing, or rate residual.

## 5. Leakage firewall

Forbidden modal predictors:

- normal modes fitted or selected because they correlate with the target rate;
- a reaction coordinate optimized using the held-out target rate;
- transmission coefficients inferred from the target rate and then reused as predictors;
- modal weights chosen post hoc from target residuals;
- rate-derived effective frequencies or damping values;
- any scalar compression created after inspecting which modal combination predicts best.

## 6. Disposition of A9-A15

A9-A15 are preserved in GitHub as **environment-dynamics precursor evidence**, not as direct Capital-Chi validation.

They may support the general premise that embedded dynamics matter, but they do not satisfy the corrected modal definition unless a source independently provides the required modal/carrier structure.

No prior numeric result is deleted.

## 7. Immediate research target

Find chemical reaction datasets or native dynamical models containing, independently of the target rate:

- Hessian/normal-mode structure at reactant and transition regions;
- reaction-coordinate participation in coupled modes;
- Duschinsky/mode-mixing information;
- multidimensional coupling matrices;
- unstable-mode coupling / Grote-Hynes or Pollak-style mode structure;
- explicit system-bath normal modes;
- normal-mode-resolved friction or memory;
- mode-specific damping or lifetimes;
- enough kinetic data for independent comparison.

Priority is **modal structure first, rate second**.

## 8. Promotion rule

Capital Chi receives a kinetic role only if modal architecture adds predictive or mechanistic information beyond:

- the barrier/native rate baseline, and
- scalar chi_i where available.

If only environmental bulk variables are available, the result is not promoted as Capital Chi.
