# Capital-Chi A7 disposition: barrier-corrected metallocene solvent dynamics

**Date:** 2026-09-22  
**Parent:** Amendment A7  
**Disposition:** **P1 POSITIVE ARCHITECTURE EVIDENCE; HISTORICAL WITHIN-FAMILY REANALYSIS**

## Source

McManis et al., J. Am. Chem. Soc. 1989, 111, 5533-5541, DOI 10.1021/ja00197a004.

Table II reports experimental self-exchange rates corrected for solvent-dependent free-energy barrier variation using independently measured optical electron-transfer/barrier information, normalized to acetonitrile. The same table reports independently characterized longitudinal solvent-relaxation rates normalized to acetonitrile.

The electronic matrix-coupling values later inferred by the authors from the rate-vs-relaxation dependence were **not used as predictors**.

## Primary result

Using every recovered Table-II pair under the preregistered log-space leave-one-solvent-out comparison, solvent relaxation adds different amounts of predictive information depending on the redox couple.

The source-defined Debye-solvent sensitivity analysis is the cleanest physical comparison because the paper explicitly states that simple longitudinal relaxation is not an adequate descriptor for PC, methanol, ethanol, and strongly hydrogen-bonded NMF.

### Debye-only held-out performance

| redox couple | n | full-fit slope | barrier-only MSE | dynamics LOO MSE | Delta MSE | fractional MSE reduction |
|---|---:|---:|---:|---:|---:|---:|
| CpPrime2Co | 5 | 0.687 | 3.7467 | 0.3398 | +3.4068 | 90.9% |
| Cpe2Co | 7 | 0.821 | 3.1416 | 0.3580 | +2.7836 | 88.6% |
| Cp2Co | 7 | 0.503 | 1.9585 | 0.3121 | +1.6464 | 84.1% |
| CpPrime2Fe | 5 | 0.182 | 0.3176 | 0.0471 | +0.2705 | 85.2% |
| HMFc | 6 | 0.247 | 0.2432 | 0.1276 | +0.1156 | 47.5% |
| Cp2Fe | 6 | 0.086 | 0.1123 | 0.1322 | -0.0199 | -17.7% |

The absolute improvement for CpPrime2Fe and HMFc is much smaller than for the cobalt couples because their barrier-corrected residual variation is already small. Cp2Fe is a clean null/negative case.

## Robustness to approximate relaxation ratios

The source reports the propionitrile and nitromethane normalized relaxation ratios approximately. Removing those two conditions leaves the central cobalt result intact:

- CpPrime2Co: 90.9% held-out MSE reduction;
- Cpe2Co: 86.0%;
- Cp2Co: 80.4%.

Cp2Fe remains negative.

## Interpretation

A7 supports a **relational Capital-Chi interpretation**, not a one-variable rate law.

After independent energetic-barrier correction, the same environment-level dynamical coordinate carries strong kinetic information for some redox-carrier architectures and little or no useful information for others.

Thus the result is not simply:

> faster solvent relaxation -> faster rate.

The empirically relevant statement is:

> the kinetic value of the environmental dynamical layer depends on the carrier/electronic architecture in which that environment is embedded.

This is the first completed empirical pilot in this investigation that matches the intended Capital-Chi structure:

[
	ext{barrier/energetics} leftrightarrow 	ext{environment dynamics} leftrightarrow 	ext{carrier architecture} ightarrow 	ext{kinetic behavior}.
]

## Limits

- This is a historical reanalysis and therefore capped at P1.
- Some Table-II entries required recovery of column identity from OCR-scrambled public text. Assignments were accepted only where the raw Table-I values, source Eq. 6 barrier correction, and Table-II rounded ratio mutually reconciled; unresolved values were not invented.
- The electronic-coupling hierarchy in the source is partly inferred from the same kinetic dependence and therefore cannot serve as independent validation of the Capital-Chi carrier layer.
- The result does not establish a scalar Capital-Chi coordinate, absolute cross-family rate prediction, or replacement rate theory.

## Next required promotion

A P2 result requires an independent reaction family or prospective dataset in which:
1. energetic/native inputs are fixed independently;
2. environment/carrier architecture is measured independently of target kinetics;
3. the architecture improves held-out prediction or correctly selects the rate-controlling regime;
4. family/source holdout prevents lineage leakage.
