# Na/Cu(001) clean-slab gate

This stage consumes both the compact bulk handoff and its hashed full bulk-selection result. It converges only a symmetric, neutral, unreconstructed primitive Cu(001) clean slab. It contains no Na geometry, adsorption energy, diffusion path, barrier, or kinetic target.

## Fail-closed bulk validation

Before any slab calculation, the runner verifies:

1. the handoff and source-result schemas;
2. the source-result SHA-256 recorded in the handoff;
3. agreement of cutoff, density cutoff, k mesh, fitted lattice constant, and fitted bulk energy;
4. a joint bulk gate of `|delta a0| <= 0.005 angstrom` and `|delta e0| <= 0.001 eV/atom` against the largest registered bulk reference.

This revalidation repairs the earlier analyzer's lattice-only admission behavior without rerunning the 120 completed bulk SCFs.

## Correct Cu(001) cell

The slab uses primitive surface vectors `(a0/2,a0/2,0)` and `(-a0/2,a0/2,0)`, area `a0^2/2`, one Cu atom per layer, alternating `(0,0)` and `(1/2,1/2)` stacking, and an odd number of layers centered in vacuum. This gives two equivalent surfaces and no net slab dipole.

## Frozen matrix

- layers: `5, 7, 9, 11`
- vacuum: `12, 16, 20, 24 angstrom`
- in-plane k meshes: four even meshes derived from the accepted cubic bulk mesh around the equal-reciprocal-spacing value `sqrt(2) * k_bulk`
- total: 64 SCF calculations

The workflow remains inert until `BULK_HANDOFF.json` and `BULK_CONVERGENCE_RESULT.json` are frozen under `na_cu001_ci/frozen_bulk_input/`.

## Valid energy comparison

Raw total energies from slabs with different atom counts are never compared. For each vacuum/k-mesh pair, the four thicknesses are fitted to

`E_slab(L) = mu_slab L + 2 epsilon_surface`.

Vacuum and k-mesh convergence are tested on the fitted surface excess. Thickness convergence is then tested with the independently fitted bulk energy through `(E_slab - L e_bulk)/2`. The admission tolerance is 1.0 meV per surface atom against every registered dominating grid point, not only one corner reference.

The output reports fit residuals and the difference between the slab-fit slope and the independent bulk energy as diagnostics. A PASS advances only to a separately gated clean-surface ionic relaxation. Na remains prohibited until that relaxation passes.
