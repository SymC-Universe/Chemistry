# Public repository metadata correction required

**Status:** open mechanical/scientific-communication governance defect  
**Date identified:** 14 September 2026  
**Repository:** `SymC-Universe/Chemistry`  
**Scientific settings affected:** none

## Defect

The current public GitHub repository description states:

> SymC in chemistry shows that catalytic efficiency and reaction pathways are governed by a single stability ratio, χ = Γ/(2Ω). This framework unifies electron transfer, PCET, and heterogeneous catalysis by identifying near-critical damping (χ ≈ 1) as the condition for optimal reactivity.

That description is stale relative to the current generator-first Chemistry program and the SymC General Operations Manual v0.8.0.

It overstates the present evidence in several ways:

1. it presents one scalar as governing catalytic efficiency and reaction pathways;
2. it implies a broad unification claim across electron transfer, PCET, and heterogeneous catalysis;
3. it presents near-critical damping around chi = 1 as an established condition for optimal reactivity;
4. it does not preserve the current distinction among stable-mode damping, barrier-crossing kinetics, friction, transmission, coupling, modal/subspace structure, and exceptional-point classification;
5. it does not preserve the current refusal rule when a mechanical chi reduction is not licensed.

The active `README.md`, the frozen Chemistry inheritance contract, and the GOM v0.8.0 Chemistry guardrails are narrower than this repository description.

## Recommended replacement

Use a bounded description such as:

> ChemSA is a generator-first chemistry stability framework for licensed modal damping, coupling, barrier kinetics, and exceptional-point structure, with explicit uncertainty, refusal, and independent Barrier-Height/Rate Atlas evidence.

An even more conservative alternative is:

> Generator-first SymC chemistry research: modal stability, coupling, barrier kinetics, exceptional-point structure, and an independent Barrier-Height/Rate Atlas with explicit uncertainty and refusal.

## Closure condition

Close this defect only after the repository description itself has been changed and the live repository metadata has been re-read to confirm the new wording.

Changing this metadata does not alter any scientific result, threshold, computation, or freeze. It is a prose/capability synchronization correction required because the public description no longer matches the active scientific scope.
