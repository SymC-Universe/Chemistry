# A20: Methanol/Cu(111) modal-matrix reproduction benchmark

**Date:** 2026-09-22  
**Status:** SOURCE-INFORMED REPRODUCTION / STRUCTURE TEST  
**Source:** Chen et al., *Vibrational control of selective bond cleavage in dissociative chemisorption of methanol on Cu(111)*, Nature Communications 2018.

## Epistemic status

Some source values were already exposed during literature triage before this file was frozen. Therefore A20 is **not** a blinded confirmatory test.

It is a reproduction/structure benchmark for the corrected modal-Capital-Chi definition.

## Scientific question

For a multichannel surface reaction, does the modal correspondence between a prepared reactant vibration and the competing transition-state reaction-coordinate vectors organize:

- which bond-breaking channel is preferentially promoted;
- relative vibrational efficacy;
- branching/selectivity at matched or similar total energy;

more directly than the scalar excitation energy alone?

## Capital-Chi object

For reactant vibrational mode i and reaction channel c:

[
P_{ic}=|Q_i cdot Q_{RC,c}|
]

where (Q_i) is the reactant normal-mode vector and (Q_{RC,c}) is the transition-state reaction-coordinate / imaginary-mode vector for channel c.

The full mode-by-channel matrix (P) is treated as a modal-Capital-Chi object.

No scalarization of (P) is required.

## Frozen analyses

Using every source mode/channel pair with exact tabulated values:

1. reconstruct the complete SVP/projection matrix;
2. record exact vibrational energies and source efficacy values;
3. map each prepared mode to its chemically corresponding bond-scission channel;
4. test whether the largest projection in a row identifies the source-reported selectively promoted channel;
5. compare same/similar-energy mode pairs to show what excitation energy alone fails to distinguish;
6. within comparable mode families, report association between projection onto the relevant channel and source vibrational efficacy where such a comparison is physically matched;
7. retain modes where projection and efficacy disagree.

## Controls

- excitation energy is kept as a separate scalar predictor/descriptor;
- translational excitation is not relabeled as a vibrational mode;
- overtone states are not treated as independent new normal-mode vectors; they retain the carrier identity of the underlying normal mode;
- no mode is removed because it weakens the relation;
- channel labels come from the source reaction pathways, not from the observed efficacy.

## Promotion ceiling

A20 can strengthen the empirical/modal interpretation that a mode-to-reaction-coordinate correspondence matrix contains chemically relevant information absent from scalar excitation energy.

Because the same study supplies both the dynamics and the SVP analysis, A20 remains source-level evidence, not independent P2 validation.
