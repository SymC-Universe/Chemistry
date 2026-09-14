# Chemistry project guardrails under GOM v0.8.0

**Status:** active internal project safeguard  
**Program manual:** SymC General Operations Manual v0.8.0  
**Purpose:** preserve Chemistry-specific scientific boundaries locally after consolidation of the program-wide manual.

These rules do not replace the GOM. They are the Chemistry-local destination for exact equations, interpretation limits, and claim ceilings that are too domain-specific for the program-wide manual.

## 1. Stable-mode mechanical chi requires a licensed dynamical factor

For a stable second-order factor

`q'' + Gamma q' + Omega_0^2 q = 0`,

mechanical chi may be reported as

`chi = Gamma / (2 Omega_0)`

only when the governing physical model or an independently validated reduction licenses that factor.

Every promoted real-system value must identify the physical mode, quotient, reaction-coordinate-adjacent stable mode, or subspace to which the scalar belongs and state the Gamma/Omega convention and units. Observed damped frequency, spectral-peak frequency, linewidth, lifetime, and undamped natural frequency are not silently interchangeable.

A single real pole does not define mechanical chi. A multimode or non-normal system is not collapsed to one scalar merely because a scalar can be calculated from selected poles.

## 2. Barrier tops do not inherit stable-well critical-damping geometry

For an isolated inverted barrier coordinate

`q'' + gamma q' - omega_b^2 q = 0`,

the discriminant is

`gamma^2 / 4 + omega_b^2`,

which cannot vanish for real gamma and nonzero `omega_b`.

Therefore the barrier top does not possess the stable-well mechanical critical-damping boundary at chi = 1. `omega_b` remains a legitimate barrier-curvature quantity, but it is not substituted for restoring `Omega_0` to manufacture a canonical mechanical chi at the saddle.

Barrier transmission, reactive poles, recrossing, friction regime, memory effects, and rate turnover are treated with their native kinetics and reaction-dynamics descriptions.

## 3. Width is not damping by default

A measured spectral or lineshape width is not a mechanical amplitude-damping coefficient merely because it has frequency units.

Before a width is used as Gamma, the source/model must establish the relevant relationship and lifetime, pure-dephasing, inhomogeneous, orientational, instrumental, and other material broadening contributions must be separated or bounded as appropriate to the experiment.

Full-width versus half-width, angular versus ordinary frequency, rate versus wavenumber, and amplitude versus energy decay conventions must be explicit.

## 4. Keep distinct Chemistry quantities distinct

Unless a separately justified and frozen comparison establishes a relation, the following remain separate objects:

- barrier height;
- reaction rate;
- transmission coefficient;
- reactive-pole structure;
- friction/dissipation descriptor;
- damping morphology;
- rate turnover;
- exceptional-point proximity/classification;
- stable-mode mechanical chi.

Algebraic convenience does not license physical identity.

## 5. Multimode, non-normal, and memory-bearing dynamics preserve structure

When the admitted Chemistry System Model is coupled, multimode, non-normal, frequency-dependent, or memory-bearing:

- preserve the relevant generator/operator and modal or subspace geometry;
- retain conditioning and uncertainty;
- do not collapse a frequency-dependent friction kernel to a single Gamma without a separately justified projection/reduction;
- preserve mode correspondence and assignment provenance;
- return `UNRESOLVED`, `REFUSED`, or another licensed non-scalar outcome when the reduction is not identifiable.

The scalar is attached to its carrier. It is not a free-standing system property.

## 6. Degeneracy is not an exceptional point

Repeated or nearly repeated eigenvalues do not establish an exceptional point by themselves.

Exceptional-point language requires the additional structural evidence appropriate to the declared generator and evidence class. Finite-precision coincidence supports only the classification actually demonstrated; crowded or unresolved neighborhoods remain unresolved rather than promoted.

## 7. Cross-description and mode matching are scientific claims

If the project relates modes, coordinates, or dynamical descriptions across methods, geometries, temperatures, media, slab depths, or system scales, the correspondence rule must be justified and frozen before the target outcome is inspected when the result is intended to support prospective or confirmatory inference.

Do not select the correspondence that produces the most favorable chi, rate relation, or stability narrative after seeing the outcome.

## 8. Current numerical HOLDs remain evidence

Existing CO/Cu(111) and H/Ru(0001) numerical HOLDs are not mechanical errors to be retried until they pass.

A rerun with unchanged scientific inputs cannot convert a failed frozen convergence condition into scientific success. Any new higher-layer extension, convergence design, or result-affecting setting change must enter through the appropriate prospective scientific change/freeze route before new decisive results are inspected.

Historical failures, refusals, and superseded execution routes remain visible in provenance.

## 9. Barrier-Height/Rate Atlas independence remains intact

The frozen Barrier-Height/Rate Atlas v0.9 remains an independent evidence product and is not silently retuned from CO/Cu(111), H/Ru(0001), or another prospective system outcome.

Well-side ChemSA chi does not substitute for barrier-local friction. Atlas coordinates, source grades, reaction-family assignments, and evidence status retain their own provenance and validation rules.

## 10. Future promoted mechanical-chi reporting gap

The existing frozen inheritance contract identifies one future reporting improvement: when a real-system mechanical chi is promoted, persist the mass-normalized mechanical modal vector/subspace, or a scientifically equivalent carrier representation, together with the scalar record so scalar-to-carrier assignment is explicit.

The preferred implementation is an additive reporting adapter or backward-compatible output extension. **No core ChemSA engine change is required merely to satisfy this reporting improvement.**

## 11. Cost and execution safeguard

Repository compute remains subject to `AGENTS.md` and the free-runner policy. No paid or larger GitHub-hosted runner is enabled, selected, or recommended without an explicit current-conversation user approval of a maximum dollar amount.

Scientific inputs, thresholds, geometry, methods, or interpretation are never changed to fit a runner or to evade a numerical HOLD.

## 12. Promotion boundary

These guardrails do not themselves promote any Chemistry claim.

Any confirmatory natural-system claim inherits GOM MFR-14 and the strongest relevant Chemistry-native null/comparator path. A documented `NO_NATIVE_COMPARATOR` state is permitted only after a good-faith nearest-method search for the frozen task and does not establish `ADDS` over a standard toolkit.

Publication-level novelty remains residual after closest prior art and must not be inferred from absence in a narrow search.
