# HCN-HNC Native Modal-Chi Checkpoint

**Date:** 2026-09-23
**Branch:** `agent/capital-chi-rate-pilot-20260922`
**Rowan folder UUID:** `4459e358-6eec-4a64-a964-0f08addfcc8b`

## Frozen preregistration
`HCN_HNC_MODAL_CHI_PREREG_2026-09-23.md`
commit: `4b25cefc501c40c4b9f085bf5a36a6c798730256`

## Active Rowan workflows

### HCN R0 optimize + frequencies
- workflow UUID: `042c5369-54c1-4626-ba3d-8f3709e2e4de`
- preset: `organic_nnp`
- tasks: optimize, frequencies
- max credits: 4
- status at checkpoint: running

### HNC R0 optimize + frequencies
- workflow UUID: `cf1a011d-e312-4950-8250-3df1b709febc`
- preset: `organic_nnp`
- tasks: optimize, frequencies
- max credits: 4
- status at checkpoint: running

## Exact resume action

1. query both workflow UUIDs;
2. if complete, retrieve optimized structures and frequency/mode results;
3. require stable minima before TS progression;
4. create double-ended HCN/HNC TS search from the validated optimized endpoints;
5. frequency-check the TS and require one imaginary mode;
6. if supported, run IRC;
7. construct reactant-to-TS modal correspondence with the additive Capital-Chi adapter;
8. do not use any rate value to choose/rotate modes.

## Stop rule

Do not promote a full native Capital-Chi record until exact modal vectors/subspaces and TS connectivity are available.


## R1 TS search draft

- workflow UUID: `c2653b1c-5fc8-49ca-8f24-9b465bdb01bf`
- name: `HCN_HNC_R1_TS_same_method`
- workflow type: `double_ended_ts_search`
- method: `aimnet2_wb97md3`
- engine: `aimnet2`
- optimized R0 endpoints used directly
- optimize_inputs: false
- optimize_ts: true
- max credits: 6
- status at this checkpoint: draft
- hardware class: A100_40GB

### R1 acceptance gate

Do not promote the returned structure merely because the search terminates.
The candidate must pass a same-method frequency calculation with exactly one physically relevant imaginary mode, followed by endpoint connectivity validation if IRC is available.


## R1 completed / R2 frequency-validation draft

R1 double-ended search:
- workflow UUID: `c2653b1c-5fc8-49ca-8f24-9b465bdb01bf`
- status: completed_ok
- credits: 0.46
- candidate TS energy: -93.410584 Hartree
- search-returned frequencies: -2006.267, 2268.267, 3420.304 cm^-1
- disposition: candidate only pending separate R2 validation
- exact R1 candidate committed in `hcn_hnc_R1_ts_candidate.json`

R2 fixed-geometry same-method frequency validation:
- workflow UUID: `1d723abc-d91a-4a36-9be5-0fb93dabcf4e`
- preset: organic_nnp / AIMNet2
- task: frequencies
- max credits: 3
- status at checkpoint: draft

Acceptance remains exactly one physically relevant imaginary mode.
