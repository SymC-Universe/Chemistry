# C7 clean-slab execution and failure record

**Checkpoint:** C7  
**Scientific task:** 64-case clean Cu(001) slab convergence  
**Frozen physical grid:** 5, 7, 9, and 11 layers; 12, 16, 20, and 24 A vacuum; four registered even in-plane meshes derived from the selected 14-cubed bulk mesh  
**Frozen electrostatics:** Quantum ESPRESSO ESM `bc1` for all cases  
**Frozen numerical gate:** 1.0 meV per surface atom  
**Frozen downstream layer floor:** 7 Cu layers  

## Upstream C6 status

Bulk extension run `30843005718` is scientifically PASS despite the terminal run label `cancelled` caused by the redundant aggregate-raw upload. The compact decision, all 46 EOS summaries, all 26 individual extension raw archives, and the complete 276-SCF inventory remain present and hashed. The selected minimum-cost joint-pass bulk setting is 90 Ry wavefunction cutoff, 270 Ry density cutoff, and a 14x14x14 mesh.

## C7 launch attempts

| Run | Commit | Outcome | Classification | Numerical slab work performed | Disposition |
|---|---|---|---|---|---|
| `30862954839` | `ace9fb7aa62aa5fd0ac9ec9a0caecccbdd5f636e` | prepare failed | MECHANICAL_FAILURE | none | The run auditor matched descriptive step labels that were not exposed by the jobs API. Replaced by exact frozen step-number validation. |
| `30863042629` | `64566fab2712266d46a72c5c164de152b4c7a627` | prepare failed | MECHANICAL_FAILURE | none | The real bulk audit passed, but its adversarial fixture still lacked numbered mock steps. The fixture was corrected and expanded with a wrong-step-name negative test. |
| `30863061143` | `4c9697c264bc3bb190c3239a10c9f934d9ced575` | active at this checkpoint | IN_PROGRESS | none yet at record time | This is the registered source run for the 64 raw slab calculations. It has cleared the two prior audit defects and is rebuilding the pinned Quantum ESPRESSO engine and Na reference before releasing the slab matrix. |

## Email reconciliation

GitHub notification email was checked after each failed run.

- The notification for `ace9fb7` matches run `30862954839` and the first audit-label defect.
- The notification for `64566fa` matches run `30863042629` and the stale adversarial-fixture defect.
- The notification for `895e1aa` concerns only the first version of the separate definitive-audit watcher. Its shell fail-fast handling treated the intentional nonterminal poll code as a failure. The watcher was corrected prospectively at commit `54b5d63eb767dceb2cf1b5b3e91bd4a6b084847f`.
- No failure notification for source run `30863061143` existed when this record was written.

## Frozen layer-floor enforcement correction

The preregistered slab protocol already required a minimum of seven layers downstream, but the V2 analyzer selected the smallest numerically converged layer without explicitly applying that floor. This was an implementation omission, not a change in physical method or threshold.

The correction is versioned in:

- `na_cu001_ci/slab_runner_v4.py`
- `na_cu001_ci/test_slab_runner_v4.py`
- `.github/workflows/na-cu001-slab-floor-tests.yml`

The correction:

1. preserves all 64 raw SCFs;
2. preserves the ESM convention and 1.0 meV criterion;
3. delegates the original surface-energy analysis to V2;
4. selects the smallest converged registered layer at or above seven;
5. returns HOLD if no layer at or above seven passes;
6. records whether the V2 recommendation required promotion solely to enforce the frozen floor.

## Definitive C7 decision route

The workflow `.github/workflows/na-cu001-c7-definitive-audit.yml` is bound to source run `30863061143`. It waits for all 16 matrix jobs, requires all 64 raw slab records, downloads the immutable raw artifacts and audited bulk base, runs the versioned floor-aware analysis, constructs a new slab handoff, hashes all raw records, and uploads `na-cu001-c7-definitive-stage2`.

No slab SCF is rerun by the definitive audit. A PASS requires:

- prepare success;
- all 16 matrix jobs successful;
- exactly 64 converged raw slab records;
- one shared frozen bulk provenance;
- vacuum/k convergence within 1.0 meV per surface atom;
- thickness convergence within 1.0 meV per surface atom;
- selected thickness of at least seven layers;
- a valid v0.4-aware slab handoff and complete raw-record manifest.

Only the definitive floor-aware Stage 2 artifact is admissible for C8. The uncorrected V2 layer recommendation, even if numerically PASS, cannot by itself release downstream work.
