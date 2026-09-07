# ChemSA: Generator-First Stability Analysis in Chemistry

This repository contains the current ChemSA chemistry program, its reproducibility assets, the Barrier-Height/Rate Atlas, and prospective computational system tests.

The present scientific scope is **generator first**. A scalar stability coordinate is reported only when the physical and mathematical reduction that licenses it has been established. Scalar quantities remain attached to the mode, reaction coordinate, subspace, or generator from which they are derived.

## Current core

For an identified stable second-order damped mode,

```math
\chi = \frac{\Gamma}{2\Omega}
```

is a legitimate mechanical damping ratio. In that restricted setting, `chi < 1`, `chi = 1`, and `chi > 1` describe underdamped, repeated-root/critical, and overdamped modal morphology.

ChemSA does **not** treat this scalar as a universal reaction-rate coordinate or a system-wide stability number. For a general first-order or coupled generator, the engine withholds mechanical `chi` unless the required scalar or proportionally damped modal reduction is independently licensed.

The classifier instead preserves the relevant spectral and modal structure, including multiplicity, defectiveness at tolerance, conditioning, provenance, and response geometry.

## Exceptional-point classification

A repeated eigenvalue is not automatically an exceptional point. A semisimple degeneracy retains independent eigenvectors, whereas an exceptional point is defective.

ChemSA therefore distinguishes eigenvalue coincidence from eigenvector deficiency and scopes every exceptional-point interpretation to the declared provenance of the supplied equation. Crowded or numerically unresolved neighborhoods are returned as unresolved rather than promoted.

## Scalar-modal reporting discipline

Future promoted chemistry stability results follow a coupled scalar-modal record:

- governing generator, Hessian/dynamical object, response operator, or justified reduced model;
- licensed scalar coordinate set and applicable competing margins;
- modal, eigenvector, reaction-coordinate, or subspace geometry;
- explicit scalar-to-mode/subspace assignment;
- inter-channel or cross-description relation when applicable;
- uncertainty, conditioning, provenance, admissibility, and refusal state.

A scalar is not selected because it happens to lie near a preferred value, and a mode is not selected after inspecting the desired outcome.

The frozen inheritance contract is:

`systems/CHEMISTRY_STABILITY_ARC_INHERITANCE_v0.1.json`

## Barrier crossing is a separate dynamical question

A stable well mode and an inverted transition-state mode are not governed by the same critical-damping geometry.

For an isolated scalar inverted barrier coordinate,

```math
q'' + \gamma q' - \omega_b^2 q = 0,
```

the discriminant is

```math
\frac{\gamma^2}{4} + \omega_b^2,
```

which does not vanish for real damping and nonzero barrier frequency. There is therefore no mechanical critical-damping boundary at the saddle analogous to `chi = 1` for a stable well.

Barrier transmission is handled with the appropriate reactive-pole or transmission description. The current engine does not infer a reaction rate from local spectral architecture alone.

## Barrier-Height/Rate Atlas

The Barrier-Height/Rate Atlas is maintained as a separate evidence structure for barrier/rate coordinates and mechanistic families.

Its validation rules explicitly forbid substituting well-side ChemSA `chi` for barrier-local friction. Barrier height, reaction rate, damping morphology, transmission, friction regime, and exceptional-point proximity remain distinct quantities unless a separately frozen comparison establishes a relation.

## Current prospective computational systems

### System 2: CO/Cu(111)

The active CO/Cu(111) program is a frozen, staged first-principles workflow. Numerical convergence, clean-surface validation, adsorption-site ordering, reaction-path construction, and later dissipation validation are separated so that kinetic outcomes cannot tune upstream electronic-structure choices.

The current clean-surface audit and its no-recompute site-ordering handoff remain unchanged by the scalar-modal reporting update.

### System 3: H/Ru(0001)

H/Ru(0001) is the selected contrast/limit system. Its prospective protocol treats nuclear quantum effects explicitly and refuses a full rate claim if the required quantum tier, coordinate matching, or dissipation provenance is not established.

No ChemSA `chi` is assigned until a physically matched projected damping/friction quantity and the corresponding mode or reaction coordinate pass their validators.

## Reproducibility

Repository code and deposited data are the canonical computational sources for numerical results. Published figures and tables should be reproducible from preserved scripts and source data, with hashes and validation records retained where material.

Historical failures, refusals, numerical holds, and superseded mechanical execution routes remain part of the provenance record and are not rewritten as successes.

## Scope and nonclaims

The current program does not claim that:

- one scalar describes every chemical stability problem;
- `chi = 1` is a universal reaction-rate optimum;
- `chi = 1` is a barrier-top critical point;
- a linewidth by itself is a mechanical damping coefficient;
- a repeated eigenvalue by itself establishes an exceptional point;
- local spectral architecture determines reaction rate, yield, selectivity, or commitment probability;
- quantities from different physical modes, generator classes, temperatures, media, or coordinate definitions may be pooled without an explicit matching contract.

Refusal or nonidentifiability is a valid result when the required reduction or provenance is absent.

## Repository contents

The repository includes current and historical manuscript assets, reproducibility packages, Barrier Atlas data and validation tools, and prospective computational workflows for chemistry systems under test.

See the individual protocol, README, validation, and reproducibility files associated with each release or system for the exact scientific contract that applies to that object.
