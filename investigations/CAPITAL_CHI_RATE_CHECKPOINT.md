# Capital-Chi Rate Investigation Checkpoint

**Branch:** `agent/capital-chi-rate-pilot-20260922`  
**Checkpoint updated:** 2026-09-22 late execution block  
**Policy:** update after every substantive execution block.  
**Manuscript:** private and untouched by this investigation. No manuscript promotion has been made.

## Frozen governance

Committed before the corresponding tests:
- base preregistration;
- A1 baseline-overlap firewall;
- A2 Stage-0 / beta-CD test;
- A3 intercept-only calibration control;
- A4 native-baseline identifiability gate;
- A5 S-DPB matched-solvent test;
- A6 no-fit non-Markovian ET test;
- A7 metallocene solvent-relaxation test;
- A8 DPB solvent-class test;
- A9 modern matched tS test;
- A9A temperature-confounding control;
- A10 ttD related-solute replication;
- A11 room-temperature cross-solvent test;
- A12 post-A11 exploratory solvent-architecture decomposition.

## Completed results

### Stage 0 controlled memory benchmark
Positive mechanistic sanity result: changing memory organization with the local barrier/friction scale held fixed changes crossing kinetics strongly. Model evidence only.

### beta-CD P1
**Negative.** Three frozen independent environment-reorganization features fail to beat leave-one-out family calibration.

### old S-DPB matched-solvent P1
**Negative.** Independently measured rotational reorientation does not outperform bulk viscosity under the frozen non-leaky log-linear comparison.

### A6 Angulo 2017
**P0-Q blocked.** Strong no-fit architecture design, but exact supplementary numeric tables are in separate file `draft_si9rev.pdf`, unavailable through current retrieval routes. No figure digitization performed.

### A7 metallocene
**Numeric result quarantined / provisional P0-Q.** OCR of sparse Table II drops blank cells and can misalign columns. Do not cite the provisional positive calculation until visually aligned source table is recovered. Qualitative source trend remains valid.

### A9 tS modern matched dynamics
**P1+ positive within-system.** 34 exact matched conditions across seven solvents.

Leave-one-solvent-out:
- temperature-only MSE = 0.1953762
- rotation-only MSE = 0.1503747
- temperature + measured rotation MSE = 0.1482310
- Delta MSE(X|T) = +0.0471452

Measured environment-coupling dynamics adds held-out information beyond temperature.

### A10 ttD related-solute replication
**P1+ positive internal replication.** 24 exact matched conditions across six solvents.

Leave-one-solvent-out:
- temperature-only MSE = 0.0767073
- rotation-only MSE = 0.0903695
- temperature + measured rotation MSE = 0.0151959
- Delta MSE(X|T) = +0.0615114

### A11 room-temperature cross-solvent panel
**Mixed.**

tS:
- viscosity MSE = 0.1217117
- rotation MSE = 0.1310321
- viscosity + rotation MSE = 0.1922655
- negative incremental result.

ttD:
- viscosity MSE = 1.8451776
- rotation MSE = 2.1185364
- viscosity + rotation MSE = 0.9865314
- relational architecture improves prediction, but neither single descriptor does.

### A12 exploratory decomposition
**Hypothesis generation only. No promotion.**

tS:
- richer dielectric/size architecture does not beat viscosity alone.

ttD:
- viscosity + rotation = 0.986531 MSE
- + dielectric constant = 0.062843 MSE
- + molar volume = 0.376876 MSE
- + dielectric + volume = 0.080360 MSE

A12 nominates a future confirmatory architecture:
**bulk friction + microscopic environment coupling + dielectric/polar response.**

## Current inference ceiling

Supported:
1. whole-system dynamical organization can materially alter kinetics;
2. directly measured environment-coupling dynamics adds held-out kinetic information beyond temperature in tS and replicates in ttD within one modern experimental platform;
3. a single dynamical descriptor is not generally sufficient;
4. ttD room-temperature data nominate a relational architecture involving bulk friction, microscopic coupling, and dielectric response.

Not supported:
- scalar Capital Chi rate coordinate;
- general cross-reaction rate law;
- P2 independent-source predictive validation;
- manuscript-level claim that Capital Chi predicts rates generally.

## Current active target

**Independent-source confirmation of the A12 relational hypothesis.**

Required evidence:
- target kinetic observable;
- independently measured bulk friction/viscosity;
- independently measured microscopic solute/environment dynamical descriptor;
- independently tabulated dielectric/polar response;
- enough matched conditions for source/condition holdout;
- none derived from target rate.

Priority:
1. Dahl/Biswas/Maroncelli 2003 DPB nonpolar-solvent data if exact rotation table can be recovered without OCR ambiguity;
2. independent electron-transfer/solvation-dynamics dataset with reaction and solvent-relaxation observables measured separately;
3. independent modern/open dataset satisfying the same feature firewall.

## Exact next action

Continue external-source search and extraction. The next confirmatory test must be preregistered before target/predictor calculation. If no dataset supplies the required independent matched variables, stop at P1/P1+ and record that the evidence ceiling is data availability rather than analytical incompleteness.

## Resume rule after interruption

Open this file first. Continue from **Current active target**. Do not rerun completed A9-A12 calculations unless a source/provenance defect is discovered.
