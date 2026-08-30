# Chemistry Stability Architecture / ChemSA

This repository contains the current chemistry investigation built around generator-first stability classification, barrier/rate evidence, and prospectively frozen computational tests.

> **Current research is not being developed on `main`.**  
> The active branch is **[`agent/na-cu001-integration`](https://github.com/SymC-Universe/Chemistry/tree/agent/na-cu001-integration)**.  
> Readers looking for the current protocols, workflows, system records, and in-progress calculations should use that branch rather than treating `main` as the live scientific state.

The older README on this branch described a broad single-\(\chi\) rate-turnover picture. That framing is no longer an accurate summary of the project and has been retired here. The present program separates mechanical stability, spectral geometry, barrier dynamics, friction, and reaction rate unless an independently justified reduction or comparison licenses a relation among them.

---

## Current scientific scope

ChemSA treats the governing dynamical object first and only reduces to a scalar when the physics licenses that reduction.

For a genuine stable second-order damped mechanical mode,

```math
\chi = \frac{\Gamma}{2\Omega}
```

may be reported when \(\Gamma\) and \(\Omega\) belong to an identified physical mode or an independently justified stable quotient.

A scalar \(\chi\) is **not** treated as a universal descriptor of every chemical dynamical system, and \(\chi=1\) is **not** assumed to be a universal reaction-rate optimum.

The current architecture keeps the following quantities distinct unless a separately justified relation is established:

- mechanical damping ratio / modal \(\chi\),
- eigenvalue and exceptional-point geometry,
- modal or reaction-coordinate identity,
- barrier height,
- barrier-local friction,
- transmission / recrossing dynamics,
- reaction rate,
- uncertainty, conditioning, and admissibility.

For an inverted barrier coordinate, the stable-well critical-damping construction is not imported onto the saddle. Barrier dynamics are handled with the appropriate reactive-pole / transmission description instead of manufacturing a mechanical \(\chi\) where no real critical-damping boundary exists.

Future promoted scalar results are expected to carry their physical/modal carrier, scalar-to-mode assignment, and uncertainty/admissibility information with them.

---

## Current project status

### ChemSA engine

The current ChemSA release preserves generator spectra, indexed modal information, conditioning states, mechanical reduction rules, and refusal states for cases in which a scalar reduction is not scientifically licensed.

The Stability Arc closure work has now been inherited as an additive chemistry reporting contract on the active branch. It does **not** retroactively alter the frozen ChemSA release, but it requires future promoted real-system scalar results to retain their modal/subspace carrier and assignment explicitly.

See on the active branch:

- `systems/CHEMISTRY_STABILITY_ARC_INHERITANCE_v0.1.json`

### Barrier-Height / Rate Atlas

Barrier-Height / Rate Atlas v0.9 is currently release-closed at **61 coordinates across 26 reaction families**.

The Atlas maintains a hard separation between well-side stability quantities and barrier-local friction. The frozen v0.9 coordinates do not use well-side ChemSA \(\chi\) as the rate friction variable.

Publication figures are required to be generated from frozen data by preserved Python scripts, with the exact plotted tables and verification material retained for reproducibility.

### System 1: Na/Cu(001)

Na/Cu(001) remains development-pilot evidence. Historical results are not automatically promoted into the current real-system evidentiary ladder.

### System 2: CO/Cu(111)

CO/Cu(111) is the current active real-system computation.

The present gate is the frozen PBE Cu(111) clean-surface audit at:

- **13 layers**
- **28 Å vacuum**
- **24 × 24 surface k mesh**
- exact frozen Stage A PBE engine and pseudopotentials
- `esm`, `bc1`
- **0.020 eV/Å** movable-force gate
- **0.001 eV** independent fixed-geometry SCF reproduction gate

The active continuation protocol authorizes six bounded direct-one-rank continuation slots, logical segments **25–30**, without changing scientific settings. Later slots carry a completed relaxation forward without recomputation once `RELAX_COMPLETE` has been reached.

At the last verified status update on **29 Aug 2026**, logical segments 25 and 26 had completed successfully and logical segment 27 was running. Live status should be checked in GitHub Actions because this state will change as the audit advances.

The fifth continuation slot is present as **logical segment 29**. The sixth slot is present as **logical segment 30** as bounded fail-safe capacity. If completion occurs before the sixth slot, the sixth slot carries the completed state forward rather than rerunning the relaxation. The next mandatory stage is then the independent audit SCF, followed by the unchanged ten-case clean-surface gate.

A no-recompute handoff is already prepared so that, if the clean-surface gate passes, the workflow can move directly into the prospectively frozen top / bridge / fcc-hollow / hcp-hollow adsorption-site ordering screen while reusing the already accepted clean-surface results.

Primary active files include:

- `.github/workflows/co-cu111-pbe-surface-audit-continuation-extension-v2.yml`
- `systems/co_cu111/SYSTEM2_PBE_SURFACE_AUDIT_CONTINUATION_EXTENSION_v0.2.json`
- `systems/co_cu111/pbe_surface_audit_continuation_extension_v2.py`
- `.github/workflows/co-cu111-pbe-site-ordering-handoff-v1.yml`
- `systems/co_cu111/SYSTEM2_PBE_SITE_ORDERING_HANDOFF_v0.1.json`

### System 3: H/Ru(0001)

The H/Ru(0001) protocol is prepared prospectively but remains downstream of the System 2 closure gate.

Its current design requires reaction-coordinate matching, independently sourced projected dissipation, explicit nuclear-quantum treatment where necessary, and refusal to calculate/promote ChemSA \(\chi\) until the dissipation and admissibility gates are satisfied.

See on the active branch:

- `systems/h_ru0001/SYSTEM3_METHOD_AND_QUANTUM_TREATMENT_PROTOCOL_v0.1.json`
- `systems/h_ru0001/SYSTEM3_SELECTION_RECORD_v0.1.json`

---

## Reproducibility and evidence discipline

Current project rules include:

- freeze scientific choices before inspecting target outcomes;
- preserve raw computational inputs, outputs, hashes, and provenance;
- distinguish mechanical execution failures from scientific failures;
- do not retune thresholds after results are known;
- do not infer inaccessible literature values;
- keep barrier, rate, friction, modal stability, and EP claims separated unless a registered bridge is justified;
- return HOLD / refusal / nonidentifiable states rather than selecting the most favorable interpretation;
- generate publication figures directly from preserved data with preserved scripts.

Repository code and deposited data should be treated as the computational source of record rather than code copied from rendered PDFs.

---

## Where to look

For the live investigation, use:

**Active branch:**  
[`agent/na-cu001-integration`](https://github.com/SymC-Universe/Chemistry/tree/agent/na-cu001-integration)

**GitHub Actions:**  
[`SymC-Universe/Chemistry/actions`](https://github.com/SymC-Universe/Chemistry/actions)

`main` is currently a stable landing branch and may lag the active computational branch by design.

---

## Research status

This repository contains active and archival research material. Individual claims should be read according to the status and evidentiary level recorded in the associated protocol, result, audit, or manuscript file. Development-pilot results, frozen prospective tests, completed audits, and publication-ready evidence are not interchangeable categories.

