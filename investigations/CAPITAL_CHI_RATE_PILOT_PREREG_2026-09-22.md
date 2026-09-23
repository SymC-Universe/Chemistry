# Capital Chi as a kinetic predictor: prospective pilot preregistration

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE CAPITAL-CHI FEATURE/OUTCOME COLLISION  
**Branch:** `agent/capital-chi-rate-pilot-20260922`

## 1. Research question

The pilot asks whether the broader stability architecture, denoted capital Chi (Χ), contains kinetic information that is not captured by an independently specified native barrier/rate model.

The primary claim under test is **incremental**, not standalone:

[
\text{Does } Χ \text{ reduce out-of-sample kinetic error after native barrier physics is supplied independently?}
]

The pilot does **not** assume that Χ alone determines an absolute reaction rate.

## 2. Capital-Chi object under test

For this pilot, Χ is not compressed to one scalar. It is a structured relationship among three separately evidenced layers:

1. **Scalar/local layer**: licensed local dynamical coordinates and invariants, including mechanical \(\chi\) only when the scalar second-order reduction is independently licensed.
2. **Carrier/modal layer**: eigenmodes/eigenspaces, participation weights, reactive/nonreactive mode assignments, coupling geometry, conditioning, and mode identity where available.
3. **Conglomeration/system layer**: memory kernels/timescales, well-versus-barrier dissipation structure, cross-mode coupling, metastable-state organization, transfer-operator/slow-mode structure, path multiplicity, and other whole-system organization supported by the native model.

Capital Χ is the **relationship among these layers**, not an average of them.

## 3. Target-leakage firewall

The following are forbidden as Capital-Chi predictors for a target reaction/condition:

- the observed target rate;
- a barrier or activation energy reconstructed from the observed target rate;
- a friction or transmission parameter fitted to reproduce the observed target rate;
- a committor, latent coordinate, or model selected using the held-out target rate;
- a feature chosen or discarded because of its correlation with the target residual after inspection;
- a replicate from the held-out source/family used to tune a feature definition;
- any post-hoc replacement of the preregistered native baseline after residual inspection.

Committor or transfer-operator information is admissible only when obtained independently from trajectory/dynamical data without fitting to the held-out target rate.

## 4. Native baseline and outcomes

For every admitted empirical coordinate, the native baseline must be fixed before Capital-Chi comparison.

Primary continuous outcome:

[
r_i = \ln\left(\frac{k_{\mathrm{obs},i}}{k_{\mathrm{native},i}}\right).
]

Primary comparison quantity:

[
\Delta E = E(M_0)-E(M_2),
]

where lower held-out error is better.

A secondary outcome is **rate-controlling regime classification**, where the source independently supports labels such as well-limited, barrier-limited, memory-limited, recrossing-dominated, multichannel, or unresolved/refused.

## 5. Frozen model ladder

- **M0 native:** preregistered native barrier/rate model only.
- **M1 native + local scalar:** M0 plus licensed local scalar features such as \(\chi\).
- **M2 native + Capital Chi:** M0 plus the frozen Χ architecture feature set.
- **M3 interactions:** M2 plus preregistered interactions between native barrier variables and Χ features.

No model may be promoted merely for in-sample fit.

## 6. Stage order

### Stage 0: controlled mechanistic sanity test
Use published/native rate theories or reproducible dynamical model systems in which barrier, friction, coupling, and memory can be varied independently. Purpose: test whether the proposed Χ representation distinguishes kinetic regimes and residual structure. This stage is **not empirical validation**.

### Stage 1: empirical pilot
Select a small set of real chemical systems before calculating any Capital-Chi/rate association. Selection is based only on availability of independently sourced:
- barrier/native prediction;
- observed rate;
- at least one nontrivial modal/carrier or conglomeration feature;
- condition matching sufficient to assign those features to the same physical system.

### Stage 2: prospective expansion
Only after the feature contract is frozen and Stage 1 is evaluated may additional systems be added. Expansion cannot redefine Χ in response to Stage 1 outcomes.

## 7. Candidate feature contract

A feature is admitted only if it has a declared physical meaning, source, units/convention where applicable, condition, and independence status.

Candidate families are frozen as:

### Scalar/local
- licensed local \(\chi\);
- local frequency and damping components kept separately;
- local pole class;
- local spectral gap/relaxation timescale when independently defined.

### Carrier/modal
- number of dynamically relevant modes/subspaces;
- reactive-mode participation;
- nonreactive-mode participation/coupling;
- off-diagonal coupling magnitude or normalized coupling ratio;
- eigenvector/subspace change under perturbation;
- conditioning/non-normality diagnostic when relevant.

### Conglomeration/system
- well/barrier friction contrast;
- well memory ratio;
- barrier memory ratio;
- slow global relaxation/eigenmode timescale;
- metastable-state/path multiplicity;
- independently defined committor/reaction-coordinate quality;
- spatial heterogeneity of dissipation;
- channel/network topology when the source identifies multiple pathways.

Missing features remain missing. They are not imputed from the target rate.

## 8. Pilot selection rule

The empirical pilot will prioritize systems that span distinct kinetic architectures rather than systems with favorable residuals. Candidate selection is based on evidence availability before Capital-Chi/outcome analysis.

At least one negative/null-control architecture should be retained if available.

Repeated temperatures within one family are not independent family-level validation. They may be used for within-family trajectory tests but must be clustered by source/family in inference.

## 9. Holdout and validation

If the empirical sample is large enough:
- hold out entire reaction families;
- hold out entire primary-source lineages where possible;
- report source/family-clustered performance;
- do not allow temperatures/replicates from the same family to appear on both sides of a family holdout.

If the sample is too small for defensible predictive validation, the result remains a case-series/eligibility result and is **not promoted as a predictive model**.

## 10. Falsification / stop conditions

The rate-prediction hypothesis is disfavored if any of the following persist under eligible held-out comparisons:

1. M2 does not improve held-out error relative to M0 beyond sampling uncertainty.
2. Apparent improvement disappears under source/family holdout.
3. Improvement depends on target-derived or post-hoc features.
4. Χ features merely duplicate variables already contained in the native rate formula without adding independent information.
5. The needed architecture cannot be measured or reconstructed independently at matched conditions.
6. Different systems require incompatible Χ definitions with no stable feature contract.

A failure of numeric rate prediction does not automatically invalidate Χ as a descriptive or rate-regime classifier.

## 11. Promotion ladder

- **P0-D:** feature definitions and sources documented.
- **P0-Q:** quantitative extraction verified and condition-matched.
- **P1:** within-system or controlled-model regime discrimination.
- **P2:** independent family/source holdout shows incremental predictive information beyond native baseline.

No P2 claim is allowed from Stage 0 synthetic/model data alone.

## 12. First decision target

The first question is deliberately weaker than an absolute-rate law:

> **Can the Capital-Chi architecture identify which dynamical structure controls the rate, and does that architecture explain native-model residuals without using the observed rate in its construction?**

Only if this succeeds will a low-dimensional or scalarized Capital-Chi rate coordinate be investigated.
