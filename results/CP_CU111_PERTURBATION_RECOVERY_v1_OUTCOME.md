# Cp/Cu(111) perturbation-recovery v1 frozen outcome

**Preregistration:** `preregistration/CP_CU111_PERTURBATION_RECOVERY_v1.md`  
**Scientific freeze:** `a2b51ee7e3f9449578a67368ac58f45d475aee08`  
**Execution freeze:** `7dec19e35596d332ac0e15384859e138997e43a9`  
**Frozen implementation:** `639529e90ad3637468575191dd7fcab5e9cffa08`  
**Outcome status:** decisive v1 production outcome preserved without retuning.

## Execution note

The all-in-one production command exceeded the execution wrapper's 120 s ceiling after writing three of the four deterministic frozen ensemble artifacts. No scientific parameter or seed changed. The missing fourth ensemble was resumed independently with the frozen implementation and frozen seed, then the unmodified frozen adjudication function was run over all four preserved ensembles. This is mechanical resume only.

## Frozen adjudication

### CP-PR-01 - local recovery invariance

**FALSIFIED under the v1 rule.**

- + perturbation: RMS difference = 0.0833675227; bootstrap 95% = [0.0677320953, 0.1212967285]; upper 95% = 0.1212967285 > 0.05.
- - perturbation: RMS difference = 0.1009073834; bootstrap 95% = [0.0701849308, 0.1431243120]; upper 95% = 0.1431243120 > 0.05.
- sign-symmetry RMS, 40 meV = 0.0455473907 <= 0.05.
- sign-symmetry RMS, 55 meV = 0.0557746980 > 0.05.
- both embeddings retain at least one local-response zero crossing.

No threshold is changed and no narrower window is substituted.

### CP-PR-02 - embedding-dependent global kinetics

**SURVIVES the frozen v1 test.**

- 40 meV: D = 0.6249924387 A^2/ps; median FPT = 1.903 ps; censored fraction = 0.005625.
- 55 meV: D = 0.3772508062 A^2/ps; median FPT = 3.2485 ps; censored fraction = 0.0449375.
- bootstrap 95% CI log(D55/D40) = [-0.5422859656, -0.4707678832], entirely below 0.
- bootstrap 95% CI log(median FPT55/median FPT40) = [0.5123964141, 0.5561066189], entirely above 0.

### CP-PR-03 - full preregistered joint chi-X result

**FALSIFIED under the v1 conjunctive rule** because CP-PR-01 failed even though CP-PR-02 passed.

The result must not be redescribed as a preregistered pass.

## Raw artifact hashes

- `b40_s+1.npz`: `772d628ddebaed14fed2b105939c51eff773c83d81d20e78e6b2bd3ffb05a40c`
- `b40_s-1.npz`: `98394f20caa21dfa7e4d169d1be031287c2ceb6eebf1536ab3e6c7bd8ae26962`
- `b55_s+1.npz`: `7f3629c6b1129e1109a16394c25c0166a5543e56f9220ab2fbfe16c0831f1785`
- `b55_s-1.npz`: `b99b72dc615b61d568a238ef895f15585355c22cdd5f288d4855f5b58876b024`
- `result.json`: `896fa66e940388d5463d0a3c45b93bed71afaaa388c2af23f47c0888d0c7ebfe`

## Post-result observation, not part of frozen adjudication

The realized normalized local response differs already at t=0:
- + perturbation: 40 meV = 0.5420791; 55 meV = 0.6747554.
- - perturbation: 40 meV = 0.6151312; 55 meV = 0.7286726.

Because both embeddings have the same local curvature, damping coefficient, temperature, mass, and local chi, this points to the finite-temperature equilibrium population and broader potential shape as a plausible source of the failed local-invariance prediction. This interpretation is post-result discovery and carries promotion debt. It does not convert CP-PR-01 or CP-PR-03 into passes.

A future v2 may test a baseline-subtracted/conditional linear-response observable or a deeper-well conditioned ensemble, but only under a new preregistration and new decisive trajectories.
