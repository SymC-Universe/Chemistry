# Capital-Chi rate pilot amendment A11: solvent-controlled proton-transfer cross-family test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE ASSOCIATION/PREDICTION CALCULATION

## Source reaction

Pérez-Lustres et al., *Ultrafast Proton Transfer to Solvent: Molecularity and Intermediates from Solvation- and Diffusion-Controlled Regimes*, JACS 129 (2007) 5408-5418, DOI 10.1021/ja0664990.

The reaction target is excited-state proton transfer from 6-hydroxyquinolinium (6HQc) to protic solvent.

## Frozen conditions

Only the five genuinely protic solvents are admitted:

| solvent | mean solvation time <tau_solv> (ps) | mean 6HQc PT time <tau_PT> (ps) | solvation probe/source in Table 2 |
|---|---:|---:|---|
| water | 0.42 | 1.14 | MQz/NM6HQ-family solvation response |
| methanol | 4.0 | 7.0 | MQz/NM6HQ-family solvation response |
| ethanol | 11 | 10 | MQz/NM6HQ-family solvation response |
| 1-propanol | 26 | 18 | Coumarin 153 |
| 1-butanol | 40 | 26 | Coumarin 153 |

Acetonitrile is excluded **before analysis** because the source states that excited-state proton transfer is strongly suppressed there; its spectral relaxation cannot be treated as the same PT target.

## Predictor independence

The source constructs C(t) from an independently measured solvent relaxation observable and compares it with the distinct 6HQc proton-transfer response S(t). For propanol and butanol, C(t) is measured with Coumarin 153. For the faster protic solvents the source uses the separately characterized quinolinium solvation reporter. No C(t) parameter is fit to the 6HQc PT time for this comparison.

Because the solvation probe provenance is mixed, this dataset is capped at P1 and cannot by itself establish P2.

## Frozen bulk-viscosity control

Use independent room-temperature liquid viscosities (cP) fixed before the comparison:

- water: 0.89
- methanol: 0.55
- ethanol: 1.08
- 1-propanol: 1.94
- 1-butanol: 2.57

These values are used only as a coarse bulk-friction control. The exact solvent-relaxation values come from the reaction source itself.

## Frozen target and predictors

Target:
[
y=lnlangle	au_{PT}angle.
]

M0 bulk proxy:
[
x_0=lneta.
]

M1 Capital-Chi environment descriptor:
[
x_1=lnlangle	au_{solv}angle.
]

## Frozen analyses

With n=5:

1. Pearson correlation;
2. Spearman rank correlation;
3. leave-one-solvent-out linear prediction in log space;
4. LOO MSE;
5. LOO mean absolute log error.

Primary contrast:
[
Delta MSE_{solv|visc}=MSE_{lneta}-MSE_{ln	au_{solv}}.
]

Positive values favor the independently measured environment-relaxation descriptor.

## Robustness restriction

Because n=5 is small, no post-hoc outlier deletion, nonlinear fit, class indicator, or feature addition is permitted. The result is reported exactly as obtained.

## Promotion ceiling

- Positive: independent cross-chemistry **supporting P1** only.
- Null/negative: retained as a cross-family null.
- Never sufficient for P2 by itself.
