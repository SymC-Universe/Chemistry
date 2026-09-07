#!/usr/bin/env python3
"""Prospective PBE clean-Cu(111) and CO site-ordering gate.

This runner consumes the already executed PBE Stage A PASS result and evaluates
only clean-surface numerical stability and non-kinetic adsorption-site ordering.
It contains no diffusion barrier, hopping rate, kinetic prefactor, friction fit,
or ChemSA target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
FORCE_RE = re.compile(
    r"atom\s+\d+\s+type\s+\d+\s+force\s*=\s*"
    r"([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"HOLD: JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def close(a: float, b: float, tol: float = 1e-10) -> bool:
    return abs(float(a) - float(b)) <= tol


def verify_protocol(protocol: dict[str, Any]) -> None:
    if protocol.get("schema") != "co-cu111-pbe-surface-site-ordering-protocol-v0.1":
        raise SystemExit("HOLD: wrong surface/site protocol schema")
    if protocol.get("status") != "FROZEN_BEFORE_PBE_SURFACE_RESULTS":
        raise SystemExit("HOLD: surface/site protocol is not frozen")
    if protocol.get("provenance", {}).get("kinetic_inputs_used") is not False:
        raise SystemExit("HOLD: protocol kinetic-input provenance is not false")


def verify_stage_a(protocol: dict[str, Any], result_path: Path) -> dict[str, Any]:
    expected = protocol["authorizing_stage_a_result"]
    if sha256(result_path) != expected["result_sha256"]:
        raise SystemExit("HOLD: authorizing Stage A result hash mismatch")
    result = load_json(result_path)
    if result.get("schema") != "co-cu111-pbe-stage-a-numerical-extension-result-v0.1":
        raise SystemExit("HOLD: wrong Stage A result schema")
    if result.get("status") != expected["required_status"]:
        raise SystemExit("HOLD: Stage A result is not PASS")
    if result.get("next_gate") != expected["required_next_gate"]:
        raise SystemExit("HOLD: Stage A result does not authorize this gate")
    if result.get("provenance", {}).get("kinetic_inputs_used") is not False:
        raise SystemExit("HOLD: Stage A result kinetic-input provenance mismatch")
    selected = result.get("combined_selected_settings") or {}
    inherited = protocol["inherited_stage_a_settings"]
    checks = {
        "ecutwfc_ry": inherited["ecutwfc_ry"],
        "ecutrho_ry": inherited["ecutrho_ry"],
        "bulk_kmesh": inherited["bulk_kmesh"],
        "gas_box_angstrom": inherited["isolated_co_reference_box_angstrom"],
    }
    for key, value in checks.items():
        got = selected.get(key)
        if isinstance(value, float):
            if got is None or not close(float(got), float(value), 1e-12):
                raise SystemExit(f"HOLD: Stage A selected setting mismatch: {key}")
        elif got != value:
            raise SystemExit(f"HOLD: Stage A selected setting mismatch: {key}")
    bulk_selected = result.get("bulk_extension_gate", {}).get("selected", {})
    if not close(bulk_selected.get("fit", {}).get("a0_angstrom", float("nan")), inherited["bulk_lattice_constant_angstrom"], 1e-12):
        raise SystemExit("HOLD: frozen Stage A a0 mismatch")
    if not close(bulk_selected.get("fit", {}).get("e0_ev_per_atom", float("nan")), inherited["bulk_e0_ev_per_atom"], 1e-9):
        raise SystemExit("HOLD: frozen Stage A E0 mismatch")
    return result


def verify_bundle(protocol: dict[str, Any], bundle_path: Path, pseudo_dir: Path, pw: Path) -> dict[str, Any]:
    bundle = load_json(bundle_path)
    if bundle.get("schema") != "co-cu111-pbe-pseudopotential-bundle-v0.1" or bundle.get("status") != "PINNED_FOR_NON_KINETIC_METHOD_SCREEN":
        raise SystemExit("HOLD: wrong/unpinned PBE bundle")
    if sha256(pw) != bundle["solver_bundle"]["pw_x_sha256"]:
        raise SystemExit("HOLD: pw.x hash mismatch")
    for symbol in ("Cu", "C", "O"):
        row = bundle["pseudopotentials"][symbol]
        path = pseudo_dir / row["filename"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            raise SystemExit(f"HOLD: pseudopotential mismatch for {symbol}")
    return bundle


def frac_to_cart(u: float, v: float, a1: list[float], a2: list[float]) -> tuple[float, float]:
    return (u * a1[0] + v * a2[0], u * a1[1] + v * a2[1])


def layer_shift(layer: int) -> tuple[float, float]:
    value = (layer % 3) / 3.0
    return value, value


def clean_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[list[float]], list[dict[str, Any]]]:
    if layers < 5 or layers % 2 == 0:
        raise ValueError("clean Cu(111) slab requires odd layers >=5")
    axy = a0 / math.sqrt(2.0)
    d111 = a0 / math.sqrt(3.0)
    slab_height = (layers - 1) * d111
    cell_z = slab_height + vacuum
    a1 = [axy, 0.0, 0.0]
    a2 = [0.5 * axy, math.sqrt(3.0) * 0.5 * axy, 0.0]
    cell = [a1, a2, [0.0, 0.0, cell_z]]
    midpoint = (layers - 1) / 2.0
    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        u, v = layer_shift(layer)
        x, y = frac_to_cart(u, v, a1, a2)
        z = (layer - midpoint) * d111
        movable = layer < 2 or layer >= layers - 2
        atoms.append({"symbol": "Cu", "position_angstrom": [x, y, z], "flags": [0, 0, 1 if movable else 0], "layer": layer})
    return cell, atoms


def site_offsets(layers: int) -> dict[str, tuple[float, float]]:
    top = layer_shift(layers - 1)
    second = layer_shift(layers - 2)
    third = layer_shift(layers - 3)
    h1 = ((top[0] + 1.0 / 3.0) % 1.0, (top[1] + 1.0 / 3.0) % 1.0)
    h2 = ((top[0] + 2.0 / 3.0) % 1.0, (top[1] + 2.0 / 3.0) % 1.0)

    def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
        du = min(abs(a[0] - b[0]), 1.0 - abs(a[0] - b[0]))
        dv = min(abs(a[1] - b[1]), 1.0 - abs(a[1] - b[1]))
        return du + dv

    hcp = h1 if dist(h1, second) < dist(h2, second) else h2
    fcc = h1 if dist(h1, third) < dist(h2, third) else h2
    if hcp == fcc:
        raise ValueError("failed to distinguish fcc and hcp hollows")
    return {
        "top": top,
        "bridge": ((top[0] + 0.5) % 1.0, top[1]),
        "fcc_hollow": fcc,
        "hcp_hollow": hcp,
    }


def adsorption_geometry(clean_summary: dict[str, Any], site: str, protocol: dict[str, Any]) -> tuple[list[list[float]], list[dict[str, Any]]]:
    layers = int(clean_summary["layers"])
    layer_z = [float(x) for x in clean_summary["layer_z_angstrom"]]
    if len(layer_z) != layers:
        raise SystemExit("HOLD: selected clean summary layer-z count mismatch")
    a0 = float(protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"])
    axy = a0 / math.sqrt(2.0)
    a1 = [4.0 * axy, 0.0, 0.0]
    a2 = [2.0 * axy, 2.0 * math.sqrt(3.0) * axy, 0.0]
    selected_vacuum = float(clean_summary["vacuum_angstrom"])
    minimum_vacuum = float(protocol["adsorption_site_ordering"]["minimum_vacuum_angstrom"])
    adsorption_vacuum = max(selected_vacuum, minimum_vacuum)
    cell_z = float(clean_summary["cell_angstrom"][2][2]) + (adsorption_vacuum - selected_vacuum)
    cell = [a1, a2, [0.0, 0.0, cell_z]]
    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        su, sv = layer_shift(layer)
        for i in range(4):
            for j in range(4):
                u = (i + su) / 4.0
                v = (j + sv) / 4.0
                x, y = frac_to_cart(u, v, a1, a2)
                movable = layer >= layers - int(protocol["adsorption_site_ordering"]["site_identity_constraints"]["Cu_top_layers_movable"])
                atoms.append({"symbol": "Cu", "position_angstrom": [x, y, layer_z[layer]], "flags": [0, 0, 1 if movable else 0], "layer": layer})
    offsets = site_offsets(layers)
    if site not in offsets:
        raise SystemExit(f"HOLD: unknown site {site}")
    su, sv = offsets[site]
    u = (2.0 + su) / 4.0
    v = (2.0 + sv) / 4.0
    x, y = frac_to_cart(u, v, a1, a2)
    top_z = max(layer_z)
    c_z = top_z + float(protocol["adsorption_site_ordering"]["initial_carbon_height_above_top_Cu_plane_angstrom"])
    o_z = c_z + float(protocol["adsorption_site_ordering"]["initial_co_bond_angstrom"])
    half_z = cell_z / 2.0
    if o_z >= half_z - 2.0:
        raise SystemExit("HOLD: adsorbate is too close to the ESM cell boundary")
    atoms.append({"symbol": "C", "position_angstrom": [x, y, c_z], "flags": [0, 0, 1], "layer": None})
    atoms.append({"symbol": "O", "position_angstrom": [x, y, o_z], "flags": [0, 0, 1], "layer": None})
    return cell, atoms


def species_lines(bundle: dict[str, Any], symbols: list[str]) -> list[str]:
    masses = {"Cu": 63.546, "C": 12.000000, "O": 15.999000}
    return [f"{s} {masses[s]:.6f} {bundle['pseudopotentials'][s]['filename']}" for s in symbols]


def qe_input(
    *,
    calculation: str,
    prefix: str,
    cell: list[list[float]],
    atoms: list[dict[str, Any]],
    kmesh: int,
    protocol: dict[str, Any],
    bundle: dict[str, Any],
    pseudo_dir: Path,
    outdir: Path,
) -> str:
    inherited = protocol["inherited_stage_a_settings"]
    symbols = [s for s in ("Cu", "C", "O") if any(a["symbol"] == s for a in atoms)]
    lines = [
        "&CONTROL",
        f" calculation='{calculation}',",
        f" prefix='{prefix}',",
        f" pseudo_dir='{pseudo_dir}',",
        f" outdir='{outdir}',",
        " tprnfor=.true.,",
        " tstress=.true.,",
        " verbosity='high',",
    ]
    if calculation == "relax":
        forc_ry_bohr = float(protocol["clean_surface"]["relaxation"]["force_gate_ev_per_angstrom"]) / RY_BOHR_TO_EV_ANG
        lines += [f" forc_conv_thr={forc_ry_bohr:.12g},"]
    lines += [
        "/",
        "&SYSTEM",
        " ibrav=0,",
        f" nat={len(atoms)},",
        f" ntyp={len(symbols)},",
        f" ecutwfc={int(inherited['ecutwfc_ry'])},",
        f" ecutrho={int(inherited['ecutrho_ry'])},",
        " input_dft='PBE',",
        " occupations='smearing',",
        " smearing='mv',",
        f" degauss={float(inherited['degauss_ry'])},",
        " assume_isolated='esm',",
        " esm_bc='bc1',",
        "/",
        "&ELECTRONS",
        f" conv_thr={float(inherited['electron_conv_thr']):.12g},",
        f" mixing_beta={float(inherited['mixing_beta'])},",
        f" electron_maxstep={int(inherited['electron_maxstep'])},",
        "/",
    ]
    if calculation == "relax":
        lines += ["&IONS", " ion_dynamics='bfgs',", "/"]
    lines += ["ATOMIC_SPECIES"] + species_lines(bundle, symbols)
    lines += ["CELL_PARAMETERS angstrom"]
    lines += [" ".join(f"{x:.12f}" for x in row) for row in cell]
    lines += ["ATOMIC_POSITIONS angstrom"]
    for atom in atoms:
        p = atom["position_angstrom"]
        f = atom.get("flags", [0, 0, 0])
        lines.append(f"{atom['symbol']} {p[0]:.12f} {p[1]:.12f} {p[2]:.12f} {int(f[0])} {int(f[1])} {int(f[2])}")
    lines += ["K_POINTS automatic", f"{kmesh} {kmesh} 1 0 0 0"]
    return "\n".join(lines) + "\n"


def parse_positions(text: str, nat: int, template: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    lines = text.splitlines()
    blocks: list[list[dict[str, Any]]] = []
    for i, line in enumerate(lines):
        if not line.strip().upper().startswith("ATOMIC_POSITIONS") or "angstrom" not in line.lower():
            continue
        rows: list[dict[str, Any]] = []
        for j in range(i + 1, min(i + 1 + nat, len(lines))):
            parts = lines[j].split()
            if len(parts) < 4 or parts[0] not in {"Cu", "C", "O"}:
                rows = []
                break
            try:
                xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
            except ValueError:
                rows = []
                break
            idx = len(rows)
            row = dict(template[idx]) if idx < len(template) else {"symbol": parts[0]}
            row["symbol"] = parts[0]
            row["position_angstrom"] = xyz
            rows.append(row)
        if len(rows) == nat:
            blocks.append(rows)
    return blocks[-1] if blocks else None


def parse_forces(text: str, nat: int) -> list[tuple[float, float, float]] | None:
    vals = [(float(a), float(b), float(c)) for a, b, c in FORCE_RE.findall(text)]
    if len(vals) < nat:
        return None
    return vals[-nat:]


def max_movable_force_ev_a(forces: list[tuple[float, float, float]] | None, atoms: list[dict[str, Any]]) -> float | None:
    if forces is None or len(forces) != len(atoms):
        return None
    maxima: list[float] = []
    for force, atom in zip(forces, atoms):
        flags = atom.get("flags", [0, 0, 0])
        movable = [force[i] for i in range(3) if int(flags[i]) == 1]
        if movable:
            maxima.append(math.sqrt(sum(x * x for x in movable)) * RY_BOHR_TO_EV_ANG)
    return max(maxima) if maxima else 0.0


def run_pw(pw: Path, inp: Path, out: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    start = time.time()
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.run([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
    text = out.read_text(errors="replace")
    energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(text)]
    return {
        "returncode": proc.returncode,
        "elapsed_s": time.time() - start,
        "job_done": "JOB DONE." in text,
        "scf_converged": "convergence has been achieved" in text.lower() or "end of self-consistent calculation" in text.lower(),
        "energy_ev": energies[-1] if energies else None,
        "text": text,
    }


def cleanup_tmp(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def stage_manifest(root: Path, extra: list[Path]) -> None:
    paths = sorted(root.rglob("*.in")) + sorted(root.rglob("*.out")) + extra
    lines = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        lines.append(f"{sha256(path)}  {path.relative_to(root)}")
    (root / "STAGE_TIME_MANIFEST.sha256").write_text("\n".join(lines) + "\n")


def clean_case_id(layers: int, vacuum: float, kmesh: int, role: str) -> str:
    return f"L{layers}-V{int(round(vacuum))}-K{kmesh}-{role}"


def command_clean_run(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve()
    stage_path = Path(args.stage_a_result).resolve()
    bundle_path = Path(args.bundle).resolve()
    protocol = load_json(protocol_path); verify_protocol(protocol); verify_stage_a(protocol, stage_path)
    pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    bundle = verify_bundle(protocol, bundle_path, pseudo_dir, pw)
    spec = protocol["clean_surface"]
    role = args.role
    allowed = False
    if role == "candidate":
        allowed = args.layers in spec["candidate_layers"] and float(args.vacuum) in [float(x) for x in spec["candidate_vacuum_angstrom"]] and args.kmesh in spec["candidate_kmeshes"]
    elif role in {"reference", "audit"}:
        row = spec["terminal_reference" if role == "reference" else "independent_audit"]
        allowed = args.layers == int(row["layers"]) and close(args.vacuum, row["vacuum_angstrom"]) and args.kmesh == int(row["kmesh"])
    if not allowed:
        raise SystemExit("HOLD: clean-surface case is not frozen")

    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    cell, atoms = clean_geometry(float(protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), args.layers, float(args.vacuum))
    relax_dir = root / "relax"; relax_dir.mkdir(exist_ok=True); tmp = relax_dir / "tmp"; tmp.mkdir(exist_ok=True)
    relax_in = relax_dir / "clean_relax.in"; relax_out = relax_dir / "clean_relax.out"
    relax_in.write_text(qe_input(calculation="relax", prefix="co_cu111_clean", cell=cell, atoms=atoms, kmesh=args.kmesh, protocol=protocol, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp))
    rr = run_pw(pw, relax_in, relax_out)
    final_atoms = parse_positions(rr["text"], len(atoms), atoms) if rr["job_done"] else None
    if rr["returncode"] != 0 or not rr["job_done"] or rr["energy_ev"] is None or final_atoms is None:
        raise SystemExit("HOLD: clean-surface relaxation failed")
    forces = parse_forces(rr["text"], len(atoms))
    max_force = max_movable_force_ev_a(forces, final_atoms)
    cleanup_tmp(tmp)

    scf_dir = root / "reproduce"; scf_dir.mkdir(exist_ok=True); tmp2 = scf_dir / "tmp"; tmp2.mkdir(exist_ok=True)
    fixed_atoms = json.loads(json.dumps(final_atoms))
    for atom in fixed_atoms:
        atom["flags"] = [0, 0, 0]
    scf_in = scf_dir / "clean_reproduce.in"; scf_out = scf_dir / "clean_reproduce.out"
    scf_in.write_text(qe_input(calculation="scf", prefix="co_cu111_clean_repro", cell=cell, atoms=fixed_atoms, kmesh=args.kmesh, protocol=protocol, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp2))
    sr = run_pw(pw, scf_in, scf_out)
    cleanup_tmp(tmp2)
    if sr["returncode"] != 0 or not sr["job_done"] or sr["energy_ev"] is None:
        raise SystemExit("HOLD: clean-surface reproduction SCF failed")
    delta = abs(float(rr["energy_ev"]) - float(sr["energy_ev"]))
    bulk_e0 = float(protocol["inherited_stage_a_settings"]["bulk_e0_ev_per_atom"])
    excess = (float(sr["energy_ev"]) - args.layers * bulk_e0) / 2.0
    force_gate = float(spec["relaxation"]["force_gate_ev_per_angstrom"])
    repro_gate = float(spec["independent_scf_reproduction_gate_ev"])
    mechanical_pass = max_force is not None and max_force <= force_gate and delta <= repro_gate
    layer_z = sorted(float(a["position_angstrom"][2]) for a in final_atoms)
    summary = {
        "schema": "co-cu111-pbe-clean-surface-case-v0.1",
        "status": "COMPLETE" if mechanical_pass else "NUMERICAL_HOLD",
        "case_id": clean_case_id(args.layers, float(args.vacuum), args.kmesh, role),
        "role": role,
        "layers": args.layers,
        "vacuum_angstrom": float(args.vacuum),
        "kmesh": args.kmesh,
        "cell_angstrom": cell,
        "layer_z_angstrom": layer_z,
        "final_atoms": final_atoms,
        "relax_energy_ev": rr["energy_ev"],
        "fixed_geometry_scf_energy_ev": sr["energy_ev"],
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": max_force,
        "surface_excess_ev_per_surface_atom": excess,
        "mechanical_pass": mechanical_pass,
        "provenance": {
            "protocol_sha256": sha256(protocol_path),
            "stage_a_result_sha256": sha256(stage_path),
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "kinetic_inputs_used": False,
            "stage_a_scientific_settings_modified": False
        },
        "raw_hashes": {
            "relax_input_sha256": sha256(relax_in),
            "relax_output_sha256": sha256(relax_out),
            "reproduce_input_sha256": sha256(scf_in),
            "reproduce_output_sha256": sha256(scf_out)
        }
    }
    summary_path = root / "summary.json"; write_json(summary_path, summary); stage_manifest(root, [summary_path])
    print(json.dumps(summary, indent=2, sort_keys=True))


def find_summaries(root: Path, schema: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        try:
            row = load_json(path)
        except Exception:
            continue
        if row.get("schema") == schema:
            row["_source_path"] = str(path)
            row["_source_sha256"] = sha256(path)
            found.append(row)
    return found


def clean_case_pass(row: dict[str, Any], spec: dict[str, Any]) -> bool:
    return bool(row.get("mechanical_pass")) and float(row.get("max_movable_force_ev_per_angstrom", 1e9)) <= float(spec["relaxation"]["force_gate_ev_per_angstrom"]) and float(row.get("energy_reproduction_delta_ev", 1e9)) <= float(spec["independent_scf_reproduction_gate_ev"])


def command_clean_gate(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); protocol = load_json(protocol_path); verify_protocol(protocol)
    stage_path = Path(args.stage_a_result).resolve(); verify_stage_a(protocol, stage_path)
    rows = find_summaries(Path(args.root).resolve(), "co-cu111-pbe-clean-surface-case-v0.1")
    by_id = {row["case_id"]: row for row in rows}
    spec = protocol["clean_surface"]
    expected: list[str] = []
    for layers in spec["candidate_layers"]:
        for vacuum in spec["candidate_vacuum_angstrom"]:
            for kmesh in spec["candidate_kmeshes"]:
                expected.append(clean_case_id(int(layers), float(vacuum), int(kmesh), "candidate"))
    ref = spec["terminal_reference"]; aud = spec["independent_audit"]
    ref_id = clean_case_id(int(ref["layers"]), float(ref["vacuum_angstrom"]), int(ref["kmesh"]), "reference")
    aud_id = clean_case_id(int(aud["layers"]), float(aud["vacuum_angstrom"]), int(aud["kmesh"]), "audit")
    expected += [ref_id, aud_id]
    missing = [x for x in expected if x not in by_id]
    if missing:
        raise SystemExit("HOLD: missing clean-surface summaries: " + ",".join(missing))
    ref_row = by_id[ref_id]; aud_row = by_id[aud_id]
    tol = float(spec["surface_excess_convergence_max_ev_per_surface_atom"])
    reference_audit_delta = abs(float(ref_row["surface_excess_ev_per_surface_atom"]) - float(aud_row["surface_excess_ev_per_surface_atom"]))
    reference_audit_pass = clean_case_pass(ref_row, spec) and clean_case_pass(aud_row, spec) and reference_audit_delta <= tol
    candidates: list[dict[str, Any]] = []
    if reference_audit_pass:
        a0 = float(protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"])
        d111 = a0 / math.sqrt(3.0)
        for cid in expected[:-2]:
            row = by_id[cid]
            delta = abs(float(row["surface_excess_ev_per_surface_atom"]) - float(ref_row["surface_excess_ev_per_surface_atom"]))
            cell_z = (int(row["layers"]) - 1) * d111 + float(row["vacuum_angstrom"])
            cost = int(row["layers"]) * int(row["kmesh"]) ** 2 * cell_z
            row2 = {k: v for k, v in row.items() if not k.startswith("_")}
            row2["surface_excess_delta_to_reference_ev_per_surface_atom"] = delta
            row2["surface_convergence_pass"] = clean_case_pass(row, spec) and delta <= tol
            row2["estimated_cost_score"] = cost
            row2["source_sha256"] = row["_source_sha256"]
            candidates.append(row2)
    passing = [x for x in candidates if x["surface_convergence_pass"]]
    passing.sort(key=lambda x: (x["estimated_cost_score"], x["layers"], x["vacuum_angstrom"], x["kmesh"]))
    selected = passing[0] if passing else None
    status = "CLEAN_SURFACE_PASS" if selected is not None and reference_audit_pass else "NUMERICAL_HOLD"
    result = {
        "schema": "co-cu111-pbe-clean-surface-gate-v0.1",
        "status": status,
        "reference_audit_pass": reference_audit_pass,
        "reference_audit_delta_ev_per_surface_atom": reference_audit_delta,
        "reference": {k: v for k, v in ref_row.items() if not k.startswith("_")},
        "audit": {k: v for k, v in aud_row.items() if not k.startswith("_")},
        "candidates": candidates,
        "selected": selected,
        "next_gate": "PBE_CO_SITE_ORDERING_SCREEN" if status == "CLEAN_SURFACE_PASS" else protocol["decision"]["clean_surface_hold_next_gate"],
        "provenance": {
            "protocol_sha256": sha256(protocol_path),
            "stage_a_result_sha256": sha256(stage_path),
            "kinetic_inputs_used": False
        }
    }
    write_json(Path(args.out).resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))


def selected_clean_summary(clean_gate: dict[str, Any], clean_root: Path) -> dict[str, Any]:
    selected = clean_gate.get("selected")
    if clean_gate.get("status") != "CLEAN_SURFACE_PASS" or not selected:
        raise SystemExit("HOLD: clean-surface gate did not PASS")
    cid = selected["case_id"]
    rows = find_summaries(clean_root, "co-cu111-pbe-clean-surface-case-v0.1")
    matches = [row for row in rows if row.get("case_id") == cid]
    if len(matches) != 1:
        raise SystemExit("HOLD: selected clean-surface source is not unique")
    return matches[0]


def command_site_run(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); protocol = load_json(protocol_path); verify_protocol(protocol)
    stage_path = Path(args.stage_a_result).resolve(); verify_stage_a(protocol, stage_path)
    bundle_path = Path(args.bundle).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    bundle = verify_bundle(protocol, bundle_path, pseudo_dir, pw)
    clean_gate = load_json(Path(args.clean_gate).resolve())
    clean_summary = selected_clean_summary(clean_gate, Path(args.clean_root).resolve())
    site_spec = protocol["adsorption_site_ordering"]
    if args.site not in site_spec["sites"]:
        raise SystemExit("HOLD: site is not frozen")
    cell, atoms = adsorption_geometry(clean_summary, args.site, protocol)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    relax_dir = root / "relax"; relax_dir.mkdir(exist_ok=True); tmp = relax_dir / "tmp"; tmp.mkdir(exist_ok=True)
    kmesh = int(site_spec["primary_kmesh"])
    inp = relax_dir / f"{args.site}_relax.in"; out = relax_dir / f"{args.site}_relax.out"
    inp.write_text(qe_input(calculation="relax", prefix=f"co_cu111_{args.site}", cell=cell, atoms=atoms, kmesh=kmesh, protocol=protocol, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp))
    rr = run_pw(pw, inp, out)
    final_atoms = parse_positions(rr["text"], len(atoms), atoms) if rr["job_done"] else None
    if rr["returncode"] != 0 or not rr["job_done"] or rr["energy_ev"] is None or final_atoms is None:
        raise SystemExit(f"HOLD: site relaxation failed for {args.site}")
    forces = parse_forces(rr["text"], len(atoms)); max_force = max_movable_force_ev_a(forces, final_atoms)
    cleanup_tmp(tmp)
    repro_dir = root / "reproduce"; repro_dir.mkdir(exist_ok=True); tmp2 = repro_dir / "tmp"; tmp2.mkdir(exist_ok=True)
    fixed = json.loads(json.dumps(final_atoms))
    for atom in fixed: atom["flags"] = [0, 0, 0]
    rin = repro_dir / f"{args.site}_reproduce.in"; rout = repro_dir / f"{args.site}_reproduce.out"
    rin.write_text(qe_input(calculation="scf", prefix=f"co_cu111_{args.site}_repro", cell=cell, atoms=fixed, kmesh=kmesh, protocol=protocol, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp2))
    sr = run_pw(pw, rin, rout); cleanup_tmp(tmp2)
    if sr["returncode"] != 0 or not sr["job_done"] or sr["energy_ev"] is None:
        raise SystemExit(f"HOLD: site reproduction SCF failed for {args.site}")
    delta = abs(float(rr["energy_ev"]) - float(sr["energy_ev"]))
    force_gate = float(site_spec["primary_relax_force_gate_ev_per_angstrom"])
    repro_gate = float(site_spec["primary_independent_scf_reproduction_gate_ev"])
    mechanical_pass = max_force is not None and max_force <= force_gate and delta <= repro_gate
    summary = {
        "schema": "co-cu111-pbe-site-primary-v0.1",
        "status": "COMPLETE" if mechanical_pass else "NUMERICAL_HOLD",
        "site": args.site,
        "kmesh": kmesh,
        "clean_case_id": clean_summary["case_id"],
        "cell_angstrom": cell,
        "final_atoms": final_atoms,
        "relax_energy_ev": rr["energy_ev"],
        "fixed_geometry_scf_energy_ev": sr["energy_ev"],
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": max_force,
        "mechanical_pass": mechanical_pass,
        "provenance": {
            "protocol_sha256": sha256(protocol_path),
            "stage_a_result_sha256": sha256(stage_path),
            "clean_gate_sha256": sha256(Path(args.clean_gate).resolve()),
            "clean_summary_sha256": clean_summary["_source_sha256"],
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "kinetic_inputs_used": False
        },
        "raw_hashes": {
            "relax_input_sha256": sha256(inp), "relax_output_sha256": sha256(out),
            "reproduce_input_sha256": sha256(rin), "reproduce_output_sha256": sha256(rout)
        }
    }
    sp = root / "summary.json"; write_json(sp, summary); stage_manifest(root, [sp])
    print(json.dumps(summary, indent=2, sort_keys=True))


def command_site_audit(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); protocol = load_json(protocol_path); verify_protocol(protocol)
    bundle_path = Path(args.bundle).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    bundle = verify_bundle(protocol, bundle_path, pseudo_dir, pw)
    primary_path = Path(args.primary).resolve(); primary = load_json(primary_path)
    if primary.get("schema") != "co-cu111-pbe-site-primary-v0.1" or primary.get("site") not in protocol["adsorption_site_ordering"]["sites"]:
        raise SystemExit("HOLD: wrong site primary summary")
    if not primary.get("mechanical_pass"):
        raise SystemExit("HOLD: primary site calculation did not pass numerical mechanics")
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True); tmp = root / "tmp"; tmp.mkdir(exist_ok=True)
    atoms = json.loads(json.dumps(primary["final_atoms"]))
    for atom in atoms: atom["flags"] = [0, 0, 0]
    cell = primary["cell_angstrom"]
    kmesh = int(protocol["adsorption_site_ordering"]["independent_numerical_audit_kmesh"])
    inp = root / f"{primary['site']}_k{kmesh}_audit.in"; out = root / f"{primary['site']}_k{kmesh}_audit.out"
    inp.write_text(qe_input(calculation="scf", prefix=f"co_cu111_{primary['site']}_audit", cell=cell, atoms=atoms, kmesh=kmesh, protocol=protocol, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp))
    ar = run_pw(pw, inp, out); cleanup_tmp(tmp)
    if ar["returncode"] != 0 or not ar["job_done"] or ar["energy_ev"] is None:
        raise SystemExit("HOLD: site numerical audit SCF failed")
    summary = {
        "schema": "co-cu111-pbe-site-audit-v0.1",
        "status": "COMPLETE",
        "site": primary["site"],
        "kmesh": kmesh,
        "fixed_geometry_scf_energy_ev": ar["energy_ev"],
        "primary_summary_sha256": sha256(primary_path),
        "provenance": {"protocol_sha256": sha256(protocol_path), "bundle_sha256": sha256(bundle_path), "pw_sha256": sha256(pw), "kinetic_inputs_used": False},
        "raw_hashes": {"input_sha256": sha256(inp), "output_sha256": sha256(out)}
    }
    sp = root / "summary.json"; write_json(sp, summary); stage_manifest(root, [sp])
    print(json.dumps(summary, indent=2, sort_keys=True))


def classify_site_gate(primary: dict[str, float], audit: dict[str, float], sensitivity_max: float) -> dict[str, Any]:
    competitors = ["bridge", "fcc_hollow", "hcp_hollow"]
    rel_primary = {site: primary[site] - primary["top"] for site in ["top"] + competitors}
    rel_audit = {site: audit[site] - audit["top"] for site in ["top"] + competitors}
    sensitivity = max(abs(rel_primary[s] - rel_audit[s]) for s in competitors)
    numerical_pass = sensitivity <= sensitivity_max
    primary_margin = min(rel_primary[s] for s in competitors)
    audit_margin = min(rel_audit[s] for s in competitors)
    required_margin = 2.0 * sensitivity
    ordering_pass = numerical_pass and primary_margin > required_margin and audit_margin > 0.0
    return {
        "relative_primary_ev_per_CO": rel_primary,
        "relative_audit_ev_per_CO": rel_audit,
        "numerical_site_energy_sensitivity_ev_per_CO": sensitivity,
        "numerical_sensitivity_pass": numerical_pass,
        "primary_top_margin_ev_per_CO": primary_margin,
        "audit_top_margin_ev_per_CO": audit_margin,
        "required_margin_ev_per_CO": required_margin,
        "top_site_ordering_pass": ordering_pass
    }


def command_finalize(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); protocol = load_json(protocol_path); verify_protocol(protocol)
    stage_path = Path(args.stage_a_result).resolve(); verify_stage_a(protocol, stage_path)
    clean_gate_path = Path(args.clean_gate).resolve(); clean = load_json(clean_gate_path)
    if clean.get("schema") != "co-cu111-pbe-clean-surface-gate-v0.1":
        raise SystemExit("HOLD: wrong clean-surface gate schema")
    if clean.get("status") != "CLEAN_SURFACE_PASS":
        result = {
            "schema": "co-cu111-pbe-surface-site-ordering-result-v0.1",
            "status": "NUMERICAL_HOLD",
            "clean_surface_gate": clean,
            "site_ordering_gate": None,
            "next_gate": protocol["decision"]["clean_surface_hold_next_gate"],
            "automatic_downstream_dispatch": False,
            "provenance": {"protocol_sha256": sha256(protocol_path), "stage_a_result_sha256": sha256(stage_path), "clean_gate_sha256": sha256(clean_gate_path), "kinetic_inputs_used": False}
        }
        write_json(Path(args.out).resolve(), result); print(json.dumps(result, indent=2, sort_keys=True)); return
    if not args.site_root:
        raise SystemExit("HOLD: clean surface passed but site-root was not provided")
    site_root = Path(args.site_root).resolve()
    prim_rows = find_summaries(site_root, "co-cu111-pbe-site-primary-v0.1")
    aud_rows = find_summaries(site_root, "co-cu111-pbe-site-audit-v0.1")
    sites = protocol["adsorption_site_ordering"]["sites"]
    pmap = {r["site"]: r for r in prim_rows}; amap = {r["site"]: r for r in aud_rows}
    missing = [s for s in sites if s not in pmap or s not in amap]
    if missing:
        raise SystemExit("HOLD: missing site summaries: " + ",".join(missing))
    mechanics_ok = all(bool(pmap[s].get("mechanical_pass")) for s in sites)
    if not mechanics_ok:
        status = "NUMERICAL_HOLD"; next_gate = protocol["decision"]["site_numerical_hold_next_gate"]
        site_gate = {"mechanical_pass": False, "reason": "PRIMARY_SITE_RELAXATION_OR_REPRODUCTION_GATE_FAILED"}
    else:
        primary = {s: float(pmap[s]["fixed_geometry_scf_energy_ev"]) for s in sites}
        audit = {s: float(amap[s]["fixed_geometry_scf_energy_ev"]) for s in sites}
        site_gate = classify_site_gate(primary, audit, float(protocol["adsorption_site_ordering"]["numerical_site_energy_sensitivity_max_ev_per_CO"]))
        site_gate["mechanical_pass"] = True
        site_gate["primary_source_sha256"] = {s: pmap[s]["_source_sha256"] for s in sites}
        site_gate["audit_source_sha256"] = {s: amap[s]["_source_sha256"] for s in sites}
        if not site_gate["numerical_sensitivity_pass"]:
            status = "NUMERICAL_HOLD"; next_gate = protocol["decision"]["site_numerical_hold_next_gate"]
        elif not site_gate["top_site_ordering_pass"]:
            status = "METHOD_REJECT_SITE_ORDERING"; next_gate = protocol["decision"]["site_ordering_rejection_next_gate"]
        else:
            status = "PASS"; next_gate = protocol["decision"]["pass_next_gate"]
    result = {
        "schema": "co-cu111-pbe-surface-site-ordering-result-v0.1",
        "status": status,
        "clean_surface_gate": clean,
        "site_ordering_gate": site_gate,
        "next_gate": next_gate,
        "automatic_downstream_dispatch": False,
        "provenance": {
            "protocol_sha256": sha256(protocol_path),
            "stage_a_result_sha256": sha256(stage_path),
            "clean_gate_sha256": sha256(clean_gate_path),
            "kinetic_inputs_used": False,
            "stage_a_scientific_settings_modified": False
        }
    }
    write_json(Path(args.out).resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))


def command_self_test(args: argparse.Namespace) -> None:
    protocol = load_json(Path(args.protocol).resolve()); verify_protocol(protocol)
    a0 = float(protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"])
    cell, atoms = clean_geometry(a0, 7, 16.0)
    assert len(atoms) == 7 and close(sum(a["position_angstrom"][2] for a in atoms), 0.0, 1e-10)
    assert sum(1 for a in atoms if a["flags"][2] == 1) == 4
    s7 = site_offsets(7); s9 = site_offsets(9)
    assert s7["fcc_hollow"] != s7["hcp_hollow"] and s9["fcc_hollow"] != s9["hcp_hollow"]
    fake_clean = {"layers": 7, "vacuum_angstrom": 16.0, "layer_z_angstrom": sorted(a["position_angstrom"][2] for a in atoms), "cell_angstrom": cell, "case_id": "synthetic"}
    scell, satoms = adsorption_geometry(fake_clean, "top", protocol)
    assert len(satoms) == 7 * 16 + 2 and len(scell) == 3
    good = classify_site_gate(
        {"top": -100.000, "bridge": -99.960, "fcc_hollow": -99.950, "hcp_hollow": -99.940},
        {"top": -100.020, "bridge": -99.979, "fcc_hollow": -99.969, "hcp_hollow": -99.959},
        0.005,
    )
    assert good["numerical_sensitivity_pass"] and good["top_site_ordering_pass"]
    bad = classify_site_gate(
        {"top": -100.000, "bridge": -99.990, "fcc_hollow": -100.010, "hcp_hollow": -99.980},
        {"top": -100.020, "bridge": -100.010, "fcc_hollow": -100.030, "hcp_hollow": -100.000},
        0.005,
    )
    assert bad["numerical_sensitivity_pass"] and not bad["top_site_ordering_pass"]
    print("SELF_TEST_PASS")
    print("KINETIC_INPUTS_USED=false")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("self-test"); s.add_argument("--protocol", required=True); s.set_defaults(func=command_self_test)

    s = sub.add_parser("clean-run")
    for name in ("protocol", "stage-a-result", "bundle", "pseudo-dir", "pw", "role", "out"):
        s.add_argument("--" + name, required=True)
    s.add_argument("--layers", type=int, required=True); s.add_argument("--vacuum", type=float, required=True); s.add_argument("--kmesh", type=int, required=True); s.set_defaults(func=command_clean_run)

    s = sub.add_parser("clean-gate")
    s.add_argument("--protocol", required=True); s.add_argument("--stage-a-result", required=True); s.add_argument("--root", required=True); s.add_argument("--out", required=True); s.set_defaults(func=command_clean_gate)

    s = sub.add_parser("site-run")
    for name in ("protocol", "stage-a-result", "clean-gate", "clean-root", "bundle", "pseudo-dir", "pw", "site", "out"):
        s.add_argument("--" + name, required=True)
    s.set_defaults(func=command_site_run)

    s = sub.add_parser("site-audit")
    for name in ("protocol", "bundle", "pseudo-dir", "pw", "primary", "out"):
        s.add_argument("--" + name, required=True)
    s.set_defaults(func=command_site_audit)

    s = sub.add_parser("finalize")
    s.add_argument("--protocol", required=True); s.add_argument("--stage-a-result", required=True); s.add_argument("--clean-gate", required=True); s.add_argument("--site-root"); s.add_argument("--out", required=True); s.set_defaults(func=command_finalize)

    args = p.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
