# Cp/Cu(111) prospective computational perturbation-recovery preregistration v1

**Project:** Chemistry Stability Architecture / ChemSA  
**System:** cyclopentadienyl (Cp, C5H5) on Cu(111)  
**Status at creation:** preregistration candidate; no production trajectories from the two-embedding confirmatory design have been opened.  
**Governance:** SymC GOM v0.8.1 MFR-14, Sections 15.3, 21.7, 25, and 13.2.  
**Intended maturity:** P0-Q prospective computational qualification of a physically anchored model. This is not independent empirical confirmation of Cp/Cu(111) in nature because the system and source literature have already been inspected.

## 1. Frozen question and claims

### Claim CP-PR-01: local recovery invariance under matched local dynamics
For two periodic Cp/Cu(111) embeddings with the same local well curvature, mass, temperature, and Langevin damping but different independently reported barrier heights (40 meV and 55 meV), a sufficiently small displacement perturbation will produce equivalent early-time normalized local recovery over 0 <= t <= 0.5 ps.

### Claim CP-PR-02: embedding-dependent global kinetics
Under the same local mode and damping, the 55 meV embedding will produce slower long-time transport than the 40 meV embedding, operationalized as lower diffusion coefficient and longer first-passage time between neighboring wells.

### Claim CP-PR-03: joint chi-X interpretation
If CP-PR-01 and CP-PR-02 both survive, the declared model demonstrates that a licensed local scalar chi can remain unchanged while broader embedded organization changes realized hopping and transport. This supports a model-level joint chi-X result, not an independent empirical law of Cp/Cu(111).

No claim of universal chemistry, catalytic optimality, or independent experimental confirmation is preregistered.

## 2. MFR-14 record

### MFR-01 - Frozen claim
Claim IDs: CP-PR-01, CP-PR-02, CP-PR-03. Scope is the declared one-dimensional periodic Langevin model anchored to published Cp/Cu(111) quantities. Version: v1.

### MFR-02 - Hypothesis provenance
- DOMAIN_THEORY: underdamped Langevin recovery and diffusion in periodic potentials.
- FRAMEWORK_DERIVED: local chi versus embedded X separation and recovery qualification.
- DATA_DERIVED: system choice and numerical anchors come from already inspected Cp/Cu(111) literature; therefore no claim of untouched system selection is made.

### MFR-03 - Target object / native observable
Primary observables are ensemble-mean local displacement response after a frozen perturbation, first-passage time from the initial well, and long-time unwrapped mean-square displacement/diffusion coefficient. These are native outputs of the Langevin model; no internal SymC score is used as the decisive observable.

### MFR-04 - Representation and validity regime
The production model is one-dimensional motion along a minimum-energy diffusion path in a periodic surface potential with a Markovian Langevin bath:

m xddot = -dV/dx - m eta_L xdot + sqrt(2 m eta_L k_B T) xi(t),

with delta-correlated unit Gaussian xi(t). The model is classical, Markovian, dilute/single-particle, and restricted to a single diffusion path. It does not represent the full two-dimensional Cu(111) surface, internal Cp modes, non-Markovian substrate response, quantum nuclear dynamics, adsorbate-adsorbate interactions, or electron-hole-pair friction separately. Results are not promoted outside this validity regime.

### MFR-05 - Strongest relevant native comparator
COMPARATOR_IDENTIFIED.
- Local recovery comparator: exact damped-harmonic Langevin mean response using the same omega_0 and eta_L.
- Global dynamics comparator: ordinary Langevin simulation of the same frozen periodic potential. ChemSA is not claimed to outperform Langevin dynamics; the added-value question is whether the qualification architecture correctly separates local recovery from embedding-dependent kinetics.

### MFR-06 - Null / competing explanations
1. Different barrier embeddings may alter the response already within 0.5 ps because higher-order potential terms matter despite equal curvature.
2. Apparent kinetic differences may be stochastic uncertainty rather than a reproducible barrier effect.
3. Any surviving local/global separation is expected by ordinary mechanics and does not by itself establish a new physical law; the framework contribution is the predeclared inference boundary and promotion rule.

### MFR-07 - Expected response
- CP-PR-01: normalized local responses for the 40 and 55 meV embeddings are equivalent within the frozen early-time margin; both display underdamped recovery morphology.
- CP-PR-02: D_55 < D_40 and median FPT_55 > median FPT_40.
- CP-PR-03: local chi is identical by construction while the long-time kinetic observables differ.

### MFR-08 - Decision / adjudication rule
CP-PR-01 passes only if:
1. the scaled responses for +delta and -delta are sign-symmetric within the perturbation-linearity gate;
2. both embeddings show at least one local-response zero crossing before 0.5 ps; and
3. the RMS difference between the two normalized ensemble-mean local responses over 0 <= t <= 0.5 ps is <= 0.05, with the bootstrap 95% upper confidence bound also <= 0.05.

CP-PR-02 passes only if both preregistered directional kinetic criteria are satisfied:
- bootstrap 95% CI for log(D_55 / D_40) lies entirely below 0;
- bootstrap 95% CI for log(median_FPT_55 / median_FPT_40) lies entirely above 0.

CP-PR-03 passes only if CP-PR-01 and CP-PR-02 both pass. Partial outcomes remain partial and are not redescribed as full closure.

### MFR-09 - Uncertainty, tolerance, and indeterminate zone
- Ensemble uncertainty: nonparametric bootstrap over independent trajectories, B = 2000, fixed before production.
- Local equivalence margin: 0.05 in normalized displacement response. This is conservative relative to the approximately 1% leading nonlinear-force correction at the largest preregistered displacement.
- Numerical convergence: primary production timestep 0.001 ps; convergence comparison at 0.0005 ps must change preregistered observables by <= 5%.
- If a directional kinetic CI includes zero, CP-PR-02 is INDETERMINATE rather than passed.
- If required preflight gates fail, the production test is INVALID_TEST / NOT_RUN, not a scientific failure.

### MFR-10 - Evidence-independence / leakage map
Known prior exposure:
- Cp/Cu(111) was selected after inspection of the published literature and deposited HeSE data.
- Published diffusion barrier/friction and vibrational-mode facts are known.
- Earlier development work inspected raw HeSE polarization and an unrelated raw-dephasing reduction.

Frozen separation for this test:
- The two-embedding 40-versus-55 meV perturbation-recovery design has not been run at preregistration.
- Production random seeds and production trajectories are unopened.
- No parameter may be tuned against the production recovery, FPT, or diffusion outputs.
- Comparison with published Cp kinetics is contextual/same-lineage only unless a genuinely untouched comparator is separately registered before inspection.

### MFR-11 - Multiplicity / search-space accounting
Primary confirmatory family contains three hierarchical claims: CP-PR-01 -> CP-PR-02 -> CP-PR-03. CP-PR-03 is evaluated only if both parent claims pass. No alternate potential family, damping value, temperature, fitting window, perturbation size, or outcome metric may replace the frozen primary definitions after production output is opened.

Sensitivity analyses, if later run, are explicitly secondary and cannot rescue a failed primary claim.

### MFR-12 - Freeze identity and untouched decisive test
This preregistration is frozen in the canonical SymC-Universe/Chemistry GitHub repository before production trajectories are generated. The decisive evidence is a fresh production ensemble generated after the final analysis-code commit is frozen. Exact code commit, Python/NumPy versions, seed registry, and production artifact hashes will be appended to the execution receipt before outcome interpretation.

### MFR-13 - Explicit falsifiers
- CP-PR-01 is falsified if the early responses fail the 0.05 equivalence rule, fail perturbation sign symmetry, or do not show the preregistered underdamped morphology.
- CP-PR-02 is falsified if either preregistered kinetic effect is significantly opposite in direction. It is indeterminate if uncertainty spans zero.
- CP-PR-03 is falsified if either parent claim is falsified and is indeterminate if either parent is indeterminate.

### MFR-14 - Precommitted failure consequence
A failure narrows or rejects the corresponding model-level joint chi-X claim. Parameters, thresholds, potential form, or endpoints will not be retuned under the same freeze. A scientifically motivated revised model may be developed only as a new version with new promotion debt and a new untouched decisive run.

## 3. Frozen physical inputs

| Quantity | Frozen value | Role / source lineage |
|---|---:|---|
| Temperature | 300 K | matched Cp/Cu(111) vibrational measurement condition |
| Cp mass | 65.095 u | C5H5 composition |
| Cu bulk lattice constant | 3.615 A | experimental Cu lattice constant |
| Adjacent hollow-path period L = a0/sqrt(6) | 1.47581757 A | geometric derivation from Cu(111) |
| Local T-mode energy | 4.6 meV | Lechner et al., PCCP 2015, DOI 10.1039/C5CP03123K |
| omega_0 = E/hbar | 6.98863026 ps^-1 | derived before production |
| local spring constant | 5.27935489 N/m | derived from mass and omega_0; source paper reports about 5.3 N/m |
| Langevin eta_L | 2.6 ps^-1 | source-model vibrational dephasing/friction convention, PCCP 2015 and JCP 2013 Eq. (1) convention |
| local chi = eta_L/(2 omega_0) | 0.18601642 | model-conditional scalar; identical in both embeddings |
| Embedding A barrier | 40 meV | Hedgeland et al., PRL 2011, DOI 10.1103/PhysRevLett.106.186101 |
| Embedding B barrier | 55 meV | Sacchi et al., JPC C 2011, DOI 10.1021/jp2049537 |

The 2.6 ps^-1 value is not treated as independently validated friction by this test; it is a source-model input under the declared Langevin convention.

## 4. Frozen potential family

For each barrier Delta in {40, 55} meV:

V_Delta(x) = A_Delta [1 - cos(q x)] + B_Delta [1 - cos(2 q x)],
q = 2 pi / L.

A_Delta = Delta/2. B_Delta is chosen analytically so both embeddings have the same local curvature k:

B_Delta = (k/q^2 - A_Delta) / 4,

with consistent energy units.

| Barrier Delta | A_Delta | B_Delta |
|---:|---:|---:|
| 40 meV | 20.000000 meV | -0.455186 meV |
| 55 meV | 27.500000 meV | -2.330186 meV |

Each potential therefore has the frozen barrier at x = L/2 and the same second derivative k at x = 0. The coefficients do not introduce an additional stationary point between a minimum and the barrier.

## 5. Frozen perturbation and outputs

Primary perturbation: initialize a conditional thermal ensemble in the central well at 300 K, then displace every member by delta = +0.05 L or -0.05 L without changing its velocity. The displacement magnitude is 0.0737909 A and its harmonic energy is approximately 0.897 meV, much smaller than k_B T = 25.852 meV.

A second amplitude, 0.025 L, is used only for the preflight linearity gate and is not an alternate primary endpoint.

Primary recovery output:
R_Delta(t) = <x_local(t)> / delta,
where x_local is position relative to the nearest well center. The early window is frozen at 0 <= t <= 0.5 ps.

Kinetic outputs:
- first-passage time to either neighboring well;
- unwrapped mean-square displacement;
- long-time diffusion coefficient from the frozen post-equilibration fitting interval defined in the execution code before production.

No alternative recovery statistic or kinetic endpoint may replace these after production data are opened.

## 6. Mandatory preflight gates before production

Production is authorized only if all gates pass:

1. **Analytic harmonic recovery:** deterministic/noise-averaged implementation reproduces the exact damped-harmonic response for omega_0 and eta_L with normalized RMS error <= 0.01 over 0-2 ps.
2. **Equipartition:** equilibrium <m v^2>/(k_B T) is within 3% of 1.
3. **Free Langevin diffusion:** with V=0, D_est agrees with k_B T/(m eta_L) within 5%.
4. **Potential identity:** numerical barrier and minimum curvature agree with their frozen analytic values to relative error <= 1e-8.
5. **Timestep convergence:** dt = 0.001 ps and 0.0005 ps change each preregistered preflight observable by <= 5%.
6. **Perturbation linearity:** after amplitude normalization, the 0.025 L and 0.05 L recovery curves differ by RMS <= 0.05 over 0-0.5 ps for both signs.

A failed gate receives at most one mechanical correction cycle if the scientific specification is unchanged. Repeated or science-changing failure circuit-breaks the experiment and preserves rc21 without this extension.

## 7. Execution freeze still required

This document freezes the scientific question, model, inputs, perturbation, endpoints, gates, and adjudication. Before production, the exact implementation must be committed and a separate execution receipt must freeze:

- code commit SHA;
- Python and NumPy versions;
- BAOAB implementation identity;
- production trajectory count and duration after a resource-only preflight establishes the minimum ensemble needed for stable bootstrap intervals;
- random-seed registry;
- output schema;
- artifact paths/hashes;
- exact MSD fitting interval, selected from preflight without inspecting production trajectories.

Resource-only choices may scale trajectory count upward but may not change the scientific model or endpoints.

## 8. Literature anchors

- H. Hedgeland et al., Physical Review Letters 106, 186101 (2011), DOI 10.1103/PhysRevLett.106.186101.
- M. Sacchi et al., Journal of Physical Chemistry C 115, 16134-16141 (2011), DOI 10.1021/jp2049537.
- B. A. J. Lechner et al., Journal of Chemical Physics 138, 194710 (2013), DOI 10.1063/1.4804269.
- B. A. J. Lechner et al., Physical Chemistry Chemical Physics 17, 21819-21823 (2015), DOI 10.1039/C5CP03123K.

## 9. Promotion ceiling

Even if all three claims pass, the allowed statement is limited to:

> In a preregistered, physically anchored Cp/Cu(111) Langevin calculation, matched local curvature and damping produced equivalent early local recovery across two surface embeddings while the different barriers reorganized long-time hopping/transport, demonstrating a model-level distinction between licensed local chi and embedded system behavior X.

The result may not be described as independent empirical validation of Cp/Cu(111), proof of a universal chi-X law, or proof that the 2.6 ps^-1 dephasing quantity is a universally transferable friction coefficient.
