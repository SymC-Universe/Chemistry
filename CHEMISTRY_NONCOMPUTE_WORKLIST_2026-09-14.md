# Chemistry non-compute worklist

**Status:** active  
**Date:** 14 September 2026  
**Governing baseline:** SymC General Operations Manual v0.8.0  
**Purpose:** keep Chemistry advancing while long numerical work is running, waiting, held, or being adjudicated, without changing frozen scientific settings.

This list intentionally separates work that can proceed from work that requires a new scientific freeze or user decision.

## Priority A — can proceed now without waiting for current computations

### A1. Manuscript and reproducibility reconciliation

Reconcile the Chemistry manuscript, supplement, reproducibility guide, repository descriptions, and current system notes so they state the evidence actually earned.

Required checks:

- CO/Cu(111) and H/Ru(0001) numerical HOLDs are reported as negative/limit evidence where relevant, not hidden as missing data and not rewritten as mechanical failures;
- stable-well damping architecture remains separate from barrier crossing;
- barrier height, rate, transmission, friction, damping morphology, and exceptional-point classification are not collapsed into one coordinate;
- every real-system chi statement names its dynamical license, carrier, and Gamma/Omega convention;
- any older prose that implies a universal chi = 1 optimum, barrier-top critical point, or linewidth-equals-damping shortcut is removed or explicitly scoped.

This can be completed before new numerical results arrive. Result-dependent tables or sentences can retain clearly marked placeholders.

### A2. GOM terminology and governance synchronization

Update active Chemistry documentation to treat **SymC General Operations Manual (GOM) v0.8.0** as the current program baseline. Older GP references remain historical aliases rather than active governance pointers.

Do not mass-rewrite frozen historical artifacts merely for terminology. Update current pointers, reader-facing documentation, and new work only unless a stale reference could materially mislead execution.

### A3. Chi provenance and convention audit

Perform a source-to-claim audit of every promoted or manuscript-facing Chemistry chi quantity:

- exact/derived, operational estimator, proxy, or empirical coordinate;
- physical carrier or quotient;
- Gamma definition;
- Omega definition;
- angular/ordinary-frequency convention;
- amplitude/energy-decay convention;
- full-width/half-width convention where applicable;
- source provenance;
- uncertainty/conditioning;
- refusal condition.

This is documentary/mathematical auditing and does not require new DFT computation.

### A4. Width/dephasing/lifetime audit

Audit every use of a spectral width or lifetime that could be read as a damping coefficient. Confirm whether the source/model separates or bounds lifetime, pure-dephasing, inhomogeneous, orientational, instrumental, or other broadening contributions.

Any unsupported identification should be downgraded to the source-supported quantity rather than repaired by algebra.

### A5. Open-channel, HOLD, and dead-end ledger consolidation

Create one reader-facing index of material unresolved items, numerical HOLDs, refused reductions, stale/superseded recovery routes, and closed mechanical failures.

Each item should identify:

- source record;
- current disposition;
- what would legitimately reopen it;
- downstream objects materially dependent on it;
- whether any active computation is expected to resolve it.

Do not delete historical failures merely because a later route superseded them.

### A6. Source-of-record project-state index

Maintain one current project-state record that distinguishes:

- active branch and commit;
- active or waiting computation;
- completed/frozen evidence products;
- current scientific HOLDs;
- current mechanical/infrastructure HOLDs;
- superseded runs;
- next decision after each active dependency resolves.

This prevents new chats or collaborators from inheriting stale workflow identity.

### A7. Reproducibility-package readiness audit

Without rerunning expensive science, audit whether the current package contains the files needed to regenerate every already-closed result:

- source data or declared external dependency;
- code and environment/dependency record;
- configuration/freeze identity;
- output artifact;
- hashes;
- semantic validators;
- negative/mutation tests where material;
- exact regeneration instructions.

Do not regenerate result artifacts merely to change wording. If an artifact must change, preserve the old identity and record the new version.

### A8. Nearest-prior-art and native-comparator audit

For each current narrow Chemistry claim that may eventually be promoted, perform a good-faith literature audit of the strongest native methods addressing the **same scientific question**.

Output:

- frozen question candidate;
- nearest methods;
- what each actually answers;
- whether a fair comparator appears to exist;
- what residual scientific contribution remains after prior art.

This audit may narrow or sharpen a future claim. It must **not** freeze the final comparator or confirmatory claim without user review.

### A9. Attribution and novelty ledger

Separate:

- established before this work;
- inherited method/known truth;
- known-truth calibration;
- closest prior art;
- residual unanswered question;
- candidate new contribution;
- not claimed as new.

This can be done before computation completes and will reduce later manuscript churn. Publication-level novelty is not certified merely by creating the ledger.

### A10. Function Map / Limit Map balance audit

Audit whether manuscript and figure emphasis represents both:

- ordinary functioning/interior behavior; and
- limits, refusals, numerical HOLDs, exceptional cases, or failure boundaries.

Rare or dramatic failures should not dominate primary figures solely because they are visually striking. Conversely, negative/limit evidence should not disappear because it is inconvenient.

### A11. Experimental-opportunity and literature-collision pass

For Chemistry questions that admit meaningful direct physical testing, independently sketch the best feasible experiment **before** searching for prior experiments that answer it.

Then perform the targeted literature collision and classify the residual question. The possible outcome may be that the experiment should not be built because the literature already answers the question.

This is planning and literature work only. No physical experiment is authorized by this item.

### A12. Monitor-coverage and recovery audit

For every material active or externally waiting dependency, verify:

- what is actually running or waiting;
- where its liveness/progress evidence comes from;
- what checkpoint/restart path exists;
- what failure classes may auto-recover mechanically;
- what numerical/scientific states must stop rather than retry;
- whether a stale or superseded run could still consume resources.

Monitoring is not scientific computation and must not be described as such.

### A13. Workflow and branch hygiene plan

Inventory stale, duplicated, superseded, nested, and historical workflow files, including nested `.github/workflows/.github/workflows` material.

Classify each as:

- active execution path;
- active recovery path;
- historical provenance required;
- superseded but retained;
- safe candidate for archival relocation;
- unresolved.

Do **not** delete a workflow or historical artifact until provenance and restart dependencies are checked. The first pass is inventory only.

### A14. Future scalar-to-carrier reporting adapter specification

Design the additive output contract that will persist the mass-normalized mechanical modal vector/subspace together with any future promoted real-system `MechanicalModeRecord` or equivalent scalar record.

This closes the reporting gap already identified in `systems/CHEMISTRY_STABILITY_ARC_INHERITANCE_v0.1.json` without changing the frozen core ChemSA engine.

The adapter can be specified and tested on known/synthetic objects before any new real-system mechanical chi becomes eligible.

### A15. Manuscript-release closure checklist

Build a release checklist independent of unresolved System 2/System 3 compute so the paper does not idle unnecessarily.

At minimum track:

- claims reconciled to evidence;
- figures regenerated from current source data where required;
- citations/source lines verified;
- Atlas v0.9 identity preserved;
- system HOLDs represented correctly;
- code/package hashes current;
- semantic validation current;
- clean-room instructions available;
- remaining result-dependent slots explicitly marked;
- journal formatting/submission package readiness.

## Priority B — can be prepared now but not scientifically frozen without user review

The following can be drafted, audited, or preflighted now, but their final scientific specification should not be frozen or executed as decisive work without explicit review:

1. any new L17/L19/higher-layer convergence extension intended to reopen a numerical HOLD;
2. any change to tolerance, DFT functional, pseudopotential, k-point rule, geometry, slab construction, quantum tier, friction model, dissipation route, or kinetic model;
3. final native comparator identity for a confirmatory added-value claim;
4. a complete MFR-14 confirmatory record;
5. final P1 claim text, decision threshold, multiplicity rule, or untouched decisive dataset/system;
6. a new physical matching contract joining well-side damping, barrier-local friction, rate, turnover, or transmission;
7. publication-level novelty certification;
8. any paid or larger-runner compute route.

## Priority C — wait for computation because the answer itself depends on the result

Only result-dependent adjudication must wait. Examples include:

- deciding whether a currently running frozen gate passes or fails;
- populating final numerical values that do not yet exist;
- interpreting a new system response that has not completed;
- deciding the next branch of a precommitted workflow when the branch condition is the pending result.

Everything in Priority A should continue independently unless it would overwrite or prejudge a frozen result-dependent field.

## Immediate sequence

Recommended parallel order while computation is pending:

`GOM sync -> chi/provenance audit -> open-channel/HOLD index -> reproducibility readiness -> prior-art/comparator audit -> novelty ledger -> Function/Limit balance -> experimental-opportunity collision -> release checklist`

Monitor coverage and project-state truth run alongside the entire sequence.

**User action currently required for Priority A:** none.
