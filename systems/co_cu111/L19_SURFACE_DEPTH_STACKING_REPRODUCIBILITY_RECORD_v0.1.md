# CO/Cu(111) L19 surface-depth stacking reproducibility record v0.1

Date opened: 2026-09-07
Repository: `SymC-Universe/Chemistry`
Branch: `agent/na-cu001-integration`

## Purpose

This record preserves the prospective opening of the clean-surface L19 convergence rung after the historical L17 rung remained on its unchanged 1.0 meV/surface-atom adjacent-depth gate. It records scientific authorization, frozen continuation rules, source evidence, software tests, checkpoint semantics, cost controls, and live execution lineage. It does not reclassify L17 or change any frozen threshold.

## Historical L17 source state preserved

Source run: `33956049744`
Source case: `L17-V36-K32-extension-audit`
Historical status: `NUMERICAL_HOLD_L17_TERMINAL_UNDER_CURRENT_CONTRACT`

- movable force: `0.0176094870072678 eV/A` <= `0.020`, PASS
- independent fixed-geometry SCF reproduction delta: `2.7212081477046013e-07 eV` <= `0.001`, PASS
- surface excess: `0.47904687052505324 eV/surface atom`
- L15-to-L17 adjacent-depth delta: `0.001106435876863543 eV/surface atom` > `0.001`, FAIL

Pinned L17 artifacts:

- relaxation artifact `co-cu111-l17-exact-restart-relax-06`, ID `9972622333`, artifact digest `sha256:d882dbe1b5c69bb980655cd199699dd9631a6b96ec699a502daeeda07f4834d5`, final state SHA-256 `3aaf41c304c4238da5804d095c5724f810ff06f67060dccecb3277efa46a1d15`
- result artifact `co-cu111-l17-convergence-result-v1`, ID `9983282108`, artifact digest `sha256:87bbd0138943a71e9962dd9f952d52ca2d64e7e8dede5e36e5f03f4b9d7462ca`, result JSON SHA-256 `45eb9c31a954d736f799e70964508c22a2cfb8781e11f171801ad4b4a3681b2d`

## New prospective authorization and rung rule

On 2026-09-07 the user explicitly authorized opening L19 and prospectively stacking further odd-layer rungs if the frozen continuation rule warrants it. The new policy was frozen before any L19 result.

Frozen rung progression:

- L19/V40/K36
- if authorized by the frozen rule: L21/V44/K40
- then L23/V48/K44, etc.

Each new rung is exactly `+2 layers`, `+4 Angstrom vacuum`, and `+4 in-plane k points` from the immediately preceding mechanically valid, relaxed, independently reproduced rung. Each next rung must receive a new hash-bound protocol before compute begins.

The target is seeded only from symmetric outer-two-layer-per-face z offsets of the immediately preceding relaxed rung applied to an otherwise ideal target slab. Energy, surface excess, pass/fail result, kinetics, barriers, or expected outcome may not select the seed.

Unchanged gates:

- force <= `0.020 eV/A`
- independent SCF reproduction delta <= `0.001 eV`
- adjacent-rung surface-excess delta <= `0.001 eV/surface atom`

Continuation is authorized only when force and reproduction pass and only the adjacent-rung surface-excess gate remains open. Force/reproduction/provenance failure stops automatic depth progression for scientific review.

## Frozen files and hashes

- `SYSTEM2_PBE_SURFACE_DEPTH_STACKING_POLICY_v0.1.json`: `db0ff7ea1e85c4c709548a81351030d90d1db95b2df7d99659e362aba79a0b4f`
- `SYSTEM2_PBE_SURFACE_CONVERGENCE_L19_v0.1.json`: `f27ecf8ee22776e695b92549c1f2a8a8818df57d8f8f24033d0cd2c49f5f361e`
- `pbe_surface_depth_stack_v1.py`: `0cd11a12c5f031197e4cc11880e5b0dd963ee83e5b223b1eae308d5bec9e0401`
- `test_pbe_surface_depth_stack_v1.py`: `7dc5f5cbd5592ee9535b471732bfd2c2e459a4221c8b6d1a1fd6b27c8ed1ba6f`

The first proposed generic runner filename collided with a historical L15 extension runner. GitHub rejected creation rather than overwriting it. The historical file was left untouched and the new stacking runner was given the distinct `pbe_surface_depth_stack_v1.py` path. This event is retained as a lineage-preservation safeguard.

## Pre-launch testing

The prospective test suite contains 11 fail-closed tests covering:

1. full frozen protocol validation
2. exact L17 -> L19 `+2/+4/+4` rung construction
3. preservation of the historical L17 HOLD
4. unchanged thresholds and stacking-policy agreement
5. exact checkpoint contract and meter-conscious runner policy
6. restart input semantics
7. rejection of prior-state protocol hash drift
8. checkpoint-manifest mutation detection
9. geometry-only symmetric surface-offset seeding
10. deadline separation from scientific settings
11. pinned source/policy hash presence

During construction one test initially used exact equality for a tiny floating-point coordinate difference. That test-only assertion was corrected to a tolerance-based comparison. No scientific setting or production calculation changed. The complete suite then passed 11/11.

## Live L19 launch

Workflow: `CO Cu111 L19 exact QE restart convergence v1`
Workflow run: `34134967279`
Launch commit: `f0197db254beb96da959685e71474c6e6ce590d1`

Preflight job: `101783655609`, completed SUCCESS.

The live preflight:

- reverified all four frozen file hashes
- ran Python byte compilation
- ran all 11 tests, `OK`
- ran the runner self-test
- downloaded the actual pinned L17 relaxation and result artifacts
- verified the L17 artifact digests and source identities
- verified the unchanged Stage-A engine, Stage-A result, pseudopotential bundle, and one-rank selection
- reported `SOURCE=L17-V36-K32`, `TARGET=L19-V40-K36`, `QE_MAX_SECONDS=16200`, `APPROXIMATE_RESTART_ALLOWED=false`, `THRESHOLDS_CHANGED=false`, and `SOURCE_FAILURE_PRESERVED=true`
- issued preflight status `PASS`

L19 relaxation segment 1 job: `101783730961`; at this record update it was in progress in `Run exact-restart segment`.

## Exact restart and cost-control contract

L19 begins on standard `ubuntu-24.04`, not a paid larger runner. Larger-runner escalation is allowed only after demonstrated resource failure.

Each real QE segment receives `max_seconds=16200` inside a 360-minute GitHub job, retaining 5400 seconds for clean shutdown and artifact preservation. A clean max-seconds stop preserves the full QE outdir plus a SHA-256 manifest. The next segment verifies the prior state identity, frozen protocol SHA, checkpoint manifest, and file hashes before using `restart_mode='restart'`.

If a prior segment is already COMPLETE, later bookkeeping segments carry it forward without QE recomputation. Valid checkpoints are always preferred over starting from scratch. Duplicate paid computation is forbidden when a compatible checkpoint survives.

Frozen runway per rung:

- relaxation: maximum 6 segments
- independent SCF: maximum 4 segments

If a rung cannot complete within that frozen runway, it stops for review rather than silently extending the segment bound.

## Deadline firewall

The approximately one-month publication deadline is treated only as an operational boundary for deciding whether completed evidence belongs in the current manuscript or a later revision. It may not change the method, thresholds, target selection, checkpoint semantics, or interpretation.

This record should be updated after each meaningful L19 checkpoint, final L19 adjudication, and every subsequently authorized odd-depth rung.