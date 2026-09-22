# Checkpoint C4 progress: audited bulk extension at 25 of 26 EOS cases

**Status:** IN PROGRESS  
**Workflow run:** `30843005718`  
**Frozen launch commit:** `ec0e18c86ead22e7062047fdff68e43ead72945f`  
**Scientific decision:** not yet available  

## Numerical state

- all 24 registered selectable candidates completed successfully;
- 140 Ry / 22x22x22 finite reference completed successfully and its artifact upload closed;
- 150 Ry / 24x24x24 independent audit remains in progress;
- completed extension EOS jobs: 25/26;
- failed extension EOS jobs: 0;
- final `extension-gate` has not been released;
- no candidate has been selected and no v0.4 bulk PASS exists at this checkpoint.

The final audit remains mandatory. Neither the completed candidate matrix nor the completed 140 Ry reference may be interpreted prospectively or used to open the surface route before the 150 Ry / 24-cubed audit, the final decision artifact, and independent bridge verification finish.

## Email reconciliation

Recent GitHub notification email was rechecked by timestamp, workflow, and run identity. No failure or cancellation notice corresponds to active extension run `30843005718`. Older unread failure notifications remain matched to the previously classified installation failures, superseded exploratory route, and v0.3 scientific HOLD.

## Downstream preflight completed while C4 runs

The following were frozen before the v0.4 result existed:

- audited v0.4 result/handoff/46-summary bridge verifier;
- versioned v0.4 slab and closure entrypoints that leave V2 physical calculations unchanged;
- v0.3 integration artifact plan and validator;
- V3 stage harness;
- deterministic 20-job V3 workflow builder;
- 20-job workflow DAG and 19-stage non-circular artifact DAG contracts.

GitHub run `30851502637` passed all substantive V3 preflight checks. The generated workflow has:

- size: 20,134 bytes;
- SHA-256: `250d0d16189777590b5851a5eff81016761202356bca174acaea65308484bf52`;
- jobs: 20;
- registered Hessian matrix jobs: 108.

The exact verified bytes are stored only at the ordinary non-executable path:

`na_cu001_ci/workflow_fixtures/na-cu001-computational-route-v3.yml`

They are not installed under `.github/workflows`, so no surface calculation can execute yet.

## Fixture publication history

A one-time trusted verification run, `30851944394`, reran all bridge, entrypoint, workflow-DAG, and artifact-DAG checks, regenerated the workflow, required the frozen SHA-256, and published the bytes to a descendant fixture branch. The integration ref was then fast-forwarded to the identical one-file fixture commit. No pull-request merge action or merge commit was used.

Because temporary inspection PR `#16` had the fixture branch as its head, GitHub automatically marked that PR as merged when the base ref became identical to the head commit. This was a platform status consequence of the fast-forward, not an invoked PR merge. The changed-file audit showed exactly one ordinary non-executable fixture file. This fast-forward-through-an-open-inspection-PR pattern will not be reused for the executable workflow promotion.

The temporary workflow `contents: write` permission used only for fixture publication was removed immediately afterward. The verification workflow is restored to `contents: read`.

## Next permitted action

1. finish the 150 Ry / 24-cubed audit;
2. run the registered extension gate over all 46 EOS summaries;
3. download the compact decision and summary artifacts;
4. independently re-evaluate the reference audit, candidate gates, minimum-cost ordering, 46 summary hashes, and 276 SCF records;
5. classify the result as PASS or SCIENTIFIC_HOLD;
6. only after verified PASS, promote the exact fixture blob directly into `.github/workflows/na-cu001-computational-route-v3.yml` through a single tree/commit/ref update, without opening a PR;
7. record the launch commit and begin C7 clean-slab convergence.
