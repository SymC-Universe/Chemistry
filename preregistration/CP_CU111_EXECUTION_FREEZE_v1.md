# Cp/Cu(111) perturbation-recovery execution freeze v1

- Scientific preregistration commit: a2b51ee7e3f9449578a67368ac58f45d475aee08
- Preregistration receipt commit: c6c0dc29d6658217cd9165a00ff1e44a5651cb92
- Production implementation commit: 85bead206bd526e6bf7e24b6d96145e363dd690f
- Final model/preflight code freeze commit (contains production parent): d86bcb748c585c215fcb1235997db9d4118afa5d
- Branch: prereg/cp-cu111-perturbation-recovery-v1
- Python: 3.13.5
- NumPy: 2.3.5
- Local model/preflight code SHA256: 566afbdf96d86f9aeaaf717f2efadb073b88dc074a8399b01239a4262bba3b28
- Local production code SHA256: 098cd859f60a752feea406347782ca1ca2bbe843ee8c2f5f1b7cd009f6125e72
- Final preflight JSON SHA256: edf33f7369d82632749c174717f06f3f7a17ef2d5a5a1d1ffa8afcb3c7876784

## Preflight disposition
All six frozen gates PASS after one mechanical correction cycle. The correction changed only estimator/sampling implementation: paired random streams for the amplitude-linearity gate, analytic curvature evaluation for the already frozen potential, and a finite-time OU-corrected free-diffusion estimator to reduce resource cost. No scientific input, potential, threshold, perturbation, endpoint, or expected direction changed.

## Production freeze
- dt: 0.001 ps
- recovery trajectories: 20,000 per sign per embedding
- recovery duration: 0.5 ps
- recovery recording interval: 0.005 ps
- long trajectories: 5,000 per embedding
- long duration: 100 ps
- long recording interval: 0.5 ps
- MSD fit interval: 20-100 ps
- displacement: +/-0.05 L
- bootstrap: B=2000, seed 92026
- barrier 40 seeds: recovery + 41040, recovery - 42040, long 40040
- barrier 55 seeds: recovery + 41055, recovery - 42055, long 40055

## Resource preflight
A free-Langevin benchmark of 1,000 trajectories for 20 ps required about 1.13 s in the current container. The production plan is therefore bounded and split by embedding for independent restart/recovery.

No production trajectory has been generated at the time of this execution freeze.
