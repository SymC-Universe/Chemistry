# CO/Cu(111) System 2 Method Feasibility Audit v0.1

**State:** `SCIENTIFIC_PROTOCOL_DECISION_PENDING`
**Purpose:** identify an electronic-structure route capable of representing CO/Cu(111) without selecting a method from the known diffusion barrier or rate.

## 1. Why Na/Cu(001) PBE cannot simply be inherited

CO/Cu(111) is a documented density-functional site-preference problem.

Published calculations show that common LDA/GGA treatments including PBE-type approaches tend to favor higher-coordination hollow adsorption even though experiment identifies on-top adsorption. Therefore the Na/Cu(001) exchange-correlation choice is not automatically portable to System 2.

This is a **method-physics issue**, not a convergence issue. Increasing slab thickness, k-point density, or force convergence cannot by itself repair an exchange-correlation functional that gives the wrong adsorption-site ordering.

## 2. Published method families relevant to the problem

### PBE / conventional GGA

Role in System 2: **diagnostic baseline only unless it unexpectedly passes all prospectively frozen structural gates**.

Published literature repeatedly documents incorrect higher-coordination site preference for CO/Cu(111). A PBE diffusion barrier therefore cannot be accepted merely because its numerical magnitude happens to agree with an experimental diffusion barrier.

### BLYP

Published Physical Review B work reports that the semilocal BLYP functional correctly predicts the experimentally observed CO adsorption site on Cu(111) and other tested (111) metal surfaces. In the published Cu case, the top site is favored relative to hollow.

Advantages:
- semilocal computational cost is compatible with the intended Reaction-Path Engine better than hybrids/RPA;
- correct site ordering is obtained without fitting to diffusion kinetics.

Known limitation:
- BLYP can describe metal bulk/cohesive properties poorly. Therefore it cannot be selected from site preference alone; the Cu substrate and CO structural/vibrational calibration gates must also pass.

**Current status:** `PRIMARY_FEASIBILITY_CANDIDATE`, not selected production method.

### PBE0 / HSE-type hybrids

Published plane-wave hybrid-functional calculations report that PBE0/HSE03 correct the CO adsorption-site ordering for Cu(111), improving over PBE.

Advantages:
- independent literature support for the qualitative site problem;
- no diffusion-kinetic fitting required.

Limitations:
- substantially higher computational cost for a metallic 4x4-scale surface and especially for repeated relaxations/NEB;
- hybrid treatments can improve site order while worsening other adsorption energetics.

**Current status:** `HIGH_COST_REFERENCE_CANDIDATE`.

### Molecular DFT+U

Published work demonstrates that correcting the underestimated CO HOMO-LUMO gap with a molecular DFT+U treatment restores the on-top preference and improves adsorption energetics.

Strength:
- directly targets a documented source of the site-preference error.

Risk for this program:
- the definition and value of U become additional scientific choices;
- a U selected using the diffusion barrier would be circular;
- the implementation must reproduce the molecular-subspace correction intended by the published method rather than applying an unrelated atomic U and calling it equivalent.

**Current status:** `REFERENCE_METHOD_REQUIRING_IMPLEMENTATION_AND_PARAMETER_PROVENANCE_AUDIT`.

### RPA / correlated-wavefunction benchmarks

Published RPA and embedded correlated-wavefunction calculations improve the site ordering and adsorption energetics substantially.

Role here: high-level reference evidence, not the default production route on current CI resources.

**Current status:** `BENCHMARK_REFERENCE_NOT_PRODUCTION_DEFAULT`.

## 3. Proposed method-screen logic

No diffusion barrier, diffusion coefficient, hopping rate, attempt frequency, or fitted Langevin barrier may participate in this screen.

A candidate method must be judged only from a prospectively declared non-kinetic calibration set, including:

1. internally converged Cu bulk structure for that method;
2. internally converged clean Cu(111) slab;
3. gas-phase CO geometry/frequency sanity checks where technically appropriate;
4. experimentally established on-top adsorption preference at the target low-coverage limit;
5. adsorption geometry and vibrational observables chosen and frozen before the diffusion path is computed;
6. numerical convergence and computational feasibility sufficient to execute adsorption, NEB, and Hessian stages without changing the method midstream.

Selection principle proposed for freezing:

> Choose the lowest-cost candidate that passes every frozen non-kinetic calibration gate. Do not inspect or calculate its production diffusion barrier until the method has been selected.

If no tractable candidate passes, return `METHOD_HOLD` rather than selecting the method whose barrier best matches experiment.

## 4. Initial candidate order for feasibility tests

1. PBE as a negative/control baseline, not presumed admissible.
2. BLYP as the first production-feasibility candidate because published evidence supports correct Cu(111) site ordering at semilocal cost.
3. A hybrid reference calculation on a reduced calibration set if BLYP cannot satisfy both substrate and adsorption gates.
4. Molecular DFT+U only after the exact correction/projection and U provenance are specified independently of diffusion kinetics.
5. RPA/correlated methods remain external benchmarks unless compute resources and a new protocol justify their use.

This order is based on method capability and cost, not on closeness to the known CO diffusion barrier.

## 5. Scientific decision still required before launch

The following must be frozen before any System 2 production diffusion calculation:

- exact candidate method set;
- exact pseudopotential families compatible with each method;
- numeric bulk/slab/adsorption calibration tolerances;
- target coverage/supercell rule;
- which experimental structural/vibrational quantities are calibration inputs and which remain held out;
- what happens if PBE and BLYP disagree on bulk versus adsorption quality;
- whether a hybrid reference is mandatory or only a fallback.

Until this is written into a machine-readable protocol and hashed, System 2 remains in `METHOD_SELECTION_REQUIRED` and no barrier/NEB production run should start.