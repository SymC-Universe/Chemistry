# A15 result: motor-specific diffusion reproduction benchmark

**Source:** Lubbe et al., PCCP 2016, DOI 10.1039/C6CP03571J.  
**Exact matched subset:** 13 solvents with unambiguous Table-2 DOSY-NMR diffusion values and Table-1 ln(k), ln(eta).  
**Status:** source-result reproduction benchmark.

## Predictive results

LOO MSE:
- intercept = 0.121942
- viscosity = 0.074634
- motor-specific diffusion = 0.069770
- viscosity + diffusion = 0.103079

Associations:
- ln(k) vs ln(eta): Pearson -0.674; Spearman -0.764
- ln(k) vs ln(D): Pearson +0.708; Spearman +0.797

The motor-specific diffusion descriptor slightly improves held-out prediction over viscosity alone and shows stronger monotonic/linear association. Combining the two worsens prediction, consistent with substantial information overlap and small-sample collinearity.

## Interpretation

This reproduces the source's reported ordering using a predictive score rather than correlation alone. It supports the bounded proposition that a solute-specific environment-coupling observable can be more kinetically informative than a bulk property.

Because the source already reported this qualitative ranking, A15 is not blinded independent confirmation of Capital Chi. It is cross-source mechanistic/empirical consistency evidence.
