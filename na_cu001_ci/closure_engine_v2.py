#!/usr/bin/env python3
"""Corrected, fail-closed Na/Cu(001) computational route.

This module supersedes the v0.1 downstream commands. It preserves the original
raw code for auditability but removes known physical and logical weaknesses:
one-sided Cu mobility is explicit, basin verification is three-dimensional,
cutoffs come from pinned SSSP metadata, clean relaxation is reproduced by an
independent SCF, CI-NEB starts from the selected ordinary path, active-region
Hessians are mass weighted, and barrier sensitivity is not mislabeled as a
statistical uncertainty.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Any, Iterable

import numpy as np

import closure_engine as legacy

SCHEMA_PROTOCOL = "na-cu001-method-protocol-v0.2"
RY_TO_EV = legacy.RY_TO_EV
EV_A2_TO_N_M = legacy.EV_ANG2_TO_N_M
AMU_TO_KG = legacy.AMU_TO_KG
KB_EV_K = legacy.KB_EV_K
MASS_AMU = {"Na": legacy.NA_MASS_AMU, "Cu": legacy.CU_MASS_AMU}


def sha256(path: Path) -> str:
    return legacy.sha256(path)


def read_json(path: Path) -> dict[str, Any]:
    return legacy.read_json(path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    legacy.write_json(path, data)


def artifact(path: Path) -> dict[str, str]:
    return {"path": path.name, "sha256": sha256(path)}


def load_protocol(path: str | Path) -> dict[str, Any]:
    p = Path(path).resolve(); data = read_json(p)
    if data.get("schema") != SCHEMA_PROTOCOL or data.get("status") != "FROZEN_BEFORE_DOWNSTREAM_RESULTS":
        raise SystemExit("HOLD: unsupported or unfrozen method protocol")
    return data


def require(data: dict[str, Any], schema: str, states: set[str] = {"PASS"}) -> None:
    if data.get("schema") != schema:
        raise SystemExit(f"HOLD: expected {schema}, found {data.get('schema')}")
    state = next((data.get(k) for k in ("status", "gate", "scientific_status") if isinstance(data.get(k), str)), None)
    if state not in states:
        raise SystemExit(f"HOLD: {schema} state is {state!r}")


def periodic_delta(a: Iterable[float], b: Iterable[float], cell: list[list[float]], include_z: bool = True) -> np.ndarray:
    fa = legacy.cart_to_frac(a, cell); fb = legacy.cart_to_frac(b, cell); df = fa - fb
    df[0] -= round(float(df[0])); df[1] -= round(float(df[1]))
    if include_z:
        dz = float(a[2]) - float(b[2])
        cart = legacy.frac_to_cart([df[0], df[1], 0.0], cell)
        cart[2] = dz
        return np.asarray(cart, dtype=float)
    df[2] = 0.0
    return np.asarray(legacy.frac_to_cart(df, cell), dtype=float)


def periodic_3d_distance(a: Iterable[float], b: Iterable[float], cell: list[list[float]]) -> float:
    return float(np.linalg.norm(periodic_delta(a, b, cell, include_z=True)))


def unique_cu_layers(atoms: list[dict[str, Any]], tolerance: float = 1e-4) -> list[float]:
    zs = sorted(float(a["position_angstrom"][2]) for a in atoms if a["symbol"] == "Cu")
    layers: list[float] = []
    for z in zs:
        if not layers or abs(z - layers[-1]) > tolerance:
            layers.append(z)
    return layers


def apply_one_sided_mobility(atoms: list[dict[str, Any]], model: str, protocol: dict[str, Any]) -> list[dict[str, Any]]:
    spec = protocol["surface"]["mobility_models"].get(model)
    if not isinstance(spec, dict):
        raise SystemExit(f"HOLD: unknown mobility model {model}")
    output = json.loads(json.dumps(atoms))
    layers = unique_cu_layers(output)
    full = int(spec["full_xyz_top_layers"]); zbuf = int(spec["z_only_buffer_layers"])
    if len(layers) <= full + zbuf:
        raise SystemExit("HOLD: selected slab is too thin for registered one-sided mobility model")
    top = list(reversed(layers))
    full_z = top[:full]; z_only = top[full:full + zbuf]
    for atom in output:
        if atom["symbol"] == "Na":
            atom["flags"] = [1, 1, 1]
            continue
        z = float(atom["position_angstrom"][2])
        if any(abs(z - target) <= 1e-4 for target in full_z):
            atom["flags"] = [1, 1, 1]
        elif any(abs(z - target) <= 1e-4 for target in z_only):
            atom["flags"] = [0, 0, 1]
        else:
            atom["flags"] = [0, 0, 0]
    return output


def active_indices_by_region(atoms: list[dict[str, Any]], cell: list[list[float]]) -> dict[str, list[int]]:
    ni = legacy.na_index(atoms); na_pos = atoms[ni]["position_angstrom"]
    layers = unique_cu_layers(atoms, tolerance=0.60); top_z = layers[-1]; second_z = layers[-2]
    top = [i for i, a in enumerate(atoms) if a["symbol"] == "Cu" and abs(float(a["position_angstrom"][2]) - top_z) <= 0.60]
    second = [i for i, a in enumerate(atoms) if a["symbol"] == "Cu" and abs(float(a["position_angstrom"][2]) - second_z) <= 0.60]
    top.sort(key=lambda i: np.linalg.norm(periodic_delta(atoms[i]["position_angstrom"], na_pos, cell, include_z=False)))
    second.sort(key=lambda i: np.linalg.norm(periodic_delta(atoms[i]["position_angstrom"], na_pos, cell, include_z=False)))
    if len(top) < 4 or len(second) < 4:
        raise SystemExit("HOLD: insufficient Cu atoms for registered active regions")
    return {"na_only": [ni], "na_plus_4cu": [ni] + top[:4], "na_plus_8cu": [ni] + top[:4] + second[:4]}


def adsorption_height(atoms: list[dict[str, Any]]) -> float:
    ni = legacy.na_index(atoms)
    top = max(float(a["position_angstrom"][2]) for a in atoms if a["symbol"] == "Cu")
    return float(atoms[ni]["position_angstrom"][2]) - top


def active_rmsd(a: list[dict[str, Any]], b: list[dict[str, Any]], indices: list[int], cell: list[list[float]]) -> float:
    if len(a) != len(b):
        return float("inf")
    vals = [float(np.dot(periodic_delta(a[i]["position_angstrom"], b[i]["position_angstrom"], cell),
                               periodic_delta(a[i]["position_angstrom"], b[i]["position_angstrom"], cell))) for i in indices]
    return math.sqrt(sum(vals) / len(vals)) if vals else 0.0


def scf_record(root: Path, name: str, cell: list[list[float]], atoms: list[dict[str, Any]], method: dict[str, Any],
               species: list[tuple[str, float, str]], pseudo_dir: Path, pw: Path, np_count: int, esm: bool = True) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True); tmp = root / "tmp"; tmp.mkdir(exist_ok=True)
    inp = root / f"{name}.in"; out = root / f"{name}.out"
    inp.write_text(legacy.qe_input(calculation="scf", prefix=name, outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms, species=species, ecutwfc=float(method["ecutwfc_ry"]),
        ecutrho=float(method["ecutrho_ry"]), kmesh=int(method["kmesh"]), esm=esm, relax=False, nosym=True))
    rc, elapsed = legacy.run_command(legacy.mpi_command(pw, np_count), root, out, inp)
    text = out.read_text(errors="replace"); energy = legacy.parse_qe_energy(text); forces = legacy.parse_qe_forces(text, len(atoms))
    return {"returncode": rc, "job_done": "JOB DONE." in text, "scf_converged": "convergence has been achieved" in text.lower(),
            "energy_ev": energy, "forces_ev_per_angstrom": forces, "elapsed_s": elapsed,
            "input_sha256": sha256(inp), "output_sha256": sha256(out)}


def relax_record(root: Path, name: str, cell: list[list[float]], atoms: list[dict[str, Any]], method: dict[str, Any],
                 species: list[tuple[str, float, str]], pseudo_dir: Path, pw: Path, np_count: int, esm: bool = True) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True); tmp = root / "tmp"; tmp.mkdir(exist_ok=True)
    inp = root / f"{name}.in"; out = root / f"{name}.out"
    inp.write_text(legacy.qe_input(calculation="relax", prefix=name, outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms, species=species, ecutwfc=float(method["ecutwfc_ry"]),
        ecutrho=float(method["ecutrho_ry"]), kmesh=int(method["kmesh"]), esm=esm, relax=True, nosym=True))
    rc, elapsed = legacy.run_command(legacy.mpi_command(pw, np_count), root, out, inp)
    text = out.read_text(errors="replace"); energy = legacy.parse_qe_energy(text)
    parsed = legacy.parse_final_positions(text, len(atoms)); final_atoms = legacy.restore_flags(parsed, atoms) if parsed else atoms
    forces = legacy.parse_qe_forces(text, len(atoms)); max_force = legacy.max_unconstrained_force(forces, final_atoms)
    return {"returncode": rc, "job_done": "JOB DONE." in text, "energy_ev": energy,
            "atoms": final_atoms, "forces_ev_per_angstrom": forces,
            "max_unconstrained_force_ev_per_angstrom": max_force, "elapsed_s": elapsed,
            "input_sha256": sha256(inp), "output_sha256": sha256(out)}


def cu_species() -> list[tuple[str, float, str]]:
    return [("Cu", legacy.CU_MASS_AMU, legacy.CU_PSEUDO)]


def mixed_species(na_filename: str) -> list[tuple[str, float, str]]:
    return [("Cu", legacy.CU_MASS_AMU, legacy.CU_PSEUDO), ("Na", legacy.NA_MASS_AMU, na_filename)]


def method_from_slab(slab: dict[str, Any]) -> dict[str, Any]:
    s = slab["selected_slab_settings"]
    return {"ecutwfc_ry": float(s["ecutwfc_ry"]), "ecutrho_ry": float(s["ecutrho_ry"]),
            "kmesh": int(s["kmesh_inplane"]), "smearing": "mv", "degauss_ry": 0.02,
            "electrostatics": {"assume_isolated": "esm", "esm_bc": "bc1"}}

def command_slab_handoff(args: argparse.Namespace) -> None:
    result_path = Path(args.slab_result).resolve(); bulk_path = Path(args.bulk_handoff).resolve()
    result = read_json(result_path); bulk = read_json(bulk_path)
    require(result, "na-cu001-clean-slab-selection-v0.3")
    require(bulk, "na-cu001-bulk-to-slab-handoff-v0.3", {"bulk_convergence_passed_slab_not_yet_run"})
    selected = result.get("recommended_smallest")
    if not isinstance(selected, dict): raise SystemExit("HOLD: slab result lacks selection")
    source = selected.get("source_record") or {}
    handoff = {
        "schema": "na-cu001-clean-slab-to-relaxation-handoff-v0.3", "status": "PASS", "system": "clean Cu(001)",
        "selected_slab_settings": {"layers": max(7, int(selected["layers"])), "convergence_selected_layers": int(selected["layers"]), "vacuum_angstrom": float(selected["vacuum_angstrom"]),
            "kmesh_inplane": int(selected["kmesh_inplane"]), "a0_angstrom": float(source["a0_angstrom"]),
            "ecutwfc_ry": float(source["ecutwfc_ry"]), "ecutrho_ry": float(source["ecutrho_ry"]),
            "bulk_kmesh": int(source["bulk_kmesh"]), "bulk_energy_ev_per_atom": float(source["e0_ev_per_atom"]),
            "surface_cell": "primitive Cu(001), area a0^2/2",
            "electrostatic_convention": result.get("electrostatic_convention") or {"assume_isolated": "esm", "esm_bc": "bc1"}},
        "convergence_rule": {"surface_excess_tolerance_mev_per_surface_atom": result["energy_tolerance_mev_per_surface_atom"],
            "selected_vacuum_kmesh": [selected["vacuum_angstrom"], selected["kmesh_inplane"]], "convergence_selected_layers": selected["layers"],
            "downstream_layers": max(7, int(selected["layers"])), "downstream_layer_rule": "use at least 7 layers so the expanded one-sided mobility model retains a fixed bottom surface"},
        "input_artifacts": [artifact(result_path), artifact(bulk_path)], "next_gate": "electrostatic_parity"
    }
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))


def command_parity(args: argparse.Namespace) -> None:
    """Audit ESM vacuum stability and record periodic-vs-ESM as a diagnostic.

    The full slab convergence matrix is already executed with ESM bc1, so a
    periodic-vs-ESM difference cannot invalidate method consistency. It is
    retained as a transparent boundary-condition diagnostic. The actual gate
    is stability of the selected ESM slab against the next registered vacuum.
    """
    protocol = load_protocol(args.protocol); slab_path = Path(args.slab_handoff).resolve(); slab = read_json(slab_path)
    require(slab, "na-cu001-clean-slab-to-relaxation-handoff-v0.3")
    s = slab["selected_slab_settings"]
    convention = s.get("electrostatic_convention") or {}
    if convention.get("assume_isolated") != "esm" or convention.get("esm_bc") != "bc1":
        raise SystemExit("HOLD: slab convergence did not use registered ESM bc1 convention")
    selected_v = float(s["vacuum_angstrom"]); grid = [12.0, 16.0, 20.0, 24.0]
    larger = [v for v in grid if v > selected_v]
    comparison_v = min(larger) if larger else selected_v + 4.0
    pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve(); root = Path(args.out_dir).resolve()
    method = {"ecutwfc_ry": s["ecutwfc_ry"], "ecutrho_ry": s["ecutrho_ry"], "kmesh": s["kmesh_inplane"]}
    records = []
    for vacuum, esm in ((selected_v, True), (comparison_v, True), (selected_v, False)):
        cell, atoms = legacy.primitive_clean_geometry(float(s["a0_angstrom"]), int(s["layers"]), vacuum)
        fixed = json.loads(json.dumps(atoms))
        for atom in fixed: atom["flags"] = [0, 0, 0]
        tag = f"electrostatic_v{vacuum:g}_{'esm' if esm else 'periodic'}"
        rec = scf_record(root / tag, tag, cell, fixed, method, cu_species(), pseudo_dir, pw, args.np, esm=esm)
        if rec["returncode"] or not rec["job_done"] or not rec["scf_converged"] or rec["energy_ev"] is None:
            raise SystemExit(f"HOLD: electrostatic consistency SCF failed: {tag}")
        excess = (float(rec["energy_ev"]) - int(s["layers"]) * float(s["bulk_energy_ev_per_atom"])) / 2.0
        records.append({"vacuum_angstrom": vacuum, "esm": esm, "surface_excess_ev_per_surface_atom": excess, "run": rec})
    by = {(r["vacuum_angstrom"], r["esm"]): r for r in records}
    boundary_delta = abs(by[(selected_v, True)]["surface_excess_ev_per_surface_atom"] - by[(selected_v, False)]["surface_excess_ev_per_surface_atom"])
    esm_vac_delta = abs(by[(selected_v, True)]["surface_excess_ev_per_surface_atom"] - by[(comparison_v, True)]["surface_excess_ev_per_surface_atom"])
    tol = float(protocol["surface"]["esm_vacuum_stability_tolerance_mev_per_surface_atom"]) / 1000.0
    checks = {"slab_matrix_and_downstream_share_esm_bc1": True,
              "esm_next_vacuum_change_le_tolerance": esm_vac_delta <= tol,
              "periodic_diagnostic_completed": True}
    handoff = {"schema": "na-cu001-electrostatic-consistency-v0.3", "status": "PASS" if all(checks.values()) else "HOLD",
        "selected_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
        "selected_vacuum_angstrom": selected_v, "comparison_vacuum_angstrom": comparison_v,
        "tolerance_ev_per_surface_atom": tol, "periodic_vs_esm_diagnostic_ev_per_surface_atom": boundary_delta,
        "esm_vacuum_delta_ev_per_surface_atom": esm_vac_delta, "records": records, "pass_checks": checks,
        "interpretation": "Periodic-vs-ESM is reported but not treated as an equality requirement because ESM bc1 is the registered convention for the full slab and downstream route.",
        "input_artifacts": [artifact(slab_path)], "next_gate": "clean_surface_relaxation"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)


def command_clean(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); slab_path = Path(args.slab_handoff).resolve(); parity_path = Path(args.parity_handoff).resolve()
    slab = read_json(slab_path); parity = read_json(parity_path)
    require(slab, "na-cu001-clean-slab-to-relaxation-handoff-v0.3"); require(parity, "na-cu001-electrostatic-consistency-v0.3")
    s = slab["selected_slab_settings"]; cell, atoms = legacy.primitive_clean_geometry(float(s["a0_angstrom"]), int(s["layers"]), float(s["vacuum_angstrom"]))
    method = {"ecutwfc_ry": s["ecutwfc_ry"], "ecutrho_ry": s["ecutrho_ry"], "kmesh": s["kmesh_inplane"]}
    root = Path(args.out_dir).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    relax = relax_record(root / "relax", "clean_relax", cell, atoms, method, cu_species(), pseudo_dir, pw, args.np, esm=True)
    if not relax["atoms"] or relax["energy_ev"] is None: raise SystemExit("HOLD: clean relaxation lacks final geometry/energy")
    fixed = json.loads(json.dumps(relax["atoms"])); [a.update({"flags": [0,0,0]}) for a in fixed]
    reproduce = scf_record(root / "reproduce", "clean_reproduce", cell, fixed, method, cu_species(), pseudo_dir, pw, args.np, esm=True)
    energy_delta = None if reproduce["energy_ev"] is None else abs(float(relax["energy_ev"]) - float(reproduce["energy_ev"]))
    z_values = sorted(float(a["position_angstrom"][2]) for a in relax["atoms"] if a["symbol"] == "Cu")
    symmetry_error = max((abs(z_values[i] + z_values[-1-i] - float(cell[2][2])) for i in range(len(z_values)//2)), default=0.0)
    tol_e = float(protocol["surface"]["energy_reproduction_tolerance_ev"]); tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {"relax_returncode_zero": relax["returncode"] == 0, "relax_job_done": relax["job_done"],
              "max_force_le_tolerance": relax["max_unconstrained_force_ev_per_angstrom"] is not None and relax["max_unconstrained_force_ev_per_angstrom"] <= tol_f,
              "mirror_pair_error_le_0p01": symmetry_error <= 0.01,
              "independent_scf_pass": reproduce["returncode"] == 0 and reproduce["job_done"] and reproduce["scf_converged"] and reproduce["energy_ev"] is not None,
              "independent_energy_reproduction": energy_delta is not None and energy_delta <= tol_e}
    handoff = {"schema": "na-cu001-relaxed-clean-surface-handoff-v0.2", "status": "PASS" if all(checks.values()) else "HOLD",
        "system": "clean Cu(001)", "method": {**method, "electrostatics": {"assume_isolated": "esm", "esm_bc": "bc1"}},
        "cell_angstrom": cell, "atoms": relax["atoms"], "constraint_protocol": "symmetric clean slab; outer two layer pairs z-only; inner layers fixed",
        "relax_energy_ev": relax["energy_ev"], "independent_scf_energy_ev": reproduce["energy_ev"], "energy_reproduction_delta_ev": energy_delta,
        "max_unconstrained_force_ev_per_angstrom": relax["max_unconstrained_force_ev_per_angstrom"], "mirror_pair_error_angstrom": symmetry_error,
        "pass_checks": checks, "runs": {"relax": relax, "independent_scf": reproduce},
        "input_artifacts": [artifact(slab_path), artifact(parity_path)], "next_gate": "adsorption_site_screening"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)


def command_resolve_na(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); probe_path = Path(args.probe).resolve(); bulk_path = Path(args.bulk_handoff).resolve()
    probe = read_json(probe_path); bulk = read_json(bulk_path)
    require(probe, "na-cu001-na-pseudo-probe-v0.2"); require(bulk, "na-cu001-bulk-to-slab-handoff-v0.3", {"bulk_convergence_passed_slab_not_yet_run"})
    selected = probe["selected"]; cut = probe["authoritative_cutoffs"]
    wfc = max(float(bulk["selected_bulk_settings"]["ecutwfc_ry"]), float(cut["recommended_ecutwfc_ry"]))
    rho = max(float(bulk["selected_bulk_settings"]["ecutrho_ry"]), float(cut["recommended_ecutrho_ry"]))
    source = Path(args.pseudo_root).resolve() / selected["path"]; pseudo_dir = Path(args.pseudo_dir).resolve(); pseudo_dir.mkdir(parents=True, exist_ok=True)
    dest = pseudo_dir / selected["filename"]; shutil.copy2(source, dest)
    if sha256(dest) != selected["sha256"]: raise SystemExit("HOLD: Na UPF copy hash mismatch")
    root = Path(args.out_dir).resolve(); root.mkdir(parents=True, exist_ok=True); tmp = root / "tmp"; tmp.mkdir(exist_ok=True)
    inp = root / "na_atom.in"; out = root / "na_atom.out"
    inp.write_text(legacy.na_atom_input(prefix="na_isolated", outdir=tmp, pseudo_dir=pseudo_dir, na_filename=dest.name, ecutwfc=wfc, ecutrho=rho))
    rc, elapsed = legacy.run_command(legacy.mpi_command(Path(args.pw).resolve(), args.np), root, out, inp)
    text = out.read_text(errors="replace"); energy = legacy.parse_qe_energy(text)
    checks = {"returncode_zero": rc == 0, "job_done": "JOB DONE." in text, "energy_present": energy is not None,
              "archive_hash_verified": probe["archive"]["sha256"] == protocol["immutable_sources"]["sssp_pbe_efficiency_v2_archive_sha256"],
              "upf_hash_verified": selected["sha256"] == protocol["immutable_sources"]["na_upf_sha256"]}
    handoff = {"schema": "na-cu001-na-pseudopotential-handoff-v0.2", "status": "PASS" if all(checks.values()) else "HOLD",
        "selected": {**selected, "installed_filename": dest.name, "installed_sha256": sha256(dest)}, "authoritative_cutoffs": cut,
        "selected_mixed_settings": {"ecutwfc_ry": wfc, "ecutrho_ry": rho,
            "rule": "componentwise maximum of bulk PASS and authoritative SSSP v2 metadata"},
        "isolated_atom_reference": {"energy_ev": energy, "elapsed_s": elapsed, "input_sha256": sha256(inp), "output_sha256": sha256(out)},
        "pass_checks": checks, "input_artifacts": [artifact(probe_path), artifact(bulk_path)], "next_gate": "adsorption_site_screening"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)

def build_adsorption_atoms(clean: dict[str, Any], site: str, height: float, mobility: str, protocol: dict[str, Any]) -> tuple[list[list[float]], list[dict[str, Any]]]:
    cell, atoms = legacy.replicate_surface(clean["cell_angstrom"], clean["atoms"], 4)
    atoms = apply_one_sided_mobility(atoms, mobility, protocol)
    fx, fy = legacy.surface_site_fraction(site); pos = legacy.frac_to_cart([fx, fy, 0.0], cell).tolist()
    pos[2] = legacy.top_layer_z(atoms) + height
    atoms.append({"symbol": "Na", "position_angstrom": pos, "flags": [1,1,1]})
    return cell, atoms


def command_adsorption_run(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); clean_path = Path(args.clean_handoff).resolve(); na_path = Path(args.na_handoff).resolve(); parity_path = Path(args.parity_handoff).resolve()
    clean = read_json(clean_path); na = read_json(na_path); parity = read_json(parity_path)
    require(clean, "na-cu001-relaxed-clean-surface-handoff-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2"); require(parity, "na-cu001-electrostatic-consistency-v0.3")
    sites = protocol["surface"]["adsorption_starts"]["sites"]; heights = protocol["surface"]["adsorption_starts"]["heights_angstrom"]
    if args.site not in sites or float(args.height) not in [float(x) for x in heights]: raise SystemExit("HOLD: unregistered adsorption start")
    cell, atoms = build_adsorption_atoms(clean, args.site, float(args.height), args.mobility, protocol)
    mixed = na["selected_mixed_settings"]; kmesh = legacy.adsorption_kmesh(int(clean["method"]["kmesh"]))
    method = {"ecutwfc_ry": mixed["ecutwfc_ry"], "ecutrho_ry": mixed["ecutrho_ry"], "kmesh": kmesh}
    root = Path(args.out_dir).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve(); nafile = na["selected"]["installed_filename"]
    rec = relax_record(root, f"ads_{args.mobility}_{args.site}_{args.height:g}", cell, atoms, method, mixed_species(nafile), pseudo_dir, pw, args.np, esm=True)
    ni = legacy.na_index(rec["atoms"]); classification = legacy.classify_surface_site(rec["atoms"][ni]["position_angstrom"], cell)
    tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {"returncode_zero": rec["returncode"] == 0, "job_done": rec["job_done"], "energy_present": rec["energy_ev"] is not None,
              "max_force_le_tolerance": rec["max_unconstrained_force_ev_per_angstrom"] is not None and rec["max_unconstrained_force_ev_per_angstrom"] <= tol_f}
    record = {"schema": "na-cu001-adsorption-case-v0.2", "status": "PASS" if all(checks.values()) else "HOLD",
        "mobility_model": args.mobility, "start_site": args.site, "initial_height_angstrom": float(args.height),
        "coverage_ml": float(protocol["surface"]["coverage_ml"]), "supercell": protocol["surface"]["adsorption_supercell"],
        "cell_angstrom": cell, "atoms": rec["atoms"], "final_site_classification": classification,
        "adsorption_height_angstrom": adsorption_height(rec["atoms"]), "final_energy_ev": rec["energy_ev"],
        "max_unconstrained_force_ev_per_angstrom": rec["max_unconstrained_force_ev_per_angstrom"], "kmesh_inplane": kmesh,
        "pass_checks": checks, "run": rec, "input_artifacts": [artifact(clean_path), artifact(na_path), artifact(parity_path)]}
    write_json(root / "run_record.json", record); print(json.dumps(record, indent=2))
    if record["status"] != "PASS": raise SystemExit(2)


def command_adsorption_analyze(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); records = [read_json(p) for p in sorted(Path(args.records).resolve().rglob("run_record.json"))]
    sites = protocol["surface"]["adsorption_starts"]["sites"]; heights = [float(x) for x in protocol["surface"]["adsorption_starts"]["heights_angstrom"]]
    models = list(protocol["surface"]["mobility_models"])
    expected = {(m,s,h) for m in models for s in sites for h in heights}
    found = {(r.get("mobility_model"), r.get("start_site"), float(r.get("initial_height_angstrom"))) for r in records}
    if found != expected: raise SystemExit(f"HOLD: adsorption matrix incomplete; expected {len(expected)}, found {len(found)}")
    analyses: dict[str, Any] = {}; overall = "PASS"
    for model in models:
        subset = [r for r in records if r["mobility_model"] == model]
        all_pass = all(r.get("schema") == "na-cu001-adsorption-case-v0.2" and r.get("status") == "PASS" for r in subset)
        global_min = min(subset, key=lambda r: float(r["final_energy_ev"]))
        hollow = [r for r in subset if r["final_site_classification"]["site"] == "hollow"]
        selected = min(hollow, key=lambda r: float(r["final_energy_ev"])) if hollow else None
        mechanism_state = "REGISTERED_HOLLOW_ROUTE" if selected and global_min["final_site_classification"]["site"] == "hollow" else "MECHANISM_REVISION_REQUIRED"
        status = "PASS" if all_pass and mechanism_state == "REGISTERED_HOLLOW_ROUTE" else "HOLD"
        if status != "PASS": overall = "HOLD"
        analyses[model] = {"status": status, "mechanism_state": mechanism_state, "global_minimum": global_min,
                           "selected_hollow_minimum": selected, "all_starts_converged": all_pass}
    links = [artifact(Path(x).resolve()) for x in (args.clean_handoff, args.na_handoff, args.parity_handoff)]
    handoff = {"schema": "na-cu001-adsorption-site-handoff-v0.2", "status": overall, "system": "Na/Cu(001)",
        "coverage_model": {"supercell": [4,4], "na_per_surface": 1, "coverage_ml": protocol["surface"]["coverage_ml"]},
        "mobility_analyses": analyses, "failure_rule": "unexpected minimum is retained as MECHANISM_REVISION_REQUIRED and never coerced into the hollow route",
        "input_artifacts": links, "next_gate": "endpoint_geometry_verification" if overall == "PASS" else "new_preregistered_mechanism_protocol"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if overall != "PASS": raise SystemExit(2)


def command_endpoints(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); ads_path = Path(args.adsorption_handoff).resolve(); na_path = Path(args.na_handoff).resolve()
    ads = read_json(ads_path); na = read_json(na_path); require(ads, "na-cu001-adsorption-site-handoff-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    selected = ads["mobility_analyses"][args.mobility]["selected_hollow_minimum"]
    cell = selected["cell_angstrom"]; atoms_a = json.loads(json.dumps(selected["atoms"])); ni = legacy.na_index(atoms_a)
    atoms_b0 = json.loads(json.dumps(atoms_a)); atoms_b0[ni]["position_angstrom"] = legacy.wrap_xy(legacy.vec_add(atoms_b0[ni]["position_angstrom"], legacy.vec_scale(cell[0], 0.25)), cell)
    method = {"ecutwfc_ry": na["selected_mixed_settings"]["ecutwfc_ry"], "ecutrho_ry": na["selected_mixed_settings"]["ecutrho_ry"], "kmesh": selected["kmesh_inplane"]}
    nafile = na["selected"]["installed_filename"]; root = Path(args.out_dir).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    fixed_a = json.loads(json.dumps(atoms_a)); [a.update({"flags":[0,0,0]}) for a in fixed_a]
    a_scf = scf_record(root / "a_scf", "endpoint_a", cell, fixed_a, method, mixed_species(nafile), pseudo_dir, pw, args.np, esm=True)
    b_relax = relax_record(root / "b_relax", "endpoint_b_relax", cell, atoms_b0, method, mixed_species(nafile), pseudo_dir, pw, args.np, esm=True)
    atoms_b = b_relax["atoms"]; fixed_b = json.loads(json.dumps(atoms_b)); [a.update({"flags":[0,0,0]}) for a in fixed_b]
    b_scf = scf_record(root / "b_scf", "endpoint_b", cell, fixed_b, method, mixed_species(nafile), pseudo_dir, pw, args.np, esm=True)
    da = None if a_scf["energy_ev"] is None or b_scf["energy_ev"] is None else abs(float(a_scf["energy_ev"]) - float(b_scf["energy_ev"]))
    a_force = legacy.max_unconstrained_force(a_scf["forces_ev_per_angstrom"], atoms_a); b_force = legacy.max_unconstrained_force(b_scf["forces_ev_per_angstrom"], atoms_b)
    class_a = legacy.classify_surface_site(atoms_a[ni]["position_angstrom"], cell); class_b = legacy.classify_surface_site(atoms_b[ni]["position_angstrom"], cell)
    translation = periodic_delta(atoms_b[ni]["position_angstrom"], atoms_a[ni]["position_angstrom"], cell, include_z=False)
    target = np.asarray(cell[0], dtype=float) * 0.25; translation_error = float(np.linalg.norm(translation[:2] - target[:2]))
    tol_e = float(protocol["surface"]["energy_reproduction_tolerance_ev"]); tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {"a_scf_pass": a_scf["returncode"] == 0 and a_scf["job_done"] and a_scf["scf_converged"],
              "b_relax_pass": b_relax["returncode"] == 0 and b_relax["job_done"], "b_scf_pass": b_scf["returncode"] == 0 and b_scf["job_done"] and b_scf["scf_converged"],
              "energy_difference_le_tolerance": da is not None and da <= tol_e, "a_force_le_tolerance": a_force is not None and a_force <= tol_f,
              "b_force_le_tolerance": b_force is not None and b_force <= tol_f, "both_hollow": class_a["site"] == class_b["site"] == "hollow",
              "translation_error_le_0p05": translation_error <= 0.05}
    handoff = {"schema": "na-cu001-endpoints-handoff-v0.2", "status": "PASS" if all(checks.values()) else "HOLD", "mobility_model": args.mobility,
        "system": "Na diffusion between nearest-neighbor hollow sites on Cu(001)", "cell_angstrom": cell, "method": method,
        "endpoint_a": {"atoms": atoms_a, "energy_ev": a_scf["energy_ev"], "site": class_a, "scf": a_scf},
        "endpoint_b": {"atoms": atoms_b, "energy_ev": b_scf["energy_ev"], "site": class_b, "relax": b_relax, "scf": b_scf},
        "energy_difference_ev": da, "primitive_translation_error_angstrom": translation_error, "pass_checks": checks,
        "input_artifacts": [artifact(ads_path), artifact(na_path)], "next_gate": "path_and_image_convergence"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)

def neb_input_frames(*, prefix: str, outdir: Path, pseudo_dir: Path, cell: list[list[float]], frames: list[list[dict[str, Any]]],
                     method: dict[str, Any], na_filename: str, ci: bool, path_thr: float) -> str:
    if len(frames) < 3: raise SystemExit("HOLD: NEB requires at least three frames")
    lines = ["BEGIN", "BEGIN_PATH_INPUT", "&PATH", "  restart_mode = 'from_scratch',", "  string_method = 'neb',",
        "  nstep_path = 250,", f"  num_of_images = {len(frames)},", "  opt_scheme = 'broyden',",
        f"  CI_scheme = '{'auto' if ci else 'no-CI'}',", "  first_last_opt = .false.,", "  minimum_image = .true.,",
        f"  path_thr = {path_thr:.8f},", "/", "END_PATH_INPUT", "BEGIN_ENGINE_INPUT",
        "&CONTROL", "  calculation = 'scf',", f"  prefix = '{prefix}',", f"  outdir = '{outdir}',", f"  pseudo_dir = '{pseudo_dir}',",
        "  tprnfor = .true.,", "  verbosity = 'high',", "/", "&SYSTEM", "  ibrav = 0,",
        f"  nat = {len(frames[0])},", "  ntyp = 2,", f"  ecutwfc = {float(method['ecutwfc_ry']):.8f},",
        f"  ecutrho = {float(method['ecutrho_ry']):.8f},", "  occupations = 'smearing',", "  smearing = 'mv',", "  degauss = 0.02,",
        "  nosym = .true.,", "  assume_isolated = 'esm',", "  esm_bc = 'bc1',", "/", "&ELECTRONS",
        "  conv_thr = 1.0d-9,", "  mixing_beta = 0.3,", "  electron_maxstep = 300,", "/", "&IONS", "/",
        "ATOMIC_SPECIES", f"Cu {legacy.CU_MASS_AMU:.10f} {legacy.CU_PSEUDO}", f"Na {legacy.NA_MASS_AMU:.10f} {na_filename}", "BEGIN_POSITIONS"]
    for index, frame in enumerate(frames):
        lines.append("FIRST_IMAGE" if index == 0 else "LAST_IMAGE" if index == len(frames)-1 else "INTERMEDIATE_IMAGE")
        lines.append("ATOMIC_POSITIONS angstrom")
        for atom in frame:
            x,y,z = atom["position_angstrom"]; f = atom.get("flags", [0,0,0])
            lines.append(f"{atom['symbol']} {x:.12f} {y:.12f} {z:.12f} {f[0]} {f[1]} {f[2]}")
    lines.extend(["END_POSITIONS", "K_POINTS automatic", f"{int(method['kmesh'])} {int(method['kmesh'])} 1 0 0 0", "CELL_PARAMETERS angstrom"])
    lines.extend(" ".join(f"{x:.12f}" for x in vector) for vector in cell)
    lines.extend(["END_ENGINE_INPUT", "END", ""])
    return "\n".join(lines)


def linear_frames(a: list[dict[str, Any]], b: list[dict[str, Any]], n: int, cell: list[list[float]]) -> list[list[dict[str, Any]]]:
    frames: list[list[dict[str, Any]]] = []
    for k in range(n):
        t = k / (n - 1); frame = []
        for aa, bb in zip(a, b):
            delta = periodic_delta(bb["position_angstrom"], aa["position_angstrom"], cell, include_z=True)
            pos = np.asarray(aa["position_angstrom"], dtype=float) + t * delta
            pos = np.asarray(legacy.wrap_xy(pos.tolist(), cell))
            frame.append({"symbol": aa["symbol"], "position_angstrom": pos.tolist(), "flags": list(aa.get("flags", [0,0,0]))})
        frames.append(frame)
    frames[0] = json.loads(json.dumps(a)); frames[-1] = json.loads(json.dumps(b))
    return frames


def run_neb(root: Path, endpoints: dict[str, Any], na: dict[str, Any], neb: Path, pseudo_dir: Path,
            image_count: int, np_count: int, ci: bool, initial_frames: list[list[dict[str, Any]]] | None, protocol: dict[str, Any]) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True); tmp = root / "tmp"; tmp.mkdir(exist_ok=True)
    frames = initial_frames or linear_frames(endpoints["endpoint_a"]["atoms"], endpoints["endpoint_b"]["atoms"], image_count, endpoints["cell_angstrom"])
    if len(frames) != image_count: raise SystemExit("HOLD: frame count does not match image count")
    reference_flags = [a.get("flags", [0,0,0]) for a in endpoints["endpoint_a"]["atoms"]]
    for frame in frames:
        if len(frame) != len(reference_flags): raise SystemExit("HOLD: NEB frame atom count mismatch")
        for atom, flags in zip(frame, reference_flags): atom["flags"] = list(flags)
    tag = f"{endpoints['mobility_model']}_{'ci' if ci else 'neb'}_{image_count}"
    inp = root / f"{tag}.in"; out = root / f"{tag}.out"
    threshold = float(protocol["surface"]["ci_path_force_tolerance_ev_per_angstrom"] if ci else protocol["surface"]["path_force_tolerance_ev_per_angstrom"])
    inp.write_text(neb_input_frames(prefix=tag, outdir=tmp, pseudo_dir=pseudo_dir, cell=endpoints["cell_angstrom"], frames=frames,
                                    method=endpoints["method"], na_filename=na["selected"]["installed_filename"], ci=ci, path_thr=threshold))
    rc, elapsed = legacy.run_command(legacy.mpi_command(neb, np_count, ["-inp", str(inp)]), root, out)
    text = out.read_text(errors="replace"); parsed = legacy.parse_neb_output(text, image_count)
    xyz = root / f"{tag}.xyz"; parsed_frames = legacy.parse_xyz_frames(xyz) if xyz.is_file() else []
    if parsed_frames:
        for frame in parsed_frames:
            for atom, flags in zip(frame, reference_flags): atom["flags"] = list(flags)
    checks = {"returncode_zero": rc == 0, "job_done": parsed["job_done"], "converged": parsed["converged"],
              "barrier_present": parsed["forward_barrier_ev"] is not None, "image_table_complete": len(parsed["images"]) == image_count,
              "coordinate_frames_complete": len(parsed_frames) == image_count}
    return {"schema": "na-cu001-neb-case-v0.2", "status": "PASS" if all(checks.values()) else "HOLD",
        "mobility_model": endpoints["mobility_model"], "ci": ci, "image_count": image_count, "path_threshold_ev_per_angstrom": threshold,
        **parsed, "frames": parsed_frames, "initial_frames_sha256": hashlib.sha256(json.dumps(frames, sort_keys=True).encode()).hexdigest(),
        "elapsed_s": elapsed, "input_sha256": sha256(inp), "output_sha256": sha256(out), "xyz_sha256": sha256(xyz) if xyz.is_file() else None,
        "pass_checks": checks}


def command_neb_run(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); ep_path = Path(args.endpoints_handoff).resolve(); na_path = Path(args.na_handoff).resolve()
    endpoints = read_json(ep_path); na = read_json(na_path); require(endpoints, "na-cu001-endpoints-handoff-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    if int(args.images) not in {5,7,9}: raise SystemExit("HOLD: unregistered image count")
    result = run_neb(Path(args.out_dir).resolve(), endpoints, na, Path(args.neb).resolve(), Path(args.pseudo_dir).resolve(), int(args.images), args.np, False, None, protocol)
    result["input_artifacts"] = [artifact(ep_path), artifact(na_path)]; write_json(Path(args.out_dir).resolve() / "run_record.json", result); print(json.dumps(result, indent=2))
    if result["status"] != "PASS": raise SystemExit(2)


def command_neb_analyze(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); records = [read_json(p) for p in sorted(Path(args.records).resolve().rglob("run_record.json"))]
    subset = [r for r in records if r.get("mobility_model") == args.mobility]
    if {int(r.get("image_count")) for r in subset} != {5,7,9} or len(subset) != 3: raise SystemExit("HOLD: ordinary NEB matrix incomplete")
    if not all(r.get("status") == "PASS" and not r.get("ci") for r in subset): raise SystemExit("HOLD: ordinary NEB case failed")
    by = {int(r["image_count"]): r for r in subset}; barriers = {n: float(by[n]["forward_barrier_ev"]) for n in (5,7,9)}
    tol = 0.005; selected = None
    for n in (5,7,9):
        if max(abs(barriers[n]-barriers[m]) for m in (5,7,9) if m >= n) <= tol: selected = n; break
    links = [artifact(Path(args.endpoints_handoff).resolve()), artifact(Path(args.na_handoff).resolve())]
    handoff = {"schema": "na-cu001-path-convergence-handoff-v0.2", "status": "PASS" if selected else "HOLD", "mobility_model": args.mobility,
        "registered_image_counts": [5,7,9], "barrier_tolerance_ev": tol, "barriers_ev": barriers,
        "barrier_range_ev": max(barriers.values())-min(barriers.values()), "selected_image_count": selected,
        "selected_record": by.get(selected), "all_records": by, "input_artifacts": links, "next_gate": "climbing_image_neb"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)


def command_ci(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); path_path = Path(args.path_handoff).resolve(); ep_path = Path(args.endpoints_handoff).resolve(); na_path = Path(args.na_handoff).resolve()
    path = read_json(path_path); endpoints = read_json(ep_path); na = read_json(na_path)
    require(path, "na-cu001-path-convergence-handoff-v0.2"); require(endpoints, "na-cu001-endpoints-handoff-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    initial_frames = path["selected_record"].get("frames") or []
    if len(initial_frames) != int(path["selected_image_count"]): raise SystemExit("HOLD: selected ordinary NEB frames absent")
    result = run_neb(Path(args.out_dir).resolve(), endpoints, na, Path(args.neb).resolve(), Path(args.pseudo_dir).resolve(),
                     int(path["selected_image_count"]), args.np, True, initial_frames, protocol)
    images = result.get("images") or []; internal = images[1:-1]; max_row = max(internal, key=lambda r: r["energy_ev"]) if internal else None
    frames = result.get("frames") or []; saddle_atoms = frames[max_row["index"]-1] if max_row and len(frames)==len(images) else None
    tol_e = float(protocol["surface"]["energy_reproduction_tolerance_ev"]); tol_path = float(protocol["surface"]["ci_path_force_tolerance_ev_per_angstrom"])
    checks = {"neb_pass": result["status"] == "PASS", "maximum_internal": max_row is not None and 1 < max_row["index"] < len(images),
              "saddle_frame_available": saddle_atoms is not None,
              "endpoint_energy_difference_reproduced": bool(images) and abs((float(images[-1]["energy_ev"]) - float(images[0]["energy_ev"])) - (float(endpoints["endpoint_b"]["energy_ev"]) - float(endpoints["endpoint_a"]["energy_ev"]))) <= tol_e,
              "path_error_le_tolerance": result["max_internal_error_ev_per_angstrom"] is not None and result["max_internal_error_ev_per_angstrom"] <= tol_path,
              "initialized_from_ordinary_path": result["initial_frames_sha256"] == hashlib.sha256(json.dumps(initial_frames, sort_keys=True).encode()).hexdigest()}
    handoff = {"schema": "na-cu001-ci-neb-handoff-v0.2", "status": "PASS" if all(checks.values()) else "HOLD", "mobility_model": endpoints["mobility_model"],
        "image_count": result["image_count"], "forward_barrier_ev": result["forward_barrier_ev"], "reverse_barrier_ev": result["reverse_barrier_ev"],
        "images": images, "maximum_energy_image": max_row, "saddle_atoms": saddle_atoms, "cell_angstrom": endpoints["cell_angstrom"],
        "method": endpoints["method"], "pass_checks": checks, "run_record": result,
        "input_artifacts": [artifact(path_path), artifact(ep_path), artifact(na_path)], "next_gate": "mobility_convergence"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)


def command_mobility_gate(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); p_ci = Path(args.primary_ci).resolve(); e_ci = Path(args.expanded_ci).resolve()
    p_ep = Path(args.primary_endpoints).resolve(); e_ep = Path(args.expanded_endpoints).resolve(); p_path = Path(args.primary_path).resolve(); e_path = Path(args.expanded_path).resolve()
    primary = read_json(p_ci); expanded = read_json(e_ci)
    require(primary, "na-cu001-ci-neb-handoff-v0.2"); require(expanded, "na-cu001-ci-neb-handoff-v0.2")
    delta = abs(float(primary["forward_barrier_ev"]) - float(expanded["forward_barrier_ev"])); tol = float(protocol["surface"]["mobility_barrier_tolerance_ev"])
    checks = {"models_are_primary_and_expanded": primary["mobility_model"] == "primary" and expanded["mobility_model"] == "expanded",
              "barrier_difference_le_tolerance": delta <= tol}
    status = "PASS" if all(checks.values()) else "HOLD"
    handoff = {"schema": "na-cu001-mobility-convergence-v0.2", "status": status, "selected_model": "primary" if status == "PASS" else None,
        "primary_barrier_ev": primary["forward_barrier_ev"], "expanded_barrier_ev": expanded["forward_barrier_ev"],
        "barrier_difference_ev": delta, "tolerance_ev": tol, "pass_checks": checks,
        "extension_required": None if status == "PASS" else "A third, larger mobile region must be preregistered; no barrier is admitted.",
        "selected_artifacts": {"endpoints": artifact(p_ep), "path": artifact(p_path), "ci": artifact(p_ci)} if status == "PASS" else None,
        "comparison_artifacts": {"endpoints": artifact(e_ep), "path": artifact(e_path), "ci": artifact(e_ci)},
        "input_artifacts": [artifact(p_ep), artifact(e_ep), artifact(p_path), artifact(e_path), artifact(p_ci), artifact(e_ci)],
        "next_gate": "mass_weighted_active_region_hessian"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if status != "PASS": raise SystemExit(2)

def selected_inputs(gate: dict[str, Any], primary_ep: dict[str, Any], expanded_ep: dict[str, Any], primary_ci: dict[str, Any], expanded_ci: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    require(gate, "na-cu001-mobility-convergence-v0.2")
    if gate["selected_model"] == "primary": return primary_ep, primary_ci
    if gate["selected_model"] == "expanded": return expanded_ep, expanded_ci
    raise SystemExit("HOLD: mobility gate has no selected model")


def command_hessian_plan(args: argparse.Namespace) -> None:
    gate_path = Path(args.mobility_gate).resolve(); gate = read_json(gate_path)
    p_ep = read_json(Path(args.primary_endpoints)); e_ep = read_json(Path(args.expanded_endpoints)); p_ci = read_json(Path(args.primary_ci)); e_ci = read_json(Path(args.expanded_ci))
    endpoints, ci = selected_inputs(gate, p_ep, e_ep, p_ci, e_ci)
    require(endpoints, "na-cu001-endpoints-handoff-v0.2"); require(ci, "na-cu001-ci-neb-handoff-v0.2")
    regions = active_indices_by_region(endpoints["endpoint_a"]["atoms"], endpoints["cell_angstrom"])
    plan = {"schema": "na-cu001-hessian-plan-v0.2", "status": "PASS", "selected_mobility_model": gate["selected_model"],
        "cell_angstrom": endpoints["cell_angstrom"], "method": endpoints["method"], "minimum_atoms": endpoints["endpoint_a"]["atoms"], "saddle_atoms": ci["saddle_atoms"],
        "endpoint_b_atoms": endpoints["endpoint_b"]["atoms"], "regions": regions,
        "centers": ["minimum", "saddle"], "deltas_angstrom": [0.02,0.04],
        "input_artifacts": [artifact(gate_path), artifact(Path(args.primary_endpoints).resolve()), artifact(Path(args.expanded_endpoints).resolve()),
                            artifact(Path(args.primary_ci).resolve()), artifact(Path(args.expanded_ci).resolve())],
        "next_gate": "mass_weighted_hessian_cases"}
    write_json(Path(args.out).resolve(), plan); print(json.dumps(plan, indent=2))


def hessian_center_atoms(plan: dict[str, Any], center: str) -> list[dict[str, Any]]:
    if center == "minimum": return json.loads(json.dumps(plan["minimum_atoms"]))
    if center == "saddle": return json.loads(json.dumps(plan["saddle_atoms"]))
    raise SystemExit("HOLD: invalid Hessian center")


def command_hessian_center(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan).resolve(); na_path = Path(args.na_handoff).resolve(); plan = read_json(plan_path); na = read_json(na_path)
    require(plan, "na-cu001-hessian-plan-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    atoms = hessian_center_atoms(plan, args.center); fixed = json.loads(json.dumps(atoms)); [a.update({"flags":[0,0,0]}) for a in fixed]
    method = {"ecutwfc_ry": na["selected_mixed_settings"]["ecutwfc_ry"], "ecutrho_ry": na["selected_mixed_settings"]["ecutrho_ry"], "kmesh": int(args.kmesh)}
    rec = scf_record(Path(args.out_dir), f"hessian_{args.center}_center", plan["cell_angstrom"], fixed, method,
                     mixed_species(na["selected"]["installed_filename"]), Path(args.pseudo_dir), Path(args.pw), args.np, esm=True)
    active = plan["regions"]["na_plus_8cu"]; forces = rec["forces_ev_per_angstrom"]
    max_active = max((float(np.linalg.norm(forces[i])) for i in active), default=None) if len(forces)==len(atoms) else None
    record = {"schema": "na-cu001-hessian-center-v0.2", "status": "PASS" if rec["returncode"]==0 and rec["job_done"] and rec["scf_converged"] and max_active is not None else "HOLD",
        "center": args.center, "max_active_force_ev_per_angstrom": max_active, "forces_active": {str(i): forces[i] for i in active} if len(forces)==len(atoms) else {},
        "run": rec, "input_artifacts": [artifact(plan_path), artifact(na_path)]}
    write_json(Path(args.out).resolve(), record); print(json.dumps(record, indent=2))
    if record["status"] != "PASS": raise SystemExit(2)


def command_hessian_case(args: argparse.Namespace) -> None:
    plan_path = Path(args.plan).resolve(); na_path = Path(args.na_handoff).resolve(); plan = read_json(plan_path); na = read_json(na_path)
    require(plan, "na-cu001-hessian-plan-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    indices = [int(x) for x in plan["regions"][args.region]]; slot = int(args.slot)
    root = Path(args.out_dir).resolve(); root.mkdir(parents=True, exist_ok=True)
    if slot >= len(indices):
        record = {"schema": "na-cu001-hessian-case-v0.2", "status": "SKIP", "center": args.center, "region": args.region,
                  "delta_angstrom": float(args.delta), "slot": slot, "reason": "slot outside region"}
        write_json(Path(args.out).resolve(), record); print(json.dumps(record, indent=2)); return
    atoms0 = hessian_center_atoms(plan, args.center); displaced_index = indices[slot]
    method = {"ecutwfc_ry": na["selected_mixed_settings"]["ecutwfc_ry"], "ecutrho_ry": na["selected_mixed_settings"]["ecutrho_ry"], "kmesh": int(args.kmesh)}
    pseudo_dir = Path(args.pseudo_dir); pw = Path(args.pw); species = mixed_species(na["selected"]["installed_filename"])
    cases = []
    for axis in range(3):
        for sign in (-1,1):
            atoms = json.loads(json.dumps(atoms0)); [a.update({"flags":[0,0,0]}) for a in atoms]
            atoms[displaced_index]["position_angstrom"][axis] += sign * float(args.delta)
            tag = f"{args.center}_{args.region}_d{float(args.delta):.2f}_s{slot}_a{axis}_{sign:+d}".replace(".","p").replace("+","p").replace("-","m")
            rec = scf_record(root / tag, tag, plan["cell_angstrom"], atoms, method, species, pseudo_dir, pw, args.np, esm=True)
            if rec["returncode"] or not rec["job_done"] or not rec["scf_converged"] or len(rec["forces_ev_per_angstrom"]) != len(atoms):
                raise SystemExit(f"HOLD: Hessian displacement failed: {tag}")
            cases.append({"axis": axis, "sign": sign, "forces_active": [rec["forces_ev_per_angstrom"][i] for i in indices],
                          "run": {k: rec[k] for k in ("energy_ev","elapsed_s","input_sha256","output_sha256")}})
    record = {"schema": "na-cu001-hessian-case-v0.2", "status": "PASS", "center": args.center, "region": args.region,
        "delta_angstrom": float(args.delta), "slot": slot, "displaced_atom_index": displaced_index,
        "active_indices": indices, "cases": cases, "input_artifacts": [artifact(plan_path), artifact(na_path)]}
    write_json(Path(args.out).resolve(), record); print(json.dumps(record, indent=2))


def assemble_hessian(records: list[dict[str, Any]], indices: list[int], delta: float) -> np.ndarray:
    n = len(indices); h = np.zeros((3*n,3*n), dtype=float); by_slot = {int(r["slot"]): r for r in records}
    if set(by_slot) != set(range(n)): raise ValueError(f"missing Hessian slots: expected {set(range(n))}, found {set(by_slot)}")
    for slot in range(n):
        rec = by_slot[slot]; case_map = {(int(c["axis"]), int(c["sign"])): c for c in rec["cases"]}
        for axis in range(3):
            plus = np.asarray(case_map[(axis,1)]["forces_active"], dtype=float).reshape(-1)
            minus = np.asarray(case_map[(axis,-1)]["forces_active"], dtype=float).reshape(-1)
            h[:,3*slot+axis] = -(plus-minus)/(2.0*delta)
    return 0.5*(h+h.T)


def mass_weighted_modes(hessian_ev_a2: np.ndarray, atoms: list[dict[str, Any]], indices: list[int], zero_tol: float) -> dict[str, Any]:
    masses = np.array([MASS_AMU[atoms[i]["symbol"]] * AMU_TO_KG for i in indices for _ in range(3)], dtype=float)
    dyn = hessian_ev_a2 * EV_A2_TO_N_M / np.sqrt(np.outer(masses,masses))
    evals, evecs = np.linalg.eigh(dyn)
    freqs = np.sign(evals) * np.sqrt(np.abs(evals)) / (2.0*math.pi)
    neg = int(np.sum(evals < -zero_tol)); zero = int(np.sum(np.abs(evals) <= zero_tol)); pos = int(np.sum(evals > zero_tol))
    return {"dynamical_matrix_s_minus_2": dyn.tolist(), "eigenvalues_s_minus_2": evals.tolist(), "frequencies_hz": freqs.tolist(),
            "negative_count": neg, "zero_count": zero, "positive_count": pos, "eigenvectors_mass_weighted": evecs.tolist()}


def vineyard_prefactor(min_modes: dict[str, Any], sad_modes: dict[str, Any], zero_tol: float) -> float | None:
    me = np.asarray(min_modes["eigenvalues_s_minus_2"],dtype=float); se = np.asarray(sad_modes["eigenvalues_s_minus_2"],dtype=float)
    if np.any(me <= zero_tol) or np.sum(se < -zero_tol) != 1 or np.any(np.abs(se) <= zero_tol): return None
    mf = np.sqrt(me)/(2*math.pi); sf = np.sqrt(se[se>zero_tol])/(2*math.pi)
    return float(math.exp(float(np.sum(np.log(mf))-np.sum(np.log(sf)))))


def rel_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None: return None
    return abs(a-b)/max(abs(a),abs(b),1e-300)


def command_hessian_analyze(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); plan_path = Path(args.plan).resolve(); gate_path = Path(args.mobility_gate).resolve()
    plan = read_json(plan_path); gate = read_json(gate_path)
    require(plan, "na-cu001-hessian-plan-v0.2"); require(gate, "na-cu001-mobility-convergence-v0.2")
    case_records = [read_json(p) for p in Path(args.records).resolve().rglob("*.json")]
    case_records = [r for r in case_records if r.get("schema") == "na-cu001-hessian-case-v0.2" and r.get("status") == "PASS"]
    center_records = [read_json(p) for p in Path(args.centers).resolve().rglob("*.json")]
    centers = {r["center"]: r for r in center_records if r.get("schema") == "na-cu001-hessian-center-v0.2" and r.get("status") == "PASS"}
    if set(centers) != {"minimum","saddle"}: raise SystemExit("HOLD: Hessian center SCFs incomplete")
    zero_tol = float(protocol["hessian"]["zero_mode_eigenvalue_tolerance_s_minus_2"]); analyses: dict[str,Any] = {}; prefactors: dict[str,dict[str,float|None]] = {}
    for region, indices in plan["regions"].items():
        indices = [int(x) for x in indices]; analyses[region] = {}; prefactors[region] = {}
        for delta in (0.02,0.04):
            pair = {}
            for center in ("minimum","saddle"):
                subset = [r for r in case_records if r["region"]==region and r["center"]==center and abs(float(r["delta_angstrom"])-delta)<1e-9]
                h = assemble_hessian(subset, indices, delta); modes = mass_weighted_modes(h, plan[f"{center}_atoms"], indices, zero_tol)
                pair[center] = {"hessian_ev_per_angstrom2": h.tolist(), "modes": modes}
            pref = vineyard_prefactor(pair["minimum"]["modes"], pair["saddle"]["modes"], zero_tol)
            pair["vineyard_prefactor_hz"] = pref; analyses[region][str(delta)] = pair; prefactors[region][str(delta)] = pref
        analyses[region]["delta_prefactor_relative_difference"] = rel_diff(prefactors[region]["0.02"], prefactors[region]["0.04"])
    region_rel_02 = rel_diff(prefactors["na_plus_4cu"]["0.02"], prefactors["na_plus_8cu"]["0.02"])
    region_rel_04 = rel_diff(prefactors["na_plus_4cu"]["0.04"], prefactors["na_plus_8cu"]["0.04"])
    cancellation = {"na_only_to_na_plus_4cu_relative_change_0p02": rel_diff(prefactors["na_only"]["0.02"], prefactors["na_plus_4cu"]["0.02"]),
                    "na_plus_4cu_to_na_plus_8cu_relative_change_0p02": region_rel_02}
    largest = analyses["na_plus_8cu"]["0.02"]; se = np.asarray(largest["saddle"]["modes"]["eigenvalues_s_minus_2"]); evec = np.asarray(largest["saddle"]["modes"]["eigenvectors_mass_weighted"])
    unstable = int(np.argmin(se)); q = evec[:,unstable]; indices = [int(x) for x in plan["regions"]["na_plus_8cu"]]
    masses = np.array([MASS_AMU[plan["saddle_atoms"][i]["symbol"]]*AMU_TO_KG for i in indices for _ in range(3)])
    cart = q/np.sqrt(masses); cart = cart/np.linalg.norm(cart); displacements = {str(idx): cart[3*j:3*j+3].tolist() for j,idx in enumerate(indices)}
    ni = legacy.na_index(plan["minimum_atoms"]); na_slot = indices.index(ni); na_vec = cart[3*na_slot:3*na_slot+3]
    hop = periodic_delta(plan["endpoint_b_atoms"][ni]["position_angstrom"], plan["minimum_atoms"][ni]["position_angstrom"], plan["cell_angstrom"], include_z=False)
    alignment = abs(float(np.dot(na_vec/np.linalg.norm(na_vec), hop/np.linalg.norm(hop)))) if np.linalg.norm(na_vec)>0 and np.linalg.norm(hop)>0 else 0.0
    hspec = protocol["hessian"]; delta_tol = float(hspec["delta_relative_tolerance"]); region_tol = float(hspec["region_prefactor_relative_tolerance"])
    index_checks = {}
    for region in analyses:
        index_checks[region] = all(analyses[region][str(d)]["minimum"]["modes"]["negative_count"]==0 and analyses[region][str(d)]["minimum"]["modes"]["zero_count"]==0 and
                                   analyses[region][str(d)]["saddle"]["modes"]["negative_count"]==1 and analyses[region][str(d)]["saddle"]["modes"]["zero_count"]==0 for d in (0.02,0.04))
    checks = {"all_regions_have_correct_index": all(index_checks.values()),
              "active_delta_convergence": analyses["na_plus_8cu"]["delta_prefactor_relative_difference"] is not None and analyses["na_plus_8cu"]["delta_prefactor_relative_difference"] <= delta_tol,
              "active_region_convergence_0p02": region_rel_02 is not None and region_rel_02 <= region_tol,
              "active_region_convergence_0p04": region_rel_04 is not None and region_rel_04 <= region_tol,
              "unstable_mode_alignment": alignment >= float(hspec["unstable_mode_path_alignment_min"]),
              "saddle_max_active_force": centers["saddle"]["max_active_force_ev_per_angstrom"] is not None and centers["saddle"]["max_active_force_ev_per_angstrom"] <= float(protocol["surface"]["ci_path_force_tolerance_ev_per_angstrom"])}
    handoff = {"schema": "na-cu001-active-region-hessian-v0.2", "status": "PASS" if all(checks.values()) else "HOLD",
        "analyses": analyses, "prefactors_hz": prefactors, "cancellation_test": cancellation,
        "selected_prefactor_hz": prefactors["na_plus_8cu"]["0.02"], "selected_prefactor_region": "na_plus_8cu",
        "unstable_mode": {"eigenvalue_s_minus_2": float(se[unstable]), "active_indices": indices, "cartesian_displacements_normalized": displacements,
                          "na_component_alignment_with_hop": alignment}, "center_force_records": centers, "pass_checks": checks,
        "input_artifacts": [artifact(plan_path), artifact(gate_path)], "next_gate": "three_dimensional_downhill_connectivity"}
    write_json(Path(args.out).resolve(), handoff); print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS": raise SystemExit(2)

def basin_metrics(final_atoms: list[dict[str, Any]], endpoint_atoms: list[dict[str, Any]], active_indices: list[int], cell: list[list[float]], final_energy: float | None, endpoint_energy: float, protocol: dict[str, Any]) -> dict[str, Any]:
    ni = legacy.na_index(final_atoms); nj = legacy.na_index(endpoint_atoms)
    d3 = periodic_3d_distance(final_atoms[ni]["position_angstrom"], endpoint_atoms[nj]["position_angstrom"], cell)
    hdiff = abs(adsorption_height(final_atoms)-adsorption_height(endpoint_atoms))
    rmsd = active_rmsd(final_atoms, endpoint_atoms, active_indices, cell)
    ediff = None if final_energy is None else abs(float(final_energy)-float(endpoint_energy))
    site_final = legacy.classify_surface_site(final_atoms[ni]["position_angstrom"], cell)["site"]
    site_endpoint = legacy.classify_surface_site(endpoint_atoms[nj]["position_angstrom"], cell)["site"]
    c = protocol["connectivity"]
    checks = {"na_periodic_3d_distance": d3 <= float(c["na_periodic_3d_distance_tolerance_angstrom"]),
              "adsorption_height": hdiff <= float(c["adsorption_height_tolerance_angstrom"]),
              "active_region_rmsd": rmsd <= float(c["active_region_rmsd_tolerance_angstrom"]),
              "energy": ediff is not None and ediff <= float(c["endpoint_energy_tolerance_ev"]),
              "site": site_final == site_endpoint}
    return {"pass": all(checks.values()), "na_periodic_3d_distance_angstrom": d3, "adsorption_height_difference_angstrom": hdiff,
            "active_region_rmsd_angstrom": rmsd, "energy_difference_ev": ediff, "site_final": site_final, "site_endpoint": site_endpoint, "checks": checks}


def command_connectivity(args: argparse.Namespace) -> None:
    protocol = load_protocol(args.protocol); plan_path = Path(args.plan).resolve(); h_path = Path(args.hessian).resolve(); ep_path = Path(args.endpoints).resolve(); ci_path = Path(args.ci).resolve(); na_path = Path(args.na_handoff).resolve()
    plan = read_json(plan_path); hess = read_json(h_path); endpoints = read_json(ep_path); ci = read_json(ci_path); na = read_json(na_path)
    require(plan, "na-cu001-hessian-plan-v0.2"); require(hess, "na-cu001-active-region-hessian-v0.2"); require(endpoints, "na-cu001-endpoints-handoff-v0.2"); require(ci, "na-cu001-ci-neb-handoff-v0.2"); require(na, "na-cu001-na-pseudopotential-handoff-v0.2")
    atoms_sad = json.loads(json.dumps(ci["saddle_atoms"])); displacements = {int(k): np.asarray(v,dtype=float) for k,v in hess["unstable_mode"]["cartesian_displacements_normalized"].items()}
    max_norm = max(np.linalg.norm(v) for v in displacements.values()); scale = 0.05/max_norm
    method = endpoints["method"]; species = mixed_species(na["selected"]["installed_filename"]); root = Path(args.out_dir).resolve(); active = [int(i) for i in hess["unstable_mode"]["active_indices"]]
    results = []
    for sign in (-1,1):
        atoms0 = json.loads(json.dumps(atoms_sad))
        for idx, vec in displacements.items():
            atoms0[idx]["position_angstrom"] = (np.asarray(atoms0[idx]["position_angstrom"],dtype=float)+sign*scale*vec).tolist()
        rec = relax_record(root / f"downhill_{'p' if sign>0 else 'm'}", f"downhill_{sign:+d}".replace("+","p").replace("-","m"), endpoints["cell_angstrom"], atoms0,
                           method, species, Path(args.pseudo_dir), Path(args.pw), args.np, esm=True)
        metrics_a = basin_metrics(rec["atoms"], endpoints["endpoint_a"]["atoms"], active, endpoints["cell_angstrom"], rec["energy_ev"], endpoints["endpoint_a"]["energy_ev"], protocol)
        metrics_b = basin_metrics(rec["atoms"], endpoints["endpoint_b"]["atoms"], active, endpoints["cell_angstrom"], rec["energy_ev"], endpoints["endpoint_b"]["energy_ev"], protocol)
        basin = "A" if metrics_a["pass"] and not metrics_b["pass"] else "B" if metrics_b["pass"] and not metrics_a["pass"] else "AMBIGUOUS" if metrics_a["pass"] and metrics_b["pass"] else "NONE"
        results.append({"sign":sign,"basin":basin,"metrics_A":metrics_a,"metrics_B":metrics_b,"run":rec})
    tol_f = float(protocol["surface"]["force_tolerance_ev_per_angstrom"])
    checks = {"downhill_relaxations_converged": all(r["run"]["returncode"]==0 and r["run"]["job_done"] and r["run"]["max_unconstrained_force_ev_per_angstrom"] is not None and r["run"]["max_unconstrained_force_ev_per_angstrom"]<=tol_f for r in results),
              "distinct_unambiguous_basins": {r["basin"] for r in results}=={"A","B"},
              "no_desorption_or_wrong_height": all(r["basin"] in {"A","B"} for r in results)}
    handoff = {"schema":"na-cu001-saddle-handoff-v0.2","status":"PASS" if all(checks.values()) else "HOLD",
        "saddle_verification":"mass-weighted nested active-region Hessians plus 3D energetic and structural downhill basin return",
        "hessian":hess,"downhill_connectivity":results,"pass_checks":checks,
        "input_artifacts":[artifact(plan_path),artifact(h_path),artifact(ep_path),artifact(ci_path),artifact(na_path)],"next_gate":"barrier_sensitivity"}
    write_json(Path(args.out).resolve(),handoff);print(json.dumps(handoff,indent=2))
    if handoff["status"]!="PASS":raise SystemExit(2)


def shift_vacuum(cell: list[list[float]], atoms: list[dict[str, Any]], extra: float) -> tuple[list[list[float]],list[dict[str,Any]]]:
    new_cell=json.loads(json.dumps(cell));new_cell[2][2]=float(new_cell[2][2])+extra
    out=json.loads(json.dumps(atoms))
    for a in out:a["position_angstrom"][2]+=extra/2.0
    return new_cell,out


def command_sensitivity_case(args: argparse.Namespace) -> None:
    protocol=load_protocol(args.protocol);ep=read_json(Path(args.endpoints));ci=read_json(Path(args.ci));na=read_json(Path(args.na_handoff))
    require(ep,"na-cu001-endpoints-handoff-v0.2");require(ci,"na-cu001-ci-neb-handoff-v0.2");require(na,"na-cu001-na-pseudopotential-handoff-v0.2")
    variant=args.variant
    if variant not in {"primary","higher_cutoff","higher_rho","denser_kmesh","larger_vacuum"}:raise SystemExit("HOLD: unregistered sensitivity variant")
    method=dict(ep["method"]);cell=json.loads(json.dumps(ep["cell_angstrom"]));atoms_a=json.loads(json.dumps(ep["endpoint_a"]["atoms"]));atoms_s=json.loads(json.dumps(ci["saddle_atoms"]))
    if variant=="higher_cutoff":
        method["ecutwfc_ry"]=float(method["ecutwfc_ry"])+10.0;method["ecutrho_ry"]=max(float(method["ecutrho_ry"]),3.0*float(method["ecutwfc_ry"]))
    elif variant=="higher_rho":method["ecutrho_ry"]=float(method["ecutrho_ry"])+60.0
    elif variant=="denser_kmesh":method["kmesh"]=int(method["kmesh"])+2
    elif variant=="larger_vacuum":
        cell,atoms_a=shift_vacuum(cell,atoms_a,4.0);_,atoms_s=shift_vacuum(ep["cell_angstrom"],atoms_s,4.0)
    for atoms in (atoms_a,atoms_s):
        for a in atoms:a["flags"]=[0,0,0]
    root=Path(args.out_dir);species=mixed_species(na["selected"]["installed_filename"])
    ra=scf_record(root/"endpoint",f"sens_{variant}_endpoint",cell,atoms_a,method,species,Path(args.pseudo_dir),Path(args.pw),args.np,esm=True)
    rs=scf_record(root/"saddle",f"sens_{variant}_saddle",cell,atoms_s,method,species,Path(args.pseudo_dir),Path(args.pw),args.np,esm=True)
    barrier=None if ra["energy_ev"] is None or rs["energy_ev"] is None else float(rs["energy_ev"])-float(ra["energy_ev"])
    checks={"endpoint_scf":ra["returncode"]==0 and ra["job_done"] and ra["scf_converged"],"saddle_scf":rs["returncode"]==0 and rs["job_done"] and rs["scf_converged"],"positive_barrier":barrier is not None and barrier>0}
    record={"schema":"na-cu001-barrier-sensitivity-case-v0.2","status":"PASS" if all(checks.values()) else "HOLD","variant":variant,"method":method,
        "cell_angstrom":cell,"fixed_geometry_barrier_ev":barrier,"endpoint_run":ra,"saddle_run":rs,"pass_checks":checks}
    write_json(Path(args.out).resolve(),record);print(json.dumps(record,indent=2))
    if record["status"]!="PASS":raise SystemExit(2)


def command_sensitivity_analyze(args: argparse.Namespace) -> None:
    protocol=load_protocol(args.protocol);mob=read_json(Path(args.mobility_gate));path=read_json(Path(args.path_handoff));ci=read_json(Path(args.ci))
    require(mob,"na-cu001-mobility-convergence-v0.2");require(path,"na-cu001-path-convergence-handoff-v0.2");require(ci,"na-cu001-ci-neb-handoff-v0.2")
    records=[read_json(p) for p in Path(args.records).rglob("*.json")];records=[r for r in records if r.get("schema")=="na-cu001-barrier-sensitivity-case-v0.2"]
    by={r["variant"]:r for r in records}
    expected={"primary","higher_cutoff","higher_rho","denser_kmesh","larger_vacuum"}
    if set(by)!=expected or not all(r["status"]=="PASS" for r in by.values()):raise SystemExit("HOLD: sensitivity matrix incomplete")
    base=float(by["primary"]["fixed_geometry_barrier_ev"])
    deviations={k:abs(float(v["fixed_geometry_barrier_ev"])-base) for k,v in by.items() if k!="primary"}
    deviations["expanded_mobility_full_path"]=float(mob["barrier_difference_ev"])
    envelope=max(deviations.values())
    ordinary=[float(x) for x in path["barriers_ev"].values()];selected_ord=float(path["selected_record"]["forward_barrier_ev"])
    diagnostics={"path_image_sensitivity_ev":max(abs(x-selected_ord) for x in ordinary),"ci_refinement_shift_ev":abs(float(ci["forward_barrier_ev"])-selected_ord),
                 "endpoint_asymmetry_ev":abs(float(ci["forward_barrier_ev"])-float(ci["reverse_barrier_ev"]))}
    links=[artifact(Path(args.mobility_gate).resolve()),artifact(Path(args.path_handoff).resolve()),artifact(Path(args.ci).resolve())]
    handoff={"schema":"na-cu001-barrier-sensitivity-v0.2","status":"PASS","primary_fixed_geometry_barrier_ev":base,
        "variant_deviations_ev":deviations,"barrier_numerical_sensitivity_envelope_ev":envelope,"probability_coverage":None,
        "interpretation":protocol["sensitivity"]["envelope_rule"],"non_uncertainty_diagnostics":diagnostics,"records":by,
        "input_artifacts":links,"next_gate":"qualified_barrier_and_rate_model"}
    write_json(Path(args.out).resolve(),handoff);print(json.dumps(handoff,indent=2))


def command_barrier(args: argparse.Namespace) -> None:
    ci=read_json(Path(args.ci));saddle=read_json(Path(args.saddle));sens=read_json(Path(args.sensitivity));mob=read_json(Path(args.mobility_gate))
    require(ci,"na-cu001-ci-neb-handoff-v0.2");require(saddle,"na-cu001-saddle-handoff-v0.2");require(sens,"na-cu001-barrier-sensitivity-v0.2");require(mob,"na-cu001-mobility-convergence-v0.2")
    barrier=float(ci["forward_barrier_ev"]);reverse=float(ci["reverse_barrier_ev"]);pref=float(saddle["hessian"]["selected_prefactor_hz"])
    temps=[100.0,150.0,200.0,250.0,300.0];curve=[{"temperature_k":t,"rate_s_minus_1":pref*math.exp(-barrier/(KB_EV_K*t))} for t in temps]
    coordinate={"schema":"na-cu001-barrier-coordinate-v0.2","status":"PASS","system":"Na diffusion on Cu(001)",
        "system_role":"development_pilot_not_validation_cohort","mechanism":"nearest-neighbor hollow-to-hollow hop through bridge region","coverage_ml":0.0625,
        "electronic_forward_barrier_ev":barrier,"electronic_reverse_barrier_ev":reverse,
        "barrier_numerical_sensitivity_envelope_ev":sens["barrier_numerical_sensitivity_envelope_ev"],"probability_coverage":None,
        "sensitivity_components":sens,"attempt_frequency":{"value_hz":pref,"method":"mass-weighted Vineyard prefactor, Na plus eight Cu active region",
            "na_only_cancellation_test":saddle["hessian"]["cancellation_test"],"active_region_convergence":saddle["hessian"]["pass_checks"]},
        "computed_rate_curve":{"independence_unit_id":"Na_Cu001_hollow_hop_0p0625ML","eligible_as_independent_rows":False,"points":curve,
            "model":"harmonic transition-state model using the qualified electronic barrier and active-region prefactor"},
        "tiers":{"barrier_tier":"CI_NEB_NUMERICAL_SENSITIVITY_TESTED","saddle_tier":"MASS_WEIGHTED_ACTIVE_REGION_INDEX_ONE_AND_3D_CONNECTIVITY",
            "prefactor_tier":"NA_PLUS_8CU_ACTIVE_REGION_CONVERGED","rate_tier":"HARMONIC_MODEL_RATE_ACTIVE_REGION_PREFACTOR","experimental_tier":"NONE"},
        "zero_point_correction_ev":None,"thermal_free_energy_correction_ev":None,"friction_or_linewidth":None,
        "turnover_status":"NOT_TESTED_NO_INDEPENDENT_FRICTION_SERIES",
        "input_artifacts":[artifact(Path(args.ci).resolve()),artifact(Path(args.saddle).resolve()),artifact(Path(args.sensitivity).resolve()),artifact(Path(args.mobility_gate).resolve())],
        "next_gate":"computational_atlas_admission"}
    write_json(Path(args.out).resolve(),coordinate);print(json.dumps(coordinate,indent=2))


def command_atlas(args: argparse.Namespace) -> None:
    barrier=read_json(Path(args.barrier));evidence=read_json(Path(args.public_evidence));require(barrier,"na-cu001-barrier-coordinate-v0.2")
    record={"schema":"na-cu001-atlas-admission-v0.2","status":"PASS","admission_scope":"Barrier-Rate Atlas surface computational extension",
        "mechanism_record":{"mechanism_id":"Na_Cu001_hollow_hop_0p0625ML","independence_unit_id":"Na_Cu001_hollow_hop_0p0625ML",
            "system_role":barrier["system_role"],"phase":"surface","coverage_ml":barrier["coverage_ml"],"barrier_ev":barrier["electronic_forward_barrier_ev"],
            "barrier_sensitivity_envelope_ev":barrier["barrier_numerical_sensitivity_envelope_ev"],"attempt_frequency_hz":barrier["attempt_frequency"]["value_hz"],
            "temperature_rate_curve":barrier["computed_rate_curve"],"tiers":barrier["tiers"],"eligible_for_independent_regression_count":1},
        "public_evidence_candidates":evidence,"experimental_admission_status":"HOLD_PENDING_EXACT_STATE_POINT_TABLE",
        "non_blending_rule":"Experimental and computational quantities remain separate; derived temperatures are not independent replications.",
        "turnover_status":barrier["turnover_status"],"input_artifacts":[artifact(Path(args.barrier).resolve()),artifact(Path(args.public_evidence).resolve())],"next_gate":"integration_readiness"}
    write_json(Path(args.out).resolve(),record);print(json.dumps(record,indent=2))


def command_manifest(args: argparse.Namespace) -> None:
    root=Path(args.root).resolve();rows=[]
    for p in sorted(x for x in root.rglob("*") if x.is_file() and x.name!=Path(args.out).name):rows.append({"path":str(p.relative_to(root)),"sha256":sha256(p),"size_bytes":p.stat().st_size})
    write_json(Path(args.out).resolve(),{"schema":"na-cu001-computational-manifest-v0.2","status":"PASS","files":rows})

def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    def proto(cmd):cmd.add_argument("--protocol",required=True);return cmd
    c=sub.add_parser("slab-handoff");c.add_argument("--slab-result",required=True);c.add_argument("--bulk-handoff",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_slab_handoff)
    c=proto(sub.add_parser("parity"));c.add_argument("--slab-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_parity)
    c=proto(sub.add_parser("clean"));c.add_argument("--slab-handoff",required=True);c.add_argument("--parity-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_clean)
    c=proto(sub.add_parser("resolve-na"));c.add_argument("--probe",required=True);c.add_argument("--bulk-handoff",required=True);c.add_argument("--pseudo-root",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--pw",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=1);c.set_defaults(func=command_resolve_na)
    c=proto(sub.add_parser("adsorption-run"));c.add_argument("--mobility",choices=["primary","expanded"],required=True);c.add_argument("--site",required=True);c.add_argument("--height",type=float,required=True);c.add_argument("--clean-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--parity-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_adsorption_run)
    c=proto(sub.add_parser("adsorption-analyze"));c.add_argument("--records",required=True);c.add_argument("--clean-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--parity-handoff",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_adsorption_analyze)
    c=proto(sub.add_parser("endpoints"));c.add_argument("--mobility",choices=["primary","expanded"],required=True);c.add_argument("--adsorption-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_endpoints)
    c=proto(sub.add_parser("neb-run"));c.add_argument("--images",type=int,required=True);c.add_argument("--endpoints-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--neb",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_neb_run)
    c=proto(sub.add_parser("neb-analyze"));c.add_argument("--mobility",choices=["primary","expanded"],required=True);c.add_argument("--records",required=True);c.add_argument("--endpoints-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_neb_analyze)
    c=proto(sub.add_parser("ci"));c.add_argument("--path-handoff",required=True);c.add_argument("--endpoints-handoff",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--neb",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_ci)
    c=proto(sub.add_parser("mobility-gate"));c.add_argument("--primary-ci",required=True);c.add_argument("--expanded-ci",required=True);c.add_argument("--primary-endpoints",required=True);c.add_argument("--expanded-endpoints",required=True);c.add_argument("--primary-path",required=True);c.add_argument("--expanded-path",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_mobility_gate)
    c=proto(sub.add_parser("hessian-plan"));c.add_argument("--mobility-gate",required=True);c.add_argument("--primary-endpoints",required=True);c.add_argument("--expanded-endpoints",required=True);c.add_argument("--primary-ci",required=True);c.add_argument("--expanded-ci",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_hessian_plan)
    c=proto(sub.add_parser("hessian-center"));c.add_argument("--center",choices=["minimum","saddle"],required=True);c.add_argument("--plan",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--kmesh",type=int,required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_hessian_center)
    c=proto(sub.add_parser("hessian-case"));c.add_argument("--center",choices=["minimum","saddle"],required=True);c.add_argument("--region",choices=["na_only","na_plus_4cu","na_plus_8cu"],required=True);c.add_argument("--delta",type=float,required=True);c.add_argument("--slot",type=int,required=True);c.add_argument("--plan",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--kmesh",type=int,required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_hessian_case)
    c=proto(sub.add_parser("hessian-analyze"));c.add_argument("--plan",required=True);c.add_argument("--mobility-gate",required=True);c.add_argument("--records",required=True);c.add_argument("--centers",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_hessian_analyze)
    c=proto(sub.add_parser("connectivity"));c.add_argument("--plan",required=True);c.add_argument("--hessian",required=True);c.add_argument("--endpoints",required=True);c.add_argument("--ci",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_connectivity)
    c=proto(sub.add_parser("sensitivity-case"));c.add_argument("--variant",required=True);c.add_argument("--endpoints",required=True);c.add_argument("--ci",required=True);c.add_argument("--na-handoff",required=True);c.add_argument("--pw",required=True);c.add_argument("--pseudo-dir",required=True);c.add_argument("--out-dir",required=True);c.add_argument("--out",required=True);c.add_argument("--np",type=int,default=2);c.set_defaults(func=command_sensitivity_case)
    c=proto(sub.add_parser("sensitivity-analyze"));c.add_argument("--records",required=True);c.add_argument("--mobility-gate",required=True);c.add_argument("--path-handoff",required=True);c.add_argument("--ci",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_sensitivity_analyze)
    c=sub.add_parser("barrier");c.add_argument("--ci",required=True);c.add_argument("--saddle",required=True);c.add_argument("--sensitivity",required=True);c.add_argument("--mobility-gate",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_barrier)
    c=sub.add_parser("atlas");c.add_argument("--barrier",required=True);c.add_argument("--public-evidence",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_atlas)
    c=sub.add_parser("manifest");c.add_argument("--root",required=True);c.add_argument("--out",required=True);c.set_defaults(func=command_manifest)
    return p


def main()->None:
    args=build_parser().parse_args();args.func(args)

if __name__=="__main__":main()
