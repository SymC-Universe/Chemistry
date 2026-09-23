# Capital Chi modal definition v0.1

**Date:** 2026-09-22  
**Status:** FROZEN MODAL DEFINITION BEFORE NEW RATE TESTS

## Canonical layer distinction

### Scalar chi

[
\chi_i
]

is a scalar coordinate attached to a specific licensed mode/carrier/subspace. It reports a scalar property of that carrier. It is never the modal architecture itself.

### Capital Chi

[
\Chi
]

is the **modal/vector representation** of the admitted dynamical structure.

A minimum Capital-Chi record is:

[
\Chi =
(\Lambda, V_R, V_L, A_{s\to V}, P, K_V, U_V)
]

where terms are included only when licensed:

- (Lambda): indexed modal poles/eigenvalues;
- (V_R): indexed right mode vectors/eigenspaces/subspaces;
- (V_L): left mode vectors/response basis where required;
- (A_{s\to V}): explicit assignment of scalar coordinates such as chi_i to their carrier modes/subspaces;
- (P): participation/projection of physically declared coordinates onto modes;
- (K_V): modal coupling, mixing, or subspace-reorganization information in the native representation;
- (U_V): conditioning, uncertainty, degeneracy, identifiability, and refusal state of the modal representation.

Capital Chi is not required to be scalarized.

## Separate layer: embedded/system organization

Bulk solvent properties, dielectric environment, network topology, memory kernels, barriers, substrate, global recovery, and other conglomerate/system variables are **not automatically Capital Chi**.

They may:
- generate or perturb the modal structure;
- condition how modal Chi is realized;
- be tested jointly with modal Chi;
- belong to a broader system/conglomerate architecture.

But they do not become Capital Chi merely by being dynamically relevant.

## Correct chemistry rate question

The modal rate investigation asks:

> At fixed or independently controlled barrier/native energetics, does the modal/vector architecture Χ explain kinetic behavior that scalar chi_i alone does not?

Preferred contrasts:

1. similar chi_i, different modal vectors/couplings;
2. similar barrier and scalar spectrum, different mode mixing;
3. same modes/frequencies but rotated mode basis;
4. perturbations that redistribute participation among modes while preserving or nearly preserving local scalar coordinates;
5. changes in reactive-coordinate projection onto the modal basis;
6. stable/unstable subspace rotation or mixing that changes transmission/recrossing.

## Existing ChemSA contract alignment

This definition instantiates the frozen Chemistry Stability Arc inheritance contract:

- (s): scalar coordinate set -> local chi_i layer;
- (V): modal/eigenvector/reaction-coordinate/subspace geometry -> Capital Chi core;
- (C): scalar-to-mode correspondence -> required chi-to-Chi mapping;
- (G,R,U): generator, cross-description relation, and uncertainty/provenance remain companion reporting fields rather than being collapsed into either scalar chi or modal Chi.

## Disposition of prior rate-pilot features

Environmental variables from A9-A15 are not Capital Chi by themselves.

They are retained only as:
- perturbations of the modal system;
- potential external conditioning variables;
- evidence that embedded dynamics can matter.

They cannot be cited as direct modal-Capital-Chi validation unless the source also supplies the mode/vector structure that mediates the effect.
