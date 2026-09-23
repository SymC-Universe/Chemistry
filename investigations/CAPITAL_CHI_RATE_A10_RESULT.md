# A10 result: ttD related-solute replication

**Source:** Dobryakov et al., JACS 2024, DOI 10.1021/jacs.4c09134.  
**Solute:** trans,trans-diphenylbutadiene (ttD).  
**Data:** 24 exact matched conditions, six solvents, 293-323 K.  
**Status:** P1+ internal replication of A9 architecture effect.

## Frozen validation result

### Leave-one-condition-out
- T0 MSE = 0.1916969
- T1 temperature-only MSE = 0.0644730
- X1 rotation-only MSE = 0.0806303
- TX temperature + rotation MSE = 0.0101204
- Delta MSE(X|T) = +0.0543526

### Leave-one-solvent-out
- T0 MSE = 0.1992281
- T1 temperature-only MSE = 0.0767073
- X1 rotation-only MSE = 0.0903695
- TX temperature + rotation MSE = 0.0151959
- Delta MSE(X|T) = +0.0615114

Every solvent shows a strong monotonic within-solvent relation between measured rotational and isomerization times. Absolute Pearson correlations range from 0.9731 to 0.9992; Spearman rho = -1 for all six trajectories at reported precision.

## Interpretation

The A9 finding replicates in a distinct related solute measured on the same platform: measured environment-coupling dynamics adds held-out kinetic information beyond temperature alone, including when entire solvent identities are held out.

This remains internal/source-level replication, not independent-source P2 validation.
