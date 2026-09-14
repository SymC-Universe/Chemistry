# Chemistry GOM v0.8.0 Migration Audit

**Date:** 14 September 2026  
**Branch lineage audited:** `agent/na-cu001-integration` at `65a4a5104d32207e2014f8b5b694db544d35392e`  
**Program manual:** SymC General Operations Manual v0.8.0, Definitive Active Baseline  
**Authoritative GOM Markdown SHA-256:** `ee3d9955e19f280ad385488180800d1cdb2d5054823cfa2fa6a697ab3f51d396`  
**Change class:** governance/documentation synchronization only

## Scientific-change firewall

- `scientific_settings_changed = false`
- `thresholds_changed = false`
- `acceptance_rule_changed = false`
- `kinetic_inputs_used = false`
- `hypothesis_changed = false`
- `interpretation_changed = false`
- `prior_failure_preserved = true`
- `prospective_before_new_results = true`

No numerical HOLD, convergence threshold, physical model, barrier/rate coordinate, chi definition, exceptional-point classification, or frozen system protocol is changed by this audit.

## 1. Version and authority reconciliation

The program-level governing document is now the **SymC General Operations Manual (GOM)**. Legacy references to the General Cross-Project Research Protocol or GP are historical aliases unless a historical version is explicitly named.

Chemistry should therefore cite GOM v0.8.0 as its current program manual while retaining older protocol names in immutable historical records where they were correct at the time.

No historical evidence file is rewritten merely to modernize terminology.

## 2. Migration-integrity result

GOM v0.8.0 intentionally keeps program-wide transferable rules in the central manual and moves project-specific equations, datasets, atlas targets, implementation details, and claim ceilings to project-local governance.

Chemistry already contained most of the necessary safeguards across `README.md`, system protocols, the Barrier Atlas, and `governance/SCIENTIFIC_CHANGE_CONTROL_PROTOCOL_v1.1.json`, but they were distributed rather than indexed as the explicit project-local destination required by the GOM migration-integrity rule.

**Action:** created `governance/CHEMISTRY_PROJECT_GUARDRAILS.md` as the local safeguard index. It adds no new scientific gate and points back to the more specific frozen sources that remain controlling.

## 3. Current operational-state defect discovered

`governance/IMPLEMENTATION_STATUS_v1.0.json` still describes several August workflows as `ACTIVE` even though their recorded GitHub Actions runs have completed. That file was accurate as a deployment snapshot when created, but is no longer an accurate current execution registry.

The stale status is material because GOM v0.8.0 requires source-of-record execution state, monitoring state, and prose capability claims to remain synchronized.

**Disposition:** preserve v1.0 as historical evidence and supersede it with a new v1.1 current-state registry rather than rewriting the old snapshot.

## 4. Current execution check

At the 14 September 2026 audit, repository-wide GitHub Actions queries returned:

- in-progress runs: `0`
- queued runs: `0`

Therefore no Chemistry GitHub Actions computation is currently running or queued. Monitoring or an old `ACTIVE` registry field must not be described as active scientific computation.

This does not imply that every external/local calculation is absent; it is specifically the verified GitHub Actions state for this repository at audit time.

## 5. Current scientific dispositions preserved

The audit inherits, without changing, the dated closure record in `PROGRAM_CLOSURE_STATUS_2026-09-04.md`:

- CO/Cu(111): `NUMERICAL_HOLD_EXTENSION_AUDIT`
- H/Ru(0001): `CLEAN_SURFACE_NUMERICAL_HOLD`
- Barrier-Height/Rate Atlas v0.9: independently closed and reproducible

A workflow-level `success` from a mechanical or checkpoint chain does not override a later scientific HOLD.

## 6. GOM v0.8.0 changes material to Chemistry

### 6.1 Project-local safeguards must remain local and auditable

Chemistry-specific stable-well versus barrier-top rules, linewidth/damping conditions, Atlas family rules, substrate-inheritance constraints, and system-specific claim ceilings stay in Chemistry. They are not copied wholesale back into the GOM.

### 6.2 `NO_NATIVE_COMPARATOR` is an exclusion result, not a fake benchmark

For a future confirmatory chemistry claim, a good-faith frozen search must identify the strongest native comparator for the same frozen task. If no method answers that task, record `NO_NATIVE_COMPARATOR` plus the nearest methods considered and the reason each is not task-equivalent. Do not run irrelevant methods merely to manufacture a benchmark.

### 6.3 Function Map and Limit Map remain coequal

The recent numerical convergence work is rich in limit information. Chemistry must not let numerical HOLDs make the research program failure-only. Supported operating behavior, modal organization, coupling, inheritance, information loss, and ordinary occupied regimes remain coequal mapping targets where the native science permits.

### 6.4 Foundational dependencies require proportional robustness

When a result becomes a foundation inherited by later systems or claims, passing its minimum gate is not automatically enough. A bounded robustness challenge is appropriate when a plausible vulnerability could materially change downstream interpretation. Successful robustness work stops when the declared vulnerability is resolved; it does not create an endless compute ladder.

### 6.5 Directly testable questions trigger an experimental-opportunity pass

Chemistry contains questions that admit direct physical testing. Before proposing new fabrication or measurement, first sketch the experiment from native science without searching for a preferred outcome, then perform a targeted literature collision to determine whether the question is already answered. Only the residual question should proceed toward a new prospective experiment.

### 6.6 Attribution follows residual contribution

The mature ChemSA claim should remain the smallest defensible residual contribution after native chemistry, spectroscopy, modal analysis, non-Hermitian/EP methods, reaction-rate theory, and prior SymC work are accounted for. Citation volume cannot substitute for a precise novelty boundary.

## 7. Safe work authorized without reopening science

The following can proceed while numerical systems are on HOLD:

1. synchronize execution-status registries, README, PR descriptions, and monitoring records;
2. preserve the September HOLDs in manuscript/reproducibility status tables;
3. audit Function Map versus Limit Map coverage;
4. build foundational-dependency maps for the ChemSA Engine, Barrier Atlas, and substrate-inheritance bridge;
5. draft native-comparator or `NO_NATIVE_COMPARATOR` search records for intended confirmatory claims;
6. run the experimental-opportunity pass and then targeted prior-experiment literature collisions;
7. audit linewidth/lifetime/friction evidence provenance without changing frozen coordinates;
8. audit manuscript claim status, figure prominence, and nearest-prior-art attribution;
9. draft MFR-14 records for future P1 chemistry claims without opening decisive evidence;
10. run stored-output information-loss, refusal, negative-control, mutation, and semantic-validation audits that do not alter frozen rules;
11. package/revalidate Barrier Atlas v0.9 and ChemSA reproducibility assets without changing scientific content;
12. rationalize stale branches/PR descriptions and monitor coverage.

## 8. Work that still requires a new scientific decision

The following are not silently authorized by this migration:

- any deeper CO/Cu(111) numerical rung beyond the currently adjudicated extension;
- a higher-layer H/Ru(0001) extension versus terminal HOLD closure;
- changes to functional, pseudopotential, cutoff, k-mesh, geometry constraints, convergence threshold, acceptance rule, or kinetic model;
- reinterpretation of a numerical HOLD as a PASS;
- assigning a barrier-top `chi = 1` critical point;
- treating a proxy, linewidth, or reaction-rate coordinate as a mechanical damping ratio without the required license;
- promotion of a new empirical or mechanistic claim without its required frozen evidence path.

## 9. Immediate synchronization package

This audit accompanies:

- `governance/CHEMISTRY_PROJECT_GUARDRAILS.md`
- `governance/IMPLEMENTATION_STATUS_v1.1.json`
- updated `governance/verify_implementation_state.py`
- updated `.github/workflows/program-governance-audit.yml`
- `PROGRAM_STATUS_2026-09-14.md`
- `governance/CHEMISTRY_NONCOMPUTE_WORK_REGISTER_2026-09-14.md`
- README and PR control-surface synchronization

These changes are intentionally operational. They do not spend the scientific decision budget reserved for the next physical rung.