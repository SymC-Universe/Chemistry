# A14 result: 50-solvent apolar-motor counter-test

**Source:** Lubbe et al., PCCP 2016, DOI 10.1039/C6CP03571J.  
**Data:** all 50 exact room-temperature Table-1 solvent/mixture rows.  
**Status:** P1 cross-source bounded support.

LOO MSE:
- intercept only = 0.123058
- viscosity only = 0.067695
- viscosity + molecular weight = 0.050765
- Delta MSE(MW|eta) = +0.016930

The improvement from molecular weight is modest. The full two-predictor design is more conditioned than viscosity alone, so this does not justify a new general predictor.

The source's independent analysis agrees with the broader interpretation: viscosity dominates within many solvent groups, but whole-dataset behavior reflects multiple solvent-solvent and solvent-solute properties. The paper explicitly concludes that the solvent effect is governed by a complex interplay rather than one or two universal solvent parameters.

Disposition: bounded cross-source support for relational environment effects, not confirmation of the A12 ttD dielectric architecture.
