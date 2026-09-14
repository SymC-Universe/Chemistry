# Adversarial manuscript reframe changeset — 14 September 2026

**Status:** ACTIVE review changeset against the frozen Release-38 Main and Supplementary sources  
**Governing title:** **Stability Architecture for Chemical Systems: A Diagnostic and Predictive Engine with an Expandable Stability Atlas**

This changeset is reader-facing only. It changes no frozen numerical value, Atlas coordinate, evidence grade, physical threshold, method, test result, or provenance record.

## Main manuscript changes

### Title

Replace the former classifier/linewidth title with:

**Stability Architecture for Chemical Systems: A Diagnostic and Predictive Engine with an Expandable Stability Atlas**

### Abstract contract

The revised abstract must state all of the following without first-person language:

1. a chemical stability description is incomplete when a scalar damping coordinate, modal spectrum, or kinetic rate is interpreted in isolation;
2. the Stability Architecture contains two separately governed components, the Engine and the Stability Atlas;
3. the Engine resolves admitted generator/operator structure, stability, temporal form, modal/subspace structure, multiplicity, provenance, licensed scalar coordinates, and channel-dependent response;
4. mechanical chi is reported only where a second-order or decoupled modal representation is licensed;
5. structural predictions are conditional on the declared model/provenance domain;
6. linewidth is not automatically mechanical damping and must pass lifetime/dephasing/orientational qualification;
7. frozen Barrier-Height/Rate Atlas v0.9 contains 61 physical coordinates across 26 reaction families and preserves predictions, observations, residuals, evidence grades, provenance, HOLDs, and refusals;
8. Atlas kinetic predictions arise from mechanism-appropriate kinetic models, not local chi;
9. the approximately 148-fold constructive counterexample remains the executable firewall against local-architecture-to-rate inference;
10. conglomeration is non-voting integration that preserves individual physical meaning and failure states;
11. the framework is diagnostic, conditionally predictive, and refusal-capable rather than a universal scalar commitment theory.

### New Introduction subsection

Insert **Architecture, Engine, Atlas, and conglomeration** immediately after the machinery subsection.

Required definitions:

- **Stability Architecture:** the scientific representation obtained when qualified local system analysis and independently typed comparative evidence are considered together.
- **Engine:** the computational/analytical machinery for generator or quadratic-pencil structure, modal/subspace content, stability and temporal class, multiplicity, licensed scalar coordinates, coupling/parentage, provenance, and channel response.
- **Stability Atlas:** separately governed evidence structure preserving qualified records, kinetic predictions/observations, uncertainty, grades, HOLDs, refusals, and source relations.
- **Conglomeration:** non-voting integration. Within a system, scalar information where licensed, modal/subspace structure, coupling, response geometry, physical role, and provenance remain distinct but jointly interpreted. Across systems, those qualified architectures are read with typed barrier/rate evidence and conditions. Contradictions and failures remain visible.

### Prediction classes

The manuscript must distinguish:

- **structural prediction:** prospective pole motion, perturbation sensitivity, trace-constrained redistribution, and channel-specific response from a declared generator/operator;
- **kinetic prediction:** rate or transport prediction from a mechanism-appropriate kinetic model with typed barrier, prefactor/transmission treatment, and state conditions;
- **comparative prediction:** a prediction generated without using the target observation, then compared against an independent matched observation;
- **refusal:** no prediction when a required coordinate, projection, mechanism, state match, model domain, or independence condition is absent.

### Scope paragraph

Replace any wording that could imply that the framework has no predictive capability with the narrower and correct statement:

> Local stability architecture supplies no universal reaction-rate, yield, commitment-probability, or selectivity estimator. The Engine contains no rate estimator derived from local chi or local mode class. Structural response predictions remain available from declared generators, while kinetic predictions in the Stability Atlas arise from separately qualified mechanism-appropriate barrier/rate models and are tested against independent observations where available.

### Reader-facing naming

Replace reader-facing `ChemSA` with **the Engine** or **Stability Architecture for Chemical Systems** according to meaning.

Retain `ChemSA` only where required to identify historical implementation artifacts such as `run_all_chemsa.py`, frozen archive names, manifests, or hashes. Include one explicit note that the historical development identifier is retained for reproducibility and is not the reader-facing framework name.

## Supplementary changes

### Title

Use the same locked reader-facing title.

### New epistemic-lineage section

Insert a dedicated section before the reproduction section mapping the predecessor rejection to the present architecture. The detailed source-of-record table is:

`manuscript/EPISTEMIC_PREDECESSOR_REJECTION_RESPONSE_TABLE_2026-09-14.md`

The manuscript-level table must cover at minimum:

- unsupported commitment-efficiency law;
- stable-well versus barrier-crossing conflation;
- estimator non-equivalence;
- linewidth decomposition;
- Newns-Anderson hybridization versus projected nuclear friction;
- model-sensitive solvent route;
- local-timescale Markov criterion;
- incomplete imported provenance;
- rate-derived circular evidence;
- failed universal chi-to-commitment interpretation.

The table must state that the rejected commitment law was withdrawn rather than rescued.

### Claim-status table

Expand the claim-status table to include distinct rows for:

- previously established scalar boundary;
- Engine contribution;
- predictive scope;
- Atlas contribution;
- conglomerated architecture;
- real-source demonstrations;
- model-class benchmark;
- illustrative quantities;
- explicit non-claims.

The non-claim row must exclude any universal reaction-rate, yield, commitment-probability, or selectivity law from local architecture; any universal chemical boundary; any unsupported real chemical exceptional point; and any automatic equivalence among linewidth, solvent-relaxation, electronic-hybridization, and nuclear-friction estimators.

## Mechanical validation already completed on the review candidate

- zero first-person narrative pronouns found in Main;
- zero first-person narrative pronouns found in Supplementary;
- reader-facing `ChemSA` survives only in explicit historical implementation notes and code filenames;
- Main LaTeX compiles successfully when the existing `linewidth_hierarchy.png` release asset is present;
- Supplementary LaTeX compiles successfully;
- brace-balance check passes for both sources;
- no scientific value or frozen Atlas record was changed by the reframing pass.

### Known non-scientific layout item

The Main build retains a large-float warning around the existing representative Barrier-Height/Rate Atlas table. This is a mechanical layout issue for publication formatting, not a scientific-review blocker. It must be repaired before final submission without changing table content.

## Adversarial-review status

The scientific manuscript is sufficiently integrated to enter adversarial review. Remaining changes should now be driven by identified blocking defects, reproducibility defects, or clearly justified reader-facing corrections rather than another open-ended rewrite cycle.
