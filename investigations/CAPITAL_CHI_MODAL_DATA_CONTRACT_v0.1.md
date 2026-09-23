# Capital-Chi Modal Data Contract v0.1

**Date:** 2026-09-22  
**Status:** FROZEN AFTER A17-A21 / BEFORE NEXT REAL-SYSTEM DATA ACQUISITION

## Purpose

Define the minimum evidence required to report capital Chi in chemistry without collapsing it into a scalar or over-promoting partial literature information.

Lowercase chi and capital Chi remain distinct:

- `chi_i`: scalar coordinate carried by one licensed mode/subspace;
- `Chi`: modal/vector architecture and correspondence among those carriers.

## Full native Capital-Chi record

A **full native record** requires, from one matched physical model/condition:

1. native generator/Hessian/operator or equivalent reproducible matrices;
2. indexed modal eigenvalues/frequencies/poles;
3. indexed right mode vectors or invariant subspaces;
4. left/response basis when the native problem is non-normal;
5. scalar-to-carrier assignment for every licensed chi_i;
6. declared physical-coordinate/reaction-coordinate projections;
7. modal coupling/mixing or path correspondence when claimed;
8. conditioning/degeneracy/refusal information;
9. source/provenance and condition matching.

A full record may still have refused fields where the native model does not license them.

## Partial Capital-Chi record

A **partial record** may be reported when a source exposes an invariant modal relation but not the complete native generator, for example:

- mode-to-reaction-coordinate projection matrix;
- Duschinsky rotation matrix;
- principal-angle/subspace correspondence;
- experimentally prepared modal identity plus independently calculated reaction-coordinate overlap;
- stable/unstable collective mode vector.

Every partial record must explicitly list what is absent.

A partial record is not upgraded to a full record by reconstructing missing vectors from the target rate.

## Matrix-valued modal correspondence

For a carrier set (i) and reaction/path subspaces (c), an admissible partial Chi object is

[
P_{ic}=|Q_i^\dagger W Q_{RC,c}|
]

or the source's equivalent invariant projection convention.

The matrix is preserved. No row maximum, norm, average, or fitted score replaces the matrix as capital Chi.

Derived scalar summaries may be reported only as diagnostics.

## Path correspondence

For two configurations/conditions A and B, correspondence should be represented by basis-invariant subspace relations where possible.

The additive adapter uses principal cosines between metric-orthonormalized subspaces and returns the full vector of principal cosines for each pair. It does not select a target-driven permutation.

## Maturity

### P0-D
Modal object and provenance identified; extraction may still be qualitative.

### P0-Q
Exact quantitative modal matrix/subspace/vector extracted and condition matched.

### P1
A controlled or empirical contrast shows that changing modal Chi changes or organizes a kinetic/response outcome while key scalar alternatives are held fixed or explicitly controlled.

### P1+
The modal result replicates in a related system/source or survives an independent modal mechanism test.

### P2
Independent-source held-out prediction or prospective perturbation demonstrates incremental information beyond:
- native energetics/barrier baseline;
- local scalar chi_i where licensed;
- predeclared scalar controls.

## Current real-chemistry records

### A19 CH3D / CH2D2 on Pt(111)
P0-Q partial modal record:
- exact mode-to-C-H/C-D reaction-coordinate projections;
- exact state-resolved sticking coefficients;
- no full native Hessian/generator persisted in this project.

### A20 CH3OH on Cu(111)
P0-Q partial modal record:
- exact 5 x 3 stretch-mode/transition-state SVP matrix;
- exact channel barriers and vibrational efficacies;
- no full source Hessian/eigenvector set persisted in this project.

### A21 CH3D + Cl
P0-D path-modal record:
- experimentally established near-energy-matched mode specificity;
- qualitative ab initio eigenvector evolution along the reaction path;
- exact pathwise vector-overlap trajectory not available in accessible source material.

## Current acquisition target

The next high-value dataset is a real chemical system for which the native calculation files expose:
- reactant Hessian/mass matrix;
- transition-state Hessian/mass matrix;
- normal modes in a common or explicitly transformable coordinate convention;
- mode-resolved damping/lifetimes if available;
- observed or independently predicted kinetics.

That dataset would allow the first full real-system Capital-Chi record and direct chi_i-to-Chi mapping.
