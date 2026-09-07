# Na/Cu(001) Computational Investigation: Corrected-Route Implementation Amendment v1.1

**Status:** frozen before corrected downstream numerical results  
**Date:** 3 August 2026  
**Repository:** `SymCUniverse/Chemistry`  
**Pilot system:** Na diffusion on Cu(001), one Na in a 4x4 primitive surface cell, nominal coverage 0.0625 ML  
**Scope:** correction and executable implementation of the critical gates identified by adversarial review of the original plan and process report  
**Supersession rule:** where this amendment conflicts with Version 0.1 of the computational-process report or its original reproducibility insert, this amendment is authoritative.

## 1. Scientific object separation

No mathematical maximum has been transferred from one theory object to another.

1. The ARC efficiency maximum is the maximum of an approach-region dynamical-efficiency function such as `eta(chi)=2 chi/(1+chi^2)`. It concerns a stable precursor mode.
2. The reaction-path saddle is the maximum electronic energy along a converged minimum-energy path. It defines an electronic activation barrier relative to a verified minimum.
3. A kinetic turnover maximum is a maximum in rate as a function of an independently varied friction or damping coordinate. It is not implied by locating a saddle and is not required for the present computational route.

The corrected workflow computes the second object. It does not reconstruct the first or assume the third. The turnover branch remains `NOT_TESTED_NO_INDEPENDENT_FRICTION_SERIES` unless an independent friction axis and independent rate evidence become available.

## 2. Evidence classes and timeline

The completed 120-SCF Cu bulk matrix remains an executed dataset. Its original automatic selection is superseded because the selector enforced lattice convergence but omitted the registered energy convergence condition. The raw SCFs and fitted summaries remain usable.

The corrected downstream route is a prospective implementation. No adsorption, NEB, saddle, prefactor, or model-rate number may be described as executed until the corresponding hashed PASS artifact exists.

The corrected timeline is:

1. Execute and retain the original 120-SCF matrix.
2. Diagnose the selector defect after the run.
3. Freeze a joint lattice-and-energy gate.
4. Add a separately executed 80 Ry, 16x16x16 holdout equation of state.
5. Re-evaluate the original candidate matrix against that holdout.
6. Freeze the full corrected surface method before downstream output exists.
7. Run negative and workflow-contract tests.
8. Launch the corrected computational route.
9. Admit no barrier or rate unless all required artifacts validate.

## 3. Accepted review findings and implemented corrections

### 3.1 Bulk selector and higher holdout

The bulk selector now requires both:

- `abs(delta_a0) <= 0.005 A`;
- `abs(delta_e0) <= 0.001 eV/atom`.

The 70 Ry, 14x14x14 point is no longer treated as an asymptotic proof merely because it is the highest point in the original matrix. A separate six-SCF holdout EOS is run at 80 Ry, 240 Ry charge-density cutoff, and 16x16x16 k mesh over the same six lattice constants. Every original candidate is then compared with the holdout. The smallest registered candidate satisfying both conditions is selected. If no candidate passes, the route stops.

The original 50 Ry, 8x8x8 selection cannot pass solely because its lattice constant is close to the reference. A negative regression test constructs that exact failure pattern and requires rejection.

### 3.2 Immutable software and pseudopotential provenance

The corrected method pins and verifies:

- Quantum ESPRESSO 7.6 source archive SHA-256;
- SSSP PBE Efficiency v2 archive SHA-256;
- Cu UPF filename and SHA-256;
- Na UPF filename and SHA-256;
- the authoritative Na cutoff metadata location and JSON pointer.

The Na probe no longer merely discovers a file while the engine uses unrelated constants. It must find exactly one Na UPF, verify its hash, locate the expected `cutoffs.json`, read `/Na`, verify the metadata values and units against the frozen method protocol, and produce `na-cu001-na-pseudo-probe-v0.2`. The mixed Cu-Na cutoffs are calculated from those extracted values. Frozen expected values are assertions, not computational inputs substituted for the metadata.

### 3.3 Electrostatic consistency

The original design converged a periodic clean slab and then changed to ESM for single-sided adsorption. The corrected design removes that discontinuity.

All 64 clean-slab convergence calculations use:

```text
assume_isolated = 'esm'
esm_bc = 'bc1'
```

The same convention is used for clean relaxation, adsorption, endpoint verification, ordinary NEB, CI-NEB, saddle analysis, and fixed-geometry sensitivity calculations.

After slab selection, an electrostatic consistency audit repeats the selected ESM slab, repeats it at the next larger vacuum, and computes one periodic diagnostic at the selected vacuum. PASS depends on the ESM next-vacuum difference remaining within the frozen 1 meV per surface atom tolerance. The periodic-vs-ESM difference is reported but cannot select or retune the ESM route.

### 3.4 Correct Cu(001) surface geometry and energy analysis

The primitive Cu(001) cell uses vectors `(a0/2,a0/2,0)` and `(-a0/2,a0/2,0)`, area `a0^2/2`, one atom per atomic layer, and alternating fcc stacking. Raw total energies for different numbers of atoms are never compared as if they were commensurate.

For each vacuum and in-plane mesh, the layer series is fit as:

```text
E_slab(L) = mu_slab L + 2 epsilon_surface
```

Vacuum and k-mesh convergence use fitted surface excess. Layer convergence uses bulk-referenced surface excess at the selected vacuum and k mesh. The downstream slab uses at least seven layers even if the convergence rule selects five, because the expanded one-sided mobility model must retain a genuinely fixed lower surface.

### 3.5 Independent clean-surface energy reproduction

The clean slab is relaxed symmetrically with the registered z-only clean-surface masks. The final relaxed geometry is then frozen and evaluated in a separate SCF. PASS requires the independent SCF to converge and reproduce the final relaxation energy within 0.001 eV. This calculation and its hashes are part of the Stage 4 handoff.

### 3.6 One-sided substrate mobility

The clean-surface z-only masks are not propagated blindly into adsorption and path calculations.

The primary single-sided model uses:

- top three Cu layers: full x, y, z motion;
- one Cu buffer layer: z-only motion;
- deeper and lower-surface Cu layers: fixed;
- Na: full x, y, z motion.

The expanded model uses:

- top four Cu layers: full x, y, z motion;
- one z-only buffer layer;
- all remaining Cu atoms fixed;
- Na fully mobile.

Both models undergo the complete adsorption, endpoint, ordinary-NEB, and CI-NEB sequence. Their full-path barriers must differ by no more than 0.005 eV. If they do not, the route stops and requires a newly preregistered larger mobile region. The direction of the barrier shift is not assumed.

### 3.7 Adsorption mechanism refusal rule

Hollow, bridge, and top starts are run at initial Na heights 2.0, 2.5, and 3.0 A for both mobility models. Site collapse and unexpected minima are retained.

If the global minimum is not the registered hollow site under either mobility model, the workflow writes `MECHANISM_REVISION_REQUIRED`, retains the computed landscape, and stops before endpoint or NEB construction. It does not coerce the system into the literature-anticipated path.

### 3.8 Ordinary NEB and CI-NEB

Ordinary NEB is run at 5, 7, and 9 images for both mobility models. The smallest image count whose forward barrier differs by no more than 0.005 eV from every larger registered count is selected.

CI-NEB is initialized from the hashed frames of the selected ordinary path. It does not restart from a fresh endpoint-only interpolation. PASS requires a complete image table and coordinate frames, an internal maximum, converged path status, and maximum internal path error no greater than 0.03 eV/A.

### 3.9 Mass-weighted nested active-region Hessians

The corrected route computes nested active-region Hessians at the minimum and saddle for:

1. Na only;
2. Na plus the four nearest top-layer Cu atoms;
3. Na plus four nearest top-layer and four nearest second-layer Cu atoms.

Each region is evaluated using central finite differences at 0.02 and 0.04 A. The dynamical matrix is mass weighted before diagonalization. PASS requires:

- no negative mode at the minimum;
- exactly one negative mode at the saddle;
- no unresolved zero mode under the frozen tolerance;
- finite-displacement convergence of the largest-region prefactor within 20 percent;
- Na+4Cu to Na+8Cu prefactor convergence within 20 percent at both displacements;
- unstable-mode alignment with the hop direction;
- maximum active-atom saddle force within 0.03 eV/A.

The Na-only and active-region prefactors are both retained. Their difference is a cancellation diagnostic. No cancellation is assumed in advance.

### 3.10 Three-dimensional downhill connectivity

The old x-y-only basin metric is prohibited. Downhill relaxations from positive and negative unstable-mode displacements must reach distinct endpoint basins under all of the following:

- periodic three-dimensional Na distance;
- Na adsorption-height agreement relative to the local top Cu layer;
- active-region RMSD including Na and the selected Cu atoms;
- final energy agreement with the target endpoint;
- endpoint site classification;
- force convergence.

A desorbed Na atom positioned over endpoint-like x-y coordinates therefore cannot pass.

### 3.11 Barrier numerical sensitivity, not pseudo-statistical uncertainty

The old sum of image-count range, CI correction, and endpoint asymmetry is removed. These quantities are not independent random errors and do not define a confidence interval.

The route reports a nonprobabilistic numerical sensitivity envelope:

```text
max(abs(E_variant - E_primary))
```

The variants are:

- higher wavefunction cutoff;
- higher charge-density cutoff;
- denser surface k mesh;
- larger vacuum;
- expanded full-path substrate mobility.

Path image sensitivity, CI refinement shift, and endpoint asymmetry remain separate diagnostics. `probability_coverage` is explicitly null.

### 3.12 Tiered barrier and rate outputs

The label `COMPUTATIONAL_FULL` is forbidden. The final coordinate carries separate fields for:

- barrier tier;
- saddle tier;
- prefactor tier;
- rate tier;
- experimental tier.

The five temperature points form one nested model-rate curve for one mechanism. They are not five independent observations and are ineligible as independent regression rows. The Atlas admission record contains one `mechanism_id` and one `independence_unit_id`.

Zero-point correction, thermal free-energy correction, friction, and linewidth remain null unless separately calculated or independently supported.

## 4. Anti-circularity implementation

The anti-circularity boundary now covers construction, system selection, numerical analysis, and prose.

1. Public Na/Cu(001) barrier, prefactor, rate, friction, linewidth, and turnover values cannot select the functional, cutoff, k mesh, slab, vacuum, supercell, adsorption site, mobility region, path, image count, Hessian region, or tolerance.
2. Na/Cu(001) is labeled a development pilot selected for tractability and prior evidentiary promise. It is not counted as an independently selected validation system.
3. Before System 2, the candidate universe, eligibility rules, candidate-list hash, selection seed, and sampling method must be frozen.
4. Systems are drawn before their outcome-favorability is inspected.
5. Failures, alternate mechanisms, nonconvergence, disagreement, and absence of turnover remain in the cohort.
6. An engine change after validation sampling creates a new engine version and requires rerunning all affected validation systems.
7. Machine output and prose must carry the barrier, saddle, prefactor, and rate tiers. A tier linter rejects the overbroad legacy label.
8. The generated integration artifact is not part of its own input hash chain. Stages 1 through 18 and the raw manifest are validated before Stage 19 is generated.

## 5. Artifact graph

The corrected route contains the following result stages:

1. bulk holdout and joint gate;
2. ESM clean-slab convergence;
3. electrostatic consistency audit;
4. clean-surface relaxation and independent SCF;
5. Na pseudopotential and isolated reference;
6. adsorption screening for both mobility models;
7. primary endpoints;
8. expanded endpoints;
9. primary path convergence;
10. expanded path convergence;
11. primary CI-NEB;
12. expanded CI-NEB;
13. substrate-mobility convergence;
14. mass-weighted active-region Hessian;
15. three-dimensional downhill connectivity;
16. barrier sensitivity envelope;
17. qualified barrier and model-rate curve;
18. computational Atlas admission;
19. generated integration-readiness verdict.

Each result artifact must identify direct dependency artifacts by basename and SHA-256. The validator rejects a stage that lists a dependency in the plan but omits its hash link. All retained raw files are independently indexed by path, size, and SHA-256. Required frozen protocols and the source manifest must exist and match their registered schemas and states.

## 6. Negative testing

The corrected local pre-launch suite contains 23 tests across three scripts plus the workflow- and artifact-contract linters.

The tests include:

- rejection of a lattice-only bulk pass;
- selection of the first joint-pass bulk candidate in a synthetic matrix;
- one-sided Cu x-y mobility;
- detection of Na desorption despite matching x-y coordinates;
- rejection of adsorption-height mismatch;
- active-region RMSD sensitivity to displaced Cu atoms;
- mass-weighted mode counting and Vineyard prefactor construction;
- robust active-region selection under surface rumpling;
- mechanism revision for a non-hollow global minimum;
- rejection of the overbroad tier label;
- deterministic validation-cohort selection;
- full synthetic artifact-DAG PASS;
- rejection after raw-file corruption;
- rejection after dependency-hash corruption;
- rejection when a frozen protocol is missing;
- rejection when a declared dependency is not hash linked;
- workflow job-DAG acyclicity;
- exact matrix cardinalities;
- correct matrix-artifact collection directories;
- preservation of raw artifacts in separate artifact-name directories;
- commit-specific, non-cancelling long-run concurrency.

The actual SSSP archive probe was also executed against the retained archive and returned the registered archive hash, Na UPF hash, and authoritative 50/150 Ry cutoff values.

## 7. Exact pre-launch commands

From the repository root:

```bash
python3 -m py_compile na_cu001_ci/*.py
bash -n na_cu001_ci/run_computational_stage_v2.sh
python3 na_cu001_ci/workflow_contract_linter_v2.py .github/workflows/na-cu001-computational-route-v2.yml
python3 na_cu001_ci/artifact_contract_linter_v2.py --plan na_cu001_ci/integration_closure_plan_v0.2.json --stage-script na_cu001_ci/run_computational_stage_v2.sh
python3 na_cu001_ci/test_closure_engine.py
python3 na_cu001_ci/test_closure_engine_v2.py
python3 na_cu001_ci/test_negative_gates_v2.py
```

The GitHub Actions `prepare` job repeats these checks after building the pinned Quantum ESPRESSO binaries, executing the higher bulk holdout, resolving the Na metadata from the pinned SSSP archive, and calculating the isolated Na reference.

## 8. Launch and refusal behavior

The corrected workflow is intentionally fail closed.

- A failed 80 Ry/16x16x16 holdout prevents slab execution.
- An absent joint bulk pass prevents slab execution.
- An incomplete ESM slab matrix prevents selection.
- Failed ESM vacuum stability prevents clean relaxation.
- A failed independent clean-surface SCF prevents adsorption.
- Ambiguous or mismatched Na metadata prevents mixed calculations.
- A non-hollow global minimum triggers mechanism revision rather than the registered NEB.
- A mobility-model barrier difference above 5 meV prevents Hessian and rate admission.
- Failed active-region convergence prevents prefactor and model-rate admission.
- Failed three-dimensional connectivity prevents saddle admission.
- Missing sensitivity variants prevent barrier admission.
- Missing tier fields or an overbroad tier label prevent Atlas admission.
- Missing, unhashed, corrupted, or circular artifacts prevent integration readiness.

A stopped workflow is a retained scientific outcome. It is not permission to relax a threshold after observing the result.

## 9. Report corrections

The original Version 0.1 report remains valuable as a record of the process before adversarial review, but the following statements are superseded:

- the clean-slab matrix is no longer periodic; it is ESM bc1 throughout;
- the electrostatic stage is a consistency audit, not a parity requirement between two different numerical models;
- the pseudopotential probe is now the source of authoritative Na cutoffs;
- adsorption and path calculations no longer inherit z-only Cu masks;
- downhill connectivity is three dimensional and includes substrate geometry and endpoint energy;
- CI-NEB begins from the selected ordinary path frames;
- the saddle analysis is mass weighted and nested across Na-only, Na+4Cu, and Na+8Cu regions;
- the barrier field is a nonprobabilistic sensitivity envelope, not a summed uncertainty;
- `COMPUTATIONAL_FULL` is forbidden;
- five temperature points are one derived curve, not five observations;
- Na/Cu(001) is a pilot, not a validation-cohort member.

## 10. Remaining limits

Even a full PASS cannot establish a universal surface law. It establishes one versioned PBE computational pilot under one idealized coverage, surface, pseudopotential family, electrostatic convention, and harmonic rate model.

The following remain outside computational closure unless separately addressed:

- exact state-matched experimental rates;
- independently supported friction or linewidth;
- anharmonic prefactors;
- finite-temperature surface reconstruction;
- coverage dependence beyond 0.0625 ML;
- defect, step, and multidimensional mechanisms not encountered in the registered landscape;
- exchange-correlation functional uncertainty;
- physical experimental replication;
- kinetic turnover without an independent friction series.

Those limits are not failures of the route. They define the honest boundary of what the route may claim.
