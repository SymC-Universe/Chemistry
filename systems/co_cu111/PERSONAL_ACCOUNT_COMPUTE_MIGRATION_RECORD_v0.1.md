# CO/Cu(111) personal-account free-compute migration record v0.1

Date opened: 2026-09-07
Source repository: `SymC-Universe/Chemistry`
Prepared migration branch: `personal-free-compute`
Target personal owner: `SymCUniverse`

## Purpose

This record preserves the execution/provenance transition caused by an unacceptable GitHub Actions larger-runner billing outcome. The transition is infrastructure-only. No frozen scientific setting, threshold, geometry rule, physical interpretation, or historical scientific HOLD is changed by this migration.

## Triggering operational event

During the checkpointed L15/L17 CO/Cu(111) diagnostic, GitHub-hosted larger runners accumulated substantially more cost than the user intended. The user ordered all compute stopped after the account charge reached approximately USD 112. The prior willingness to tolerate a much smaller one-off compute cost is not interpreted as authorization for further larger-runner use.

Standing rule after this event:

- GitHub larger-runner budget is zero unless the user explicitly changes that rule in a new message.
- No automatic paid escalation is permitted for deadline, performance, resource, or convenience reasons.
- A calculation that does not fit the no-cost execution route becomes an infrastructure HOLD, not an instruction to buy a larger runner.

## Preserved scientific state at stop

### L15/L17 matched adsorption diagnostic

Frozen science remains governed by `SYSTEM2_PBE_L15_L17_SITE_DEPTH_DIAGNOSTIC_v0.2.json`:

- L15 and L17
- top, bridge, fcc_hollow, hcp_hollow
- 2x2
- K8
- nominal 0.25 ML
- slab-depth sensitivity gate 0.005 eV/CO
- exact QE clean-stop restart semantics
- original L17 clean-surface HOLD preserved

Cancelled larger-runner production run: `34048806316`.

Existing upstream evidence is retained rather than discarded. At migration time the run still exposes, among others:

- L15/top segment 2: artifact `10019501335`, about 9.09 GB, digest `sha256:2fa8d31985222e00580f4a8e5cb47960d5250e8440292378d5b70551eaeec42c`.
- L15/fcc_hollow segment 2: artifact `10025157970`, about 9.03 GB, digest `sha256:04fe2a6707ddd532fc4028433c2bcecb6d899b23a0f5d924f11f1cca3acf035d`.
- L15/bridge segment 1: artifact `9998322616`, about 18.89 GB.
- L15/hcp_hollow segment 1: artifact `10002959473`, about 9.03 GB.
- L17/top segment 1: artifact `10003623068`, about 10.86 GB.
- L17/bridge segment 1: artifact `10009406827`, about 22.71 GB.
- L17/fcc_hollow segment 1: artifact `10011294774`, about 10.87 GB.
- L17/hcp_hollow segment 1: artifact `10019255946`, about 10.87 GB.

The unequal checkpoint sizes are operationally important. The personal free-cache route may accept a compatible state only if it fits the default repository cache ceiling. A checkpoint larger than the free cache envelope is not silently uploaded as a billable Actions artifact.

### L19 clean-surface extension

L19 was prospectively frozen as L19/V40/K36 under the already-recorded odd-depth continuation policy. Launch run `34134967279` passed its 11-test preflight and began relaxation segment 1 on standard `ubuntu-24.04`, but it was cancelled during the global cost stop before a new L19 checkpoint was admitted.

The L19 scientific contract therefore remains frozen and outcome-unseen at the checkpoint level. It may restart from segment 1 on a no-cost route without changing science.

## Why the migration uses a personal public fork

The target execution owner is the user's personal GitHub account, `SymCUniverse`. The source organization repository is kept intact as historical evidence. The preferred migration is a public personal fork with all branches copied, including `personal-free-compute`.

This avoids treating the organization's existing multi-GB Actions artifact inventory as new personal-account storage. Historical artifacts remain upstream evidence and are read only when explicitly pinned by run/artifact identity and hash.

## New execution/storage firewall

The machine-readable policy is `PERSONAL_ACCOUNT_FREE_COMPUTE_POLICY_v0.1.json`.

The personal route requires:

1. repository exactly `SymCUniverse/Chemistry`;
2. repository visibility public;
3. standard GitHub-hosted runner `ubuntu-24.04` unless an explicitly configured no-cost self-hosted personal runner is later used;
4. no larger runner labels;
5. no automatic paid escalation;
6. no multi-GB QE checkpoint as a new Actions artifact;
7. exact QE restart state preferred over recomputation;
8. default 10 GB repository cache ceiling is never increased;
9. checkpoint state above the hard free-cache ceiling stops with an infrastructure HOLD;
10. small provenance/result artifacts only.

## Prepared no-cost workflows

### L15/L17 standard-runner survival probe

Workflow: `.github/workflows/co-cu111-l15-l17-personal-standard-probe-v1.yml`.

This is explicitly non-admissible scientifically. It runs one L15/top case for only five minutes on standard `ubuntu-24.04` and then deliberately terminates it. It uploads only a tiny mechanical resource record. It cannot create or promote a scientific result or checkpoint.

Its purpose is to distinguish whether the previous roughly 79-second standard-runner shutdown still occurs on the personal public route before dispatching the eight-case diagnostic.

### L19 personal free-cache continuation

Parent workflow: `.github/workflows/co-cu111-l19-personal-free-cache-v1.yml`.

Reusable worker: `.github/workflows/co-cu111-personal-cache-segment-worker-v1.yml`.

The worker:

- runs only on standard `ubuntu-24.04`;
- verifies the personal-public zero-paid policy first;
- downloads small pinned upstream source artifacts by immutable artifact ID and verifies their ZIP SHA-256 digests;
- preserves exact QE restart semantics;
- stores a CHECKPOINT only in the repository cache, not as a large Actions artifact;
- refuses to save a state above 9.5 GB;
- strips the multi-GB QE outdir only after a state is established as COMPLETE, because COMPLETE carry-forward no longer requires restart files;
- uploads at most a small provenance bundle;
- reuses an exact compatible segment cache if it already exists rather than recomputing it;
- streams checkpoint hashes so verification does not load multi-GB files into RAM.

L19 remains scientifically unchanged from the prospectively frozen L19 protocol.

## Interpretation firewall

The billing incident and migration do not alter the scientific record:

- the original L17 HOLD remains a HOLD;
- the L15/L17 diagnostic remains pending;
- L19 remains a prospectively frozen extension, not evidence obtained by changing the method after outcome view;
- cost and publication timing cannot tune thresholds or physical parameters;
- resource infeasibility is reported as an infrastructure limitation rather than converted into a scientific result.
