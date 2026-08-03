# Na/Cu(001) clean-slab gate

This stage consumes the verified bulk handoff and converges only the symmetric clean Cu(001) substrate. It deliberately contains no Na geometry, adsorption energy, diffusion path, barrier, or kinetic target.

The frozen matrix is 4 slab thicknesses x 4 vacuum widths x 4 in-plane k meshes, for 64 SCF calculations. Bulk lattice constant, cutoffs, pseudopotential, exchange-correlation functional, and smearing are inherited without fallback values.

The gate selects the smallest lexicographic `(layers, vacuum, kmesh)` whose total-energy difference from the largest reference cell, divided across the two equivalent surfaces, is at most 1.0 meV per surface atom. Failure to load a PASS bulk handoff or failure to admit any candidate produces `HOLD`.

After PASS, the next scientific stage is clean-surface ionic relaxation. Na adsorption remains forbidden until that stage is separately preregistered.
