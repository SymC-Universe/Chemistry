# Capital-Chi rate pilot amendment A3: intercept-only residual control

**Date:** 2026-09-22  
**Status:** POST-FIRST-PASS DESIGN CORRECTION; FROZEN BEFORE RECALCULATION

## Why this amendment is required

The first preregistered beta-CD calculation revealed that all seven native q4MD-CD association-rate residuals have the same sign. A leave-one-out linear feature model contains an intercept, so it can improve strongly over the raw native residual predictor r_hat=0 even when the feature itself carries no useful information.

Therefore the original baseline comparison cannot isolate the incremental contribution of a Capital-Chi feature from a simple family-wide calibration offset.

This is a design correction, not a feature-selection change. All three frozen features remain mandatory and no new feature is introduced.

## Added control

For every leave-one-out fold, add an **intercept-only family calibration**:

[
hat r_{cal} = ar r_{training}.
]

The Capital-Chi feature model remains:

[
hat r_{Chi} = a + b x.
]

Report three errors:

1. raw native baseline: r_hat = 0;
2. intercept-only family calibration: r_hat = mean(training residual);
3. Capital-Chi feature model: r_hat = a + b x.

The decisive incremental quantity for the beta-CD P1 test is now:

[
Delta MSE_{Chi|cal} = MSE_{calibration} - MSE_{Chi-feature}.
]

Only positive Delta MSE_(Chi|cal) supports incremental within-family predictive information from the feature.

The original raw-baseline comparison is retained in the record but is no longer sufficient for a Capital-Chi result.
