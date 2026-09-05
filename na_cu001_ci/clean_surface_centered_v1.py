#!/usr/bin/env python3
"""Centered clean-surface relaxation gate for the definitive Na/Cu(001) route.

The scientific protocol is unchanged from the frozen v0.2 clean-surface gate:
a symmetric constrained Cu(001) relaxation, force threshold 0.02 eV/A,
mirror-pair z deviation <= 0.01 A, and an independent fixed-geometry SCF energy
reproduction within 0.001 eV. This wrapper corrects only the coordinate origin:
all ESM bc1 inputs and downstream coordinates use explicit Cartesian z=0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

CU_PSEUDO = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"HOLD: JSON root is not an object: {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def centered_clean_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[list[float]], list[dict[str, Any]]]:
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    h = a0 / 2.0
    cell = [[h, h, 0.0], [-h, h, 0.0], [0.0, 0.0, cell_z]]
    midpoint = (layers - 1) / 2.0
    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        x = shift * h + shift * (-h)
        y = shift * h + shift * h
        z = (layer - midpoint) * dz
        movable = layer < 2 or layer >= layers - 2
        atoms.append({
            "symbol": "Cu",
            "position_angstrom": [x, y, z],
            "flags": [0, 0, 1 if movable else 0],
        })
    return cell, atoms


def canonicalize_z(atoms: list[dict[str, Any]], cell_z: float) -> list[dict[str, Any]]:
    output = json.loads(json.dumps(atoms))
    for atom in output:
        z = float(atom["position_angstrom"][2])
        atom["position_angstrom"][2] = ((z + cell_z / 2.0) % cell_z) - cell_z / 2.0
    return output


def verify_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    slab = read_json(Path(args.slab_handoff).resolve())
    parity = read_json(Path(args.parity_handoff).resolve())
    protocol = read_json(Path(args.protocol).resolve())
    if slab.get("schema") != "na-cu001-clean-slab-to-relaxation-handoff-v0.3" or slab.get("status") != "PASS":
        raise SystemExit("HOLD: definitive slab handoff is not PASS")
    if parity.get("schema") != "na-cu001-electrostatic-consistency-v0.3" or parity.get("status") != "PASS":
        raise SystemExit("HOLD: electrostatic consistency gate is not PASS")
    if parity.get("next_gate") != "clean_surface_relaxation":
        raise SystemExit("HOLD: electrostatic handoff does not authorize clean relaxation")
    if protocol.get("schema") != "na-cu001-method-protocol-v0.2" or protocol.get("status") != "FROZEN_BEFORE_DOWNSTREAM_RESULTS":
        raise SystemExit("HOLD: method protocol is not frozen v0.2")
    s = slab.get("selected_slab_settings") or {}
    if [int(s.get("layers", -1)), float(s.get("vacuum_angstrom", -1)), int(s.get("kmesh_inplane", -1))] != [11, 12.0, 16]:
        raise SystemExit("HOLD: slab handoff is not bound to 11 layers, 12 A, k=16")
    if parity.get("selected_slab") != {"layers": 11, "vacuum_angstrom": 12.0, "kmesh_inplane": 16}:
        raise SystemExit("HOLD: parity selection disagrees with definitive slab")
    electro = s.get("electrostatic_convention") or {}
    coord = s.get("coordinate_convention") or {}
    if electro.get("assume_isolated") != "esm" or electro.get("esm_bc") != "bc1":
        raise SystemExit("HOLD: slab handoff is not ESM bc1")
    if coord.get("atomic_position_card") != "angstrom" or coord.get("origin") != "cartesian_z_zero":
        raise SystemExit("HOLD: slab handoff is not explicit Cartesian z=0")
    if parity.get("selected_convention") != {"assume_isolated": "esm", "esm_bc": "bc1"}:
        raise SystemExit("HOLD: parity selected convention is not ESM bc1")
    surface = protocol.get("surface") or {}
    if float(surface.get("force_tolerance_ev_per_angstrom", -1)) != 0.02:
        raise SystemExit("HOLD: clean force threshold is not frozen at 0.02 eV/A")
    if float(surface.get("energy_reproduction_tolerance_ev", -1)) != 0.001:
        raise SystemExit("HOLD: energy reproduction threshold is not frozen at 0.001 eV")
    expected_pseudo = str(protocol.get("immutable_sources", {}).get("cu_upf_sha256") or "")
    pseudo = Path(args.pseudo_dir).resolve() / CU_PSEUDO
    if not pseudo.is_file() or sha256(pseudo) != expected_pseudo:
        raise SystemExit("HOLD: Cu pseudopotential identity mismatch")
    if not Path(args.pw).resolve().is_file():
        raise SystemExit("HOLD: pw.x is missing")
    return slab, parity, protocol


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--slab-handoff", required=True)
    parser.add_argument("--parity-handoff", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--pw", required=True)
    parser.add_argument("--pseudo-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--np", type=int, default=2)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--parity-run-id", required=True)
    parser.add_argument("--parity-commit", required=True)
    parser.add_argument("--control-commit", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    sys.path.insert(0, str(source_dir))
    import closure_engine_v2 as v2  # type: ignore

    slab, parity, protocol = verify_inputs(args)
    s = slab["selected_slab_settings"]
    a0 = float(s["a0_angstrom"])
    layers = int(s["layers"])
    vacuum = float(s["vacuum_angstrom"])
    cell, atoms = centered_clean_geometry(a0, layers, vacuum)
    cell_z = float(cell[2][2])
    initial_z = [float(atom["position_angstrom"][2]) for atom in atoms]
    if abs(sum(initial_z) / len(initial_z)) > 1e-12 or abs(min(initial_z) + max(initial_z)) > 1e-12:
        raise SystemExit("HOLD: constructed clean slab is not centered at Cartesian z=0")

    method = {
        "ecutwfc_ry": float(s["ecutwfc_ry"]),
        "ecutrho_ry": float(s["ecutrho_ry"]),
        "kmesh": int(s["kmesh_inplane"]),
    }
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pw = Path(args.pw).resolve()

    relax = v2.relax_record(
        root / "relax", "clean_relax", cell, atoms, method,
        v2.cu_species(), pseudo_dir, pw, args.np, esm=True,
    )
    if not relax.get("atoms") or relax.get("energy_ev") is None:
        raise SystemExit("HOLD: clean relaxation lacks final geometry or energy")
    relax["atoms"] = canonicalize_z(relax["atoms"], cell_z)
    fixed = json.loads(json.dumps(relax["atoms"]))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]
    reproduce = v2.scf_record(
        root / "reproduce", "clean_reproduce", cell, fixed, method,
        v2.cu_species(), pseudo_dir, pw, args.np, esm=True,
    )

    energy_delta = None
    if reproduce.get("energy_ev") is not None:
        energy_delta = abs(float(relax["energy_ev"]) - float(reproduce["energy_ev"]))
    z_values = sorted(float(atom["position_angstrom"][2]) for atom in relax["atoms"] if atom["symbol"] == "Cu")
    mirror_error = max((abs(z_values[i] + z_values[-1 - i]) for i in range(len(z_values) // 2)), default=0.0)
    center_atom_error = abs(z_values[len(z_values) // 2]) if len(z_values) % 2 else 0.0
    tol_e = float(protocol["surface"]["energy_reproduction_tolerance_ev"])
    tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {
        "explicit_cartesian_z_zero_input": abs(sum(initial_z) / len(initial_z)) <= 1e-12 and abs(min(initial_z) + max(initial_z)) <= 1e-12,
        "esm_bc1_preserved": True,
        "relax_returncode_zero": relax.get("returncode") == 0,
        "relax_job_done": bool(relax.get("job_done")),
        "max_force_le_0p02_ev_per_angstrom": relax.get("max_unconstrained_force_ev_per_angstrom") is not None and float(relax["max_unconstrained_force_ev_per_angstrom"]) <= tol_f,
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
        "atoms": relax["atoms"],
        "constraint_protocol": "symmetric clean slab; outer two layer pairs z-only; inner layers fixed",
        "relax_energy_ev": relax.get("energy_ev"),
        "independent_scf_energy_ev": reproduce.get("energy_ev"),
        "energy_reproduction_delta_ev": energy_delta,
        "max_unconstrained_force_ev_per_angstrom": relax.get("max_unconstrained_force_ev_per_angstrom"),
        "mirror_pair_error_angstrom": mirror_error,
        "center_atom_z_error_angstrom": center_atom_error,
        "pass_checks": checks,
        "runs": {"relax": relax, "independent_scf": reproduce},
        "provenance": {
            "source_c7_run_id": int(args.source_run_id),
            "source_c7_commit": args.source_commit,
            "electrostatic_consistency_run_id": int(args.parity_run_id),
            "electrostatic_consistency_commit": args.parity_commit,
            "control_commit": args.control_commit,
            "scientific_settings_changed": False,
            "coordinate_origin_correction_only": True,
        },
        "input_artifacts": {
            "slab_handoff_sha256": sha256(Path(args.slab_handoff).resolve()),
            "parity_handoff_sha256": sha256(Path(args.parity_handoff).resolve()),
            "protocol_sha256": sha256(Path(args.protocol).resolve()),
            "pw_x_sha256": sha256(pw),
            "cu_pseudo_sha256": sha256(pseudo_dir / CU_PSEUDO),
        },
        "next_gate": "adsorption_site_screening",
    }
    write_json(Path(args.out).resolve(), handoff)
    write_json(root / "CLEAN_RELAX_RUN_RECORD.json", {
        "schema": "na-cu001-clean-relax-run-record-v0.1",
        "status": status,
        "relax": relax,
        "independent_scf": reproduce,
        "coordinate_convention": handoff["method"]["coordinate_convention"],
        "checks": checks,
    })
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
