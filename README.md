# Chemistry Stability Architecture / ChemSA

**Current research notice: 19 September 2026**

This repository contains the chemistry arm of the SymC stability-architecture program. Current work is generator-first and governed by the SymC General Operations Manual v0.8.0 plus chemistry-local scientific controls.

The canonical repository is **`SymC-Universe/Chemistry`**. A similarly named personal-account repository exists as an older mirror and should not be treated as the current source of record.

## Scientific scope

For a genuine stable second-order mechanical mode,

```math
\chi = \frac{\Gamma}{2\Omega}
```

may be reported when `Gamma` and `Omega` belong to an identified physical mode or an independently justified stable reduction.

The present chemistry program does **not** assume that:

- one scalar chi describes every chemical dynamical system;
- chi = 1 is a universal reaction-rate optimum;
- a barrier-top friction ratio is a stable-well critical-damping exceptional point;
- spectral width is automatically mechanical damping;
- a favorable rate trend licenses a dynamical interpretation.

Mechanical stability, eigenvalue/EP geometry, barrier height, barrier-local friction, transmission/recrossing, reaction rate, uncertainty, and admissibility remain separate unless a registered bridge earns a relation among them. Under GOM v0.8.3, any licensed local scalar must also be interpreted jointly with the broader modal/carrier/system architecture where applicable, while perturbation/recovery remains distinct from barrier crossing, adsorption, reaction and relaxation physics.

## Current source-of-record map

`main` is a public landing/history branch and intentionally lags active investigation branches.

- **Program integration / Barrier Atlas:** `agent/na-cu001-integration`
- **CO/Cu(111) current closure lineage:** `bridge/co-cu111-l19-20260916`
- **H/Ru(0001) current closure lineage:** `bridge/h-ru0001-relax-pass-20260917`

Live execution state comes from GitHub Actions and the result/ledger artifacts on those branches, not from historical status prose.

## Current scientific status

### Barrier-Height / Rate Atlas

Barrier-Height / Rate Atlas v0.9 is release-closed at **61 coordinates across 26 reaction families**. The Atlas preserves a hard separation between well-side stability quantities and barrier-local friction and does not use a well-side ChemSA chi as the reaction-rate friction variable.

Additive family-depth work is allowed to extend coverage without silently rewriting the frozen v0.9 release.

### Na/Cu(001)

Na/Cu(001) remains development-pilot evidence rather than automatic promotion evidence. Resource-limited calculations must fail closed rather than change scientific settings to fit an inadequate execution environment.

### CO/Cu(111)

The current L19 independent-reproduction lineage is in a **SCIENTIFIC_HOLD**. The frozen independent SCF did not complete within its authorized bounded runway. The later post-HOLD provenance closure succeeded and did not reopen the physics.

Current consequence:

```text
CO_CU111_L19 = SCIENTIFIC_HOLD
additional unchanged retries = STOPPED
new SCF runway = requires a new prospective scientific freeze
```

A successful mechanical/provenance closure is not a scientific PASS.

### H/Ru(0001)

The 17-layer clean Ru(0001) surface passed its frozen relaxation/reproduction gate. The next shared-H reference qualification did **not** fully close.

The no-recompute v0.2 adjudication closed with:

```text
H2 reference at 70 Ry = PASS
H2 reference at 80 Ry = PASS
H atom at 70 Ry = ATOM_RECOVERY_HOLD
H atom at 80 Ry = ATOM_RECOVERY_HOLD
shared-H disposition = SHARED_H_PSEUDOPOTENTIAL_RECOVERY_HOLD
next gate = STOP_SHARED_H_BRANCH_WITHOUT_RETUNING
```

Binding energies remain withheld and adsorption promotion remains blocked. The HOLD is preserved rather than repaired by changing thresholds or pseudopotential settings after the result.

## Evidence discipline

Current project rules include:

- freeze science-changing choices before target inspection;
- preserve raw inputs, outputs, hashes, checkpoints, and failure history;
- distinguish mechanical failure, numerical failure, scientific HOLD, and scientific PASS;
- do not retry deterministic failures unchanged;
- do not retune thresholds after decisive evidence;
- preserve refusal/nonidentifiability as valid outcomes;
- keep modal carrier and uncertainty attached to any promoted scalar;
- compare against native chemistry methods before assigning SymC-specific meaning;
- generate publication figures from preserved data and scripts.

Historical manuscripts and releases remain provenance. Where older prose conflicts with a later explicit project-local correction, result record, or GOM-v0.8.3 migration record, the later record governs the present interpretation.

## Where to start

For current chemistry work, begin with the active branch relevant to the system above and its project-state/result artifacts. Do not infer present scientific status from an old PDF, an old workflow failure, or the similarly named personal-account mirror.

The chemistry program is allowed to close with narrower or negative results. The target is a defensible physical map, not preservation of a preferred chi narrative.
