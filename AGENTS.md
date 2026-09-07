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
