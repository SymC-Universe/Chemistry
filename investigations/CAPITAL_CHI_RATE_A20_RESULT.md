# A20 result: methanol/Cu(111) modal-matrix reproduction

**Source:** Chen et al., Nature Communications 2018, DOI 10.1038/s41467-018-06478-6.  
**Status:** source-informed empirical/computational modal reproduction.

## Modal matrix

The source supplies the reactant-mode to transition-state reaction-coordinate SVP matrix:

| mode | TS1 O-H | TS2 C-H | TS3 C-O |
|---|---:|---:|---:|
| nu1 O-H stretch | 0.869 | 0.033 | 0.013 |
| nu2 C-H as-stretch | 0.003 | 0.178 | 0.023 |
| nu9 C-H as-stretch | 0.003 | 0.515 | 0.087 |
| nu3 C-H s-stretch | 0.005 | 0.508 | 0.104 |
| nu8 C-O stretch | 0.026 | 0.015 | 0.745 |

The row maximum identifies the chemically corresponding selectively promoted channel for **5/5 listed stretching carriers**.

This is a matrix-valued modal correspondence object. It is not reducible to excitation energy.

## Similar-energy contrast

Four preparations are especially useful because their scalar excitation energies are tightly clustered:

- 1nu3 C-H: 2887 cm^-1
- 1nu9 C-H: 2935 cm^-1
- 3nu8 C-O: 2970 cm^-1
- 1nu2 C-H: 2979 cm^-1

Thus the full spread is only 92 cm^-1.

Yet the source mean vibrational efficacies across the five tabulated P0 levels are:

- 1nu2: 0.912
- 1nu9: 0.890
- 1nu3: 1.026
- 3nu8: 3.692

The C-O overtone therefore has about **3.60 times** the efficacy of the strongest of the three similarly energetic C-H preparations and about **3.92 times** their mean efficacy.

At matched total energy the source further reports that C-O excitation can change the C-O/C-H branching ratio by about **100-fold** relative to the ground-state preparation.

The scalar energy budget therefore cannot identify the realized channel response. The carrier identity and its projection into the transition-state modal directions are required.

## Projection versus efficacy

Using the five fundamental carrier identities and their source mean fundamental efficacies:

- Pearson r between relevant-channel SVP projection and mean efficacy = 0.574
- Spearman rho = 0.600

With only five heterogeneous carrier modes, neither association is statistically resolved and no regression claim is promoted.

That null/weak small-n correlation is important: **Capital Chi is not a claim that one projection scalar alone determines rate efficacy.** The informative object is the full modal correspondence structure together with the native energetics and channel.

## Channel structure

Transition-state barriers from the source are:

- TS1 O-H: 0.79 eV
- TS2 C-H: 1.12 eV (DFT; 1.13 eV PES)
- TS3 C-O: 1.32 eV (DFT; 1.34 eV PES)

The highest-barrier C-O channel can nevertheless be strongly promoted by excitation of the C-O carrier because that carrier has by far the largest projection onto TS3.

This is precisely the corrected rate question:

[
\text{kinetic response} =
F(\text{native barrier/channel energetics},\;\Chi_{modal},\;\text{other licensed dynamics})
]

rather than a function of scalar excitation energy alone.

## Boundaries

- same source supplies both dynamics and SVP analysis;
- state-selected dynamics are computational, not a new experimental validation;
- overtone 3nu8 is the same nu8 carrier at higher occupation, not a new normal mode;
- the five-mode projection/efficacy correlation is too small for a standalone predictive claim.

A20 strengthens the modal interpretation but does not establish a general rate law.
