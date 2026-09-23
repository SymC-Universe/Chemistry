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
