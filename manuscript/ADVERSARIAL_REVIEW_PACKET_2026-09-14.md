# Adversarial review packet — Stability Architecture for Chemical Systems

**Status:** READY FOR ADVERSARIAL REVIEW STAGING  
**Date:** 14 September 2026  
**Governing baseline:** SymC General Operations Manual v0.8.0  
**Source-of-record branch:** `agent/na-cu001-integration`

## Reader-facing title

**Stability Architecture for Chemical Systems: A Diagnostic and Predictive Engine with an Expandable Stability Atlas**

## Review basis

The current scientific manuscript basis is the frozen Release-38 Main and Supplementary source, with a reader-facing reframing pass that changes no frozen numerical result, threshold, model setting, Atlas coordinate, evidence grade, test result, or provenance record.

The reframing is governed by:

1. `manuscript/STABILITY_ARCHITECTURE_TERMINOLOGY_AND_CLAIM_CONTRACT_2026-09-14.md`
2. `manuscript/EPISTEMIC_PREDECESSOR_REJECTION_RESPONSE_TABLE_2026-09-14.md`

The historical implementation label `ChemSA` is not the reader-facing framework name. It remains only where required by frozen filenames, code entry points, archive names, manifests, or hashes.

## What changed for adversarial review

The front matter and claim architecture are being revised to reflect the scientific object already present in the source:

- the framework is **Stability Architecture for Chemical Systems**;
- the **Engine** is a diagnostic and conditionally predictive computational/analytical component;
- the **Stability Atlas** is a separately governed, expandable evidence structure;
- scalar chi is a conditional compressed coordinate rather than the framework itself;
- modal/subspace structure remains explicit;
- conglomeration is non-voting integration that preserves contradictions, uncertainty, HOLDs, refusals, and physical identity;
- structural prediction and kinetic prediction are separate classes with different physical inputs;
- local stability architecture does not imply reaction rate, yield, commitment probability, or selectivity;
- Barrier-Height/Rate Atlas v0.9 remains frozen and immutable;
- the rejected predecessor's universal commitment interpretation remains withdrawn.

## Mandatory adversarial attacks

The review should attempt to falsify or expose overreach in the following areas.

### 1. Architecture / Engine / Atlas separation

Determine whether any sentence silently collapses the Engine, the Atlas, or the full Stability Architecture into one object. Flag any passage implying that the Atlas is generated solely from scalar chi or that the Engine itself is the Atlas.

### 2. Predictive capability

Test every use of `predict`, `prediction`, `predictive`, or equivalent language. Each prediction must be identifiable as structural, kinetic, or comparative and must state or inherit the physical model that licenses it. Flag any claim that local chi or local mode class alone predicts a reaction rate.

### 3. Scalar / modal / conglomerated completeness

Test whether the manuscript preserves the three complementary representation levels:

- scalar coordinate where mathematically and physically licensed;
- modal/subspace structure;
- conglomerated system-level organization.

Flag any sentence that promotes one level into a universal replacement for the others.

### 4. Conglomeration semantics

Conglomeration is non-voting. A contradiction, HOLD, refusal, weak evidence grade, or failed comparator cannot disappear through averaging or aggregate success. Flag any aggregate statement that exceeds the individual evidence carried into it.

### 5. Predecessor-regression test

Use the Chemical Physics rejection as an explicit attack surface. Any reappearance of the following substitutions is a blocking defect:

- critical damping -> commitment optimum;
- stable-well relaxation -> barrier-crossing probability;
- local stability class -> reaction rate;
- total linewidth -> mechanical damping;
- electronic hybridization -> projected nuclear friction without projection;
- solvent relaxation -> scalar reaction-coordinate friction without a licensed reduction;
- rate-derived input -> independent validation of the same rate;
- favorable residual -> retrospective model selection.

### 6. Linewidth / lifetime / dephasing audit

Verify the dimensional and physical meaning of every linewidth conversion. Population relaxation, pure dephasing, orientational relaxation, inhomogeneous broadening, and other broadening channels must not be silently identified with one another. The lifetime-derived Rh(CO)2acac chi values remain illustrative pending calibrated digitization; the source-anchored endpoint width growth is the quantitative result.

### 7. Markov / memory audit

Where a Markovian or scalar damping reduction is invoked, verify that the relevant separation is against the local coordinate timescale rather than the overall reaction waiting time. Any application lacking the required time-scale evidence should be downgraded, held, or explicitly bounded.

### 8. Barrier/rate independence and circularity

Verify that predicted rates, barriers, prefactors, transmission factors, and observed comparators have the declared independence. Rate-derived barriers may not independently validate the same rate. Post-comparison model shopping is prohibited.

### 9. Atlas evidence grades and retained failures

Check that Grade A/B/C language matches the actual source chain. Large residuals, condition mismatches, proxies, network ambiguity, and incomplete primary-source inspection must remain visible. Coverage counts cannot be used as evidence quality.

### 10. Numerical exceptional-point claims

Confirm that finite-precision defectivity language remains tolerance-qualified. Higher-order exceptional-point evidence must remain candidate-level unless independently certified by stronger structural evidence. Crowded unresolved spectra must remain unresolved.

### 11. Novelty / nearest-prior-art collision

Identify the closest existing methods for generator analysis, quadratic eigenvalue classification, non-Hermitian/EP analysis, linewidth decomposition, reaction-rate prediction, and evidence-atlas construction. Separate established ingredients from the residual contribution made by their audited integration and refusal logic.

### 12. Reproducibility

Attempt clean-room reconstruction from the declared package, code, inputs, manifest, validators, and frozen Atlas. Historical implementation filenames must remain reproducible even where reader-facing terminology has changed.

## Zero-first-person rule

Reader-facing manuscript prose must contain no first-person language. Draft review candidates have been screened for first-person pronouns; any reintroduced first-person prose is a mechanical defect to be corrected before release.

## Current known limitations that must not be hidden

- no universal chemical commitment law is established;
- no universal chemical boundary is claimed;
- no demonstrated real chemical exceptional point is claimed unless a specific entry independently satisfies that burden;
- local stable-well architecture does not supply a reaction rate;
- lifetime-derived numerical chi in the Rh(CO)2acac figure remains illustrative until calibrated digitization;
- Markovian reduction requires application-specific time-scale justification;
- System 2 CO/Cu(111) remains a numerical HOLD under the frozen convergence rule;
- System 3 H/Ru(0001) remains a numerical HOLD under the frozen clean-surface rule;
- Barrier-Height/Rate Atlas v0.9 remains frozen and is not rewritten to improve agreement.

## Review decision rule

A review comment should be classified as one of:

- **BLOCKING SCIENTIFIC:** changes claim validity, physical interpretation, evidence independence, or mathematical correctness;
- **BLOCKING REPRODUCIBILITY:** prevents independent reconstruction or hides provenance;
- **MECHANICAL:** wording, cross-reference, formatting, naming, or code/package defect that does not alter frozen science;
- **SCOPE / FUTURE:** valuable extension not required for the claims actually made;
- **NO CHANGE:** criticism already addressed by an explicit boundary and supported by the record.

Mechanical defects may be corrected directly. Blocking scientific changes require explicit adjudication before the manuscript is promoted beyond adversarial review.
