#!/usr/bin/env python3
"""Auditable Na/Cu(001) adsorption-screen case with safe force parsing.

This runner changes no frozen scientific setting. It binds the converged centered
clean-surface handoff, the frozen C7 Na handoff/protocol, and the registered ESM
bc1 convention. The only additions are mechanical: an explicit QE max_seconds
runtime guard, an unambiguous parser for QE's total-force block, and checkpoint
output when a hosted runner ends before BFGS convergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def artifact(path: Path) -> dict[str, str]:
    return {"path": path.name, "sha256": sha256(path)}


def inject_runtime_control(text: str, max_seconds: float) -> str:
    anchor = "  verbosity = 'high',\n"
    if text.count(anchor) != 1:
        raise SystemExit("HOLD: cannot bind QE runtime-control insertion point")
    insertion = (
        "  restart_mode = 'from_scratch',\n"
        f"  max_seconds = {float(max_seconds):.1f},\n"
    )
    return text.replace(anchor, anchor + insertion, 1)


def parse_total_forces(text: str, nat: int, conversion: float) -> list[list[float]]:
    """Read the last QE total-force block and exclude verbose decompositions."""
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
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--clean-handoff", required=True)
    parser.add_argument("--na-handoff", required=True)
    parser.add_argument("--parity-handoff", required=True)
    parser.add_argument("--pw", required=True)
    parser.add_argument("--pseudo-dir", required=True)
    parser.add_argument("--mobility", required=True)
    parser.add_argument("--site", required=True)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--np", type=int, default=2)
    parser.add_argument("--max-seconds", type=float, default=18000.0)
    parser.add_argument("--resume-record")
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--clean-run-id", required=True)
    parser.add_argument("--clean-commit", required=True)
    parser.add_argument("--parity-run-id", required=True)
    parser.add_argument("--parity-commit", required=True)
    parser.add_argument("--control-commit", required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    sys.path.insert(0, str(source_dir))
    import closure_engine as legacy  # type: ignore
    import closure_engine_v2 as v2  # type: ignore

    protocol_path = Path(args.protocol).resolve()
    clean_path = Path(args.clean_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    parity_path = Path(args.parity_handoff).resolve()
    protocol = v2.load_protocol(protocol_path)
    clean = legacy.read_json(clean_path)
    na = legacy.read_json(na_path)
    parity = legacy.read_json(parity_path)
    v2.require(clean, "na-cu001-relaxed-clean-surface-handoff-v0.2")
    v2.require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    v2.require(parity, "na-cu001-electrostatic-consistency-v0.3")

    surface = protocol["surface"]
    electro = surface["registered_electrostatic_convention"]
    if electro.get("assume_isolated") != "esm" or electro.get("esm_bc") != "bc1":
        raise SystemExit("HOLD: frozen protocol electrostatic convention is not ESM bc1")
    if clean.get("next_gate") != "adsorption_site_screening" or na.get("next_gate") != "adsorption_site_screening":
        raise SystemExit("HOLD: upstream handoffs are not registered for adsorption screening")
    if clean.get("method", {}).get("electrostatics") != {"assume_isolated": "esm", "esm_bc": "bc1"}:
        raise SystemExit("HOLD: clean handoff electrostatics differ from frozen ESM bc1")
    if clean.get("method", {}).get("coordinate_convention") != {"atomic_position_card": "angstrom", "origin": "cartesian_z_zero"}:
        raise SystemExit("HOLD: clean handoff is not explicit Cartesian z=0")
    if bool(clean.get("provenance", {}).get("scientific_settings_changed")):
        raise SystemExit("HOLD: clean handoff reports changed scientific settings")
    if int(clean.get("provenance", {}).get("source_c7_run_id", -1)) != int(args.source_run_id):
        raise SystemExit("HOLD: clean handoff source-run provenance mismatch")
    if clean.get("provenance", {}).get("source_c7_commit") != args.source_commit:
        raise SystemExit("HOLD: clean handoff source-commit provenance mismatch")
    if int(clean.get("provenance", {}).get("electrostatic_consistency_run_id", -1)) != int(args.parity_run_id):
        raise SystemExit("HOLD: clean handoff electrostatic-run provenance mismatch")
    if clean.get("provenance", {}).get("electrostatic_consistency_commit") != args.parity_commit:
        raise SystemExit("HOLD: clean handoff electrostatic-commit provenance mismatch")
    if clean.get("provenance", {}).get("control_commit") != args.clean_commit:
        raise SystemExit("HOLD: clean handoff control-commit provenance mismatch")
    if len(clean.get("atoms", [])) != 11:
        raise SystemExit("HOLD: adsorption runner expected the selected 11-layer clean slab")
    if float(clean["method"]["ecutwfc_ry"]) != 90.0 or float(clean["method"]["ecutrho_ry"]) != 270.0 or int(clean["method"]["kmesh"]) != 16:
        raise SystemExit("HOLD: clean handoff method differs from the frozen selected surface method")
    if float(clean.get("max_unconstrained_force_ev_per_angstrom", 1e9)) > float(surface["force_tolerance_ev_per_angstrom"]):
        raise SystemExit("HOLD: clean handoff does not satisfy frozen force gate")
    if not all(bool(v) for v in clean.get("pass_checks", {}).values()):
        raise SystemExit("HOLD: clean handoff contains a failed PASS check")

    selected = na.get("selected", {})
    if selected.get("sha256") != protocol["immutable_sources"]["na_upf_sha256"]:
        raise SystemExit("HOLD: Na handoff UPF hash differs from frozen protocol")
    if selected.get("installed_sha256") != selected.get("sha256"):
        raise SystemExit("HOLD: Na installed UPF hash is inconsistent")
    mixed = na.get("selected_mixed_settings", {})
    if float(mixed.get("ecutwfc_ry", -1)) != 90.0 or float(mixed.get("ecutrho_ry", -1)) != 270.0:
        raise SystemExit("HOLD: mixed Cu/Na cutoff handoff differs from frozen route")
    if parity.get("selected_convention") != {"assume_isolated": "esm", "esm_bc": "bc1"}:
        raise SystemExit("HOLD: electrostatic PASS handoff is not ESM bc1")

    sites = list(surface["adsorption_starts"]["sites"])
    heights = [float(x) for x in surface["adsorption_starts"]["heights_angstrom"]]
    models = list(surface["mobility_models"])
    if args.mobility not in models or args.site not in sites or float(args.height) not in heights:
        raise SystemExit("HOLD: adsorption case is outside the frozen registered matrix")

    pseudo_dir = Path(args.pseudo_dir).resolve()
    na_filename = selected["installed_filename"]
    cu_path = pseudo_dir / legacy.CU_PSEUDO
    na_pseudo = pseudo_dir / na_filename
    if not cu_path.is_file() or not na_pseudo.is_file():
        raise SystemExit("HOLD: required Cu/Na pseudopotential is missing")
    if sha256(cu_path) != protocol["immutable_sources"]["cu_upf_sha256"]:
        raise SystemExit("HOLD: Cu pseudopotential hash mismatch")
    if sha256(na_pseudo) != protocol["immutable_sources"]["na_upf_sha256"]:
        raise SystemExit("HOLD: Na pseudopotential hash mismatch")

    continuation_from_checkpoint = False
    prior_link = None
    if args.resume_record:
        prior_path = Path(args.resume_record).resolve()
        prior = legacy.read_json(prior_path)
        if prior.get("schema") != "na-cu001-adsorption-case-v0.2" or prior.get("status") != "CHECKPOINT":
            raise SystemExit("HOLD: resume record is not a registered adsorption CHECKPOINT")
        if prior.get("mobility_model") != args.mobility or prior.get("start_site") != args.site or float(prior.get("initial_height_angstrom")) != float(args.height):
            raise SystemExit("HOLD: resume record identifies a different adsorption case")
        if bool(prior.get("provenance", {}).get("scientific_settings_changed")):
            raise SystemExit("HOLD: resume record reports changed scientific settings")
        cell = prior["cell_angstrom"]
        atoms = prior["atoms"]
        continuation_from_checkpoint = True
        prior_link = artifact(prior_path)
    else:
        cell, atoms = v2.build_adsorption_atoms(clean, args.site, float(args.height), args.mobility, protocol)

    if len(atoms) != 177 or sum(1 for atom in atoms if atom["symbol"] == "Na") != 1:
        raise SystemExit("HOLD: registered 4x4 adsorption geometry must contain 176 Cu + 1 Na")
    kmesh = legacy.adsorption_kmesh(int(clean["method"]["kmesh"]))
    if int(kmesh) != 4:
        raise SystemExit("HOLD: frozen primitive k mesh did not map to registered 4x4 adsorption k mesh")

    method = {"ecutwfc_ry": 90.0, "ecutrho_ry": 270.0, "kmesh": int(kmesh)}
    root = Path(args.out_dir).resolve()
    raw = root / "raw"
    tmp = raw / "tmp"
    raw.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    inp = raw / "adsorption_relax.in"
    out = raw / "adsorption_relax.out"
    base_input = legacy.qe_input(
        calculation="relax",
        prefix=f"ads_{args.mobility}_{args.site}_{args.height:g}",
        outdir=tmp,
        pseudo_dir=pseudo_dir,
        cell=cell,
        atoms=atoms,
        species=v2.mixed_species(na_filename),
        ecutwfc=method["ecutwfc_ry"],
        ecutrho=method["ecutrho_ry"],
        kmesh=method["kmesh"],
        esm=True,
        relax=True,
        nosym=True,
    )
    inp.write_text(inject_runtime_control(base_input, args.max_seconds))

    start = time.time()
    rc, _ = legacy.run_command(legacy.mpi_command(Path(args.pw).resolve(), args.np), raw, out, inp)
    elapsed = time.time() - start
    text = out.read_text(errors="replace") if out.is_file() else ""
    energy = legacy.parse_qe_energy(text)
    parsed = legacy.parse_final_positions(text, len(atoms))
    final_atoms = legacy.restore_flags(parsed, atoms) if parsed else atoms
    forces = parse_total_forces(text, len(atoms), legacy.RY_BOHR_TO_EV_ANG)
    max_force = legacy.max_unconstrained_force(forces, final_atoms)
    job_done = "JOB DONE." in text
    bfgs_finished = "End of BFGS Geometry Optimization" in text
    force_tol = float(surface["force_tolerance_ev_per_angstrom"])
    converged = (
        rc == 0
        and job_done
        and bfgs_finished
        and energy is not None
        and max_force is not None
        and float(max_force) <= force_tol
    )

    ni = legacy.na_index(final_atoms)
    classification = legacy.classify_surface_site(final_atoms[ni]["position_angstrom"], cell)
    checks = {
        "returncode_zero": rc == 0,
        "job_done": job_done,
        "bfgs_finished": bfgs_finished,
        "energy_present": energy is not None,
        "actual_total_force_block_present": len(forces) == len(final_atoms),
        "max_force_le_tolerance": max_force is not None and float(max_force) <= force_tol,
    }
    if converged:
        status = "PASS"
        exit_code = 0
    elif rc == 0 and job_done and not bfgs_finished:
        status = "CHECKPOINT"
        exit_code = 75
    else:
        status = "HOLD"
        exit_code = 2

    links = [artifact(clean_path), artifact(na_path), artifact(parity_path), artifact(protocol_path)]
    if prior_link is not None:
        links.append(prior_link)
    record = {
        "schema": "na-cu001-adsorption-case-v0.2",
        "status": status,
        "mobility_model": args.mobility,
        "start_site": args.site,
        "initial_height_angstrom": float(args.height),
        "coverage_ml": float(surface["coverage_ml"]),
        "supercell": list(surface["adsorption_supercell"]),
        "cell_angstrom": cell,
        "atoms": final_atoms,
        "final_site_classification": classification,
        "adsorption_height_angstrom": v2.adsorption_height(final_atoms),
        "final_energy_ev": energy,
        "max_unconstrained_force_ev_per_angstrom": max_force,
        "kmesh_inplane": int(kmesh),
        "method": {
            **method,
            "electrostatics": {"assume_isolated": "esm", "esm_bc": "bc1"},
            "force_tolerance_ev_per_angstrom": force_tol,
        },
        "pass_checks": checks,
        "run": {
            "returncode": rc,
            "job_done": job_done,
            "bfgs_finished": bfgs_finished,
            "energy_ev": energy,
            "forces_ev_per_angstrom": forces,
            "max_unconstrained_force_ev_per_angstrom": max_force,
            "elapsed_s": elapsed,
            "qe_max_seconds_runtime_control": float(args.max_seconds),
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out) if out.is_file() else None,
        },
        "continuation_from_checkpoint": continuation_from_checkpoint,
        "mechanical_runtime_checkpoint": status == "CHECKPOINT",
        "input_artifacts": links,
        "provenance": {
            "source_c7_run_id": int(args.source_run_id),
            "source_c7_commit": args.source_commit,
            "clean_surface_run_id": int(args.clean_run_id),
            "clean_surface_commit": args.clean_commit,
            "electrostatic_consistency_run_id": int(args.parity_run_id),
            "electrostatic_consistency_commit": args.parity_commit,
            "control_commit": args.control_commit,
            "scientific_settings_changed": False,
            "safe_total_force_parser_only": True,
            "runtime_checkpoint_control_only": True,
        },
    }
    write_json(root / "run_record.json", record)
    print(json.dumps(record, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
