# A12 Co2(CO)8 ground-state Markovian-control result

**Disposition:** PASSED NEGATIVE CONTROL / SIMPLE REGIME

Five linear-alkane solvents were frozen before calculation. Cyclohexane was excluded prospectively because the source shows a distinct static energetic effect there.

## Forward rate

Fit:
[
ln k_f = a + blneta
]

- slope b = **-0.79791**
- Pearson r = **-0.99518**
- Spearman rho = **-1.00000**
- LOO MSE = **0.0042938**
- LOO mean absolute log error = **0.05651**

## Reverse rate

- slope b = **-0.76814**
- Pearson r = **-0.99430**
- Spearman rho = **-1.00000**
- LOO MSE = **0.0045262**
- LOO mean absolute log error = **0.05878**

## Interpretation

This ground-state barrier-crossing series behaves as the intended simple-regime control: after the source establishes negligible barrier-energy variation across the linear alkane series, bulk viscosity alone captures the solvent dependence of both forward and reverse rates extremely well.

This is **not** an incremental Capital-Chi predictor success. It supports the architecture-level rule that a richer description should collapse to a simple bulk-friction/native-barrier model when memory, static energetics, and path organization do not require additional structure.

The fitted slopes are subunity in magnitude, consistent with the source's statement that the system is slightly below the ideal Smoluchowski limit.
