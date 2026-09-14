# Barrier Atlas family-independence six-trail conglomerate readout v0.1

Status: ADDITIVE ANALYSIS ONLY. Barrier_Height_Rate_Atlas_v0.9 remains immutable. No coordinate is admitted and no grade changes in this document.

## Question

What do the six prospectively registered family-independence trails tell us when read together, while preserving each trail's individual result?

This is a non-voting conglomerate analysis. Individual contradictions, refusals, and HOLDs are not averaged away. Likewise, one strong candidate cannot promote the other five.

## Individual trail results

1. **Trypsin-benzamidine association, provisional MC01**
   - Source, directional association FES barrier, and independent association-rate comparator are now qualified.
   - The physical barrier is 11.6 kJ/mol from the 297 K metadynamics FES. The experimental association rate carried by the literature is 2.9e7 M^-1 s^-1.
   - The original experimental temperature/buffer record has not been reconstructed sufficiently from accessible primary text. Result: **CONDITION_MATCH_HOLD**, highest contiguous state COMPARATOR_QUALIFIED.
   - Important negative control: the separate OPES input value `BARRIER=22` is a bias cap and is not promoted as a physical activation barrier.

2. **Cyclobutene -> 1,3-butadiene, provisional MC02**
   - The QMC barrier evidence is strong, but the reaction is explicitly a conrotatory electrocyclic ring opening.
   - Result: **REFUSED_FOR_MC02_CLASSIFICATION**. It remains useful pericyclic evidence, but it cannot be moved into dissociation/fragmentation merely because MC02 needs a second family.

3. **Cyclopropane -> propene, MC06**
   - Later high-level theory resolves the earlier multistep-mechanism objection: the biradical pathway dominates, a carbene branch contributes only about 1-2 percent at higher temperature, and the concerted pathway is not supported.
   - The theoretical high-pressure-limit Arrhenius representation is independently comparable to historical high-pressure kinetic data over overlapping temperatures.
   - All registered gates are satisfied for candidate adjudication. Result: **READY_FOR_ADJUDICATION**, explicitly as a **NETWORK_RESOLVED** case rather than pretending one isolated saddle explains the full kinetics.
   - Agreement was inspected only after the gates: the theory/high-pressure-experiment rate ratio is about 1.68-1.73 at the three historical measurement temperatures. This agreement played no role in candidate selection or promotion.

4. **P. furiosus formaldehyde ferredoxin oxidoreductase, 1B25, provisional MC13**
   - The pinned enzyme database reproduces a model-D energy profile. The source mechanism assigns the second step to proton transfer coupled to two-electron reduction of tungsten, making MC13 scientifically plausible.
   - Independent pre-steady-state kinetics provide 4.7 and 1.9 s^-1 events at 50 C.
   - The model is a static cluster potential-energy profile and the experiment retains ambiguity over whether the first fast event is binding or oxidation. The overall reactant-to-TS2 maximum (14.5 kcal/mol) and internal intermediate-to-TS2 barrier (16.6 kcal/mol) are therefore kept distinct.
   - Result: **CONDITION_AND_EVENT_MAPPING_HOLD**, highest contiguous state COMPARATOR_QUALIFIED.

5. **LiPRED-2026 screen**
   - This is an unusually rich activation-free-energy candidate source: 4513 liquid-phase values for 28 reactions at 298.15 K across seven computational schemes.
   - It does not by itself provide a selected independent raw-rate chain for a new addition-family Atlas coordinate. Experimental activation free energies that were themselves reconstructed from rates cannot serve as independent validation of those same rates.
   - Result: **COMPARATOR_MISSING**, highest contiguous state BARRIER_QUALIFIED.

6. **Barrier-only repository screen**
   - The three pinned resources collectively contain very large, high-quality barrier/energy benchmark collections.
   - None of the three is, as registered, a matched observed-rate database. Dataset size cannot substitute for a condition-matched independent kinetic comparator.
   - Result: **BARRIER_HALF_TRAIL_COMPARATOR_MISSING**, highest contiguous state BARRIER_QUALIFIED.

## Conglomerate result

The six trails do not produce six new Atlas coordinates. They produce a clearer result about what currently limits the Atlas.

**Barrier availability is not the primary bottleneck. The bottleneck is the complete physical evidence chain from a correctly typed barrier, through the correct elementary event or network, to an independent observed rate under matched conditions.**

The aggregate gate pattern is:

- source-qualified: 6/6
- candidate- or pool-level barrier evidence available: 6/6
- independent kinetic comparator qualified: 3/6
- condition matching fully closed: 1/6
- READY_FOR_ADJUDICATION: 1/6
- target-class refusal: 1/6
- comparator-missing half trails: 2/6
- condition/event-mapping holds: 2/6

The pattern is more informative than a simple success fraction because the failures occur at different scientific layers.

## What the six tell us together

### 1. Barrier-rich does not mean kinetics-rich

LiPRED and the barrier repositories make activation-energy evidence abundant. They do not automatically create independent rate tests. The scarce resource is a matched chain with explicit reaction identity, direction, state point, mechanism, kinetic order, standard state, and independent observation.

### 2. Direction is part of the observable

Trypsin-benzamidine demonstrates that association and dissociation cannot share evidence merely because they involve the same two species. `k_on` must be paired with an association barrier and `k_off` with a dissociation barrier. Reversibility does not erase directionality.

### 3. Mechanistic taxonomy is an evidentiary firewall

Cyclobutene is a high-quality negative result for the family-depth campaign. Its barrier may be excellent, but the reaction is electrocyclic/pericyclic. Refusing to relabel it as MC02 protects the ontology from goal-driven filling of empty cells.

### 4. A HOLD can be scientifically reversible

Cyclopropane is the clearest demonstration. The earlier HOLD was not a verdict that the reaction was unusable forever; it identified a specific unresolved multistep-mechanism problem. Later network-resolving theory directly addressed that reason, allowing the candidate to advance. This validates preserving HOLDs with explicit failure reasons instead of deleting them.

### 5. Some kinetics require network-resolved representation

Cyclopropane and the FOR enzyme both warn against treating every reaction as a single barrier plus one rate. A reaction network can contain intermediates, competing channels, internal barriers, binding steps, redox changes, and pressure dependence. The evidence architecture should therefore distinguish at least:

- `SINGLE_BARRIER_CLOSURE`
- `NETWORK_RESOLVED_CLOSURE`
- `BARRIER_HALF_TRAIL`
- `KINETIC_HALF_TRAIL`
- `CLASSIFICATION_MISMATCH`
- `CONDITION_OR_EVENT_MISMATCH`

These are evidence states, not new physical laws.

### 6. Evidence quality is multidimensional

The six-trail campaign argues against collapsing qualification into one score. At minimum, future candidate records should preserve orthogonal axes for:

1. barrier provenance and physical typing,
2. kinetic-comparator provenance and independence,
3. mechanism/classification alignment,
4. condition/state-point alignment,
5. representation topology: single-barrier versus network-resolved.

A strong result on one axis cannot compensate for a failure on another.

## What this does and does not support

This campaign supports a stronger **methodological** conclusion: family independence should be built by complete evidence chains, not by accumulating barrier values or condition replicas.

It does not adjudicate universality, does not establish a universal chemical boundary, does not alter the frozen v0.9 predicted-versus-observed results, and does not use chi or residual magnitude to select chemistry.

## Next actions

1. Independently adjudicate the cyclopropane MC06 network-resolved candidate for possible inclusion only in a new Atlas release.
2. Close the narrow condition record for trypsin-benzamidine rather than replacing the candidate.
3. For FOR, determine whether one experimentally resolved oxidation event can be mapped to the computed proton/two-electron-transfer step without conflating binding or active-site rearrangement.
4. Use LiPRED and barrier repositories only as candidate generators, then search outward from each selected reaction for primary raw kinetics.
5. Attack the remaining single-family classes with a two-sided search strategy: `barrier-first -> kinetics` and `kinetics-first -> independent barrier`, prioritizing whichever side of the evidence chain is missing.

The practical target remains unchanged: increase independent-family depth without changing Barrier_Height_Rate_Atlas_v0.9 or rewarding favorable agreement.
