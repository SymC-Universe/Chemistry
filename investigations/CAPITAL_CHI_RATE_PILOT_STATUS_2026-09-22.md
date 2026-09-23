# Capital-Chi Rate Pilot: Current Execution Status

**Branch:** `agent/capital-chi-rate-pilot-20260922`  
**Execution state:** pushed to current evidence ceiling  
**Manuscript state:** private working manuscript is not stored on this public Chemistry repository. Do not add manuscript source/PDF files to this repo.

## Scientific result stack

### Mechanistic floor
- Stage-0 non-Markovian benchmark: positive. Memory organization changes barrier-crossing kinetics while ordinary local barrier/friction scale is held fixed.
- Brünig-Netz-Kappler literature collision independently supports well/barrier memory and friction-regime dependence.

### Clean empirical negatives
1. beta-cyclodextrin: three frozen independent environment-reorganization features do not beat family calibration.
2. old S-DPB matched-solvent test: rotational reorientation does not outperform viscosity under the frozen non-leaky log-linear comparison.
3. A11 tS room-temperature cross-solvent panel: rotation does not improve viscosity and the joint model worsens held-out error.

These negatives are retained as constraints on Capital-Chi interpretation.

### Clean empirical positives
#### A9 tS, modern simultaneous rotation/isomerization
34 exact matched conditions, seven solvents.
Leave-one-solvent-out:
- temperature only: 0.195376 MSE
- temperature + measured rotation: 0.148231 MSE
- Delta MSE(X|T): +0.047145

#### A10 ttD related-solute replication
24 exact matched conditions, six solvents.
Leave-one-solvent-out:
- temperature only: 0.076707 MSE
- temperature + measured rotation: 0.015196 MSE
- Delta MSE(X|T): +0.061511

A10 is an internal related-solute replication from the same experimental source/platform.

### Mixed relational evidence
#### A11 room-temperature ttD
- viscosity only: 1.845178 MSE
- rotation only: 2.118536 MSE
- viscosity + rotation: 0.986531 MSE

Neither scalar descriptor is sufficient, while their relationship carries held-out information.

#### A12 exploratory ttD decomposition
Exploratory only:
- viscosity + rotation: 0.986531
- + dielectric constant: 0.062843
- + molar volume: 0.376876
- + dielectric + volume: 0.080360

This nominates, but does not confirm, the relational hypothesis:
**bulk friction + microscopic environment coupling + dielectric/polar response**.

### Independent-source bounded support
#### A14 50-solvent apolar molecular motor
- viscosity: 0.067695 LOO MSE
- viscosity + molecular weight: 0.050765
- modest improvement only.

The source independently concludes that solvent effects reflect a complex interplay and are not reducible to one or two generic solvent parameters.

#### A15 motor-specific diffusion reproduction benchmark
13 exact matched solvents:
- viscosity: 0.074634 LOO MSE
- motor-specific diffusion: 0.069770
- viscosity + diffusion: 0.103079

The solute-specific diffusion observable is slightly more predictive than bulk viscosity, but combining both worsens prediction because of overlapping information.

A15 reproduces an already reported source ranking and is therefore consistency/reproduction evidence, not blinded confirmation.

## Quarantined or blocked lanes

### A6 Angulo 2017
P0-Q blocked. Excellent no-fit architecture design, but exact SI numeric tables are unavailable through current retrieval routes. Exact SI filename: `draft_si9rev.pdf`.

### A7 metallocene
Numeric extraction quarantined as provisional P0-Q because sparse-table OCR can drop blank cells and misalign columns. Qualitative source conclusion remains usable; numeric pilot result is not promoted.

### A8 Dahl/Biswas/Maroncelli 2003
Main/SI kinetic table is partially available and article identity is verified. Exact independent rotational table cannot currently be recovered cleanly through available tools. Keep as resumable independent-source candidate.

### A13 Dalton/Kiefer/Netz 2024
P0-Q blocked for the preregistered numeric memory-kernel regression because exact Supplementary Table 2 / Zenodo parameter bytes are not reachable through current retrieval routes. Main paper strongly supports the mechanistic premise but does not satisfy the exact-data gate.

## Current evidence ceiling

### Supported now
1. Whole-system/environmental dynamical organization can alter reaction kinetics in ways a local scalar or bulk property can miss.
2. In one modern experimental platform, directly measured rotational/environment coupling adds held-out kinetic information beyond temperature for tS and replicates in related ttD.
3. At fixed temperature across solvents, a single environment descriptor is not generally sufficient.
4. Independent-source evidence is consistent with solute-specific environment dynamics being at least as informative as, and sometimes more informative than, bulk viscosity.
5. The emerging useful object is relational architecture, not a single Capital-Chi rate scalar.

### Not supported yet
- a scalar Capital-Chi rate coordinate;
- a general absolute rate law;
- P2 independent-source predictive validation of the A12 relational feature set;
- a claim that adding more Capital-Chi features always improves prediction;
- manuscript-level promotion of Capital Chi as a general rate predictor.

## Hard next gate

To move beyond P1/P1+ we need a genuinely independent source with exact matched:
- target reaction kinetics;
- bulk friction/viscosity;
- microscopic solute/environment dynamical observable;
- dielectric/polar environmental descriptor;
- enough conditions for held-out validation;
- no target-derived calibration.

The exact A12 relational feature set must be frozen before that target is inspected.

## Operational privacy rule

`SymC-Universe/Chemistry` is currently **public**.

Repository search found no current ChemSA R4/ChiArchitecture manuscript source or working-manuscript filenames in this repo. Therefore:
- investigation artifacts may remain on this branch;
- **do not commit current manuscript .tex/.pdf or submission-ready manuscript source to this public repository**;
- if manuscript GitHub storage is needed, use or create a private repository first.

## Resume rule

At the next execution session:
1. read `CAPITAL_CHI_RATE_CHECKPOINT.md`;
2. do not rerun A9-A15 unless a provenance defect is discovered;
3. resume blocked source retrieval or locate a new independent matched dataset;
4. preregister the exact test before calculating it;
5. keep manuscript files off the public Chemistry repo.
