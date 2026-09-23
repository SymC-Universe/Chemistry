# HCN <-> HNC native modal-Capital-Chi benchmark preregistration

**Date:** 2026-09-23  
**Status:** FROZEN BEFORE COMPUTATION  
**Rowan folder:** Capital_Chi_Modal_HCN_HNC_2026-09-23  
**Folder UUID:** 4459e358-6eec-4a64-a964-0f08addfcc8b

## Purpose

Construct the first full native molecular Capital-Chi record in this chemistry program from a real chemical reaction using independently generated reactant and transition-state modal data.

This is an implementation/physics benchmark. It is not being selected because of a known favorable rate result.

## System

HCN <-> HNC isomerization.

Reasons for selection:
- chemically real;
- small closed-shell triatomic;
- computationally inexpensive enough for prospective full Hessian/normal-mode work;
- contains a genuine reactant minimum, product minimum, and isomerization saddle;
- permits exact storage of all modal vectors without dimensional compression.

## Frozen calculation ladder

### R0 reactant/product minima
For HCN and HNC independently:
- optimize geometry;
- compute harmonic frequencies;
- preserve optimized Cartesian coordinates;
- preserve Hessian/frequency-normal-mode outputs where exposed by the workflow result.

### R1 transition state
Perform a double-ended TS search using the prospectively declared HCN and HNC endpoint structures, with endpoint optimization enabled and TS optimization enabled.

### R2 TS validation
After R1 returns:
- compute TS harmonic frequencies on the located TS;
- require exactly one physically relevant imaginary frequency for a first-order saddle before promotion;
- if available, run IRC from the TS to verify endpoint connectivity.

No TS is accepted merely because its energy lies between HCN and HNC.

## Modal-Capital-Chi target

For matched reactant and TS native calculations construct:

- indexed reactant mode frequencies/eigenvectors;
- TS stable-mode frequencies/eigenvectors;
- TS unstable reaction-coordinate mode;
- reactant-to-TS subspace/modal correspondence using a declared mass metric;
- projection of each reactant vibrational mode onto the TS unstable reaction subspace;
- conditioning/degeneracy/refusal state.

If a mode-resolved mechanical damping quantity is absent, lowercase chi_i is marked unavailable rather than invented.

## No kinetic tuning

The following are forbidden before the modal record is frozen:
- choosing a different TS because its modes better match a desired kinetic narrative;
- rotating nondegenerate modes to improve projection;
- selecting only the reactant mode with the largest rate correlation;
- fitting any modal combination to a target rate;
- inferring damping from the known HCN/HNC rate.

## Promotion

P0-Q: exact native modal record reconstructed and provenance-closed.

P1 modal mechanism: a declared modal correspondence/projection can be related to a native reaction-coordinate role without target fitting.

No empirical rate-prediction claim is allowed from this benchmark alone.
