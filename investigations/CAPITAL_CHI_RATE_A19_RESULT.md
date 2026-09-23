# A19 empirical modal-Capital-Chi benchmark: deuterated methane on Pt(111)

**Source:** Hundt et al., J. Phys. Chem. A 2015, DOI 10.1021/acs.jpca.5b07949.  
**Status:** source-result reproduction / empirical modal benchmark.

## Modal object

The source independently computes Sudden Vector Projection (SVP) values as overlaps between reactant normal-mode vectors and the transition-state reaction-coordinate vector.

For each isotopologue, the resulting projection matrix is a direct modal/vector object:

[
P_{ic}=|Q_i\cdot Q_{RC,c}|.
]

This is treated here as an empirical example of modal Capital Chi.

It is not a scalar chi.

## Exact source values used

### CH3D

- nu1 projection onto C-H cleavage coordinate: 0.44
- nu4 projection onto C-H cleavage coordinate: 0.38

Measured state-resolved sticking coefficients at Ts=150 K and Et=24 +/- 4.5 kJ/mol:

- nu1: (2.2 +/- 0.5) x 10^-3
- nu4: (1.8 +/- 0.2) x 10^-3

Projection ratio nu1/nu4 = 1.158.

Measured reactivity ratio nu1/nu4 = 1.22 +/- 0.31.

### CH2D2

- nu1 projection onto C-H cleavage coordinate: 0.57
- nu6 projection onto C-H cleavage coordinate: 0.48

Measured sticking coefficients:

- nu1: (2.02 +/- 0.09) x 10^-3
- nu6: (1.47 +/- 0.07) x 10^-3

Projection ratio nu1/nu6 = 1.188.

Measured reactivity ratio nu1/nu6 = 1.374 +/- 0.090.

## Bond-selective structure

The source projection matrix also distinguishes competing C-H and C-D reaction-coordinate modes.

For CH3D:
- nu1: 0.44 onto C-H versus 0.04 onto C-D
- nu4: 0.38 onto C-H versus 0.01 onto C-D

For CH2D2:
- nu1: 0.57 onto C-H versus 0.04 onto C-D
- nu6: 0.48 onto C-H versus 0.02 onto C-D

Experiment observes C-H bond-selective dissociation for the prepared C-H stretch states.

## Interpretation

This is direct empirical support for the corrected modal framing:

> reactivity depends on how a prepared vibrational mode projects into the reaction-coordinate mode at the transition state.

A scalar energy/frequency description alone does not encode that orientation/correspondence.

The comparison is small and source-aware:
- only two within-isotopologue mode pairs are quantitatively comparable here;
- CH3D nu1 is reconstructed from mixed eigenstate analysis in the source and therefore has more model dependence than the directly prepared CH2D2 states;
- the same paper both measures reactivity and computes SVP values, although the modal projections are derived from DFT transition-state/normal-mode calculations rather than fitted to the sticking coefficients.

## Capital-Chi consequence

A practical chemistry Capital-Chi representation can therefore include a **mode-to-reaction-coordinate projection matrix**, not merely eigenvalues or scalar damping values.

Scalar chi_i, when licensed, remains attached to each mode separately.

The modal projection/correspondence matrix is information that scalar chi_i does not contain.
