# Chemistry Project Guardrails

**Status:** Active internal project safeguard index  
**Program manual:** SymC General Operations Manual v0.8.0  
**Authoritative GOM date:** 14 September 2026  
**Authoritative GOM Markdown SHA-256:** `ee3d9955e19f280ad385488180800d1cdb2d5054823cfa2fa6a697ab3f51d396`  
**Purpose:** preserve chemistry-specific claim ceilings and implementation safeguards locally after the program-wide GOM consolidation.

This file does **not** create a new scientific result, relax a frozen gate, or promote any chemistry claim. It indexes and consolidates safeguards already present in the Chemistry repository so that project-specific rules do not disappear when the GOM keeps only their transferable program-wide form.

## 1. Stable-well mechanical chi has a narrow license

For an identified stable second-order damped mode,

`chi = Gamma / (2 Omega_0)`

may be reported as a mechanical damping ratio only when the governing model, mode assignment, frequency convention, damping convention, and required scalar/modal reduction are licensed.

A single real pole does not define this chi. A scalar is not selected because it lies near a preferred value. In coupled or general first-order generators, mechanical chi is withheld unless a justified second-order or proportionally damped modal reduction exists.

Primary local source: `README.md` and the frozen stability-arc inheritance contract in `systems/CHEMISTRY_STABILITY_ARC_INHERITANCE_v0.1.json`.

## 2. Barrier-top frequency is not stable-well Omega_0

For an inverted scalar barrier coordinate,

`q'' + gamma q' - omega_b^2 q = 0`,

the characteristic discriminant is `gamma^2/4 + omega_b^2`, which does not vanish for real damping and nonzero barrier frequency. The barrier therefore does not inherit the stable-well `chi = 1` critical-damping boundary.

Barrier height, barrier frequency, reaction rate, transmission, friction, damping morphology, and exceptional-point proximity remain distinct quantities unless a separately frozen physical matching contract establishes a relation.

Primary local sources: `README.md`, Barrier-Height/Rate Atlas validation assets, and `PROGRAM_CLOSURE_STATUS_2026-09-04.md`.

## 3. Scalar, vector/modal, and conglomerate/system evidence remain distinct

Scalar stability coordinates, resolved modal/subspace structure, and system-level organization are complementary starting layers. None substitutes for the others. Disagreement among them is preserved as evidence rather than tuned away.

A system-level scalar may not be manufactured by averaging or otherwise conglomerating lower-level chi values without an independent derivation and validation appropriate to the system representation.

Primary local sources: `README.md`, `architecture/CHEMSA_CHEMISTRY_PIPELINE_STRUCTURE_v0.1.md`, and `architecture/VALIDATED_SUBSTRATE_INHERITANCE_CONTRACT_v0.1.md`.

## 4. Local dynamical identity and embedded realized behavior are separate

A locally identified mode, pole, reaction coordinate, or subspace retains its own provenance. Its behavior after adsorption, coupling, substrate embedding, environmental change, or hierarchical organization is a separate empirical/dynamical question.

Substrate inheritance is therefore tested rather than presumed. Preserved local structure, transformed structure, suppression, emergence, and failed closure are all legitimate outcomes.

## 5. Exceptional-point language requires defectiveness evidence

Eigenvalue coincidence or a repeated root does not by itself establish an exceptional point. ChemSA distinguishes repeated-root structure from eigenvector deficiency, preserves representation provenance, and returns unresolved/refusal states when finite precision cannot support the stronger classification.

A tolerance-qualified degeneracy is not silently promoted to an exact exceptional point.

Primary local source: `README.md` and the ChemSA engine/test suite.

## 6. A linewidth is not damping by default

A measured linewidth can enter a mechanical damping interpretation only after the source model and available evidence separate or bound the relevant lifetime, pure-dephasing, inhomogeneous, orientational, and instrumental contributions and state the width/frequency convention.

A source-reported spectral width is not automatically an amplitude damping coefficient.

Primary local sources: the ChemSA manuscript/reproducibility package and spectroscopy-side validation assets.

## 7. Numerical HOLDs and failed gates remain evidence

Completed failures, HOLDs, raw outputs, and prior adjudications are preserved. A failed convergence or acceptance threshold is not loosened after the result. A deeper numerical rung, changed physical model, changed functional/pseudopotential, changed cutoff or k-mesh, changed geometry constraint, changed threshold, or changed scientific interpretation requires a new prospective scientific protocol before affected results are opened.

Mechanical recovery may proceed only when the frozen scientific contract is unchanged.

Primary local source: `governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json`.

## 8. Barrier Atlas evidence remains independent of Engine tuning

The Barrier-Height/Rate Atlas is an independent evidence structure. Its coordinates, source eligibility, family counting, and evidence grades are not tuned to make Engine outputs favorable.

Additional temperatures, pressures, or repeated conditions within one reaction family deepen that family but do not count as additional independent mechanistic families.

Final literature evidence requires independently verified bibliographic identity and enough accessible numerical evidence to support the extracted coordinate. Missing required numerical evidence is caveated, refused, or replaced rather than inferred.

## 9. Current system-specific scientific dispositions live in dated status records

This guardrail file does not freeze new System 2 or System 3 numerical decisions. Current scientific dispositions are maintained in dated program-status records so operational state can change without rewriting this safeguard index.

As of the 14 September 2026 synchronization, the inherited source record is `PROGRAM_CLOSURE_STATUS_2026-09-04.md`: CO/Cu(111) is on `NUMERICAL_HOLD_EXTENSION_AUDIT`; H/Ru(0001) is on `CLEAN_SURFACE_NUMERICAL_HOLD`; Barrier-Height/Rate Atlas v0.9 is independently closed and reproducible.

## 10. GOM migration rule

Program-wide safeguards are governed by GOM v0.8.0. Chemistry-specific equations, mappings, dataset conventions, atlas targets, and claim ceilings remain local. If a later GOM consolidation removes chemistry-specific wording, that wording is not treated as safely removed until a project-local destination is identified or created.

This file is the Chemistry project-level destination for the claim ceilings above. More specific frozen system protocols remain controlling where they impose stricter rules.