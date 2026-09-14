# Chemistry source-of-record map

**Snapshot:** 2026-09-14  
**Purpose:** prevent branch/PR age, historical run text, or monitoring state from being mistaken for the current scientific source of record.

## Governing hierarchy

1. **Program-wide governance:** SymC General Operations Manual v0.8.0.
2. **Chemistry-local scientific governance:** `governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json` plus system/atlas-specific frozen protocols.
3. **Current program scientific status:** `PROGRAM_CLOSURE_STATUS_2026-09-04.md`, unless a later versioned adjudication explicitly supersedes a component.
4. **Live execution truth:** GitHub Actions live run state, not frozen prose in an older ledger or PR body.
5. **Historical execution/evidence:** frozen ledgers, artifacts, run records, and prior protocols remain immutable evidence of what occurred, but do not provide present-tense liveness.

## Open PR roles

### PR #1: `agent/na-cu001-run` -> `main`

Historical Na/Cu(001) bulk convergence harness. Its body describes an early 120-SCF matrix as future/current work. Do **not** use the body as current project status.

### PR #2: `agent/na-cu001-slab` -> `agent/na-cu001-run`

Historical stacked clean-slab gate. Its body describes a dependency on the early bulk run. Do **not** use it as current execution state.

### PR #3: `agent/na-cu001-integration` -> `agent/na-cu001-slab`

Primary integration/history branch containing the large corrected Na/Cu(001) program, later System 2/System 3/Barrier Atlas governance, and current local status records. The PR body itself contains stale execution language, so the branch files and later adjudication records outrank that body for current status.

A 2026-09-14 top-level PR comment records the liveness/status correction.

### PR #18: `governance/gom-v080-continuity-20260914` -> `agent/na-cu001-integration`

Current governance-only GOM v0.8.0 continuity/migration patch. It changes no frozen science. It remains draft and unmerged.

## System-specific branch note

`co-cu111-l17-prospective-extension` contains the 2026-09-05 closure-status commit `379988f9d5903852ba0c10400311b1b7039bc626` recording current scientific holds and closure path. The authoritative scientific content of that status file is also present on the integration lineage used by this governance audit.

## Current live execution rule

Immediately before PR #18 was opened, repository-wide GitHub Actions returned zero in-progress and zero queued workflows. PR #18 then triggered only the cheap `Program governance audit` workflow, which completed successfully. Neither fact authorizes a scientific restart.

## Supersession rule

Do not delete or rewrite the historical PRs merely because their prose is stale. Treat them as provenance. Current status must be inherited from later versioned adjudication records and live execution state.

Closing, retargeting, or merging the historical PRs is a separate repository-management decision and is not performed by this map.
