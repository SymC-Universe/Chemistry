# Capital-Chi rate pilot amendment A1: baseline-overlap firewall

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE RESIDUAL ASSOCIATION TESTING  
**Parent preregistration:** `CAPITAL_CHI_RATE_PILOT_PREREG_2026-09-22.md`

## Rationale

Full-text eligibility extraction showed that several physically meaningful Capital-Chi features are already explicit inputs or factors in the native predicted rate. Counting those variables again as an incremental Capital-Chi predictor would double-count information and could create a trivial apparent improvement.

This amendment therefore adds a mandatory **baseline-overlap status** to every candidate Capital-Chi feature.

## Feature status

Every extracted feature must be assigned exactly one of:

1. **incremental_independent**  
   Independently determined architecture information that is not already used in the preregistered native rate prediction and is not derived from the target observed rate. Only this class may enter M2/M3 residual-prediction tests.

2. **baseline_embedded**  
   Physically valid architecture information that is already used explicitly or implicitly in the native predicted rate (examples: a tunneling coefficient multiplied into the native rate, a transmission/recrossing coefficient used by the native Kramers calculation, an electronic coupling already used in the native ET rate). This class may be used for rate-regime classification and architecture description but not claimed as incremental predictive information.

3. **target_leaking**  
   Any feature fitted, reconstructed, selected, or calibrated using the held-out observed target rate. This class is excluded.

4. **unresolved_overlap**  
   It cannot be established whether the feature is independent of the native prediction or target outcome. This class is excluded from predictive tests until resolved.

## Additional allowed conglomeration features

The following are explicitly admitted as candidate **incremental_independent** features when independently computed/measured and not already included in the native rate model:

- solvent/environment reorganization measures;
- released/retained solvent counts;
- solvent or host entropy decomposition;
- independently characterized host/catalyst conformational organization;
- active-species/resting-state population or speciation;
- independently characterized path multiplicity/topology;
- global slow-mode/metastable organization not used to calculate the native rate.

These additions clarify the original conglomeration/system layer; they do not redefine Capital Chi as a scalar.

## Consequence for current pilot candidates

- Morphinone reductase recrossing and tunneling factors: **baseline_embedded** for incremental-rate purposes.
- Porphycene channel fractions/tunneling factors: **baseline_embedded** in the instanton total rate.
- Koczor-Benda ET electronic coupling, barrier, and frequency factor: **baseline_embedded** in the native ET prediction, though useful for regime classification.
- Campeggio SN2 barrier-local friction/recrossing: **baseline_embedded** in its Kramers-rate prediction.
- Beta-cyclodextrin water release, water entropy, host-water organization, and pathway class: potentially **incremental_independent** relative to the q4MD-CD association-rate baseline, subject to exact extraction and feature freeze before residual testing.
- Pd/PCy3 speciation/pathway organization: potentially **incremental_independent** only to the extent it is not already folded into the selected barrier/rate baseline.

No outcome correlation may be used to change these labels.
