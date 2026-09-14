# Chemistry Non-Compute Work Register

**Date:** 14 September 2026  
**Program manual:** SymC General Operations Manual v0.8.0  
**Mode:** P0-D / P0-Q unless a task is explicitly promoted later  
**Current GitHub Actions compute:** none running or queued at the time of this register

This register separates productive work that can proceed without reopening the current numerical HOLDs from work that would consume a new scientific decision.

## Priority A: do now

| Work item | Why it matters | Output | Scientific change required? | Status |
|---|---|---|---|---|
| GOM v0.8.0 migration integrity | Prevent chemistry-specific safeguards from disappearing during program consolidation | `CHEMISTRY_PROJECT_GUARDRAILS.md` + migration audit | No | DONE IN SYNC BRANCH |
| Execution-state truth | Old implementation registry still called completed runs active | `IMPLEMENTATION_STATUS_v1.1.json` + verifier update | No | DONE IN SYNC BRANCH |
| Current program status | Prevent monitoring/HOLD state from being mistaken for active compute | `PROGRAM_STATUS_2026-09-14.md` | No | DONE IN SYNC BRANCH |
| README and PR synchronization | Reader-facing control surfaces are stale | README + PR #3 status refresh | No | IN PROGRESS IN SYNC BRANCH |
| Barrier Atlas v0.9 closure audit | This product is already independently closed and should not be held hostage by surface calculations | manuscript/reproducibility closure checklist | No if content is unchanged | READY |
| Function Map / Limit Map balance audit | Recent work is limit-heavy; GOM requires both supported interior behavior and limits where native science permits | coverage matrix with missing-but-answerable cells | No | READY |
| Foundational-dependency map | Identify which downstream claims actually depend on Engine, Atlas, linewidth mapping, substrate inheritance, or surface calculations | dependency graph/table + bounded robustness candidates | No | READY |
| Claim-status reconciliation | Ensure manuscript, figures, supplement, repository, and release notes all use the same earned epistemic class | claim/figure/status ledger | No unless a stronger interpretation is proposed | READY |
| Monitoring-coverage audit | GOM requires monitors to observe real dependencies and not silently fall off | monitor/dependency matrix with stale monitor cleanup | No | READY |

## Priority B: scientific preparation that does not need the current QE runs

| Work item | Why it matters | Output | Scientific change required? | Status |
|---|---|---|---|---|
| Native-comparator audit | Future P1 claims must face the strongest fair native method for the same frozen task, or document `NO_NATIVE_COMPARATOR` | one comparator record per intended claim | No for literature review/planning | READY |
| Experimental-opportunity pass | Chemistry has directly testable questions; independent design must precede targeted literature collision | native experiment sketches, then literature-collision table | No while exploratory | READY |
| Linewidth/lifetime/dephasing provenance audit | Mechanical damping cannot be inferred from linewidth alone | source-by-source decomposition and eligibility ledger | No if frozen coordinates are not changed | READY |
| Friction/transmission evidence audit | Barrier kinetics must remain separate from stable-well chi | source/equation/provenance map | No | READY |
| Information-loss audit | Scalar and modal reductions can hide structure | reduction-by-reduction loss inventory | No | READY |
| Engine refusal adversaries | A mature tool must correctly refuse unsupported inputs | known-bad/mutation suite using production code | No if acceptance rules stay frozen | READY |
| Stored-output semantic revalidation | Verify existing outputs compute the object the claim is about | independent recomputation/check tables | No | READY |
| MFR-14 drafting | Avoid waiting until a new run is ready before defining the confirmatory claim | candidate MFR records, explicitly NOT YET FROZEN | No | READY |
| Nearest-prior-art / residual-novelty audit | Keep ChemSA contribution narrower than native chemistry and modal-analysis prior art where appropriate | attribution matrix + residual novelty statement | No | READY |
| Figure-evidence prominence audit | Rare/failure cases should not dominate merely because they are dramatic | figure-to-claim evidence proportionality table | No | READY |

## Priority C: publication and reproducibility closure

- Re-run dependency-free validators and semantic checks on the already-frozen ChemSA and Barrier Atlas release assets without changing scientific content.
- Verify all hashes, manifests, archive members, formula counts, and regeneration instructions.
- Check that every manuscript numerical claim is reader-checkable from a table, source record, or reproducibility artifact.
- Preserve System 2 and System 3 numerical HOLDs as negative/limit evidence in the reproducibility narrative rather than leaving them as apparently missing work.
- Verify that the main text, supplement, README, repository description, figures, and PR descriptions do not resurrect the retired claim that chemistry is governed by one universal stability ratio or that `chi ~= 1` is a universal reactivity optimum.
- Close or clearly label stale/superseded execution routes so they cannot be mistaken for current production.

These tasks require no new physical calculation unless a validation uncovers a defect that cannot be resolved from preserved evidence.

## Priority D: direct experimental questions to design before literature collision

The experimental-opportunity pass should independently sketch tests for at least these question classes before searching for studies that may already answer them:

1. **Stable-mode damping identification:** can a chemically relevant mode be measured with enough independent lifetime, coherence/dephasing, and frequency information to license a mechanical chi rather than a linewidth proxy?
2. **Coupled-mode degeneracy versus defectiveness:** can a tunable chemical or spectroscopic coupled-mode system distinguish a semisimple coincidence from a defective exceptional point using both eigenvalue and response/eigenvector information?
3. **Substrate inheritance:** when the same local adsorbate/reaction motif is embedded in different substrates or coupling environments, which local modal properties survive and which are transformed at the system level?
4. **Barrier-crossing separation:** can matched measurements of barrier geometry, friction/transmission, and stable-well dynamics show whether any relation exists without presuming that well-side chi is the barrier coordinate?
5. **Recovery/resilience under perturbation:** where a chemical system has a supported dynamical state description, does perturbation recovery preserve the same modal architecture or reorganize it before the observable state returns?

After the independent sketches are fixed as exploratory design records, search the literature specifically for prior experiments that collide with each question. If prior work already answers a question, inherit it and isolate the residual experiment rather than duplicating it.

## Scientific decisions intentionally not taken here

The register does **not** authorize:

- CO/Cu(111) layers beyond the currently adjudicated L15 extension;
- H/Ru(0001) layers beyond the current frozen ladder;
- different DFT methods or numerical thresholds;
- a new surface/adsorbate system;
- new rate, friction, linewidth, or chi definitions;
- a new claim that a HOLD is evidence for or against the broader framework;
- any P1 freeze.

Those remain explicit decision points after the non-compute work has reduced the uncertainty around what the next expensive test is actually for.

## Stop condition for this register

A non-compute task is complete when it either:

1. closes a known documentation/provenance/reproducibility defect;
2. produces a bounded scientific decision record for a future test;
3. demonstrates that prior literature already resolves the question;
4. identifies a genuine unresolved residual question; or
5. reaches a point where continuing would alter frozen science and therefore requires explicit authorization.

The purpose is to keep the program moving without substituting paperwork for science or manufacturing computation merely because a runner is available.