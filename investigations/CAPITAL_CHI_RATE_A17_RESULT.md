# A17 local modal benchmark result

**Status:** controlled modal-mechanism benchmark; not an empirical rate law.

## Frozen scalar inventory

- frequencies: 400 and 1800 cm^-1;
- mixed-mode displacements: zero;
- solvent reorganization energy: 3000 cm^-1;
- temperature: 78 K;
- energy gap: 12000 cm^-1;
- same initial/final frequency spectrum.

Only the Duschinsky modal basis matrix J(theta) changes.

## Numerical result

The two-mode harmonic Franck-Condon calculation converges to unit total overlap probability for all tested angles. At the largest 80 x 40 final-state truncation:

| theta | FC probability sum | rate proxy | log10(rate/rate_0) |
|---:|---:|---:|---:|
| 0 | 0.9999999999999996 | 8.43e-52 | 0 |
| 5 | 1.0000000000000002 | 1.71e-9 | 42.31 |
| 10 | 1.0 | 3.47e-7 | 44.62 |
| 20 | 0.9999999999999997 | 4.44e-5 | 46.72 |
| 30 | 0.9999999999999997 | 5.44e-4 | 47.81 |
| 45 | 0.9999999999999969 | 3.50e-3 | 48.62 |
| 60 | 0.9999999999902444 | 5.09e-3 | 48.78 |

## Interpretation

The absolute enhancement is intentionally **not compared numerically to Sando et al.'s Figure 10**. This minimal model omits the paper's other unchanged displaced modes, so the unmixed inverted-region baseline is far smaller and the resulting ratio is correspondingly much larger.

What the benchmark establishes is narrower and cleaner:

> Holding the scalar mode frequencies, displacements, solvent broadening, temperature, and energy gap fixed while changing only the modal basis J(theta) drastically redistributes Franck-Condon weight and changes the kinetic rate proxy.

This is a direct controlled demonstration that modal information can carry kinetic content not present in the scalar inventory.

## Capital-Chi consequence

For this benchmark, Capital Chi is the changing modal correspondence matrix J(theta) together with the indexed basis it maps. Scalar chi-like information is not being asked to encode that rotation.

This satisfies the first modal-rate mechanism target but remains below empirical promotion.
