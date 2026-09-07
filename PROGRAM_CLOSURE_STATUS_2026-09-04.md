# Chemistry program closure status

**Snapshot:** 2026-09-04 America/Chicago  
**Branch:** `agent/na-cu001-integration`  
**Purpose:** Consolidate the current evidentiary state and prevent further mechanical rerun loops from being mistaken for scientific progress.

## Current execution state

At this snapshot, no GitHub Actions workflow is actively running on the branch. Monitoring alone must not be interpreted as active scientific computation.

## System 2: CO/Cu(111)

**Current status:** `NUMERICAL_HOLD_EXTENSION_AUDIT`  
**Last adjudication run:** `33712992505`  
**Scientific settings changed during recovery:** no  
**Threshold changed:** no

The five-cell PAW-safe L15 recovery completed the numerical work and reproduced the relaxed L15 energy with an absolute fixed-SCF/relax difference of approximately `1.36e-7 eV`. The recovered structure was mechanically acceptable (`max movable force ~= 0.01815 eV/A`).

The frozen extension audit nevertheless failed:

- L13 reference surface excess: `0.47680671935813734 eV/surface atom`
- L15 extension surface excess: `0.4779404346481897 eV/surface atom`
- absolute L13-L15 delta: `0.0011337152900523506 eV/surface atom`
- frozen tolerance: `0.001 eV/surface atom`
- prior L11-L13 delta: `0.001572865239722887 eV/surface atom`

Therefore the clean-surface model is not numerically closed under the frozen convergence rule. Adsorption-site ordering and downstream kinetic progression remain blocked. A rerun with the same inputs cannot convert this result into PASS. Any further layer extension would require a new prospective scientific protocol before additional results are inspected.

## System 3: H/Ru(0001)

**Current status:** `CLEAN_SURFACE_NUMERICAL_HOLD`  
**Last adjudication run:** `33389260021`  
**Failed gate:** `layer_stage`  
**Scientific settings changed during recovery:** no  
**Threshold changed:** no

The mechanical timeout recovery succeeded and produced ten valid QE cases. The frozen layer ladder was `[5, 7, 9, 11, 13]` with terminal reference L13 and a `0.001 eV/surface atom` tolerance.

Absolute layer deltas to the L13 terminal value were:

- L5: `0.006105622814175149 eV/surface atom`
- L7: `0.00023748736930429004 eV/surface atom`
- L9: `0.002743519986324827 eV/surface atom`
- L11: `0.003122234460533946 eV/surface atom`
- L13: `0`

Although L7 itself lies within tolerance of L13, the frozen suffix rule requires the candidate and every finer/larger point to remain within tolerance. L9 and L11 violate that requirement, so no eligible non-terminal layer demonstrates convergence. Automatic adsorption progression is forbidden by the frozen protocol.

A simple rerun is not scientifically justified. Further work requires either a prospectively frozen layer extension or terminal closure as a numerical HOLD.

## Barrier-Height/Rate Atlas v0.9

The v0.9 release is independently closed and reproducible as a frozen evidence product:

- 61 physical coordinates
- 26 reaction families
- 18/18 operational classes
- 67 sources
- environment floor achieved without Grade-A inflation
- v0.9 release validator PASS
- 131/131 dependency-free adversarial checks
- 113/113 Atlas pytest suite
- 138/138 focused ChemSA boundary suite
- workbook verification PASS with 228 formulas and zero cached formula errors
- clean-room archive verification PASS

This release does not depend on resolving the current System 2 or System 3 clean-surface holds.

## Current interpretation boundary

The repository now explicitly separates stable-mode damping architecture from barrier crossing. It does not treat `chi = Gamma/(2 Omega)` as a universal reaction-rate coordinate, a barrier-top critical point, or a universal commitment optimum. Barrier height, reaction rate, damping morphology, transmission, friction, and exceptional-point proximity remain distinct unless a separately frozen physical matching contract establishes a relation.

## Closure path

1. Do not rerun either current HOLD as if it were a mechanical failure.
2. Treat CO/Cu(111) as terminal under the presently frozen L15 extension unless a new prospective extension is scientifically authorized.
3. Make one explicit program-level decision for H/Ru(0001): either freeze a bounded higher-layer extension before execution or close the branch as `CLEAN_SURFACE_NUMERICAL_HOLD`.
4. Keep Barrier Atlas v0.9 frozen for manuscript closure rather than making publication depend on additional family-depth expansion.
5. Update the manuscript and reproducibility package to report the computational HOLDs as negative/limit results, not missing data and not hidden failures.
6. Do not allow monitoring jobs to be described as active computation when no scientific workflow is running.

This status record changes no scientific assumption, threshold, numerical setting, or interpretation. It only consolidates already adjudicated evidence and defines the permitted closure decisions.