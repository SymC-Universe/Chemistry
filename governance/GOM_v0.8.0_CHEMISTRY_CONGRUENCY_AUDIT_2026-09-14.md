# Chemistry congruency audit against SymC General Operations Manual v0.8.0

**Date:** 2026-09-14  
**Scope:** governance, continuity, current-source-of-record hygiene, and non-science-changing project controls  
**Base branch inspected:** `agent/na-cu001-integration` at `65a4a5104d32207e2014f8b5b694db544d35392e`  
**Program baseline:** SymC General Operations Manual (GOM) v0.8.0, Definitive Active Baseline, 14 September 2026  
**Change class:** mechanical/governance documentation only  
**Scientific settings changed:** false  
**Thresholds changed:** false  
**Acceptance rules changed:** false  
**Hypotheses changed:** false  
**Interpretations changed:** false

## 1. Executive disposition

Chemistry is **substantively congruent** with the scientific core of GOM v0.8.0. No existing chemistry result is invalidated merely because the program manual was consolidated or renamed. Historical evidence remains governed by the scientific contract and freeze that applied when it was generated unless a later scientific result explicitly challenges it.

The required work is mainly migration integrity and source-of-record repair:

1. preserve chemistry-specific safeguards locally rather than assuming they remain in the program-wide GOM;
2. stop stale execution records from presenting completed work as active;
3. synchronize reader-facing status text with the already-adjudicated System 2 and System 3 HOLDs;
4. separate Function Map, Limit Map, and cross-component claims explicitly at manuscript/tool closure;
5. preserve the Barrier-Height/Rate Atlas as an independent frozen evidence product rather than reopening it merely because the prospective surface systems are unresolved;
6. apply GOM experimental-opportunity and literature-collision controls only to residual questions that still admit meaningful direct testing.

No current frozen scientific threshold is changed by this audit.

## 2. GOM v0.8.0 changes that matter locally

### 2.1 Migration integrity is now explicit

GOM v0.8.0 requires that a project-specific safeguard removed during program-manual consolidation have an identified local destination. Chemistry already contains strong local controls in `governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json`, including evidence immutability, preauthorization of scientific changes, fail-closed execution, no post-result retuning, chi semantic licensing, scalar/modal/system separation, literature-evidence requirements, and deployment-state verification.

**Disposition:** preserve those controls as chemistry-local authority. Do not delete them because the GOM is now leaner.

### 2.2 Program-wide and project-local authority must not be confused

The GOM is the transferable program-wide floor. Chemistry-specific equations, convergence thresholds, pseudopotentials, k-meshes, system definitions, barrier-atlas rules, and claim ceilings remain project-local. Existing frozen chemistry protocols therefore remain authoritative for the calculations they govern unless prospectively superseded.

**Disposition:** no retroactive rewriting of historical protocols to claim they ran under GOM v0.8.0.

### 2.3 `NO_NATIVE_COMPARATOR` is a documented exclusion state, not a forced benchmark

Where a frozen chemistry question has a true same-task native comparator, the strongest fair comparator remains required. Where a good-faith search finds no method addressing the same frozen task, the nearest plausible methods and reasons for exclusion are recorded; a full irrelevant benchmark is not required.

**Disposition:** add comparator-selection records at the claim level when the project reaches P1. Do not invent a weak or mismatched chemistry comparator merely to fill a field.

### 2.4 Function Map and Limit Map remain coequal

The present surface-convergence HOLDs are valuable Limit Map evidence, but chemistry cannot become a failure-only program. Functioning interiors, ordinary regimes, modal organization, and supported cross-component relations must be mapped where native science permits them.

**Disposition:** manuscript and tool closure should expose both maps. The current System 2 and System 3 HOLDs are preserved as limits, not hidden missing data.

### 2.5 Local dynamical identity and embedded reaction behavior remain distinct

Chemistry must continue to separate stable-mode damping morphology, barrier crossing, transmission/friction, and realized kinetic behavior. A local scalar or modal result does not automatically determine reaction rate, selectivity, commitment, or a whole-system scalar.

**Disposition:** retain the existing firewall between ChemSA stable-mode architecture and the Barrier-Height/Rate Atlas. Any bridge requires a separately frozen matching contract.

### 2.6 Active-run monitoring requires actual underlying execution

A monitor is not evidence that scientific compute exists. At this audit, repository-wide GitHub Actions returned zero `in_progress` runs and zero `queued` runs. Several older implementation records still describe runs as active even though their referenced workflows are terminal.

**Disposition:** treat those descriptions as stale liveness text, not current source of record. Before any new continuation, verify the live run identity first.

### 2.7 Reader-facing capability/status prose must be resynchronized

The branch README is scientifically much improved and correctly rejects universal reaction-rate chi claims, but its System 2 wording still calls the CO/Cu(111) program active rather than stating the adjudicated numerical HOLD. Older implementation-state prose also describes completed runs as active.

The public repository metadata description is additionally out of sync with the current program: it still says catalytic efficiency and reaction pathways are governed by a single stability ratio and identifies chi approximately 1 as optimal reactivity. That statement conflicts with the repository's own current README and closure record.

**Disposition:** correct reader-facing status text and flag the repository metadata description for owner-level update. No scientific inference changes; this is claim-language synchronization.

## 3. Current source-of-record reconciliation

### System 2: CO/Cu(111)

Current adjudicated state from `PROGRAM_CLOSURE_STATUS_2026-09-04.md`:

`NUMERICAL_HOLD_EXTENSION_AUDIT`

The five-cell L15 recovery completed, but the frozen L13-L15 surface-excess delta exceeded the frozen `0.001 eV/surface atom` tolerance. The HOLD cannot be converted into PASS by rerunning identical inputs. A deeper layer extension is a new scientific rung and therefore requires a prospectively frozen protocol plus explicit authorization.

### System 3: H/Ru(0001)

Current adjudicated state:

`CLEAN_SURFACE_NUMERICAL_HOLD`

The mechanical recovery succeeded, but the frozen suffix convergence rule failed. Adsorption progression remains blocked. The lawful choices remain terminal closure at the HOLD or a prospectively frozen bounded higher-layer extension.

### Barrier-Height/Rate Atlas v0.9

Current closure record treats v0.9 as an independently closed and reproducible frozen evidence product. It does not depend on resolving System 2 or System 3.

**GOM consequence:** do not reopen the Atlas merely because another branch is scientifically unresolved. A robustness challenge is warranted only when there is a material downstream dependency, a plausible legitimate vulnerability, and proportional opportunity.

## 4. Chemistry-local safeguards to retain explicitly

The following remain project-local and must not disappear during GOM consolidation:

- stable-well `omega_0` and barrier-top `omega_b` are not interchangeable;
- `chi = Gamma/(2 Omega)` is licensed only for the physical reduction that actually supports it;
- a barrier-top inverted coordinate does not inherit the stable-well critical-damping boundary;
- scalar, vector/modal, and conglomerate/system evidence are complementary starting representations, not an arithmetic decomposition of chi;
- reaction rate, barrier height, transmission, friction, damping morphology, and exceptional-point proximity remain distinct unless a frozen physical matching contract establishes a relation;
- independent Barrier Atlas family counting and evidence-grade rules remain local;
- System 2 and System 3 convergence thresholds, layer ladders, and acceptance rules remain frozen under their own protocols;
- failed/HOLD states remain visible and cannot be repaired by post-result threshold relaxation;
- independent reproduction cannot silently inherit optimization scratch when the local protocol defines it as independent.

## 5. Immediate changes authorized by this audit

These are mechanical/governance changes and may proceed without altering frozen science:

- add this GOM congruency record;
- add a non-compute closure queue distinguishing work that can proceed now from work blocked by science;
- synchronize README current-status prose to the adjudicated HOLDs;
- preserve a warning that older implementation registries contain stale liveness descriptions;
- flag the public repository metadata description as scientifically stale;
- keep current scientific HOLDs closed to automatic retry;
- keep the Barrier Atlas v0.9 frozen while manuscript/reproducibility closure proceeds;
- prepare, but do not execute, any new scientific extension protocol until explicit authorization.

## 6. Refusal boundary

This audit does **not** authorize:

- L17/L19 or any deeper System 2 layer extension;
- a higher System 3 layer ladder;
- changed convergence tolerances;
- new functionals, pseudopotentials, k-meshes, constraints, or solver settings;
- retuning toward chi approximately 1;
- treating a barrier frequency as a stable-well natural frequency;
- reopening a failed/HOLD gate as mechanical;
- claiming a universal reaction-rate optimum;
- merging a governance branch into production automatically.

Any such move is scientific or science-adjacent and must enter the ordinary frozen-change path.
