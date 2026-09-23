# Capital-Chi rate pilot amendment A4: native-baseline identifiability gate

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE SYSTEMATIC FAMILY CLASSIFICATION

## Rationale

A kinetic residual cannot be interpreted as evidence for omitted Capital-Chi architecture when the preregistered native model is itself insufficiently identified. Several Atlas families contain prospectively retained method or model replicates. In some cases the spread among these physically plausible native predictions is as large as, or larger than, the nominal residual against experiment.

This amendment creates a diagnostic gate. It does not change the frozen native baseline and does not permit choosing the replicate that best matches experiment.

## Diagnostic quantities

For coordinates with at least one linked native-model rate replicate:

[
R_i = left|ln(k_{native}/k_{obs})ight|
]

and

[
S_i = max_j ln k_{j} - min_j ln k_{j},
]

where the set (j) contains the frozen native prediction and prospectively retained native-model/method sensitivity replicates. Experimental comparison-only replicates are excluded from (S_i).

Also record whether (k_{obs}) lies inside the native prediction envelope.

## Gate

A coordinate is labeled:

- **baseline_identifiable_for_residual_test** when the model-sensitivity record is narrower than the nominal discrepancy and does not itself make the sign/magnitude of the discrepancy indeterminate;
- **baseline_model_spread_dominates** when (S_i ge R_i);
- **baseline_envelope_contains_observation** when the observed rate lies inside the native prediction envelope;
- **baseline_identifiability_unknown** when no adequate model-sensitivity ensemble exists.

The two middle labels block promotion of a missing-Capital-Chi residual interpretation. They do not invalidate the coordinate for other scientific purposes.

## Restrictions

- The frozen native model remains the reported baseline. No replicate may replace it after seeing the observed rate.
- Model spread is a diagnostic of identifiability, not an uncertainty distribution unless the source explicitly licenses that interpretation.
- Absence of model replicates does not prove a baseline is well identified; it yields `baseline_identifiability_unknown`.
- This gate cannot by itself establish that Capital Chi predicts rate.

## Purpose

The gate separates two questions:

1. Is the native prediction sufficiently stable that its residual can diagnose missing physics?
2. If yes, does independently reconstructed Capital-Chi architecture explain that residual?

Question 2 is not asked when Question 1 is unresolved.
