# Repository operating instructions

## Hard cost control

- Never create, select, dispatch, rerun, or recommend a GitHub-hosted larger runner, a custom paid runner label, or any other paid compute route.
- GitHub Actions in this public repository may use only standard GitHub-hosted runner labels accepted by `.github/workflows/free-runner-policy.yml`.
- Do not bypass, weaken, or remove the free-runner policy.
- Do not enable paid Actions usage, raise a budget, create a paid runner, or use a paid model/API without the user's explicit approval of a maximum dollar amount in the current conversation.
- If standard free runners cannot safely execute a task, stop with a mechanical infrastructure hold. Do not silently upgrade resources.

## Long-compute continuity

- When a long computation is scientifically authorized, provide at least five sequential continuation cells with 19,800 seconds (5.5 hours) available per cell, while preserving checkpoint provenance and frozen science.
- Five cells are continuation capacity, not a requirement to run unnecessary compute. Stop immediately after a valid converged result, scientific/numerical hold, or unrecoverable mechanical hold.
- Never change scientific inputs, thresholds, geometry, methods, or interpretation to fit the free runner.

## Program governance bootstrap

- Before substantial Chemistry research or execution, load the current authoritative SymC General Operations Manual through `SymC-Universe/Infrastructure/governance/RESEARCH_SESSION_BOOTSTRAP.md` when repository access is available.
- The Chemistry reconciliation recorded on 14 September 2026 adopts SymC General Operations Manual v0.8.0. A later explicitly user-promoted GOM supersedes it; do not silently substitute an older manual when a newer authoritative baseline exists.
- Project-specific Chemistry safeguards remain local and auditable. Read `governance/CHEMISTRY_PROJECT_GUARDRAILS_GOM_V0_8_0.md` when work involves chi construction, damping/linewidth interpretation, barrier crossing, exceptional-point language, numerical HOLDs, Atlas independence, or claim promotion.
- Before inheriting active work, verify the actual branch, commit, workflow/run, checkpoint, monitor/recovery state, and supersession state. Do not launch duplicate work because prior conversational context is absent.
- GOM synchronization never authorizes a change to frozen scientific settings. A change that might alter the scientific result remains a scientific or science-adjacent change and must follow the applicable Chemistry change-control path.
