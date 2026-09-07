# System 2 Selection and Source Audit v0.1 — CO/Cu(111)

**System:** CO diffusion on Cu(111)
**Role:** prospective external validation target for the layered ChemSA chemistry pipeline
**Current state:** `PROVISIONAL_SELECTED_SOURCE_AUDIT_ACTIVE`
**Computation state:** not launched

## 1. Selection record inherited from the attached recommendation

The recommendation used the following predeclared eligibility criteria:

1. single or simple few-atom adsorbate on a well-defined low-index metal/semiconductor surface;
2. published barrier-relevant evidence from a source distinct from the dynamical/vibrational source;
3. published dynamical/vibrational characterization of the well;
4. no eligibility condition based on expected SymC/ChemSA agreement.

The first draw reportedly selected benzene/Cu(111). It was rejected because the previously declared simple-adsorbate rule had not been applied strictly to the candidate pool. Propane/Pt(111) and graphene/Ni(111) were removed on the same rule-enforcement pass. The corrected pool then selected CO/Cu(111).

### Selection-record limitation

The supplied recommendation states that a sorted candidate list, fixed seed, and hash-mod-pool-size rule were used, but the supplied text does not contain the complete corrected candidate list, the seed, or the selection hash. Therefore the *narrative* supports the selection logic, but the random selection is not yet independently reproducible from the retained record.

Until those exact fields are recovered or reconstructed without changing the selected target, the system is labeled `PROVISIONAL_SELECTED`, not `FULLY_REPRODUCIBLE_RANDOM_SELECTION`.

This limitation does not block literature/source investigation. It does block claiming that the selection procedure itself has already been independently reproduced.

## 2. Primary published evidence located

### A. Independent low-coverage STM diffusion source

K. L. Wong, B. V. Rao, G. Pawin, E. Ulin-Avila, and L. Bartels, "Coverage and nearest-neighbor dependence of adsorbate diffusion," *Journal of Chemical Physics* **123**, 201102 (2005), DOI `10.1063/1.2124687`.

Published identity is verified independently through PubMed. A public author-hosted copy of the published article was inspected.

For isolated CO/Cu(111), the article reports:
- diffusion barrier: `75 ± 5 meV`;
- attempt frequency: `(5.3 ± 0.4) × 10^7 Hz`.

The study is based on time-lapsed low-temperature STM and is authored by a group distinct from the later Cambridge He-spin-echo study. It is therefore a strong independent kinetic comparator.

The article also states an important methodological warning: standard density-functional treatments often fail to recover the experimentally observed on-top equilibrium site for CO/Cu(111).

### B. Helium spin-echo diffusion/dynamics source

P. R. Kole, H. Hedgeland, A. P. Jardine, W. Allison, J. Ellis, and G. Alexandrowicz, "Probing the non-pairwise interactions between CO molecules moving on a Cu(111) surface," *Journal of Physics: Condensed Matter* **24**, 104016 (2012), DOI `10.1088/0953-8984/24/10/104016`.

The published abstract reports:
- CO preferentially occupies top sites and visits bridge configurations along the motion coordinate;
- motion remains uncorrelated up to at least `0.10 ML` in the reported regime;
- effective diffusion barrier from temperature dependence: `98 ± 5 meV`;
- a Langevin molecular-dynamics model represents the data using an adiabatic hopping barrier of `123 meV`.

The `123 meV` value is **model calibrated to the HeSE data** and cannot be used as independent computational validation. The `98 ± 5 meV` effective barrier is an experimental kinetic extraction and may be used as a post-freeze comparator if the new first-principles route is not tuned to it.

### C. Low-frequency frustrated-translation dissipation source

J. P. Culver, M. Li, Z.-J. Sun, R. M. Hochstrasser, and A. G. Yodh, "Temperature-dependent coupling of low frequency adsorbate vibrations to metal substrate electrons," *Chemical Physics* **205**, 159-166 (1996), DOI `10.1016/0301-0104(95)00376-2`.

The article directly studies the CO/Cu(111) low-frequency frustrated lateral translation following femtosecond excitation and reports a model-resolved zero-temperature electron coupling rate:
- `gamma_e^0 = 25 ± 7 GHz`;
- equivalent quoted time scale `tau_e^0 = 40 ± 8 ps`.

The paper explicitly treats electron and phonon reservoirs separately and obtains the electronic coupling through a dynamical charge-transfer model.

**Dissipation-provenance status:** `PASS_MODEL_RESOLVED`, not `PASS_DIRECT_POPULATION_LIFETIME`.

**Important limitation:** the ultrafast excited-electron experiment and its overlayer conditions are not automatically condition-matched to the low-coverage thermal diffusion experiments. No scalar transfer to a diffusion friction is licensed at this stage.

### D. Electronic-structure method warning

M. Gajdos and J. Hafner, "CO adsorption on Cu(111) and Cu(001) surfaces: Improving site preference in DFT calculations," *Surface Science* **590**, 117-126 (2005), DOI `10.1016/j.susc.2005.04.047`.

The published study reports that ordinary GGA predicts the wrong adsorption-site ordering for CO/Cu(111), favoring a hollow site rather than the experimentally observed top site. Their molecular DFT+U treatment restores the top-site preference.

Independent later work also identifies CO/Cu(111) as a standard case in which semilocal DFT can fail qualitatively in site ordering.

**Consequence for System 2:** the Na/Cu(001) PBE setup cannot simply be inherited as an unquestioned electronic-structure model. System 2 requires a prospectively defined method-calibration gate before a diffusion barrier can be treated as physical evidence.

## 3. Evidence independence matrix

| Quantity | Source | Current type | Independence use |
|---|---|---|---|
| isolated diffusion barrier `75 ± 5 meV` | Wong et al. 2005 STM | experimental kinetic extraction | primary held-out comparator |
| isolated attempt frequency `(5.3 ± 0.4)×10^7 Hz` | Wong et al. 2005 STM | experimental kinetic extraction | primary held-out rate/prefactor comparator |
| effective barrier `98 ± 5 meV` | Kole et al. 2012 HeSE | experimental kinetic extraction | secondary held-out comparator |
| adiabatic barrier `123 meV` | Kole et al. 2012 | Langevin/PES value calibrated to HeSE dynamics | **not independent validation** |
| low-frequency electronic coupling `25 ± 7 GHz` | Culver et al. 1996 | model-resolved spectroscopy | candidate dissipation input only after coordinate/condition validation |
| top-site preference | multiple adsorption experiments; discussed explicitly in Wong 2005 and DFT literature | structural calibration observable | allowed for method calibration, not a kinetic holdout |

The STM, HeSE, ultrafast spectroscopy, and electronic-structure studies arise from distinct publication lineages. Shared system identity does not by itself create independence; each numerical field is typed according to how it was obtained.

## 4. Exposure status and anti-circularity rule

The numerical kinetic outcomes listed above are now known. System 2 therefore cannot honestly be described as outcome-blind.

The protection against motivated fitting is instead:

1. freeze the electronic-structure method-selection protocol before running the diffusion barrier calculation;
2. permit method calibration only against non-kinetic structural/spectroscopic observables declared in advance;
3. prohibit use of `75 meV`, `98 meV`, `123 meV`, the STM attempt frequency, HeSE rates, or later diffusion coefficients to choose cutoffs, slab size, functional, U value, adsorption path, force thresholds, image count, or prefactor model;
4. compare the completed frozen prediction against the kinetic literature only after the Reaction-Path Engine closes.

## 5. Reaction-Path Engine requirements for CO/Cu(111)

### Inheritable infrastructure

The following may be reused from the Na/Cu(001) development pilot as software/audit machinery:
- artifact hashing and provenance;
- fail-closed gate semantics;
- safe QE total-force parsing;
- checkpoint/restart mechanics;
- independent SCF reproduction;
- slab/adsorption/path convergence framework;
- raw-output retention and stage-local hash anchoring once implemented.

### Physics that must be recomputed

- Cu(111) slab convergence and electrostatic convention checks;
- C and O pseudopotential provenance and mixed cutoff selection;
- CO adsorption geometry/site/orientation screen;
- adsorption coverage/supercell convergence appropriate to the selected state point;
- top/bridge/fcc/hcp energetic ordering under the selected electronic-structure treatment;
- endpoint equivalence for the nearest-neighbor path;
- ordinary and climbing-image NEB convergence;
- saddle verification and Hessians;
- qualified multidimensional prefactor;
- rate model and uncertainties.

If the final computed global minimum is not compatible with the registered mechanism under the selected method, the result is retained as a method/mechanism HOLD rather than corrected toward the literature value.

## 6. Method-calibration gate — required before expensive production work

Because CO/Cu(111) is a documented site-preference failure case for standard semilocal DFT, a method must be selected using a calibration set that is **disjoint from the held-out diffusion kinetics**.

Allowed calibration observables may include:
- Cu bulk structural convergence;
- gas-phase CO bond length and vibrational frequency;
- experimentally established top-site adsorption preference;
- adsorption geometry and, if used, a separately declared adsorption-energy reference.

Forbidden method-selection observables:
- STM diffusion barrier or attempt frequency;
- HeSE effective barrier or hopping rates;
- HeSE-calibrated `123 meV` PES barrier;
- any later diffusion coefficient derived from those kinetic data.

Candidate electronic-structure treatments must be chosen for implementability and predeclared physical criteria, not because their diffusion barrier lands near the known experimental barrier.

**Current gate:** `METHOD_SELECTION_REQUIRED`.

## 7. Reaction-Coordinate Consistency Validator — preliminary state

Candidate joined coordinate:
- stable-well observable: low-frequency frustrated lateral translation of CO;
- reaction path: lateral motion from one top adsorption site through the bridge region to a neighboring top site.

This is a plausible coordinate match, but it is not yet a validator PASS because:
- the normal-mode projection from the calculated minimum onto the diffusion path has not been computed;
- the ultrafast dissipation experiment is not yet state-condition matched to the low-coverage thermal diffusion target;
- electronic and phononic contributions need separate treatment rather than collapse to an unqualified scalar.

**Preliminary state:** `HOLD_PROJECTION_AND_CONDITION_MATCH_PENDING`.

## 8. Dissipation Provenance Validator — preliminary state

The `25 ± 7 GHz` Culver coupling is retained as a **candidate model-resolved electronic contribution** to dissipation of the frustrated translation. It is not yet the diffusion friction and must not be inserted directly into `chi = gamma/(2 omega)` for the thermal hopping coordinate.

The validator must determine:
- exact overlayer/coverage conditions;
- the mode frequency used by the dissipation model;
- electron versus phonon coupling contributions;
- whether a frequency-dependent or memory-kernel treatment is required;
- whether the calculated reaction-coordinate mode projects onto the measured frustrated translation strongly enough to justify use.

## 9. Atlas consequence if Reaction-Path Engine closes before dissipation does

A successful first-principles CO/Cu(111) barrier/prefactor calculation may enter the computational Barrier-Rate Atlas extension with:

- `barrier_tier = FIRST_PRINCIPLES_CONVERGED`;
- `prefactor_tier` explicitly qualified by the Hessian treatment;
- `rate_model_tier` explicitly qualified;
- `dissipation_tier = NONE` or `MODEL_RESOLVED_UNVALIDATED_FOR_TRANSFER`;
- `chemsa_eligibility = false` until both validators pass.

No damping quantity is to be invented to complete the row.

## 10. Immediate next work

1. reconstruct and freeze the complete System 2 candidate-pool/seed/hash record if recoverable;
2. perform the electronic-structure method feasibility/calibration audit without using kinetic outcomes;
3. define the CO/Cu(111) computational state point and coverage-convergence plan;
4. define adsorption-site/orientation starting matrix before production results;
5. prepare generic Reaction-Path Engine interfaces while leaving the live Na/Cu(001) paths untouched;
6. keep the Reaction-Coordinate and Dissipation validators as explicit downstream gates, not implied steps.