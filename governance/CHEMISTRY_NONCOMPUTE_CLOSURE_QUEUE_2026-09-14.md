# Chemistry non-compute closure queue

**Date:** 2026-09-14  
**Purpose:** keep the chemistry program advancing while scientific computation is absent, blocked, or awaiting a new authorized rung  
**GOM baseline:** v0.8.0  
**Scientific effect of this queue:** none

At the time this queue was created, repository-wide GitHub Actions showed **0 in-progress** and **0 queued** runs. This document therefore distinguishes work that can be advanced immediately from scientific computation that is actually blocked.

## A. Can proceed now without changing frozen science

| Priority | Work item | Why it matters | Completion condition |
|---|---|---|---|
| P0 | Reconcile stale liveness/status text | Prevents completed/cancelled runs from masquerading as active computation | All current status surfaces point to live Actions state or terminal adjudication records |
| P0 | Synchronize README System 2/System 3 status | GOM requires prose to match capability/evidence state | README reports the adjudicated HOLDs and does not imply adsorption/kinetics are currently progressing |
| P0 | Correct public repository description | Current metadata still states a single stability ratio governs catalytic efficiency and implies chi approximately 1 optimality | Repository description matches the current generator-first, non-universal claim ceiling |
| P0 | Preserve GOM v0.8.0 migration/congruency record | Prevents project-specific controls from vanishing during program-manual consolidation | Local safeguard destinations and supersession rules are auditable |
| P0 | PR #3 status reconciliation | PR body contains historical execution language that no longer describes live state | PR body or top-level status comment points to the terminal/current source of record |
| P1 | Implementation-registry liveness audit | `IMPLEMENTATION_STATUS_v1.0.json` contains components labeled ACTIVE with old running-job prose | A versioned correction/supersession record distinguishes historical deployment qualification from present liveness |
| P1 | Workflow trigger and paid-runner audit | Recent commits intentionally disabled paid/larger runner recovery paths | Every enabled workflow is inventoried by trigger, runner class, scientific scope, and whether automatic continuation is lawful |
| P1 | Branch/PR source-of-record map | Many prospective and recovery branches now coexist | One map identifies canonical branch, evidence branch, frozen release, superseded execution branches, and merge prohibition where applicable |
| P1 | System 2 Limit Map closure package | The L15 extension HOLD is a scientifically meaningful limit result | Negative/limit result, provenance, uncertainty/tolerance, and refusal consequence are manuscript-ready |
| P1 | System 3 Limit Map closure package | The suffix-rule failure should not remain a vague unfinished computation | HOLD is documented as a bounded limit result with the exact lawful next-science choices |
| P1 | Chemistry Function Map inventory | GOM requires functioning interior and limits to be treated coequally | Existing supported regimes and ordinary-function evidence are listed separately from boundary/HOLD evidence |
| P1 | Scalar/modal/system relation audit | Prevents scalar success from substituting for modal or system evidence | Each major chemistry claim identifies which representation is actually supported and which are NOT_APPLICABLE/UNRESOLVED |
| P1 | Open-channel disposition audit | Residuals, unresolved modes, failed fits, and numerical anomalies cannot disappear at closure | Every material anomaly is PROMOTION_TRACK, DEAD_END, CLOSED_ARTIFACT_OR_NOISE, DEFERRED_RESOURCE_LIMIT, or UNRESOLVED |
| P1 | Barrier Atlas v0.9 manuscript/reproducibility freeze review | Atlas is already independently closed; publication should not wait on unrelated surface holds | Release claims, source grades, hashes, validators, figures/tables, and manuscript language are mutually synchronized |
| P1 | Barrier Atlas independence/dependency map | Clarifies what the Atlas can and cannot support downstream | Every downstream chemistry claim records whether it actually inherits Atlas evidence |
| P1 | Native-comparator matrix | Required before any future P1 added-value claim | Each frozen question has COMPARATOR_IDENTIFIED or a documented NO_NATIVE_COMPARATOR route with nearest alternatives |
| P1 | Evidence-independence map | Prevents reuse of development evidence as untouched confirmation | Discovery, qualification, Atlas, prospective systems, and confirmation datasets/systems are visibly separated |
| P1 | MFR-14 readiness packets | Speeds any later P1 test without opening decisive evidence | Candidate claims have draft MFR fields, with unresolved fields explicitly marked rather than guessed |
| P1 | Manuscript claim-ceiling audit | Repository history contains stronger legacy wording than the current program licenses | Main text, supplement, figure captions, abstract, README, and public metadata use the same earned claim ceiling |
| P2 | Experimental-opportunity pass for residual chemistry questions | GOM asks us to design meaningful direct tests before literature collision when physical testing is plausible | Independent experiment sketch exists before targeted prior-experiment search; only the residual unanswered question survives |
| P2 | Prior-art / residual-novelty ledger | Publication claims must distinguish what is inherited from chemistry literature from what remains SymC-specific | Nearest prior art, overlap, residual contribution, and contribution wording are recorded |
| P2 | External-confirmation candidate inventory | Current systems are development/qualification evidence, not automatically independent P1 confirmation | Candidate untouched systems/evidence are listed without opening decisive outcomes or tuning selection to results |
| P2 | Release/regeneration dry audit | Prevents a late packaging scramble | All preserved code/data needed to regenerate mature non-compute outputs have explicit paths, versions, hashes, and refusal rules |

## B. Existing data/output work that may proceed without new scientific computation

The following are permitted when they operate on already-generated evidence without changing a scientific rule:

1. inspect terminal workflow runs, jobs, and artifacts;
2. verify hashes and semantic contents of preserved outputs;
3. reconstruct an execution timeline from GitHub records;
4. classify mechanical failures using already-frozen criteria;
5. regenerate documentation, tables, or figures from already-adjudicated results where the transformation is deterministic and claim-neutral;
6. run cheap unit/schema/provenance validators that do not dispatch a new scientific calculation;
7. compare repository prose against source-of-record result files and flag stale claims;
8. prepare prospective protocols and decision packets without executing the new scientific rung.

## C. Blocked until a genuine scientific decision is authorized

The following must not be smuggled into the non-compute queue:

- additional CO/Cu(111) slab layers beyond the currently adjudicated frozen extension;
- a new H/Ru(0001) layer ladder;
- altered convergence/acceptance thresholds;
- changed DFT functional, pseudopotential, k-mesh, geometry constraints, or solver semantics;
- new friction/damping values used as kinetic inputs without the frozen provenance/matching contract;
- post-result selection of a mode, site, or coordinate because it produces preferred chi behavior;
- any claim that converts a local stable-mode damping coordinate into a reaction-rate or whole-system scalar without derivation;
- any prospective confirmation using evidence already opened during development as though it were untouched.

## D. Immediate order of operations

1. Repair source-of-record/status drift first.
2. Close the System 2 and System 3 Limit Map documentation from existing evidence.
3. Build the Function Map and scalar/modal/system relation inventory from already-supported material.
4. Finish Barrier Atlas v0.9 manuscript/reproducibility synchronization without expanding the Atlas by default.
5. Prepare comparator, independence, MFR-14, and external-confirmation packets.
6. Independently design any residual physical experiment, then perform targeted literature collision.
7. Return for explicit authorization only when the next action changes frozen science.

This queue is deliberately finite. Passing a documentation or robustness item does not create an automatic ladder of harder work.
