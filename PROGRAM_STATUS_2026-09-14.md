# Chemistry Program Status

**Snapshot:** 14 September 2026  
**GOM:** SymC General Operations Manual v0.8.0  
**Source branch inherited:** `agent/na-cu001-integration` at `65a4a5104d32207e2014f8b5b694db544d35392e`  
**Purpose:** synchronize current execution state, scientific dispositions, and next permitted work without rewriting prior evidence.

## Current execution state

Repository-wide GitHub Actions checks on 14 September 2026 returned:

- `in_progress = 0`
- `queued = 0`

Therefore no GitHub Actions computation is currently running or queued in `SymC-Universe/Chemistry` at this snapshot. Old registry fields or monitoring records that describe completed workflows as `ACTIVE` are historical/stale execution descriptions and must not be interpreted as current computation.

This statement is scoped to GitHub Actions. It does not assert the absence of calculations running outside GitHub Actions.

## Current scientific state

### System 2: CO/Cu(111)

**Status:** `NUMERICAL_HOLD_EXTENSION_AUDIT`

The inherited 4 September closure record remains controlling. The L15 calculation completed and was mechanically acceptable, but the frozen L13-L15 surface-excess difference remained above the frozen `0.001 eV/surface atom` tolerance. The same-input rerun route is not scientifically capable of converting that result into PASS.

No adsorption-site ordering or downstream kinetic progression is authorized under the current frozen surface-convergence rule.

### System 3: H/Ru(0001)

**Status:** `CLEAN_SURFACE_NUMERICAL_HOLD`

The inherited layer ladder does not satisfy the frozen suffix convergence rule. Automatic adsorption progression remains prohibited.

The next physical decision remains scientific: prospectively authorize a bounded higher-layer extension before opening its results, or close this route at the current numerical HOLD.

### Barrier-Height/Rate Atlas v0.9

**Status:** `CLOSED_REPRODUCIBLE_V0.9`

The Atlas remains independently closed and does not depend on resolving either clean-surface HOLD. It should remain frozen for manuscript/reproducibility closure unless a separately justified new version is intentionally opened.

## Governance synchronization

`governance/IMPLEMENTATION_STATUS_v1.0.json` is preserved as historical deployment-state evidence. It is superseded for current execution-state reporting by `governance/IMPLEMENTATION_STATUS_v1.1.json` because several workflows that v1.0 called active have since completed.

Chemistry project-local safeguards removed from the program-wide GOM during consolidation are indexed in `governance/CHEMISTRY_PROJECT_GUARDRAILS.md`.

The exact migration review is `governance/CHEMISTRY_GOM_V0.8.0_MIGRATION_AUDIT_2026-09-14.md`.

## What can move now without a new scientific rung

Safe work is not exhausted by the numerical HOLDs. Work can continue on:

- status/provenance/CI synchronization;
- Barrier Atlas v0.9 manuscript and reproducibility closure;
- Function Map versus Limit Map coverage audit;
- foundational-dependency mapping and bounded robustness planning;
- native-comparator / `NO_NATIVE_COMPARATOR` records for intended future confirmatory claims;
- experimental-opportunity design and subsequent literature collision;
- linewidth/lifetime/friction provenance audits;
- claim-status, figure-prominence, and attribution/novelty audits;
- MFR-14 drafting for future P1 claims before decisive evidence is opened;
- stored-output information-loss, refusal, negative-control, mutation, and semantic-validation checks that do not change frozen rules;
- monitoring/watchdog coverage audit and stale control-surface cleanup;
- branch/PR/documentation rationalization.

A prioritized register is maintained in `governance/CHEMISTRY_NONCOMPUTE_WORK_REGISTER_2026-09-14.md`.

## What cannot move automatically

Do not silently launch or redefine:

- a deeper CO/Cu(111) convergence rung;
- a higher-layer H/Ru(0001) extension;
- a changed functional, pseudopotential, cutoff, k-mesh, geometry constraint, convergence tolerance, acceptance rule, reaction coordinate, kinetic model, or interpretation;
- a new physical system not already prospectively authorized;
- a post-result rescue of either current HOLD.

These require the ordinary prospective scientific-change path before affected results are opened.

## Current operational objective

Use the numerical HOLD interval productively: close what is already mature, remove stale state claims, map what is already learned on both the Function and Limit sides, and prepare the exact prospective records needed so the next authorized numerical or experimental rung can start without another administrative delay.