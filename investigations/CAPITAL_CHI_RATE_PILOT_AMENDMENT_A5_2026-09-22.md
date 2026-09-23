# Capital-Chi rate pilot amendment A5: matched-solvent microscopic-friction test

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE RECOMPUTING ASSOCIATIONS

## Source system

Stiff diphenylbutadiene (S-DPB) isomerization in the homologous n-alkane solvent series from n-pentane through n-hexadecane, using the experimental data reported by Lee et al. (J. Chem. Phys. 1986, DOI 10.1063/1.451806) and the tabulated S-DPB rotational reorientation data reproduced by the same experimental lineage.

This is an external empirical P1 test, not part of Barrier-Height/Rate Atlas v0.9.

## Why it is eligible

Across the solvent series:
- the reacting solute is unchanged;
- the experiment reports solvent-dependent fluorescence lifetimes from which the study obtains the nonradiative/isomerization rate;
- bulk solvent viscosity is independently tabulated;
- rotational reorientation time of the same solute is independently measured by polarization spectroscopy and is not inferred from the target isomerization rate;
- the published work reports breakdown of simple Stokes-Einstein-Debye scaling and motivates rotational dynamics as a microscopic solvent-coupling proxy.

The measured rotational reorientation is treated here as a **conglomeration/environment-coupling feature**, not as scalar mechanical chi.

## Frozen data contract

Solvents: n-pentane through n-hexadecane, 12 conditions.

Rate target:
[
k_{iso}=1/\tau_f-k_r
]
using the source's fixed radiative rate (k_r=6.2\times 10^8\;s^{-1}) and source fluorescence lifetime (	au_f).

Control feature:
- (eta): bulk solvent viscosity, cP.

Capital-Chi environment feature:
- (	au_R): independently measured S-DPB rotational reorientation time, ps.

The Hubbard-derived angular-velocity correlation frequency is not required for the primary statistical comparison because it is proportional to (	au_R) at fixed solute inertia and temperature. The paper's fitted proportionality factor and fitted barrier-frequency parameters are **excluded**.

## Frozen test

Transform target and predictors logarithmically.

For each predictor separately:
1. Pearson correlation with (ln k_{iso});
2. Spearman rank correlation;
3. leave-one-solvent-out linear prediction:
   [
   ln k_{iso}=a+b\ln x
   ]
   fitted only on the 11 training solvents;
4. calculate LOO MSE.

Primary comparison:
[
Delta MSE_{micro|bulk}=MSE_{\ln\eta}-MSE_{\ln\tau_R}.
]

Positive values support incremental predictive information from the independently measured microscopic environment-coupling descriptor relative to bulk viscosity.

## Promotion limit

Because the fluorescence lifetime, viscosity, and rotational measurements are reported at slightly different nearby temperatures (approximately 19-24 C, with viscosity tabulated at 20 C), this test is capped at **P1 within-family empirical evidence**. It cannot establish P2 cross-family rate prediction.

No fitted Kramers barrier frequency, proportionality parameter, or target-rate-derived feature may be used to rescue or improve the result.
