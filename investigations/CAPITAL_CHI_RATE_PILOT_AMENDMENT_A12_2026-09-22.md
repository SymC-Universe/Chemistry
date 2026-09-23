# Capital-Chi rate pilot amendment A12: ground-state Markovian control

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE REGRESSION CALCULATION

## Source reaction

Anna & Kubarych, *Watching solvent friction impede ultrafast barrier crossings: a direct test of Kramers theory*, J. Chem. Phys. 133, 174506 (2010), DOI 10.1063/1.3492724.

Reaction: ground-state interconversion of the two principal Co2(CO)8 isomers measured directly by 2D-IR chemical exchange.

## Control purpose

This is not a search for a richer Capital-Chi predictor. It is a **regime negative control**.

The source shows that across the linear alkane series:
- equilibrium energetics vary negligibly;
- DFT forward activation energies differ by only ~0.04 kcal/mol from hexane to decane;
- the observed rate change is attributed primarily to solvent friction;
- simple Markovian Kramers behavior is reported to describe the viscosity dependence.

If the Capital-Chi framing is useful as a rate-regime architecture, it must allow simple cases to remain simple rather than demand an extra descriptor everywhere.

## Frozen five-solvent dataset

Use only the linear alkanes, excluding cyclohexane prospectively because its static potential-energy surface differs measurably from the linear series.

Experimental forward rates from Table II:
- n-hexane: 0.093 ps^-1
- n-heptane: 0.077 ps^-1
- n-octane: 0.068 ps^-1
- n-decane: 0.041 ps^-1
- n-dodecane: 0.028 ps^-1

Experimental reverse rates, retained as a mirrored secondary test:
- n-hexane: 0.086 ps^-1
- n-heptane: 0.071 ps^-1
- n-octane: 0.064 ps^-1
- n-decane: 0.039 ps^-1
- n-dodecane: 0.027 ps^-1

Independent reference viscosities at 298.15 K (mPa s = cP):
- n-hexane: 0.2950
- n-heptane: 0.3832
- n-octane: 0.5088
- n-decane: 0.8493
- n-dodecane: 1.3580

## Frozen analyses

For forward and reverse rates separately:

1. fit
   [
   ln k = a + blneta;
   ]
2. report Pearson and Spearman correlations;
3. report fitted slope b;
4. leave-one-solvent-out log-linear MSE and mean absolute log error.

The qualitative Markovian-control expectation is a strong monotonic inverse relation. The slope is reported, not forced to -1.

## Interpretation rule

A strong viscosity-only result supports classification of this solvent series as a **simple bulk-friction-controlled regime**, not a positive incremental Capital-Chi predictor result.

A weak result would challenge that simple-regime interpretation and trigger inspection for omitted architecture.

No additional predictor will be added after seeing the result.
