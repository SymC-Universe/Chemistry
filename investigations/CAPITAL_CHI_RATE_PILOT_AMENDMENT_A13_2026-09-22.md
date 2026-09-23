# Capital-Chi rate pilot amendment A13: independent memory-kernel mechanistic replication

**Date:** 2026-09-22  
**Status:** FROZEN BEFORE NUMERIC EXTRACTION

## Source

Dalton, Kiefer, and Netz, *The role of memory-dependent friction and solvent viscosity in isomerization kinetics in viscogenic media*, Nature Communications (2024), DOI 10.1038/s41467-024-48016-7.

## Purpose

A13 is an **independent-source mechanistic replication**, not empirical P2 validation.

The source directly extracts time-dependent friction memory kernels from molecular dynamics for several isomerizing molecules under different viscogenic conditions and reports corresponding isomerization kinetics.

## Frozen question

Does a descriptor of **frequency/time-dependent friction architecture** explain kinetic variation that bulk solvent viscosity alone does not?

## Frozen variables

For every source condition with exact tabulated or deposited values:
- target: log isomerization time or log rate;
- control: log bulk viscosity;
- microscopic descriptor: independently extracted integrated/zero-frequency friction if source-tabulated;
- memory descriptor: a source-defined memory timescale or equivalent normalized memory measure if source-tabulated.

Do not invent a new memory scalar from curves if the source does not tabulate one exactly.

## Frozen models

Within each molecule/media series where sufficient exact points exist:
- M0 intercept only;
- M1 viscosity only;
- M2 source microscopic friction only;
- M3 viscosity + microscopic friction;
- M4 viscosity + microscopic friction + source memory descriptor, only if the descriptor is exact and independently extracted.

Use leave-one-condition-out prediction. If multiple media classes exist, also report leave-one-medium-class-out only when sample size permits.

## Restrictions

- No values digitized from plots if deposited/tabulated values are not available.
- No friction quantity inferred from the target isomerization rate.
- No source-fit kinetic correction is reused as a predictor.
- No model promoted from A13 beyond mechanistic/P1 support.
- A13 cannot satisfy the independent empirical P2 gate because the target kinetics come from simulation.

## Interpretation target

A positive A13 result would support the mechanistic component of the emerging relational architecture:

> bulk environment + microscopic friction + memory organization can carry kinetic information not reducible to bulk viscosity.

A null result remains a cross-source counterexample.
