# Validated Substrate Inheritance Contract v0.1

**Status:** active architectural contract; CO/Cu(111) certificate remains conditional on numerical PASS of the current L17 convergence gate.

**Purpose:** define what a future validated clean-surface calculation may be reused for, what it may not be reused for, and why. This contract changes no electronic-structure setting, convergence threshold, or scientific result.

## 1. What is inherited

A clean-surface numerical PASS certifies only the tested substrate representation under its pinned computational model. For CO/Cu(111), a future PASS would allow downstream calculations that preserve the validated scope to inherit the conclusion that the clean Cu(111) substrate is adequately represented with the qualified slab thickness, vacuum treatment, reciprocal-space resolution, bulk reference, exchange-correlation method, pseudopotential family, electrostatic boundary treatment, and surface-relaxation convention.

The expensive clean-substrate thickness/vacuum/k-point qualification therefore does not need to be repeated merely because a new compatible adsorbate or reaction is placed on the same validated Cu(111) model.

Inheritance means reuse of the **substrate qualification certificate and its provenance**. It does not mean that all Cu coordinates are frozen forever. Downstream adsorbate calculations may relax the atoms permitted by their own prospectively defined protocol.

## 2. Why inheritance is bounded

A convergence test demonstrates that the reported clean-surface quantity is sufficiently insensitive to the artificial numerical boundaries that were varied within one specified physical and electronic-structure model. It does not demonstrate invariance to changing the Hamiltonian, the surface identity, the electrostatic environment, the thermodynamic state, the lateral adsorbate interaction, or the reaction coordinate.

Accordingly, a substrate certificate is transferable only while the assumptions that made the convergence result meaningful remain materially unchanged.

## 3. Cases that do not inherit the clean Cu(111) certificate automatically

The clean Cu(111) qualification must not be treated as an automatic certificate for any of the following:

- a different material, such as Ru, Pt, Pd, Au, an alloy, or an oxide;
- a different Cu facet or morphology, including Cu(001), Cu(110), stepped or vicinal surfaces, defects, terraces, or reconstructed surfaces;
- a different exchange-correlation functional, pseudopotential family/valence treatment, dispersion treatment when it changes the modeled surface response, relativistic treatment, spin treatment, or other material change to the electronic-structure model;
- a different electrostatic model, including a changed ESM/dipole treatment, charged slab, applied field or electrode potential, explicit solvent, or another boundary condition that changes surface-image interactions;
- a materially strained, alloyed, oxidized, reconstructed, high-coverage, subsurface-penetrated, or otherwise strongly perturbed Cu(111) state for which the clean-surface model is no longer the same physical state;
- lateral supercell or coverage convergence. Clean-slab thickness convergence does not establish that periodic adsorbate images are noninteracting in a chosen adsorption cell;
- an adsorbate-specific k-point claim merely by copying the primitive-cell integer mesh. Downstream supercells must preserve an appropriate reciprocal-space resolution and satisfy any prospectively required adsorption-energy or barrier sensitivity check;
- adsorption-site ordering, adsorption energy, minimum-energy paths, NEB image convergence, saddle forces, barrier height, Hessians, vibrational frequencies, transmission factors, friction, damping, rate constants, or ChemSA eligibility. These are adsorbate-, coordinate-, and/or dynamical-object-specific quantities and require their own evidence gates;
- a finite-temperature, solvent, potential, charge, coverage, or phase regime that changes the physical surface state beyond the validated clean-surface representation.

## 4. Reuse rule for compatible downstream entries

A downstream entry may inherit the validated substrate certificate when all substrate-defining fields that materially support the certificate match the certified model, while entry-specific quantities are generated or sourced through their own frozen gates.

The intended workflow is therefore:

`validated substrate certificate` -> `new compatible adsorbate/reaction` -> `entry-specific numerical/physical gates` -> `Atlas record`

rather than:

`new adsorbate` -> `repeat the entire clean-substrate convergence campaign`.

## 5. Fail-closed transfer rule

If a downstream calculation changes a substrate-defining assumption or produces evidence that the inherited clean-surface representation may no longer bound the modeled state, inheritance is held rather than silently extrapolated. The affected numerical dimension is then requalified prospectively; already valid, unaffected evidence remains reusable.

This rule is deliberately narrower than 'same element and Miller index.' Same Cu(111) is necessary for direct clean-surface inheritance, but it is not sufficient if the physical or computational model has materially changed.

## 6. Relation to the Barrier-Rate Atlas and ChemSA

Substrate inheritance removes repeated upstream numerical qualification. It does **not** promote a coordinate into the Barrier-Rate Atlas and does not make it ChemSA-eligible. Atlas admission still depends on the evidence contract for the barrier/rate record, and ChemSA classification still depends on an independently licensed dynamical object and any required coordinate/dissipation provenance.

This separation is intentional: a reusable substrate is infrastructure, not a reusable chemical conclusion.

## 7. CO/Cu(111) status

The current CO/Cu(111) L17 calculation is testing whether the clean-surface certificate can be issued under the frozen PBE numerical contract. Until that gate returns PASS, the reusable Cu(111) certificate is **PENDING** and must not be represented as established.