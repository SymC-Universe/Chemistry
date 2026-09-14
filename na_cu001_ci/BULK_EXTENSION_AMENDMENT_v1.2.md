# Na/Cu(001) Bulk Convergence Extension Amendment v1.2

**Status:** frozen after the v0.3 bulk HOLD and before any extension EOS result  
**Date:** 3 August 2026  
**System role:** numerical-construction pilot only  
**Scope:** extend the Cu bulk basis and k-point convergence ladder without relaxing, replacing, or retrospectively redefining the original gates

## 1. Triggering result

The corrected V2 route stopped at its first physical gate in Actions run `30840469734`. The 80 Ry, 240 Ry charge-density, 16x16x16 six-point EOS completed and was compared with all twenty historical candidates. The lattice-constant condition passed broadly, but no historical candidate through 70 Ry and 14x14x14 satisfied the frozen equilibrium-energy condition of 0.001 eV per atom. The selector therefore returned `recommended_smallest = null`, `gate = HOLD`, and the workflow skipped every slab and downstream job.

This is a valid negative convergence result. It is retained. The extension does not relabel that result as PASS, select the 80 Ry reference against itself, or weaken the energy threshold.

## 2. Frozen extension grid

The extension reuses the twenty historical EOS summaries and adds the Cartesian candidate grid:

- wavefunction cutoffs: 80, 90, 100, 110, 120, and 130 Ry;
- charge-density cutoff: exactly three times the wavefunction cutoff;
- cubic k meshes: 14, 16, 18, and 20;
- six lattice constants per EOS: 3.55, 3.58, 3.61, 3.64, 3.67, and 3.70 A.

This produces 24 new candidate EOS calculations, or 144 new SCFs.

The finite numerical reference is fixed at 140 Ry, 420 Ry charge-density cutoff, and 22x22x22 k mesh. It is not accepted merely because it is the largest reference used for candidate comparison. It must first agree with a separately executed 150 Ry, 450 Ry, 24x24x24 six-point EOS audit under the same unchanged criteria:

- `abs(delta_a0) <= 0.005 A`;
- `abs(delta_E0) <= 0.001 eV/atom`.

The reference and audit add twelve SCFs. The complete extension therefore contains 156 new SCFs in 26 independently retained EOS cases.

## 3. Selection and refusal rules

1. The 140 Ry/22-cubed reference must pass against the 150 Ry/24-cubed audit.
2. The reference and audit are never candidate settings and cannot select themselves.
3. Every historical and extension candidate is compared directly with the audited 140 Ry/22-cubed reference.
4. A candidate must pass both unchanged lattice and energy criteria.
5. Among passing candidates, selection uses the smallest preregistered estimated cost score `ecutwfc^(3/2) * kmesh^3`, with wavefunction cutoff and k mesh as deterministic tie breakers.
6. If the reference audit fails, or if no candidate passes, the extension returns HOLD and the slab route remains closed.
7. No Na/Cu(001) adsorption, barrier, prefactor, rate, friction, linewidth, or turnover value is available to or used by this extension.

## 4. Execution separation

The bulk extension is a dedicated three-job workflow:

1. `prepare-engine` verifies the historical source artifact, builds the pinned Quantum ESPRESSO 7.6 `pw.x`, verifies the Cu UPF, and runs the extension unit and workflow-contract tests.
2. `extension-eos` executes the 26 registered EOS cases as a bounded matrix with all raw records retained.
3. `extension-gate` verifies exact matrix cardinality, audits the reference, compares all 44 candidates, writes the v0.4 result, and creates the v0.4 handoff only on PASS.

The extension workflow cannot dispatch the downstream surface workflow. A successful v0.4 artifact must be independently inspected before the heavy route is patched to consume it. This prevents a partially verified convergence extension from silently reopening slab calculations.

## 5. Evidence labels

- Historical v0.3 result: executed HOLD.
- Extension protocol v0.1: frozen prospective response to that HOLD.
- Extension EOS values: unexecuted until raw hashed artifacts exist.
- v0.4 bulk handoff: absent until both reference audit and candidate selection pass.
- Slab and downstream results: absent and unexecuted during the bulk extension.
