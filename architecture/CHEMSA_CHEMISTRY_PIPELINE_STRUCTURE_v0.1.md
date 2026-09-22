# ChemSA Chemistry Pipeline Structure v0.1

**Status:** working architecture
**Purpose:** separate scientific functions so that each layer has one explicit job and no layer silently supplies missing physics for another.

## 1. Computational Reaction-Path Engine

**Scientific job:** compute the static and harmonic reaction-path quantities that can be obtained from the chosen electronic-structure method.

Typical outputs:
- converged substrate and adsorbate geometries;
- adsorption-site ranking;
- minimum-energy path;
- saddle geometry and barrier height;
- Hessian or force-grid information;
- harmonic or explicitly qualified approximate prefactor;
- model rate coordinates derived from the computed barrier/prefactor.

The engine does **not** infer a damping coefficient from a Hessian and does **not** assign a ChemSA stability class.

**Current implementation:** the Na/Cu(001) `na_cu001_ci` route is the development-pilot implementation of this layer. It remains in place until that active workflow closes; files are not moved while the live workflow depends on their paths.

## 2. Reaction-Coordinate Consistency Validator

**Scientific job:** determine whether quantities proposed for combination refer to the same physical coordinate and compatible thermodynamic/state conditions.

Required checks include, as applicable:
- same adsorbate/substrate and surface state;
- same translational, rotational, internal, collective, or reaction coordinate;
- well mode projects onto the barrier-crossing coordinate;
- barrier path and damping measurement are not orthogonal coordinates;
- temperature, coverage, pressure, solvent, charge state, and structural phase are compatible or the mismatch is explicitly typed;
- the local well frequency and barrier/saddle information use compatible coordinate conventions;
- any projection from a multidimensional mode to a reduced coordinate is explicit and reproducible.

Possible outputs:
- `PASS`;
- `HOLD_CONDITION_MISMATCH`;
- `HOLD_COORDINATE_MISMATCH`;
- `HOLD_PROJECTION_UNRESOLVED`;
- `NOT_APPLICABLE`.

This validator does not decide whether a damping number is independently trustworthy; that is the next layer.

## 3. Dissipation Provenance Validator

**Scientific job:** determine what a proposed damping quantity physically represents and whether it can be used for the validated reaction coordinate without circularity.

It must distinguish at minimum:
- population lifetime (`T1`);
- homogeneous dephasing (`T2` or linewidth after decomposition);
- pure dephasing;
- inhomogeneous broadening;
- phonon coupling;
- electronic friction;
- projected friction tensor component;
- generalized-Langevin memory kernel;
- rate-fitted Langevin friction;
- model-resolved coupling parameter.

Required checks include:
- source and publication identity;
- direct measurement versus fitted/model-derived quantity;
- whether target kinetics were used to determine the damping parameter;
- whether a linewidth-to-rate conversion is physically licensed;
- whether population and dephasing contributions are resolved;
- whether the damping object is scalar, tensorial, frequency dependent, or non-Markovian;
- whether a scalar transfer to the reaction coordinate is justified.

Possible outputs:
- `PASS_DIRECT`;
- `PASS_PROJECTED`;
- `PASS_MODEL_RESOLVED`;
- `HOLD_RATE_CALIBRATED`;
- `HOLD_DEPHASING_UNRESOLVED`;
- `HOLD_PROJECTION_UNRESOLVED`;
- `HOLD_CONDITION_MISMATCH`;
- `NONE_AVAILABLE`.

## 4. ChemSA Classifier

**Scientific job:** classify an already-admissible dynamical object.

The classifier may receive a validated quadratic pencil, first-order generator, or a licensed reduced second-order mode. It may compute and report quantities such as the damping ratio and spectral/exceptional-point class only after the preceding validators establish that the inputs have the required physical meaning.

The classifier does not:
- invent a missing damping coefficient;
- decide that unrelated observables are equivalent;
- repair a failed coordinate/provenance gate;
- use a kinetic outcome to tune the dynamical input being tested against that outcome.

## 5. Barrier-Rate Atlas

**Scientific job:** retain the evidence and its provenance, including successes, failures, holds, and different levels of physical completeness.

The frozen Barrier-Height/Rate Atlas v0.9 remains an immutable literature parent. Future computational and joined-dynamics records extend it rather than rewriting frozen coordinates.

A computational coordinate may be admitted even when it is not ChemSA-eligible. The record must therefore separate at least:
- `barrier_tier`;
- `prefactor_tier`;
- `rate_model_tier`;
- `dissipation_tier`;
- `reaction_coordinate_validation`;
- `chemsa_eligibility`;
- `experimental_comparison_tier`;
- provenance and source-independence fields.

Example: a first-principles barrier and harmonic prefactor with no admissible damping is a valid computational Barrier-Rate Atlas coordinate, but it has `dissipation_tier = NONE` and `chemsa_eligibility = false`.

## 6. Layer order

The default scientific route is:

`source / experiment / first-principles calculation`

→ **Computational Reaction-Path Engine**

→ **Reaction-Coordinate Consistency Validator**

→ **Dissipation Provenance Validator**

→ **ChemSA Classifier**

→ **Barrier-Rate Atlas admission and cross-system analysis**

A system may stop at any layer. A stop is a result, not a software error.

## 7. Non-substitution rule

No layer may silently perform another layer's scientific job.

- A Hessian is not a damping matrix.
- A linewidth is not automatically reaction-coordinate friction.
- A fitted diffusion friction is not independent validation of the same diffusion rate.
- A rate-derived activation energy is not an independent barrier.
- A ChemSA classification cannot promote weak provenance.
- Atlas admission cannot repair a failed physical-consistency gate.

## 8. System roles

- **System 1: Na/Cu(001)** — development pilot for the Computational Reaction-Path Engine and audit/failure machinery.
- **System 2** — externally selected validation target run with the method and layer contracts frozen before kinetic comparison wherever feasible.
- **System 3** — parallel contrast/limit target selected under a separate prospective rule so that repeated favorable-system selection cannot become the program's default.

## 9. Refactor rule

The current Na/Cu(001) implementation will not be physically relocated while active workflows depend on its paths. New generic code should be written to the layer structure above. After the Na/Cu(001) pilot reaches final closure or an honest scientific HOLD, reusable code can be extracted from `na_cu001_ci` into generic layer modules with regression tests proving that the pilot outputs are unchanged.