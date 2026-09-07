# System 3 H/Ru(0001) manuscript integration record v0.1

Status: PROSPECTIVE / ADDITIVE. This file prepares manuscript integration without promoting unadjudicated System 3 results.

## Role of System 3

H/Ru(0001) is a difficult-limit validation system for the ChemSA computational methodology. Its role is not to establish universality. The purpose is to test whether an evidence-gated workflow can progress from electronic-structure qualification through surface, adsorption, reaction-path, quantum-nuclear, and dissipation gates while preventing later kinetic agreement or a desired stability interpretation from selecting earlier settings.

## Language rule

Conventional domain terminology controls the description of each result. Exceptional point, critical damping, phase boundary, bifurcation, kinetic crossover, stability boundary, adsorption minimum, transition state, and related terms are used only when the governing equations and evidence license those terms. The symbol chi is not itself a license to rename a physical boundary.

## Current evidence state

### Ru bulk candidate: ADJUDICATED PASS

The first low-cost PBE/SSSP candidate passed the prospectively frozen Ru bulk numerical and structural gates. The recovered adjudication used the 34 completed SCFs from the original run with zero QE recomputation after the original workflow failed only at JSON serialization. The selected settings are 70/280 Ry and 16x16x10. The fitted hcp Ru lattice constants are a = 2.725291573 A and c = 4.294686729 A, with relative deviations of 0.71664% and 0.30799% from the preregistered structural comparator. The cutoff and k-mesh deltas to their frozen endpoints are 0.00009524 and 0.00048300 eV/atom, respectively.

Claim fence: this establishes METHOD_READY only at the Ru bulk-candidate level. It does not establish a qualified Ru(0001) surface, H adsorption ordering, a diffusion path, a rate, a dissipation coordinate, chi, or ChemSA eligibility.

### Clean Ru(0001) surface: PROSPECTIVELY FROZEN / PENDING COMPUTATION

The clean-surface gate selects the smallest non-terminal slab, vacuum, and surface k-mesh that remain within 0.001 eV per surface atom of the frozen terminal endpoint and then requires a joint endpoint recheck. Endpoint-only agreement is explicitly insufficient. The fixed-grid numerical calculation is separated from the subsequent checkpoint-protected surface relaxation and independent reproduction gate.

No H/Ru kinetic value, barrier, published adsorption-site ordering, chi value, expected ChemSA outcome, or System 2 result may select these settings.

### Downstream sections: NOT YET PROMOTED

H adsorption, local H vibrational stability, reaction path, classical rate baseline, quantum-nuclear rate tier, projected dissipation, and any stability mapping remain pending. Each section may enter result prose only after its corresponding readiness gate is ADJUDICATED.

## Prospective result structure

When the required evidence exists, System 3 will be reported in the following order:

1. qualified clean-surface model and reproduction result;
2. unbiased top/bridge/fcc/hcp adsorption screen plus lateral-size sensitivity;
3. local H vibrational stability of the numerically selected adsorption minimum;
4. ordinary NEB, CI-NEB, and saddle-mode verification for the path selected from the computed PES;
5. classical harmonic baseline;
6. quantum-nuclear free-energy/rate tier under its frozen bead and coordinate rules;
7. independently matched dissipation evidence;
8. only then, any licensed scalar, modal/vector, and system-level stability representation.

## Interpretation firewall

A later rate comparison cannot rescue a failed surface, adsorption, path, quantum, or dissipation gate. Similarity to another SymC system is not evidence of a shared mechanism. Broad relevance, common mathematical structure, common mechanism, and universality are separate claims. Universality is not under adjudication in System 3.
