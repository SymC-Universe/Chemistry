# Stability Architecture for Chemical Systems — terminology and claim contract

**Status:** ACTIVE manuscript-facing contract for adversarial-review staging  
**Date:** 14 September 2026  
**Governing baseline:** SymC General Operations Manual v0.8.0  
**Source-of-record branch:** `agent/na-cu001-integration`

## 1. Locked reader-facing title

**Stability Architecture for Chemical Systems: A Diagnostic and Predictive Engine with an Expandable Stability Atlas**

The historical name `ChemSA` is retired as the reader-facing scientific identity. Historical filenames, code entry points, manifests, hashes, archive names, and provenance records retain their original identifiers wherever renaming would damage reproducibility.

## 2. The four objects must remain separate

### Stability Architecture

The **Stability Architecture for Chemical Systems** is the scientific representation obtained by combining qualified local system analysis with qualified comparative evidence. It is not a software package, not a scalar chi catalogue, and not the Atlas alone.

### Engine

The **Engine** is the computational and analytical machinery that accepts an admitted chemical representation and resolves what that representation can support. Depending on the supplied model and provenance, its functions include:

- generator or quadratic-pencil reduction;
- modal and subspace structure;
- stability and temporal classification;
- algebraic-versus-geometric multiplicity discrimination;
- exceptional-point candidate/refusal logic;
- licensed scalar coordinates where a valid reduction exists;
- coupling and parentage information;
- biorthogonal residues, sensitivities, and response geometry;
- source and representation provenance gating;
- linewidth/lifetime/dephasing qualification;
- declared HOLD or refusal when required information is absent or physically incompatible.

The Engine is **diagnostic** because it determines the qualified stability structure of the supplied system. It is **predictive** only where the governing model licenses a prospective calculation. Examples include pole motion, structured-perturbation sensitivity, channel-specific response, and other model-derived observables with declared assumptions.

The Engine does **not** infer a universal chemical reaction rate, yield, commitment probability, or selectivity from local stability architecture or from chi.

### Stability Atlas

The **Stability Atlas** is a separately governed evidence structure populated by qualified system records. It preserves inputs, outputs, prediction-versus-observation comparisons, uncertainty, provenance, grades, HOLDs, refusals, and representation limits without allowing one evidentiary axis to repair another.

Barrier-Height/Rate Atlas v0.9 remains an immutable frozen release. The word **expandable** means that new qualified systems or evidence may enter a new additive release or separately versioned extension. It does not mean that v0.9 records may be silently altered, regraded, or retuned.

Kinetic predictions in the Barrier-Height/Rate Atlas arise only from mechanism-appropriate kinetic models and independently qualified barrier/prefactor/transmission inputs. They are not predictions made from local chi or local mode architecture alone.

### Conglomerated architecture

**Conglomeration** is the non-voting integration of qualified stability information into a higher-order representation while preserving the identity, provenance, uncertainty, and failure state of every contributing component.

Conglomeration is **not** averaging, majority voting, score pooling, or forcing heterogeneous observables into one scalar.

Two levels are distinguished:

1. **Within-system conglomeration:** modal/subspace structure + any licensed scalar coordinate + coupling/parentage + response information + physical-role information -> the qualified system-level stability architecture.
2. **Across-system conglomeration:** qualified system architectures + independently typed kinetic/barrier evidence + provenance + conditions + HOLDs/refusals -> the Atlas-level architecture.

A contradiction, HOLD, refusal, or failed comparator remains visible after conglomeration and cannot be averaged away by stronger results elsewhere.

## 3. Predictive capability contract

The word **predictive** is permitted only with an explicit prediction class.

### PRED-STRUCTURAL

Prospective predictions derived from a declared generator/operator and perturbation, including pole motion, response sensitivity, trace-constrained redistribution, channel-specific residues, or related observables. These predictions are conditional on the supplied representation and its validity domain.

### PRED-KINETIC

Prospective rate or transport predictions derived from a mechanism-appropriate kinetic model with explicitly typed barrier, prefactor/transmission treatment, state conditions, and provenance. These predictions do not originate from chi alone.

### PRED-COMPARATIVE

A prediction generated without using the target observation, followed by comparison with an independent observation under matched conditions. The Atlas records the residual even when agreement is poor.

### REFUSE

No prediction is reported when the required coordinate, projection, mechanism, state match, model domain, or source independence is absent. A refusal is a scientific result, not a missing software feature.

## 4. Chi contract

Scalar chi is a compressed coordinate only where the relevant second-order or decoupled modal reduction is separately established. It is not the definition of the Stability Architecture.

For general first-order generators, pole geometry and modal/subspace structure remain primary. A pole-angle index is not relabelled as a mechanical damping ratio merely because both are dimensionless.

The fullest supported representation remains:

**scalar where licensed + modal/subspace structure + conglomerated system organization**.

No manuscript wording may imply that these are interchangeable or that the scalar replaces the other two levels.

## 5. Stable-well versus barrier-kinetic firewall

Local stable-well architecture and barrier-crossing kinetics are related only when a separately justified physical bridge has been established for the same coordinate and compatible conditions.

The constructive 148-fold counterexample remains a scope fence: identical local well architecture can coexist with different activated rates when the global barrier differs. It therefore blocks any direct inference from local stability class to reaction rate.

The Barrier-Height/Rate Atlas supplies barrier/rate evidence through an independent route rather than repairing that limitation by assumption.

## 6. Reader-facing naming rule

Reader-facing prose uses:

- **Stability Architecture for Chemical Systems** for the full scientific framework;
- **the Engine** for the diagnostic/predictive computational machinery;
- **the Stability Atlas** or the specific versioned Atlas name for the evidence structure;
- **conglomerated architecture** only with the non-voting definition above.

`ChemSA` may remain only where historical implementation identity is necessary for reproducibility, such as `run_all_chemsa.py`, archive names, frozen manifests, hashes, or an explicit development-lineage note.

## 7. Non-overclaim rule

The new title does not revive the rejected predecessor claim. In particular, the manuscript must not state or imply that:

- chi = 1 maximizes chemical commitment;
- local critical damping maximizes barrier crossing;
- spectral linewidth, solvent relaxation, and electronic hybridization are interchangeable friction estimators;
- a linewidth is mechanical damping before lifetime/dephasing/orientational contributions are resolved;
- a rate-derived barrier independently validates that same rate;
- an Atlas residual may be used retrospectively to choose the model that produced the prediction;
- a numerical HOLD is a mechanical failure requiring a rerun.

The architecture is stronger because these substitutions are refused, not because the predecessor's universal commitment law was rescued.
