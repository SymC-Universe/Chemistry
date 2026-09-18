#!/usr/bin/env python3
"""Mechanical timeout recovery for the definitive Na/Cu(001) clean surface.

The original centered clean-surface relaxation was terminated by the GitHub
job timeout. This helper changes no scientific setting. It starts a new BFGS
continuation from the last accepted geometry printed by that interrupted run,
uses the same frozen method/constraints/ESM convention, and adds only a QE
max_seconds wall-clock safety control so future queue limits fail cleanly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

CU_PSEUDO = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def inject_runtime_control(text: str, max_seconds: float) -> str:
    anchor = "  verbosity = 'high',\n"
    if text.count(anchor) != 1:
        raise SystemExit("HOLD: cannot bind runtime-control insertion point")
    insertion = (
        "  restart_mode = 'from_scratch',\n"
        f"  max_seconds = {float(max_seconds):.1f},\n"
    )
    return text.replace(anchor, anchor + insertion, 1)


def parse_total_forces(text: str, nat: int, conversion: float) -> list[list[float]]:
    """Parse the last QE total-force block, excluding verbose decompositions."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if "Forces acting on atoms" in line]
    for start in reversed(starts):
        rows: list[list[float]] = []
        for line in lines[start + 1 :]:
            stripped = line.strip()
            if stripped.startswith("The non-local contrib.") or stripped.startswith("Total force ="):
                break
            if " force = " not in line or not stripped.startswith("atom"):
                continue
            parts = stripped.replace("=", " = ").split()
            try:
                eq = parts.index("=")
                xyz = [float(parts[eq + j]) * conversion for j in (1, 2, 3)]
            except (ValueError, IndexError):
                rows = []
                break
            rows.append(xyz)
            if len(rows) == nat:
                return rows
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--control-dir", required=True)
    parser.add_argument("--partial-output", required=True)
    parser.add_argument("--partial-input", required=True)
    parser.add_argument("--slab-handoff", required=True)
    parser.add_argument("--parity-handoff", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--pw", required=True)
    parser.add_argument("--pseudo-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--np", type=int, default=2)
    parser.add_argument("--max-seconds", type=float, default=12000.0)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--parity-run-id", required=True)
    parser.add_argument("--parity-commit", required=True)
    parser.add_argument("--original-clean-run-id", required=True)
    parser.add_argument("--original-clean-commit", required=True)
    parser.add_argument("--control-commit", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    control_dir = Path(args.control_dir).resolve()
    sys.path.insert(0, str(control_dir))
    sys.path.insert(0, str(source_dir))
    import closure_engine as legacy  # type: ignore
    import closure_engine_v2 as v2  # type: ignore
    import clean_surface_centered_v1 as clean  # type: ignore

    slab, parity, protocol = clean.verify_inputs(args)
    s = slab["selected_slab_settings"]
    a0 = float(s["a0_angstrom"])
    layers = int(s["layers"])
    vacuum = float(s["vacuum_angstrom"])
    method = {
        "ecutwfc_ry": float(s["ecutwfc_ry"]),
        "ecutrho_ry": float(s["ecutrho_ry"]),
        "kmesh": int(s["kmesh_inplane"]),
    }
    cell, template_atoms = clean.centered_clean_geometry(a0, layers, vacuum)
    cell_z = float(cell[2][2])

    partial_output = Path(args.partial_output).resolve()
    partial_input = Path(args.partial_input).resolve()
    if not partial_output.is_file() or not partial_input.is_file():
        raise SystemExit("HOLD: interrupted clean-surface raw input/output missing")
    partial_text = partial_output.read_text(errors="replace")
    if "JOB DONE." in partial_text or "End of BFGS Geometry Optimization" in partial_text:
        raise SystemExit("HOLD: timeout recovery was given an already completed relaxation")
    parsed = legacy.parse_final_positions(partial_text, layers)
    if len(parsed) != layers:
        raise SystemExit("HOLD: cannot recover last accepted clean-surface geometry")
    atoms = legacy.restore_flags(parsed, template_atoms)
    atoms = clean.canonicalize_z(atoms, cell_z)
    if [list(atom.get("flags", [])) for atom in atoms] != [list(atom.get("flags", [])) for atom in template_atoms]:
        raise SystemExit("HOLD: recovered geometry constraints differ from frozen clean-surface masks")
    if abs(float(atoms[layers // 2]["position_angstrom"][2])) > 1e-8:
        raise SystemExit("HOLD: recovered fixed center layer moved away from Cartesian z=0")

    root = Path(args.out_dir).resolve()
    relax_root = root / "relax_continuation"
    tmp = relax_root / "tmp"
    relax_root.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pw = Path(args.pw).resolve()
    inp = relax_root / "clean_relax_continuation.in"
    out = relax_root / "clean_relax_continuation.out"
    base_input = legacy.qe_input(
        calculation="relax",
        prefix="clean_relax_continuation",
        outdir=tmp,
        pseudo_dir=pseudo_dir,
        cell=cell,
        atoms=atoms,
        species=v2.cu_species(),
        ecutwfc=float(method["ecutwfc_ry"]),
        ecutrho=float(method["ecutrho_ry"]),
        kmesh=int(method["kmesh"]),
        esm=True,
        relax=True,
        nosym=True,
    )
    inp.write_text(inject_runtime_control(base_input, args.max_seconds))

    start = time.time()
    rc, _ = legacy.run_command(legacy.mpi_command(pw, args.np), relax_root, out, inp)
    elapsed = time.time() - start
    text = out.read_text(errors="replace") if out.is_file() else ""
    energy = legacy.parse_qe_energy(text)
    parsed_final = legacy.parse_final_positions(text, layers)
    final_atoms = legacy.restore_flags(parsed_final, atoms) if parsed_final else atoms
    final_atoms = clean.canonicalize_z(final_atoms, cell_z)
    forces = parse_total_forces(text, layers, legacy.RY_BOHR_TO_EV_ANG)
    max_force = legacy.max_unconstrained_force(forces, final_atoms)
    converged = (
        rc == 0
        and "JOB DONE." in text
        and "End of BFGS Geometry Optimization" in text
        and energy is not None
        and max_force is not None
        and float(max_force) <= float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    )

    continuation_record = {
        "schema": "na-cu001-clean-surface-timeout-continuation-v0.1",
        "status": "CONVERGED" if converged else "CHECKPOINT",
        "mechanical_recovery_only": True,
        "scientific_settings_changed": False,
        "continuation_from_last_accepted_geometry": True,
        "qe_max_seconds_runtime_control": float(args.max_seconds),
        "returncode": rc,
        "job_done": "JOB DONE." in text,
        "bfgs_finished": "End of BFGS Geometry Optimization" in text,
        "energy_ev": energy,
        "max_unconstrained_force_ev_per_angstrom": max_force,
        "elapsed_s": elapsed,
        "atoms": final_atoms,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out) if out.is_file() else None,
        "partial_input_sha256": sha256(partial_input),
        "partial_output_sha256": sha256(partial_output),
        "provenance": {
            "source_c7_run_id": int(args.source_run_id),
            "source_c7_commit": args.source_commit,
            "electrostatic_consistency_run_id": int(args.parity_run_id),
            "electrostatic_consistency_commit": args.parity_commit,
            "original_clean_run_id": int(args.original_clean_run_id),
            "original_clean_commit": args.original_clean_commit,
            "control_commit": args.control_commit,
        },
    }
    write_json(root / "CLEAN_RELAX_CONTINUATION.json", continuation_record)
    if not converged:
        print(json.dumps(continuation_record, indent=2))
        raise SystemExit(75)

    fixed = json.loads(json.dumps(final_atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]
    reproduce = v2.scf_record(
        root / "reproduce", "clean_reproduce_recovery", cell, fixed, method,
        v2.cu_species(), pseudo_dir, pw, args.np, esm=True,
    )

    energy_delta = None
    if reproduce.get("energy_ev") is not None:
        energy_delta = abs(float(energy) - float(reproduce["energy_ev"]))
    z_values = sorted(float(atom["position_angstrom"][2]) for atom in final_atoms if atom["symbol"] == "Cu")
    mirror_error = max((abs(z_values[i] + z_values[-1 - i]) for i in range(len(z_values) // 2)), default=0.0)
    center_atom_error = abs(z_values[len(z_values) // 2]) if len(z_values) % 2 else 0.0
    tol_e = float(protocol["surface"]["energy_reproduction_tolerance_ev"])
    tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {
        "explicit_cartesian_z_zero_input": True,
        "esm_bc1_preserved": True,
        "relax_returncode_zero": rc == 0,
        "relax_job_done": "JOB DONE." in text,
        "max_force_le_0p02_ev_per_angstrom": max_force is not None and float(max_force) <= tol_f,
        "mirror_pair_error_le_0p01_angstrom": mirror_error <= 0.01,
        "fixed_center_layer_remains_at_z_zero": center_atom_error <= 1e-8,
        "independent_scf_pass": reproduce.get("returncode") == 0 and bool(reproduce.get("job_done")) and bool(reproduce.get("scf_converged")) and reproduce.get("energy_ev") is not None,
        "independent_energy_reproduction_le_0p001_ev": energy_delta is not None and energy_delta <= tol_e,
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    handoff = {
        "schema": "na-cu001-relaxed-clean-surface-handoff-v0.2",
        "status": status,
        "system": "clean Cu(001)",
        "method": {
            **method,
            "electrostatics": {"assume_isolated": "esm", "esm_bc": "bc1"},
            "coordinate_convention": {"atomic_position_card": "angstrom", "origin": "cartesian_z_zero"},
        },
        "cell_angstrom": cell,
        "atoms": final_atoms,
        "constraint_protocol": "symmetric clean slab; outer two layer pairs z-only; inner layers fixed",
        "relax_energy_ev": energy,
        "independent_scf_energy_ev": reproduce.get("energy_ev"),
        "energy_reproduction_delta_ev": energy_delta,
        "max_unconstrained_force_ev_per_angstrom": max_force,
        "mirror_pair_error_angstrom": mirror_error,
        "center_atom_z_error_angstrom": center_atom_error,
        "pass_checks": checks,
        "runs": {"relax_continuation": continuation_record, "independent_scf": reproduce},
        "provenance": {
            "source_c7_run_id": int(args.source_run_id),
            "source_c7_commit": args.source_commit,
            "electrostatic_consistency_run_id": int(args.parity_run_id),
            "electrostatic_consistency_commit": args.parity_commit,
            "original_clean_run_id": int(args.original_clean_run_id),
            "original_clean_commit": args.original_clean_commit,
            "control_commit": args.control_commit,
            "scientific_settings_changed": False,
            "coordinate_origin_correction_only": True,
            "mechanical_timeout_recovery_only": True,
        },
        "input_artifacts": {
            "slab_handoff_sha256": sha256(Path(args.slab_handoff).resolve()),
            "parity_handoff_sha256": sha256(Path(args.parity_handoff).resolve()),
            "protocol_sha256": sha256(Path(args.protocol).resolve()),
            "partial_clean_input_sha256": sha256(partial_input),
            "partial_clean_output_sha256": sha256(partial_output),
            "pw_x_sha256": sha256(pw),
            "cu_pseudo_sha256": sha256(pseudo_dir / CU_PSEUDO),
        },
        "next_gate": "adsorption_site_screening",
    }
    write_json(Path(args.out).resolve(), handoff)
    write_json(root / "CLEAN_TIMEOUT_RECOVERY_RUN_RECORD.json", {
        "schema": "na-cu001-clean-timeout-recovery-run-record-v0.1",
        "status": status,
        "continuation": continuation_record,
        "independent_scf": reproduce,
        "checks": checks,
    })
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
