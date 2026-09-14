#!/usr/bin/env python3
"""Fail-closed Na/Cu(001) electrostatic consistency audit.

This stage is bound to the definitive C7 clean-slab audit. It preserves the
registered ESM bc1 route and explicit Cartesian z=0 slab geometry. The gate is
ESM next-vacuum stability at the selected 11-layer, 12 A, 16x16x1 setting.
A periodic calculation at the selected vacuum is diagnostic only and cannot
select or retune the ESM route.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any

RY_TO_EV = 13.605693122994
CU_MASS_AMU = 63.546
CU_PSEUDO = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")


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


def centered_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[tuple[float, float, float]], float]:
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    midpoint = (layers - 1) / 2.0
    h = a0 / 2.0
    atoms: list[tuple[float, float, float]] = []
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        x = shift * h + shift * (-h)
        y = shift * h + shift * h
        z = (layer - midpoint) * dz
        atoms.append((x, y, z))
    return atoms, cell_z


def geometry_audit(a0: float, layers: int, vacuum: float) -> dict[str, Any]:
    atoms, cell_z = centered_geometry(a0, layers, vacuum)
    z = [row[2] for row in atoms]
    return {
        "schema": "na-cu001-esm-centered-slab-v0.2",
        "atomic_position_card": "angstrom",
        "coordinate_origin": "cartesian_z_zero",
        "slab_center_z_angstrom": 0.0,
        "cell_boundaries_z_angstrom": [-cell_z / 2.0, cell_z / 2.0],
        "atomic_z_min_angstrom": min(z),
        "atomic_z_max_angstrom": max(z),
        "atomic_z_mean_angstrom": sum(z) / len(z),
        "vacuum_total_angstrom": vacuum,
        "vacuum_each_side_angstrom": vacuum / 2.0,
        "symmetric_about_zero": abs(min(z) + max(z)) <= 1e-12 and abs(sum(z) / len(z)) <= 1e-12,
    }


def qe_input(
    *,
    a0: float,
    layers: int,
    vacuum: float,
    kmesh: int,
    ecutwfc: float,
    ecutrho: float,
    pseudo_dir: Path,
    outdir: Path,
    tag: str,
    esm: bool,
) -> str:
    atoms, cell_z = centered_geometry(a0, layers, vacuum)
    h = a0 / 2.0
    lines = [
        "&CONTROL",
        "  calculation = 'scf',",
        f"  prefix = '{tag}',",
        f"  pseudo_dir = '{pseudo_dir}',",
        f"  outdir = '{outdir}',",
        "  tprnfor = .true.,",
        "  tstress = .true.,",
        "  verbosity = 'high',",
        "/",
        "&SYSTEM",
        "  ibrav = 0,",
        f"  nat = {layers},",
        "  ntyp = 1,",
        f"  ecutwfc = {ecutwfc:.8f},",
        f"  ecutrho = {ecutrho:.8f},",
        "  occupations = 'smearing',",
        "  smearing = 'mv',",
        "  degauss = 0.02,",
        "  nosym = .true.,",
    ]
    if esm:
        lines.extend(["  assume_isolated = 'esm',", "  esm_bc = 'bc1',"])
    lines.extend([
        "/",
        "&ELECTRONS",
        "  conv_thr = 1.0d-10,",
        "  mixing_beta = 0.3,",
        "  electron_maxstep = 250,",
        "/",
        "ATOMIC_SPECIES",
        f"Cu {CU_MASS_AMU:.8f} {CU_PSEUDO}",
        "CELL_PARAMETERS angstrom",
        f" {h:.12f} {h:.12f} 0.0",
        f" {-h:.12f} {h:.12f} 0.0",
        f" 0.0 0.0 {cell_z:.12f}",
        "ATOMIC_POSITIONS angstrom",
    ])
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in atoms)
    lines.extend(["K_POINTS automatic", f"{kmesh} {kmesh} 1 0 0 0"])
    return "\n".join(lines) + "\n"


def parse_energy(text: str) -> float | None:
    values = [float(value) for value in ENERGY_RE.findall(text)]
    return values[-1] * RY_TO_EV if values else None


def run_case(
    *,
    root: Path,
    tag: str,
    pw: Path,
    pseudo_dir: Path,
    np_count: int,
    a0: float,
    layers: int,
    vacuum: float,
    kmesh: int,
    ecutwfc: float,
    ecutrho: float,
    bulk_energy_ev_per_atom: float,
    esm: bool,
) -> dict[str, Any]:
    case = root / tag
    case.mkdir(parents=True, exist_ok=True)
    tmp = (case / "tmp").resolve()
    tmp.mkdir(exist_ok=True)
    inp = case / f"{tag}.in"
    out = case / f"{tag}.out"
    inp.write_text(qe_input(
        a0=a0,
        layers=layers,
        vacuum=vacuum,
        kmesh=kmesh,
        ecutwfc=ecutwfc,
        ecutrho=ecutrho,
        pseudo_dir=pseudo_dir.resolve(),
        outdir=tmp,
        tag=tag,
        esm=esm,
    ))
    cmd = [str(pw.resolve())]
    if np_count > 1:
        cmd = ["mpirun", "-np", str(np_count)] + cmd
    start = time.time()
    with inp.open("rb") as stdin, out.open("wb") as stdout:
        proc = subprocess.run(cmd, cwd=case, stdin=stdin, stdout=stdout, stderr=subprocess.STDOUT)
    elapsed = time.time() - start
    text = out.read_text(errors="replace")
    energy = parse_energy(text)
    complete = proc.returncode == 0 and "JOB DONE." in text and "convergence has been achieved" in text.lower() and energy is not None
    geom = geometry_audit(a0, layers, vacuum)
    record = {
        "schema": "na-cu001-electrostatic-consistency-case-v0.1",
        "tag": tag,
        "returncode": proc.returncode,
        "job_done": "JOB DONE." in text,
        "scf_converged": "convergence has been achieved" in text.lower(),
        "complete": complete,
        "energy_ev": energy,
        "surface_excess_ev_per_surface_atom": None if energy is None else (energy - layers * bulk_energy_ev_per_atom) / 2.0,
        "elapsed_s": elapsed,
        "layers": layers,
        "vacuum_angstrom": vacuum,
        "kmesh_inplane": kmesh,
        "ecutwfc_ry": ecutwfc,
        "ecutrho_ry": ecutrho,
        "electrostatic_convention": {"assume_isolated": "esm", "esm_bc": "bc1"} if esm else {"assume_isolated": None, "esm_bc": None, "role": "periodic_diagnostic_only"},
        "geometry_convention": geom,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out),
    }
    write_json(case / "run_record.json", record)
    shutil.rmtree(tmp, ignore_errors=True)
    return record


def verify_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    slab = read_json(Path(args.slab_handoff).resolve())
    audit = read_json(Path(args.audit_record).resolve())
    protocol = read_json(Path(args.protocol).resolve())
    if slab.get("schema") != "na-cu001-clean-slab-to-relaxation-handoff-v0.3" or slab.get("status") != "PASS":
        raise SystemExit("HOLD: definitive slab handoff is not PASS")
    if slab.get("next_gate") != "electrostatic_parity":
        raise SystemExit("HOLD: definitive slab handoff does not authorize electrostatic consistency")
    if audit.get("schema") != "na-cu001-c7-definitive-l13-independent-audit-v0.1" or audit.get("status") != "PASS":
        raise SystemExit("HOLD: definitive independent audit record is not PASS")
    if audit.get("scientific_settings_changed") is not False:
        raise SystemExit("HOLD: definitive audit reports changed scientific settings")
    if protocol.get("schema") != "na-cu001-method-protocol-v0.2" or protocol.get("status") != "FROZEN_BEFORE_DOWNSTREAM_RESULTS":
        raise SystemExit("HOLD: method protocol is not the frozen v0.2 protocol")
    s = slab.get("selected_slab_settings") or {}
    if [int(s.get("layers", -1)), float(s.get("vacuum_angstrom", -1)), int(s.get("kmesh_inplane", -1))] != [11, 12.0, 16]:
        raise SystemExit("HOLD: definitive selected slab is not the bound 11-layer, 12 A, k=16 setting")
    electro = s.get("electrostatic_convention") or {}
    coord = s.get("coordinate_convention") or {}
    if electro.get("assume_isolated") != "esm" or electro.get("esm_bc") != "bc1":
        raise SystemExit("HOLD: definitive handoff is not ESM bc1")
    if coord.get("atomic_position_card") != "angstrom" or coord.get("origin") != "cartesian_z_zero":
        raise SystemExit("HOLD: definitive handoff is not explicit Cartesian z=0")
    tolerance = float(protocol.get("surface", {}).get("esm_vacuum_stability_tolerance_mev_per_surface_atom", -1))
    handoff_tolerance = float(slab.get("convergence_rule", {}).get("surface_excess_tolerance_mev_per_surface_atom", -2))
    if tolerance != 1.0 or handoff_tolerance != 1.0:
        raise SystemExit("HOLD: electrostatic tolerance is not the frozen 1.0 meV per surface atom")
    expected_pseudo = str(protocol.get("immutable_sources", {}).get("cu_upf_sha256") or "")
    pseudo = Path(args.pseudo_dir).resolve() / CU_PSEUDO
    if not pseudo.is_file() or sha256(pseudo) != expected_pseudo:
        raise SystemExit("HOLD: Cu pseudopotential identity mismatch")
    pw = Path(args.pw).resolve()
    if not pw.is_file():
        raise SystemExit("HOLD: pw.x is missing")
    provenance = {
        "source_c7_run_id": int(args.source_run_id),
        "source_c7_commit": args.source_commit,
        "definitive_audit_run_id": int(args.audit_run_id),
        "definitive_audit_commit": args.audit_commit,
        "control_commit": args.control_commit,
        "scientific_settings_changed": False,
    }
    return slab, audit, protocol, provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slab-handoff", required=True)
    parser.add_argument("--audit-record", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--pw", required=True)
    parser.add_argument("--pseudo-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--np", type=int, default=2)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--audit-run-id", required=True)
    parser.add_argument("--audit-commit", required=True)
    parser.add_argument("--control-commit", required=True)
    args = parser.parse_args()

    slab, audit, protocol, provenance = verify_inputs(args)
    s = slab["selected_slab_settings"]
    a0 = float(s["a0_angstrom"])
    layers = int(s["layers"])
    selected_vacuum = float(s["vacuum_angstrom"])
    comparison_vacuum = 16.0
    kmesh = int(s["kmesh_inplane"])
    ecutwfc = float(s["ecutwfc_ry"])
    ecutrho = float(s["ecutrho_ry"])
    bulk_energy = float(s["bulk_energy_ev_per_atom"])
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    cases = [
        ("esm_selected", selected_vacuum, True),
        ("esm_next_vacuum", comparison_vacuum, True),
        ("periodic_diagnostic", selected_vacuum, False),
    ]
    records: list[dict[str, Any]] = []
    for tag, vacuum, esm in cases:
        records.append(run_case(
            root=root,
            tag=tag,
            pw=Path(args.pw),
            pseudo_dir=Path(args.pseudo_dir),
            np_count=args.np,
            a0=a0,
            layers=layers,
            vacuum=vacuum,
            kmesh=kmesh,
            ecutwfc=ecutwfc,
            ecutrho=ecutrho,
            bulk_energy_ev_per_atom=bulk_energy,
            esm=esm,
        ))

    by = {row["tag"]: row for row in records}
    complete = {tag: bool(by[tag]["complete"]) for tag, _, _ in cases}
    tol_mev = float(protocol["surface"]["esm_vacuum_stability_tolerance_mev_per_surface_atom"])
    tol_ev = tol_mev / 1000.0
    if complete["esm_selected"] and complete["esm_next_vacuum"]:
        esm_delta = abs(float(by["esm_selected"]["surface_excess_ev_per_surface_atom"]) - float(by["esm_next_vacuum"]["surface_excess_ev_per_surface_atom"]))
    else:
        esm_delta = None
    if complete["esm_selected"] and complete["periodic_diagnostic"]:
        boundary_delta = abs(float(by["esm_selected"]["surface_excess_ev_per_surface_atom"]) - float(by["periodic_diagnostic"]["surface_excess_ev_per_surface_atom"]))
    else:
        boundary_delta = None
    checks = {
        "definitive_audit_pass": audit.get("status") == "PASS",
        "frozen_selected_setting_11L_12A_K16": True,
        "explicit_cartesian_z_zero_preserved": all(bool(row["geometry_convention"]["symmetric_about_zero"]) for row in records),
        "selected_esm_scf_completed": complete["esm_selected"],
        "next_vacuum_esm_scf_completed": complete["esm_next_vacuum"],
        "periodic_diagnostic_completed": complete["periodic_diagnostic"],
        "esm_next_vacuum_change_le_1mev_per_surface_atom": esm_delta is not None and esm_delta <= tol_ev,
        "periodic_diagnostic_nonselecting": True,
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    payload = {
        "schema": "na-cu001-electrostatic-consistency-v0.3",
        "status": status,
        "system": "clean Cu(001)",
        "selected_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
        "coordinate_convention": {"atomic_position_card": "angstrom", "origin": "cartesian_z_zero"},
        "selected_slab": {"layers": layers, "vacuum_angstrom": selected_vacuum, "kmesh_inplane": kmesh},
        "comparison_vacuum_angstrom": comparison_vacuum,
        "tolerance_mev_per_surface_atom": tol_mev,
        "tolerance_ev_per_surface_atom": tol_ev,
        "esm_vacuum_delta_ev_per_surface_atom": esm_delta,
        "periodic_vs_esm_diagnostic_ev_per_surface_atom": boundary_delta,
        "periodic_diagnostic_role": "reported only; cannot select, reject, or retune the registered ESM bc1 route",
        "records": records,
        "pass_checks": checks,
        "provenance": provenance,
        "input_artifacts": {
            "slab_handoff_sha256": sha256(Path(args.slab_handoff).resolve()),
            "audit_record_sha256": sha256(Path(args.audit_record).resolve()),
            "protocol_sha256": sha256(Path(args.protocol).resolve()),
            "pw_x_sha256": sha256(Path(args.pw).resolve()),
            "cu_pseudo_sha256": sha256(Path(args.pseudo_dir).resolve() / CU_PSEUDO),
        },
        "next_gate": "clean_surface_relaxation",
    }
    write_json(Path(args.out).resolve(), payload)
    print(json.dumps(payload, indent=2))
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
