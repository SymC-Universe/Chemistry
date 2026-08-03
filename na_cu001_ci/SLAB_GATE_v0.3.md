# Corrected clean Cu(001) slab gate

The clean-slab stage is construction-only and contains no Na/Cu(001) kinetic target.

## Frozen geometry

- primitive Cu(001) cell with area `a0^2/2`;
- one atom per layer;
- alternating `(0,0)` and `(1/2,1/2)` stacking;
- odd layer counts `5, 7, 9, 11`;
- vacuum values `12, 16, 20, 24 A`;
- four in-plane meshes derived from the corrected bulk k mesh.

## Frozen electrostatics

Every one of the 64 convergence calculations uses Quantum ESPRESSO ESM with
`assume_isolated='esm'` and `esm_bc='bc1'`. This is the same boundary convention
used for clean relaxation, adsorption, endpoints, NEB, saddle verification, and
barrier sensitivity. The periodic slab is retained only as a transparent
boundary-condition diagnostic and cannot select or retune the route.

## Energy analysis

Raw total energies with unequal atom counts are never compared directly. For
each vacuum and k mesh, the thickness series is fit as

`E_slab(L) = mu_slab L + 2 epsilon_surface`.

Vacuum and reciprocal-space convergence use the fitted surface excess. Layer
convergence uses bulk-referenced surface excess at the selected vacuum and k
mesh. The tolerance is `1 meV` per surface atom.

The downstream slab contains at least seven layers even if the construction
matrix selects five, ensuring that the expanded one-sided mobility model leaves
a genuinely fixed lower surface.

## Next gate

At the downstream layer count, an electrostatic consistency audit repeats the
selected ESM calculation, repeats it at the next larger vacuum, and runs one
periodic diagnostic. PASS requires the ESM vacuum change to remain within the
frozen tolerance. Periodic-vs-ESM disagreement is reported but does not create a
method discontinuity because periodic energies are not used downstream.
