# Na/Cu(001) clean-slab strict holdout amendment v0.1

**Status:** frozen before any admissible clean-slab numerical result  
**Recorded:** 2026-08-03 America/Chicago  
**Definitive source run:** `30865655113`  
**Definitive source commit:** `e63558ce1a2bace8f45fde6f46491df176d7d950`  
**Definitive audit run:** `30865783801`  
**Definitive audit commit:** `166ac10bd2d9218dc10612a797659ef04a89de7a`  

## 1. Reason for the amendment

The inherited V2 clean-slab selector compared each vacuum/k-mesh point with all registered points at equal or greater settings and compared each thickness with all equal or thicker slabs. Because each comparison set included the candidate itself, the terminal grid points had a zero self-difference and therefore could always satisfy the numerical tolerance:

- 24 A vacuum and the densest registered in-plane mesh could validate themselves;
- the 11-layer slab could validate itself.

That structure made a terminal-grid PASS unavoidable after successful SCFs and did not constitute an independent convergence test.

The issue was identified while source run `30865468372` was still in preparation. The run was stopped before any slab matrix job or slab energy was released. No numerical result was inspected when this amendment was frozen.

## 2. Unchanged scientific inputs

The amendment does not change:

- the selected bulk setting of 90 Ry wavefunction cutoff, 270 Ry density cutoff, and 14x14x14 bulk mesh;
- the clean-slab grid of 5, 7, 9, and 11 layers;
- the vacuum grid of 12, 16, 20, and 24 A;
- the four registered even in-plane meshes derived from the bulk mesh;
- the total of 64 slab SCFs;
- PBE and the pinned Cu pseudopotential;
- Quantum ESPRESSO ESM `bc1` electrostatics;
- explicit Cartesian `ATOMIC_POSITIONS angstrom` centered around `z=0`;
- equal vacuum on both sides of the slab;
- the 1.0 meV per-surface-atom tolerance;
- the downstream minimum of seven Cu layers.

No threshold was relaxed or fitted to a result.

## 3. Strict terminal holdouts

The terminal settings are now holdouts only and are ineligible for selection:

- 11 layers;
- 24 A total vacuum;
- the densest registered in-plane k mesh, expected to be 22x22 for the selected 14x14x14 bulk mesh.

A selectable vacuum/k pair must:

1. use less than 24 A vacuum;
2. use a mesh less dense than the terminal mesh;
3. have at least one strictly larger-vacuum comparison at the same k mesh;
4. have at least one strictly denser-k comparison at the same vacuum;
5. remain within 1.0 meV per surface atom of every registered point that is at least as strict in both dimensions and strictly greater in one or both dimensions.

A selectable thickness must:

1. contain at least seven layers;
2. contain fewer than 11 layers;
3. have at least one strictly thicker registered comparison;
4. remain within 1.0 meV per surface atom of every strictly thicker registered slab at the selected vacuum and k mesh.

## 4. Decision logic

The smallest vacuum and k pair satisfying the strict holdout gate is selected. At that pair, the smallest thickness at or above seven layers satisfying the strict thickness holdout gate is selected.

Possible terminal outcomes are:

- **PASS:** a nonterminal vacuum, k mesh, and thickness satisfy all strict comparisons;
- **SCIENTIFIC_HOLD:** no nonterminal setting satisfies the unchanged 1.0 meV criterion;
- **MECHANICAL_FAILURE:** one or more calculations, records, inputs, hashes, or workflow steps fail before a scientific decision can be made.

A scientific HOLD requires a new prospective extension grid. It cannot be converted to PASS by selecting a terminal point or weakening the tolerance.

## 5. Implementation and tests

The strict decision layer is implemented in:

- `na_cu001_ci/slab_runner_v4.py`;
- `na_cu001_ci/test_slab_runner_v4.py`.

The audit schema is:

`na-cu001-clean-slab-strict-holdout-audit-v0.1`

Adversarial tests require that:

- a genuine nonterminal plateau selects a nonterminal vacuum, k mesh, and layer count;
- seven layers can fail while nine layers passes against eleven;
- a terminal vacuum/k point cannot validate itself;
- eleven layers cannot validate itself;
- every selected vacuum/k pair has holdouts along both axes;
- changed tolerances and changed registered grids are rejected;
- missing source records are rejected.

The independent C7 audit requires the strict holdout schema and independently checks that the selected settings are all below their corresponding terminal holdouts before releasing C8.
