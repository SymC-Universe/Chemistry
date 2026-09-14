# Epistemic table: predecessor rejection -> present Stability Architecture

**Status:** adversarial-review evidence map  
**Date:** 14 September 2026  
**Predecessor review source:** `CHEMPHYS-D-26-01542_report.pdf`  
**Current reader-facing title:** **Stability Architecture for Chemical Systems: A Diagnostic and Predictive Engine with an Expandable Stability Atlas**

## Purpose

The predecessor was rejected because its central physical interpretation was not established, not because of presentation defects. The rejection report is therefore treated as an adversarial design specification rather than as a rebuttal target.

The present work does **not** claim that the predecessor's universal commitment interpretation was eventually proven. The central commitment claim was abandoned. The surviving questions were decomposed into separately testable layers: local generator structure, admissible scalar reduction, observable/provenance qualification, predictive response, barrier/rate evidence, and Atlas-level comparison.

The table below records what failed, what changed, what is currently supported, and what remains bounded or open.

| ID | Referee finding that drove rejection | Why the predecessor failed | Corrective design decision in the present work | Current evidence / implementation | Present epistemic status |
|---|---|---|---|---|---|
| R1 | The proposed commitment efficiency `eta(chi0)=2chi0/(1+chi0^2)` was not derived from barrier crossing or first-passage theory. | A mathematical damping boundary was promoted into a chemical commitment law without a derivation connecting the two. | The commitment law was withdrawn rather than repaired by assertion. Local stability classification is no longer interpreted as reaction commitment. | The current Main explicitly states that local classification does not determine reaction rate, yield, commitment probability, or selectivity. A constructive pair with identical local architecture but an approximately 148-fold rate difference makes the scope fence executable. | **RETRACTED / REPLACED BY A SCOPE FENCE.** No universal commitment function is claimed. |
| R2 | The stable precursor-well oscillator contained no activation barrier, product basin, absorbing boundary, thermal stochastic force, or reactive current. | Stable-well relaxation and barrier crossing were treated as though the first supplied the second. | Stable-well stability architecture and barrier-crossing kinetics were separated into different evidence layers. | The Engine classifies supplied local generators. The independently governed Barrier-Height/Rate Atlas carries barriers, model rates, observed rates, grades, and refusals. No admitted Atlas coordinate uses local chi as a substitute for a barrier-local transmission model. | **SEPARATED.** The local Engine and the kinetic Atlas are related only through an explicitly justified future bridge, not by default. |
| R3 | Spectroscopic linewidths, solvent longitudinal relaxation times, and electronic hybridization widths were physically different observables and had not been shown to estimate one common friction. | Heterogeneous measurements were treated as interchangeable routes to one scalar. | Observable identity became a provenance gate. A scalar mechanical chi is reported only after the physical object and reduction are licensed. | The current pipeline distinguishes population lifetime, homogeneous dephasing, pure dephasing, inhomogeneous broadening, phonon coupling, electronic friction, projected friction, memory kernels, rate-fitted friction, and model-resolved coupling. General first-order generators receive modal/pole descriptors rather than a forced mechanical chi. | **GATED.** No estimator equivalence is assumed. |
| R4 | A vibrational linewidth may contain population relaxation, pure dephasing, phonon coupling, anharmonicity, and inhomogeneous broadening, so total width is not automatically reaction-coordinate friction. | Width-to-damping conversion ignored the decomposition required by spectroscopy. | A three-step admission procedure was built: homogeneous isolation; lifetime/dephasing/orientational separation; mechanical placement only from qualified lifetime damping. | The Main and Supplementary sources use `1/T2 = 1/(2T1) + 1/T_phi + ...` with an explicit orientational term where applicable. The Rh(CO)2acac worked trajectory separates source-anchored width growth from illustrative lifetime-derived chi. | **DIRECTLY ADDRESSED.** Total linewidth is not admitted as mechanical damping by default. |
| R5 | A Newns-Anderson electronic hybridization energy is not automatically a projected nuclear electronic-friction coefficient. | Electronic width and nuclear damping were conflated without a demonstrated projection. | Automatic hybridization-to-nuclear-friction conversion was prohibited. Projection and physical-coordinate identity must be explicit. | The reaction-coordinate consistency and dissipation-provenance validators require a justified projection and distinguish electronic friction from other widths/couplings. | **REFUSED UNLESS PROJECTED.** No automatic conversion survives from the predecessor. |
| R6 | The solvent-based route depended strongly on effective mass, displacement, and solvent-mode frequency; the cited uncertainty crossed underdamped, near-critical, and overdamped regimes. | A model-sensitive estimate was given more categorical meaning than its uncertainty supported. | Model-derived coordinates are typed as model-derived, uncertainty is retained, and regime labels are withheld when the uncertainty/projection/condition gate does not close. | Current admission logic includes condition mismatch, projection unresolved, model-resolved, and no-data states rather than forcing all systems onto one scalar axis. | **GATED / REFUSAL-CAPABLE.** A model-dependent route cannot obtain a stronger status from a favorable central value. |
| R7 | Markovian reduction should be justified by bath-memory time relative to the local reaction-coordinate timescale, not the overall reaction waiting time. | The relevant time-scale separation was not demonstrated. | Memory structure is treated as part of the physical model rather than silently collapsed into a scalar damping number. A Markovian scalar reduction requires a local-coordinate time-scale license; otherwise the object remains frequency dependent or non-Markovian. | The current dissipation architecture explicitly distinguishes generalized-Langevin memory kernels and frequency-dependent/non-Markovian damping from scalar damping. | **PARTIALLY CLOSED, REVIEW TARGET.** The semantic firewall exists; adversarial review must verify that every manuscript application states the local time-scale criterion wherever a Markovian reduction is invoked. |
| R8 | The N2/K-Fe result imported an electronic-friction-related quantity without enough computational detail in the manuscript. | A key entry depended on provenance that could not be independently reconstructed from the manuscript. | Source identity, role, and reproducibility status became explicit admission fields. Weak or incomplete chains receive lower grade, HOLD, or refusal rather than silent promotion. | The current source gate blocks unsourced numerical transformations; Atlas records preserve source relationships and evidence grade. The source gate is explicitly described as a disclosure/blocking device, not a magical verification that a citation supports a value. | **DESIGN DEFECT CLOSED; ENTRY-SPECIFIC SUFFICIENCY REMAINS REVIEWABLE.** No source citation alone promotes a number. |
| R9 | The cyclopropane IVR width was partly inferred from RRKM kinetics and then used to interpret the same kinetics. | The target outcome entered both predictor construction and validation, creating circularity. | Rate-derived barriers/frictions cannot independently validate the rate from which they were derived. Circular candidates are retained as refusals or descriptive controls. | The Barrier-Height/Rate Atlas candidate register explicitly refuses rate-derived activation quantities as independent barrier evidence and refuses post-comparison method shopping. Large residuals remain visible rather than retuned away. | **DIRECTLY ADDRESSED BY EVIDENCE FIREWALL.** Circular evidence may be descriptive but cannot be confirmatory. |
| R10 | The report concluded that chi0 had not been established as a quantitatively meaningful and universal descriptor of chemical commitment. | The paper's central universal claim exceeded the demonstrated physics. | The Stability Architecture no longer treats chi as universal or as the definition of chemical stability. Scalar chi is only one compressed coordinate where a licensed reduction exists; modal/subspace structure and system organization remain coequal. | General generators are classified without forcing a mechanical chi. The Atlas contains barrier/rate evidence independently of local chi. Conglomeration preserves heterogeneous valid representations rather than homogenizing them. | **UNIVERSALITY CLAIM ABANDONED.** The replacement claim is architectural and conditional, not universal-scalar. |
| R11 | The referee stated that a convincing version of the old commitment claim would require rigorous stochastic barrier-crossing derivation, direct first-passage/transmission calculations, and benchmark proof that estimator routes yield the same projected friction. | Those requirements followed from the predecessor's chosen universal commitment premise. | The rebuilt work does not claim that the old premise was proven. The problem was decomposed instead: barrier/rate predictions use mechanism-appropriate kinetic theories; local stability uses generator analysis; estimator equivalence must be demonstrated case by case or refused. | The Barrier-Height/Rate Atlas contains independently typed kinetic models, predictions, observed comparators, grades, and residuals. The Engine separately handles structural prediction and diagnosis. | **OLD BURDEN NOT EVADED; OLD CLAIM WITHDRAWN.** First-passage or transmission calculations remain appropriate for systems whose kinetic model requires them, but are no longer invoked to justify a universal chi-to-commitment law. |

## What the rejection changed structurally

The rejected manuscript attempted to travel directly from a local damping coordinate to chemical commitment. The present architecture inserts explicit scientific firewalls:

`physical source / electronic-structure result / experiment`

-> **system or reaction-path representation**

-> **coordinate / condition / provenance qualification**

-> **Engine diagnosis and licensed structural prediction**

-> **mechanism-appropriate kinetic prediction where independently justified**

-> **independent observation / comparator**

-> **versioned Stability Atlas admission**

-> **non-voting conglomerated architecture**

No downstream agreement repairs an upstream failed gate.

## Why this is not a renamed predecessor

The scientific center changed in four ways:

1. **Commitment was removed as a universal interpretation.** The predecessor's central law is not preserved under new terminology.
2. **The scalar ceased to be the framework.** Scalar, modal/subspace, and conglomerated system organization are distinct representation levels.
3. **Prediction became typed.** Structural response prediction and kinetic prediction have different physical inputs and cannot silently substitute for each other.
4. **The Atlas became an evidence product rather than a display of favorable coordinates.** Predictions, observations, residuals, refusals, HOLDs, evidence grades, and source independence remain visible.

## Adversarial-review instruction

Any review finding that one of the rejected substitutions has re-entered the manuscript under new wording must be treated as a blocking defect. In particular, the following regressions are disallowed:

- critical damping -> commitment optimum;
- local well classification -> reaction rate;
- total linewidth -> lifetime damping;
- electronic hybridization -> nuclear friction without projection;
- rate-derived quantity -> independent validation of the same rate;
- favorable residual -> retrospective model selection;
- one strong family -> promotion of unrelated weak families;
- aggregate success -> erasure of a contradiction, HOLD, refusal, or failed condition match.
