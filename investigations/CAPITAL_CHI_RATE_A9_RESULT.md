# A9 result: modern simultaneous rotation/isomerization test

**Source:** Dobryakov et al., JACS 2024, DOI 10.1021/jacs.4c09134.  
**Primary solute:** trans-stilbene (tS).  
**Data:** 34 exact matched conditions, seven solvents, 283-323 K where available.  
**Status:** P1+ within-system matched-perturbation evidence.

## Frozen test

Target: y = -ln(tau_iso).  
Environment-coupling feature: x = ln(tau_R), measured independently in the same pump-probe scan.  
Temperature control: 1/T.

Models:
- T0 intercept only;
- T1 temperature only;
- X1 rotation only;
- TX temperature + rotation.

## Results

### Leave-one-condition-out
- T0 MSE = 0.2477902
- T1 MSE = 0.1624457
- X1 MSE = 0.1123738
- TX MSE = 0.1054551
- Delta MSE(X|T) = +0.0569906

### Leave-one-solvent-out
- T0 MSE = 0.2799638
- T1 MSE = 0.1953762
- X1 MSE = 0.1503747
- TX MSE = 0.1482310
- Delta MSE(X|T) = +0.0471452

Measured rotational dynamics therefore adds held-out predictive information beyond temperature alone, including when entire solvent identities are excluded from fitting.

## Within-solvent trajectories

All seven solvents show strong monotonic matched-condition relationships between tau_R and tau_iso. Absolute Pearson correlations range from 0.9743 to 0.9983; all Spearman coefficients are -1 within reported table precision.

The cross-solvent mapping is not perfect. In particular, held-out performance varies substantially by solvent. That heterogeneity is retained and argues against scalarizing the architecture.

## Bounded interpretation

Supported:

> Within this reaction system, a directly measured solute-environment dynamical timescale contributes kinetic information beyond temperature and transfers partially to held-out solvents.

Not supported:
- a universal or cross-reaction rate law;
- a scalar Capital-Chi coordinate;
- replacement of native photoisomerization theory;
- P2 cross-family validation.

## Next preregistered move

Use ttD from the same source as a related-solute internal replication under the identical T0/T1/X1/TX and leave-one-solvent-out design, frozen before calculation.
