# A11 result: room-temperature cross-solvent panel

**Source:** Dobryakov et al., JACS 2024, DOI 10.1021/jacs.4c09134.  
**Status:** mixed P1 evidence.

## tS

Complete conditions: n=12.

LOO MSE:
- intercept: 0.1626606
- viscosity: 0.1217117
- rotation: 0.1310321
- viscosity + rotation: 0.1922655

Disposition: **negative for incremental rotation beyond viscosity**. Adding rotation worsens held-out prediction.

## ttD

Complete conditions: n=14.

LOO MSE:
- intercept: 1.9318270
- viscosity: 1.8451776
- rotation: 2.1185364
- viscosity + rotation: 0.9865314

Disposition: **mixed/architecture-positive**. Rotation alone does not beat viscosity, but the joint viscosity + rotation model reduces held-out error by 0.8586462 relative to viscosity alone.

## Interpretation

A11 argues against treating a single environmental timescale as a general rate coordinate.

For tS, bulk viscosity is at least as useful as measured rotational time and the joint model overfits/worsens prediction.

For ttD, neither viscosity nor rotation alone is sufficient, while their relationship carries substantial held-out information. This is consistent with the source's own observation that molecular-size and solvent-polarity effects generate systematic deviations from simple viscosity scaling.

The ttD joint-model result is retained as P1 mixed evidence, not promoted to a new confirmatory Capital-Chi feature because the importance of the joint structure became apparent after executing the frozen A11 comparison.
