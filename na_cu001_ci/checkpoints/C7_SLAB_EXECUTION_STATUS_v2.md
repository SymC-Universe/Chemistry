# C7 definitive clean-slab execution record v2

**Checkpoint:** C7  
**Status:** active definitive source run  
**Scientific task:** converge the clean Cu(001) slab before adsorption or NEB work  
**Definitive source run:** `30865116448`  
**Definitive source commit:** `f2dd5df52975c5eb26cb020995a82e237a085edc`  
**Definitive audit binding commit:** `55cc32bc31cf4d6de93ae4426a101d0225187c9e`  
**Main PR:** `#3`, draft and unmerged  

## Frozen physical and numerical contract

The final source package preserves the preregistered matrix and gates:

- Cu(001) clean slab;
- layers: 5, 7, 9, 11;
- total vacuum: 12, 16, 20, 24 A;
- four registered even in-plane meshes derived from the selected 14x14x14 bulk mesh;
- 64 total slab SCFs;
- Quantum ESPRESSO `assume_isolated='esm'`;
- ESM boundary condition `esm_bc='bc1'`;
- selected bulk cutoffs: 90 Ry wavefunction and 270 Ry density;
- 1.0 meV per surface atom convergence criterion;
- downstream thickness floor: at least 7 Cu layers.

No scientific threshold or candidate grid was changed during the corrections below.

## Pre-SCF failure and correction history

| Run | Outcome | Classification | Slab SCFs completed | Disposition |
|---|---|---|---:|---|
| `30862954839` | prepare failed | MECHANICAL_FAILURE | 0 | Bulk-run auditor used descriptive step labels not exposed by the Actions jobs API. Replaced by exact frozen step-number validation. |
| `30863042629` | prepare failed | MECHANICAL_FAILURE | 0 | The real audit passed, but the adversarial test fixture still lacked numbered mock steps. Fixture corrected and a wrong-step negative test added. |
| `30863061143` | cancelled during prepare | PRE-RESULTS_METHOD_CORRECTION | 0 | The inherited periodic-cell generator centered the slab at fractional z=0.5. ESM documentation and examples require the slab around Cartesian z=0. The run was stopped before any slab job was released. |
| `30864367769` | cancelled during prepare | MECHANICAL_FAILURE_PREVENTION | 0 | V5 initially searched an entire four-k-mesh worker directory for exactly one record, which would have failed on the second k mesh. Replaced by exact current-case record targeting and a sequential four-k-mesh regression test. |
| `30864668012` | cancelled during prepare | INPUT_SEMANTICS_HARDENING | 0 | ESM coordinates were centered correctly but still emitted through a `crystal` card. Replaced prospectively by explicit `ATOMIC_POSITIONS angstrom` with negative and positive z coordinates around zero. |
| `30864911500` | cancelled during prepare | PROVENANCE_HARDENING | 0 | The audit verified geometry metadata but did not parse and hash the actual QE input files. Replaced by direct 64-input validation. |
| `30865116448` | active | DEFINITIVE_C7_SOURCE | pending | First source run carrying the complete ESM geometry, exact-record, explicit-coordinate, and direct-input audit contract. |

All superseded source runs were stopped before the matrix release. None produced an admissible slab energy, result, or handoff.

## Definitive geometry convention

The definitive entrypoint is `na_cu001_ci/slab_runner_v5.py`.

For every registered case it requires:

1. the slab midpoint at Cartesian `z=0`;
2. open ESM boundaries at `-Lz/2` and `+Lz/2`;
3. half of the registered total vacuum on each side;
4. `ATOMIC_POSITIONS angstrom` rather than an implicit fractional representation;
5. the original primitive Cu(001) in-plane vectors and alternating fcc layer shift;
6. the original layer spacing `a0/2`;
7. an exact-case output path keyed by layer, vacuum, and k mesh.

Each raw `run_record.json` receives geometry schema:

`na-cu001-esm-centered-slab-v0.2`

## Direct input-file audit

The definitive Stage 2 analyzer does not trust geometry metadata alone. For all 64 cases it requires the actual `<tag>.in` file and verifies:

- the file SHA-256 equals `input_sha256` in its run record;
- `assume_isolated='esm'` is present;
- `esm_bc='bc1'` is present;
- the atomic-position card is exactly `ATOMIC_POSITIONS angstrom`;
- the number of Cu positions equals the layer count;
- atomic z coordinates average to zero;
- minimum and maximum z are symmetric around zero;
- the input cell height equals the run-record cell height;
- the automatic k mesh equals the run-record k mesh.

The full raw/input audit schema is:

`na-cu001-esm-centered-raw-audit-v0.3`

A missing, changed, malformed, or hash-mismatched input produces HOLD.

## Frozen layer-floor enforcement

The inherited V2 analyzer could recommend a numerically converged five-layer slab even though the downstream protocol required at least seven layers. `slab_runner_v4.py` now applies the pre-existing floor after the unchanged V2 energy analysis:

- keep the 1.0 meV criterion unchanged;
- select the smallest passing registered layer at or above seven;
- retain the same selected vacuum and k mesh;
- produce HOLD when no registered layer at or above seven passes;
- record whether enforcing the frozen floor changed the V2 recommendation.

## Adversarial tests before release

The source preparation firewall runs:

- 6 slab-floor tests;
- ESM centering and equal-vacuum tests;
- in-plane fcc geometry and layer-spacing tests;
- explicit angstrom QE input-card test;
- four sequential k-mesh exact-record update test;
- record-identity mismatch rejection;
- old fractional-half-centered geometry rejection;
- tampered QE input rejection;
- complete 64-record plus 64-input inventory acceptance.

The matrix cannot be released unless these tests and the independent v0.4 bulk audit pass.

## Definitive decision artifact

Workflow `.github/workflows/na-cu001-c7-definitive-audit.yml` is bound to source run `30865116448` and source commit `f2dd5df52975c5eb26cb020995a82e237a085edc`.

A C7 PASS requires:

- prepare success;
- all 16 matrix jobs successful;
- exactly 64 converged raw records;
- exactly 64 QE input files with matching hashes;
- source manifest verification against the source commit;
- ESM geometry and direct-input audit PASS;
- vacuum/k convergence within 1.0 meV per surface atom;
- thickness convergence within 1.0 meV per surface atom;
- selected thickness of at least seven layers;
- valid v0.4-aware slab handoff;
- complete raw-record and source manifests.

The only admissible C7 terminal artifact is:

`na-cu001-c7-definitive-stage2`

The source workflow's own Stage 2 output is informative but cannot release C8 without the independent definitive audit.

## Email reconciliation

All GitHub failure notifications through this checkpoint are assigned:

- `ace9fb7`: first bulk-audit label defect;
- `64566fa`: stale adversarial fixture defect;
- `895e1aa`: obsolete watcher treated a normal polling status as shell failure;
- `54b5d63`: corrected obsolete watcher reported the intentionally cancelled source prepare;
- later cancelled source runs are preregistered pre-SCF corrections, not numerical slab failures.

No email or workflow result may be interpreted as a slab convergence failure unless the definitive source run has actually released the matrix and a slab case or the frozen numerical gate fails.
