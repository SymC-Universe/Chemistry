# A12 exploratory result: solvent-architecture decomposition

**Source:** Dobryakov et al., JACS 2024, DOI 10.1021/jacs.4c09134.  
**Status:** exploratory hypothesis generation only.

## Frozen exploratory models

B1 = viscosity.  
B2 = viscosity + measured rotational time.  
P = viscosity + rotation + dielectric constant.  
V = viscosity + rotation + molar volume.  
PV = viscosity + rotation + dielectric constant + molar volume.

All quantities are source-tabulated and independent of tau_iso.

## tS

LOO MSE:
- B1 viscosity = 0.121712
- B2 viscosity + rotation = 0.192265
- P + dielectric = 0.132051
- V + molar volume = 0.127237
- PV = 0.177468

None of the richer architectures beats viscosity alone. This reinforces the A11 negative result for tS at room temperature.

## ttD

LOO MSE:
- B1 viscosity = 1.845178
- B2 viscosity + rotation = 0.986531
- P viscosity + rotation + dielectric = 0.062843
- V viscosity + rotation + molar volume = 0.376876
- PV all four = 0.080360

The three-part viscosity + microscopic rotation + dielectric model produces the lowest exploratory held-out error. Adding molar volume to all three slightly worsens prediction and increases conditioning concerns.

## Interpretation

The post-A11 exploratory result nominates a specific relational architecture for independent testing in ttD-like solution barrier crossing:

> bulk friction + directly measured microscopic solute-environment coupling + dielectric/polar environmental response.

This architecture is **not promoted** from A12 because it was motivated after observing A11 heterogeneity. It is a preregistration target for a new independent source/system only.

The tS result is an important counterexample: the richer architecture is not generically better, which argues against treating additional Capital-Chi features as automatically predictive.
