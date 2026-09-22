# Cp/Cu(111) perturbation-recovery execution freeze receipt

**Scientific preregistration:** preregistration/CP_CU111_PERTURBATION_RECOVERY_v1.md  
**Scientific freeze commit:** a2b51ee7e3f9449578a67368ac58f45d475aee08  
**Execution branch:** prereg/cp-cu111-perturbation-recovery-v1  
**Frozen implementation path:** experiments/cp_cu111_perturbation_recovery_v1.py  
**Frozen implementation commit:** 639529e90ad3637468575191dd7fcab5e9cffa08  
**Implementation SHA256:** 41565d207783d4883e7965b05ea887ae1c2cbd5211195c91170ea87d8cb5c65d

## Runtime freeze

- Python: 3.13.5
- NumPy: 2.3.5
- integrator: BAOAB Langevin implementation contained in the frozen script
- production trajectories: 8000 per perturbation sign per embedding
- embeddings: 40 meV and 55 meV barriers
- perturbation signs: +0.05 L and -0.05 L
- timestep: 0.001 ps
- duration: 15 ps
- early-response window: 0-0.5 ps
- early sampling: 0.005 ps
- long-time sampling: 0.1 ps
- MSD fitting interval: 4-15 ps
- bootstrap replicates: 2000
- + perturbation seed: 62001
- - perturbation seed: 62002
- bootstrap seed: 63001
- paired/common seed design across the two embeddings is frozen for variance reduction.

## Exact-code preflight

The exact implementation identified above was executed before production and passed all frozen gates:

- G1 harmonic recovery RMS = 2.418926450725053e-06 <= 0.01
- G2 equipartition ratio = 1.0092139137870209, within 3% of 1
- G3 free Langevin diffusion D_est / D_exact = 1.0109959830784296, within 5%
- G4 40 meV barrier relative error = 0; curvature relative error = 9.727552097160697e-12
- G4 55 meV barrier relative error = 0; curvature relative error = 1.1723999548962638e-10
- G5 timestep response RMS, 40 meV = 0.04960257735261048 <= 0.05
- G5 timestep response RMS, 55 meV = 0.044764494770729635 <= 0.05
- G6 amplitude-linearity RMS, 40 meV = 0.03554982108534288 <= 0.05
- G6 amplitude-linearity RMS, 55 meV = 0.02970575272910874 <= 0.05
- G6 sign-symmetry RMS = 0 for both embeddings under antithetic preflight
- aggregate preflight result = PASS

The earlier brute-force/variance-sensitive development checks are not confirmatory evidence. The exact frozen code above is the production implementation.

## Implementation correction lineage

Before this execution freeze and before any production output was opened, two implementation-completeness defects were corrected:

1. the frozen script was made to execute the preregistered timestep-convergence gate explicitly;
2. first-passage well identity was corrected to use the physical periodic lattice coordinate rather than a coordinate shifted by the imposed perturbation.

Neither correction changed the frozen model, physical inputs, perturbation magnitude, endpoint definitions, decision thresholds, barrier values, damping convention, or scientific claims.

## Production firewall

After this receipt is committed, production output may be generated but the following are frozen and may not be retuned to rescue an outcome: model family, physical parameters, barriers, perturbation, timestep, duration, ensemble size, random seeds, response window, MSD window, endpoints, bootstrap count, equivalence margin, directional criteria, and pass/fail logic.

A failed or indeterminate claim remains failed or indeterminate under v1. Any revised scientific model requires a new preregistration/version and new decisive evidence.
