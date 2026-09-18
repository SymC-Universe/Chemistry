#!/usr/bin/env python3
"""Executable Na/Cu(001) computational closure stages 2-12.

The engine is fail-closed: every command validates input schemas and PASS states,
records hashes, and writes one machine-readable handoff. It never promotes an
experimental quantity from a computational result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Iterable

import numpy as np

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG
EV_ANG2_TO_N_M = 16.02176634
AMU_TO_KG = 1.66053906660e-27
KB_EV_K = 8.617333262145e-5
NA_MASS_AMU = 22.98976928
CU_MASS_AMU = 63.546
CU_PSEUDO = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"
SSSP_V2_NA_WFC_RY = 50.0
SSSP_V2_NA_RHO_RY = 150.0
FORCE_TOL_EV_A = 0.02
NEB_TOL_EV_A = 0.05
CI_NEB_TOL_EV_A = 0.03
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
FORCE_RE = re.compile(
    r"atom\s+(\d+)\s+type\s+\d+\s+force\s*=\s*"
    r"([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", re.I
)
ACT_FWD_RE = re.compile(r"activation energy \(->\)\s*=\s*([-+0-9.Ee]+)\s+eV", re.I)
ACT_REV_RE = re.compile(r"activation energy \(<-\)\s*=\s*([-+0-9.Ee]+)\s+eV", re.I)
IMAGE_ROW_RE = re.compile(
    r"^\s*(\d+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([TF])\s*$", re.M
)


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def require(data: dict[str, Any], schema: str, states: set[str] = {"PASS"}) -> None:
    if data.get("schema") != schema:
        raise SystemExit(f"HOLD: expected schema {schema!r}, found {data.get('schema')!r}")
    state = next((data.get(k) for k in ("status", "gate", "scientific_status") if isinstance(data.get(k), str)), None)
    if state not in states:
        raise SystemExit(f"HOLD: {schema} is not PASS: {state!r}")


def artifact_link(path: Path) -> dict[str, str]:
    return {"path": path.name, "sha256": sha256(path)}


def vec_add(a: Iterable[float], b: Iterable[float]) -> list[float]:
    return [float(x) + float(y) for x, y in zip(a, b)]


def vec_sub(a: Iterable[float], b: Iterable[float]) -> list[float]:
    return [float(x) - float(y) for x, y in zip(a, b)]


def vec_scale(a: Iterable[float], s: float) -> list[float]:
    return [float(x) * float(s) for x in a]


def norm(a: Iterable[float]) -> float:
    return math.sqrt(sum(float(x) ** 2 for x in a))


def cell_matrix(cell: list[list[float]]) -> np.ndarray:
    return np.asarray(cell, dtype=float).T


def cart_to_frac(position: Iterable[float], cell: list[list[float]]) -> np.ndarray:
    return np.linalg.solve(cell_matrix(cell), np.asarray(position, dtype=float))


def frac_to_cart(frac: Iterable[float], cell: list[list[float]]) -> np.ndarray:
    return cell_matrix(cell) @ np.asarray(frac, dtype=float)


def wrap_xy(position: Iterable[float], cell: list[list[float]]) -> list[float]:
    f = cart_to_frac(position, cell)
    f[0] %= 1.0
    f[1] %= 1.0
    return frac_to_cart(f, cell).tolist()


def parse_qe_energy(text: str) -> float | None:
    values = [float(v) for v in ENERGY_RE.findall(text)]
    return values[-1] * RY_TO_EV if values else None


def parse_qe_forces(text: str, nat: int) -> list[list[float]]:
    matches = FORCE_RE.findall(text)
    if len(matches) < nat:
        return []
    last = matches[-nat:]
    return [[float(x) * RY_BOHR_TO_EV_ANG for x in row[1:]] for row in last]


def parse_final_positions(text: str, nat: int) -> list[dict[str, Any]]:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().upper().startswith("ATOMIC_POSITIONS")]
    for start in reversed(starts):
        atoms: list[dict[str, Any]] = []
        for line in lines[start + 1:start + 1 + nat]:
            parts = line.split()
            if len(parts) < 4 or parts[0].upper() not in {"CU", "NA"}:
                atoms = []
                break
            flags = [int(x) for x in parts[4:7]] if len(parts) >= 7 else [1, 1, 1]
            atoms.append({
                "symbol": parts[0].capitalize(),
                "position_angstrom": [float(parts[1]), float(parts[2]), float(parts[3])],
                "flags": flags,
            })
        if len(atoms) == nat:
            return atoms
    return []


def restore_flags(parsed: list[dict[str, Any]], template: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Restore registered relaxation masks when QE omits if_pos columns in output."""
    if len(parsed) != len(template):
        return parsed
    for atom, source in zip(parsed, template):
        atom["flags"] = list(source.get("flags", [1, 1, 1]))
    return parsed


def max_unconstrained_force(forces: list[list[float]], atoms: list[dict[str, Any]]) -> float | None:
    if len(forces) != len(atoms):
        return None
    values = []
    for force, atom in zip(forces, atoms):
        flags = atom.get("flags", [1, 1, 1])
        projected = [f if int(flag) else 0.0 for f, flag in zip(force, flags)]
        if any(int(flag) for flag in flags):
            values.append(norm(projected))
    return max(values) if values else 0.0


def run_command(cmd: list[str], cwd: Path, stdout: Path, stdin: Path | None = None) -> tuple[int, float]:
    start = time.time()
    stdout.parent.mkdir(parents=True, exist_ok=True)
    with stdout.open("wb") as out:
        if stdin is None:
            proc = subprocess.run(cmd, cwd=cwd, stdout=out, stderr=subprocess.STDOUT)
        else:
            with stdin.open("rb") as inp:
                proc = subprocess.run(cmd, cwd=cwd, stdin=inp, stdout=out, stderr=subprocess.STDOUT)
    return proc.returncode, time.time() - start


def mpi_command(executable: Path, np_count: int, extra: list[str] | None = None) -> list[str]:
    cmd = [str(executable)]
    if extra:
        cmd.extend(extra)
    if np_count > 1:
        cmd = ["mpirun", "-np", str(np_count)] + cmd
    return cmd


def pseudo_identity(pseudo_dir: Path, na_filename: str | None = None) -> dict[str, Any]:
    files = [CU_PSEUDO] + ([na_filename] if na_filename else [])
    result = {}
    for filename in files:
        if not filename:
            continue
        path = pseudo_dir / filename
        if not path.is_file():
            raise SystemExit(f"HOLD: pseudopotential missing: {path}")
        result[filename] = {"sha256": sha256(path), "size_bytes": path.stat().st_size}
    return result


def qe_input(
    *, calculation: str, prefix: str, outdir: Path, pseudo_dir: Path,
    cell: list[list[float]], atoms: list[dict[str, Any]], species: list[tuple[str, float, str]],
    ecutwfc: float, ecutrho: float, kmesh: int, esm: bool = True,
    relax: bool = False, nosym: bool = True, degauss: float = 0.02,
) -> str:
    etot_thr_ry = 1.0e-4 / RY_TO_EV
    force_thr_ry_bohr = FORCE_TOL_EV_A / RY_BOHR_TO_EV_ANG
    lines = [
        "&CONTROL",
        f"  calculation = '{calculation}',",
        f"  prefix = '{prefix}',",
        f"  outdir = '{outdir}',",
        f"  pseudo_dir = '{pseudo_dir}',",
        "  tprnfor = .true.,",
        "  tstress = .true.,",
        "  verbosity = 'high',",
        f"  etot_conv_thr = {etot_thr_ry:.12e},",
    ]
    if relax:
        lines.append(f"  forc_conv_thr = {force_thr_ry_bohr:.12e},")
    lines.extend([
        "/",
        "&SYSTEM",
        "  ibrav = 0,",
        f"  nat = {len(atoms)},",
        f"  ntyp = {len(species)},",
        f"  ecutwfc = {ecutwfc:.8f},",
        f"  ecutrho = {ecutrho:.8f},",
        "  occupations = 'smearing',",
        "  smearing = 'mv',",
        f"  degauss = {degauss:.8f},",
        f"  nosym = {'.true.' if nosym else '.false.'},",
    ])
    if esm:
        lines.extend(["  assume_isolated = 'esm',", "  esm_bc = 'bc1',"])
    lines.extend([
        "/",
        "&ELECTRONS",
        "  conv_thr = 1.0d-9,",
        "  mixing_beta = 0.3,",
        "  electron_maxstep = 300,",
        "/",
    ])
    if relax:
        lines.extend(["&IONS", "  ion_dynamics = 'bfgs',", "/"])
    lines.append("ATOMIC_SPECIES")
    lines.extend(f"{symbol} {mass:.10f} {filename}" for symbol, mass, filename in species)
    lines.append("ATOMIC_POSITIONS angstrom")
    for atom in atoms:
        x, y, z = atom["position_angstrom"]
        f = atom.get("flags", [1, 1, 1])
        lines.append(f"{atom['symbol']} {x:.12f} {y:.12f} {z:.12f} {f[0]} {f[1]} {f[2]}")
    lines.append("K_POINTS automatic")
    lines.append(f"{kmesh} {kmesh} 1 0 0 0")
    lines.append("CELL_PARAMETERS angstrom")
    lines.extend(" ".join(f"{x:.12f}" for x in vector) for vector in cell)
    return "\n".join(lines) + "\n"


def na_atom_input(*, prefix: str, outdir: Path, pseudo_dir: Path, na_filename: str,
                  ecutwfc: float, ecutrho: float) -> str:
    side = 20.0
    return "\n".join([
        "&CONTROL", "  calculation = 'scf',", f"  prefix = '{prefix}',",
        f"  outdir = '{outdir}',", f"  pseudo_dir = '{pseudo_dir}',",
        "  tprnfor = .true.,", "  verbosity = 'high',", "/",
        "&SYSTEM", "  ibrav = 0,", "  nat = 1,", "  ntyp = 1,",
        f"  ecutwfc = {ecutwfc:.8f},", f"  ecutrho = {ecutrho:.8f},",
        "  nspin = 2,", "  tot_magnetization = 1.0,",
        "  occupations = 'smearing',", "  smearing = 'gaussian',", "  degauss = 0.001,",
        "  assume_isolated = 'martyna-tuckerman',", "/",
        "&ELECTRONS", "  conv_thr = 1.0d-10,", "  mixing_beta = 0.2,", "/",
        "ATOMIC_SPECIES", f"Na {NA_MASS_AMU:.10f} {na_filename}",
        "ATOMIC_POSITIONS angstrom", f"Na {side/2:.8f} {side/2:.8f} {side/2:.8f} 0 0 0",
        "K_POINTS gamma", "CELL_PARAMETERS angstrom",
        f"{side:.8f} 0.0 0.0", f"0.0 {side:.8f} 0.0", f"0.0 0.0 {side:.8f}", "",
    ])


def primitive_clean_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[list[float]], list[dict[str, Any]]]:
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    h = a0 / 2.0
    cell = [[h, h, 0.0], [-h, h, 0.0], [0.0, 0.0, cell_z]]
    z0 = 0.5 * (cell_z - slab_height)
    atoms = []
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        pos = frac_to_cart([shift, shift, (z0 + layer * dz) / cell_z], cell).tolist()
        movable = layer < 2 or layer >= layers - 2
        atoms.append({"symbol": "Cu", "position_angstrom": pos, "flags": [0, 0, 1 if movable else 0]})
    return cell, atoms


def replicate_surface(cell: list[list[float]], atoms: list[dict[str, Any]], repeat: int = 4) -> tuple[list[list[float]], list[dict[str, Any]]]:
    new_cell = [vec_scale(cell[0], repeat), vec_scale(cell[1], repeat), list(cell[2])]
    output: list[dict[str, Any]] = []
    for atom in atoms:
        for i in range(repeat):
            for j in range(repeat):
                shift = vec_add(vec_scale(cell[0], i), vec_scale(cell[1], j))
                output.append({
                    "symbol": atom["symbol"],
                    "position_angstrom": vec_add(atom["position_angstrom"], shift),
                    "flags": list(atom.get("flags", [0, 0, 0])),
                })
    return new_cell, output


def surface_site_fraction(site: str) -> tuple[float, float]:
    mapping = {"top": (0.25, 0.25), "bridge": (0.375, 0.25), "hollow": (0.375, 0.375)}
    if site not in mapping:
        raise ValueError(site)
    return mapping[site]


def classify_surface_site(position: Iterable[float], cell: list[list[float]], repeat: int = 4) -> dict[str, Any]:
    f = cart_to_frac(position, cell)
    fxy = np.array([f[0] % 1.0, f[1] % 1.0])
    candidates: list[tuple[str, np.ndarray]] = []
    for i in range(repeat):
        for j in range(repeat):
            candidates.append(("top", np.array([i / repeat, j / repeat])))
            candidates.append(("hollow", np.array([(i + 0.5) / repeat, (j + 0.5) / repeat])))
            candidates.append(("bridge", np.array([(i + 0.5) / repeat, j / repeat])))
            candidates.append(("bridge", np.array([i / repeat, (j + 0.5) / repeat])))
    best = None
    for label, point in candidates:
        df = fxy - point
        df -= np.round(df)
        dcart = frac_to_cart([df[0], df[1], 0.0], cell)
        distance = float(np.linalg.norm(dcart[:2]))
        if best is None or distance < best[0]:
            best = (distance, label, point)
    assert best is not None
    return {"site": best[1], "distance_angstrom": best[0], "nearest_fractional_xy": best[2].tolist()}


def top_layer_z(atoms: list[dict[str, Any]], symbol: str = "Cu") -> float:
    return max(float(a["position_angstrom"][2]) for a in atoms if a["symbol"] == symbol)


def adsorption_kmesh(primitive_kmesh: int) -> int:
    return max(2, int(math.ceil(primitive_kmesh / 4.0)))


def na_index(atoms: list[dict[str, Any]]) -> int:
    indices = [i for i, atom in enumerate(atoms) if atom["symbol"] == "Na"]
    if len(indices) != 1:
        raise SystemExit(f"HOLD: expected exactly one Na atom, found {len(indices)}")
    return indices[0]


def parse_neb_output(text: str, image_count: int) -> dict[str, Any]:
    fwd = [float(x) for x in ACT_FWD_RE.findall(text)]
    rev = [float(x) for x in ACT_REV_RE.findall(text)]
    rows = IMAGE_ROW_RE.findall(text)
    final_rows = rows[-image_count:] if len(rows) >= image_count else []
    images = [
        {"index": int(i), "energy_ev": float(e), "error_ev_per_angstrom": float(err), "frozen": flag == "T"}
        for i, e, err, flag in final_rows
    ]
    return {
        "forward_barrier_ev": fwd[-1] if fwd else None,
        "reverse_barrier_ev": rev[-1] if rev else None,
        "images": images,
        "max_internal_error_ev_per_angstrom": max((r["error_ev_per_angstrom"] for r in images[1:-1]), default=None),
        "converged": "neb: convergence achieved" in text.lower(),
        "job_done": "JOB DONE." in text,
    }


def parse_xyz_frames(path: Path) -> list[list[dict[str, Any]]]:
    lines = path.read_text(errors="replace").splitlines()
    frames = []
    i = 0
    while i < len(lines):
        try:
            nat = int(lines[i].strip())
        except Exception:
            i += 1
            continue
        if i + 2 + nat > len(lines):
            break
        atoms = []
        for line in lines[i + 2:i + 2 + nat]:
            p = line.split()
            if len(p) < 4:
                atoms = []
                break
            atoms.append({"symbol": p[0].capitalize(), "position_angstrom": [float(p[1]), float(p[2]), float(p[3])], "flags": [0, 0, 0]})
        if len(atoms) == nat:
            frames.append(atoms)
        i += 2 + nat
    return frames


def method_from_slab(slab: dict[str, Any]) -> dict[str, Any]:
    settings = slab["selected_slab_settings"]
    return {
        "ecutwfc_ry": float(settings["ecutwfc_ry"]),
        "ecutrho_ry": float(settings["ecutrho_ry"]),
        "primitive_kmesh": int(settings["kmesh_inplane"]),
        "smearing": "mv",
        "degauss_ry": 0.02,
        "electrostatics": {"assume_isolated": "esm", "esm_bc": "bc1"},
    }


def command_slab_handoff(args: argparse.Namespace) -> None:
    result_path = Path(args.slab_result).resolve()
    bulk_path = Path(args.bulk_handoff).resolve()
    result = read_json(result_path)
    bulk = read_json(bulk_path)
    require(result, "na-cu001-clean-slab-selection-v0.2")
    require(bulk, "na-cu001-bulk-to-slab-handoff-v0.1", {"bulk_convergence_passed_slab_not_yet_run"})
    selected = result.get("recommended_smallest")
    if not isinstance(selected, dict):
        raise SystemExit("HOLD: slab result lacks recommended_smallest")
    source = selected.get("source_record") or {}
    required = ["layers", "vacuum_angstrom", "kmesh_inplane"]
    if any(selected.get(k) is None for k in required):
        raise SystemExit("HOLD: incomplete selected slab dimensions")
    for key in ("a0_angstrom", "ecutwfc_ry", "ecutrho_ry", "bulk_kmesh"):
        if source.get(key) is None:
            raise SystemExit(f"HOLD: source slab record missing {key}")
    handoff = {
        "schema": "na-cu001-clean-slab-to-relaxation-handoff-v0.2",
        "status": "PASS",
        "system": "clean Cu(001)",
        "selected_slab_settings": {
            "layers": int(selected["layers"]),
            "vacuum_angstrom": float(selected["vacuum_angstrom"]),
            "kmesh_inplane": int(selected["kmesh_inplane"]),
            "a0_angstrom": float(source["a0_angstrom"]),
            "ecutwfc_ry": float(source["ecutwfc_ry"]),
            "ecutrho_ry": float(source["ecutrho_ry"]),
            "bulk_kmesh": int(source["bulk_kmesh"]),
            "surface_cell": "primitive Cu(001), area a0^2/2",
        },
        "convergence_rule": {
            "surface_excess_tolerance_mev_per_surface_atom": result["energy_tolerance_mev_per_surface_atom"],
            "selected_vacuum_kmesh": [selected["vacuum_angstrom"], selected["kmesh_inplane"]],
            "selected_layers": selected["layers"],
        },
        "input_artifacts": [artifact_link(result_path), artifact_link(bulk_path)],
        "next_gate": "clean_surface_relaxation",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))


def command_clean_relax(args: argparse.Namespace) -> None:
    slab_path = Path(args.slab_handoff).resolve()
    slab = read_json(slab_path)
    require(slab, "na-cu001-clean-slab-to-relaxation-handoff-v0.2")
    settings = slab["selected_slab_settings"]
    cell, atoms = primitive_clean_geometry(
        float(settings["a0_angstrom"]), int(settings["layers"]), float(settings["vacuum_angstrom"])
    )
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo = pseudo_identity(pseudo_dir)
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = root / "clean_relax.in"
    out = root / "clean_relax.out"
    inp.write_text(qe_input(
        calculation="relax", prefix="cu001_clean_relax", outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms, species=[("Cu", CU_MASS_AMU, CU_PSEUDO)],
        ecutwfc=float(settings["ecutwfc_ry"]), ecutrho=float(settings["ecutrho_ry"]),
        kmesh=int(settings["kmesh_inplane"]), esm=True, relax=True, nosym=False,
    ))
    pw = Path(args.pw).resolve()
    rc, elapsed = run_command(mpi_command(pw, args.np), root, out, inp)
    text = out.read_text(errors="replace")
    energy = parse_qe_energy(text)
    parsed_atoms = parse_final_positions(text, len(atoms))
    final_atoms = restore_flags(parsed_atoms, atoms) if parsed_atoms else atoms
    forces = parse_qe_forces(text, len(atoms))
    max_force = max_unconstrained_force(forces, final_atoms)
    z_values = sorted(float(a["position_angstrom"][2]) for a in final_atoms)
    pair_errors = [abs(z_values[i] + z_values[-1 - i] - float(cell[2][2])) for i in range(len(z_values) // 2)]
    symmetry_error = max(pair_errors, default=0.0)
    if len(z_values) >= 3:
        top_d12 = z_values[-1] - z_values[-2]
        top_d23 = z_values[-2] - z_values[-3]
    else:
        top_d12 = top_d23 = None
    bulk_spacing = float(settings["a0_angstrom"]) / 2.0
    pass_checks = {
        "returncode_zero": rc == 0,
        "job_done": "JOB DONE." in text,
        "energy_present": energy is not None,
        "final_positions_present": bool(parsed_atoms),
        "forces_present": len(forces) == len(atoms),
        "max_unconstrained_force_le_0p02": max_force is not None and max_force <= FORCE_TOL_EV_A,
        "mirror_pair_error_le_0p01_angstrom": symmetry_error <= 0.01,
    }
    status = "PASS" if all(pass_checks.values()) else "HOLD"
    handoff = {
        "schema": "na-cu001-relaxed-clean-surface-handoff-v0.1",
        "status": status,
        "system": "clean Cu(001)",
        "method": method_from_slab(slab),
        "cell_angstrom": cell,
        "atoms": final_atoms,
        "constraint_protocol": {
            "outer_layer_pairs": 2,
            "allowed_components": "z only",
            "central_and_inner_layers": "fixed",
            "symmetry_enforcement": "symmetric starting geometry plus post-relax mirror-pair verification",
        },
        "final_energy_ev": energy,
        "max_unconstrained_force_ev_per_angstrom": max_force,
        "mirror_pair_error_angstrom": symmetry_error,
        "interlayer_relaxation": {
            "bulk_spacing_angstrom": bulk_spacing,
            "top_d12_angstrom": top_d12,
            "top_d12_percent": None if top_d12 is None else 100.0 * (top_d12 / bulk_spacing - 1.0),
            "top_d23_angstrom": top_d23,
            "top_d23_percent": None if top_d23 is None else 100.0 * (top_d23 / bulk_spacing - 1.0),
        },
        "pass_checks": pass_checks,
        "run": {
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
            "pseudopotentials": pseudo,
        },
        "input_artifacts": [artifact_link(slab_path)],
        "next_gate": "adsorption_site_screening",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def command_resolve_na(args: argparse.Namespace) -> None:
    probe_path = Path(args.na_probe).resolve()
    bulk_path = Path(args.bulk_handoff).resolve()
    probe = read_json(probe_path)
    bulk = read_json(bulk_path)
    require(probe, "na-cu001-na-pseudopotential-handoff-v0.1")
    require(bulk, "na-cu001-bulk-to-slab-handoff-v0.1", {"bulk_convergence_passed_slab_not_yet_run"})
    selected = probe.get("selected")
    if not isinstance(selected, dict) or not selected.get("filename") or not selected.get("path"):
        raise SystemExit("HOLD: Na probe lacks a unique selected pseudopotential")
    bulk_settings = bulk["selected_bulk_settings"]
    mixed_wfc = max(float(bulk_settings["ecutwfc_ry"]), SSSP_V2_NA_WFC_RY)
    mixed_rho = max(float(bulk_settings["ecutrho_ry"]), SSSP_V2_NA_RHO_RY)
    pseudo_root = Path(args.pseudo_root).resolve()
    source = pseudo_root / selected["path"]
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo_dir.mkdir(parents=True, exist_ok=True)
    destination = pseudo_dir / selected["filename"]
    if not source.is_file():
        raise SystemExit(f"HOLD: selected Na UPF missing from extracted archive: {source}")
    shutil.copy2(source, destination)
    if sha256(destination) != selected["sha256"]:
        raise SystemExit("HOLD: copied Na UPF hash mismatch")
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = root / "na_atom.in"
    out = root / "na_atom.out"
    inp.write_text(na_atom_input(
        prefix="na_isolated", outdir=tmp, pseudo_dir=pseudo_dir,
        na_filename=destination.name, ecutwfc=mixed_wfc, ecutrho=mixed_rho,
    ))
    rc, elapsed = run_command(mpi_command(Path(args.pw).resolve(), args.np), root, out, inp)
    text = out.read_text(errors="replace")
    atom_energy = parse_qe_energy(text)
    status = "PASS" if rc == 0 and "JOB DONE." in text and atom_energy is not None else "HOLD"
    result = dict(probe)
    result.update({
        "status": status,
        "selected": dict(selected, installed_filename=destination.name, installed_sha256=sha256(destination)),
        "sssp_v2_efficiency_recommendation": {
            "Na": {"ecutwfc_ry": SSSP_V2_NA_WFC_RY, "ecutrho_ry": SSSP_V2_NA_RHO_RY},
            "source": "SSSP PBE Efficiency v2.0, DOI 10.24435/materialscloud:f3-ym",
        },
        "selected_mixed_settings": {
            "ecutwfc_ry": mixed_wfc,
            "ecutrho_ry": mixed_rho,
            "rule": "componentwise maximum of selected Cu bulk setting and SSSP v2 Na recommendation",
        },
        "isolated_atom_reference": {
            "method": "spin-polarized neutral Na in a 20 Angstrom cubic cell with Martyna-Tuckerman isolation",
            "energy_ev": atom_energy,
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
            "pass": status == "PASS",
        },
        "mixed_cutoff_status": "RESOLVED",
        "input_artifacts": [artifact_link(probe_path), artifact_link(bulk_path)],
        "next_gate": "adsorption_site_screening",
    })
    write_json(Path(args.out).resolve(), result)
    print(json.dumps(result, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def adsorption_atoms(clean: dict[str, Any], site: str, height: float) -> tuple[list[list[float]], list[dict[str, Any]]]:
    primitive_cell = clean["cell_angstrom"]
    primitive_atoms = clean["atoms"]
    cell, atoms = replicate_surface(primitive_cell, primitive_atoms, 4)
    ztop = top_layer_z(atoms)
    fx, fy = surface_site_fraction(site)
    pos = frac_to_cart([fx, fy, 0.0], cell).tolist()
    pos[2] = ztop + height
    atoms.append({"symbol": "Na", "position_angstrom": pos, "flags": [1, 1, 1]})
    return cell, atoms


def command_adsorption_run(args: argparse.Namespace) -> None:
    clean_path = Path(args.clean_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    clean = read_json(clean_path)
    na = read_json(na_path)
    require(clean, "na-cu001-relaxed-clean-surface-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    if args.site not in {"hollow", "bridge", "top"} or args.height not in {2.0, 2.5, 3.0}:
        raise SystemExit("HOLD: unregistered adsorption start")
    cell, atoms = adsorption_atoms(clean, args.site, args.height)
    mixed = na["selected_mixed_settings"]
    na_filename = na["selected"]["installed_filename"]
    kmesh = adsorption_kmesh(int(clean["method"]["primitive_kmesh"]))
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo = pseudo_identity(pseudo_dir, na_filename)
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    tag = f"ads_{args.site}_h{args.height:.1f}".replace(".", "p")
    inp = root / f"{tag}.in"
    out = root / f"{tag}.out"
    inp.write_text(qe_input(
        calculation="relax", prefix=tag, outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms,
        species=[("Cu", CU_MASS_AMU, CU_PSEUDO), ("Na", NA_MASS_AMU, na_filename)],
        ecutwfc=float(mixed["ecutwfc_ry"]), ecutrho=float(mixed["ecutrho_ry"]),
        kmesh=kmesh, esm=True, relax=True, nosym=True,
    ))
    rc, elapsed = run_command(mpi_command(Path(args.pw).resolve(), args.np), root, out, inp)
    text = out.read_text(errors="replace")
    energy = parse_qe_energy(text)
    parsed_atoms = parse_final_positions(text, len(atoms))
    final_atoms = restore_flags(parsed_atoms, atoms) if parsed_atoms else atoms
    forces = parse_qe_forces(text, len(atoms))
    max_force = max_unconstrained_force(forces, final_atoms)
    ni = na_index(final_atoms)
    classification = classify_surface_site(final_atoms[ni]["position_angstrom"], cell)
    pass_checks = {
        "returncode_zero": rc == 0,
        "job_done": "JOB DONE." in text,
        "energy_present": energy is not None,
        "positions_present": bool(parsed_atoms),
        "max_force_le_0p02": max_force is not None and max_force <= FORCE_TOL_EV_A,
    }
    status = "PASS" if all(pass_checks.values()) else "HOLD"
    record = {
        "schema": "na-cu001-adsorption-case-v0.1",
        "status": status,
        "start_site": args.site,
        "initial_height_angstrom": args.height,
        "coverage_ml": 0.0625,
        "supercell": [4, 4],
        "cell_angstrom": cell,
        "atoms": final_atoms,
        "final_site_classification": classification,
        "final_energy_ev": energy,
        "max_unconstrained_force_ev_per_angstrom": max_force,
        "kmesh_inplane": kmesh,
        "pass_checks": pass_checks,
        "run": {
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
            "pseudopotentials": pseudo,
        },
        "input_artifacts": [artifact_link(clean_path), artifact_link(na_path)],
    }
    write_json(root / "run_record.json", record)
    print(json.dumps(record, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def command_adsorption_analyze(args: argparse.Namespace) -> None:
    records_root = Path(args.records).resolve()
    clean_path = Path(args.clean_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    clean = read_json(clean_path)
    na = read_json(na_path)
    require(clean, "na-cu001-relaxed-clean-surface-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    records = [read_json(p) for p in sorted(records_root.rglob("run_record.json"))]
    expected = {(s, h) for s in ("hollow", "bridge", "top") for h in (2.0, 2.5, 3.0)}
    found = {(r.get("start_site"), float(r.get("initial_height_angstrom"))) for r in records}
    if found != expected:
        raise SystemExit(f"HOLD: adsorption matrix incomplete, expected {len(expected)}, found {len(found)}")
    all_pass = all(r.get("schema") == "na-cu001-adsorption-case-v0.1" and r.get("status") == "PASS" for r in records)
    hollow = [r for r in records if (r.get("final_site_classification") or {}).get("site") == "hollow"]
    selected = min(hollow, key=lambda r: float(r["final_energy_ev"])) if hollow else None
    by_start = {}
    for site in ("hollow", "bridge", "top"):
        subset = [r for r in records if r["start_site"] == site]
        by_start[site] = min(subset, key=lambda r: float(r["final_energy_ev"]))
    global_min = min(records, key=lambda r: float(r["final_energy_ev"]))
    status = "PASS" if all_pass and selected is not None and global_min["final_site_classification"]["site"] == "hollow" else "HOLD"
    handoff = {
        "schema": "na-cu001-adsorption-site-handoff-v0.1",
        "status": status,
        "system": "Na/Cu(001)",
        "coverage_model": {"supercell": [4, 4], "na_per_surface": 1, "coverage_ml": 0.0625},
        "initial_height_grid_angstrom": [2.0, 2.5, 3.0],
        "site_starts": ["hollow", "bridge", "top"],
        "electrostatics": clean["method"]["electrostatics"],
        "all_starts_converged": all_pass,
        "lowest_per_start_site": by_start,
        "global_minimum": global_min,
        "selected_hollow_minimum": selected,
        "site_collapse_is_retained": True,
        "input_artifacts": [artifact_link(clean_path), artifact_link(na_path)],
        "next_gate": "endpoint_geometry_verification",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def scf_record(*, root: Path, name: str, cell: list[list[float]], atoms: list[dict[str, Any]],
               method: dict[str, Any], na_filename: str, pseudo_dir: Path, pw: Path, np_count: int) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = root / f"{name}.in"
    out = root / f"{name}.out"
    inp.write_text(qe_input(
        calculation="scf", prefix=name, outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms,
        species=[("Cu", CU_MASS_AMU, CU_PSEUDO), ("Na", NA_MASS_AMU, na_filename)],
        ecutwfc=float(method["ecutwfc_ry"]), ecutrho=float(method["ecutrho_ry"]),
        kmesh=int(method["kmesh"]), esm=True, relax=False, nosym=True,
    ))
    rc, elapsed = run_command(mpi_command(pw, np_count), root, out, inp)
    text = out.read_text(errors="replace")
    energy = parse_qe_energy(text)
    forces = parse_qe_forces(text, len(atoms))
    return {
        "returncode": rc,
        "job_done": "JOB DONE." in text,
        "energy_ev": energy,
        "forces_ev_per_angstrom": forces,
        "elapsed_s": elapsed,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out),
    }


def relax_record(*, root: Path, name: str, cell: list[list[float]], atoms: list[dict[str, Any]],
                 method: dict[str, Any], na_filename: str, pseudo_dir: Path, pw: Path, np_count: int) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = root / f"{name}.in"
    out = root / f"{name}.out"
    inp.write_text(qe_input(
        calculation="relax", prefix=name, outdir=tmp, pseudo_dir=pseudo_dir,
        cell=cell, atoms=atoms,
        species=[("Cu", CU_MASS_AMU, CU_PSEUDO), ("Na", NA_MASS_AMU, na_filename)],
        ecutwfc=float(method["ecutwfc_ry"]), ecutrho=float(method["ecutrho_ry"]),
        kmesh=int(method["kmesh"]), esm=True, relax=True, nosym=True,
    ))
    rc, elapsed = run_command(mpi_command(pw, np_count), root, out, inp)
    text = out.read_text(errors="replace")
    energy = parse_qe_energy(text)
    parsed_atoms = parse_final_positions(text, len(atoms))
    final_atoms = restore_flags(parsed_atoms, atoms) if parsed_atoms else atoms
    forces = parse_qe_forces(text, len(atoms))
    return {
        "returncode": rc,
        "job_done": "JOB DONE." in text,
        "energy_ev": energy,
        "atoms": final_atoms,
        "forces_ev_per_angstrom": forces,
        "max_unconstrained_force_ev_per_angstrom": max_unconstrained_force(forces, final_atoms),
        "elapsed_s": elapsed,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out),
    }


def command_endpoints(args: argparse.Namespace) -> None:
    ads_path = Path(args.adsorption_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    ads = read_json(ads_path)
    na = read_json(na_path)
    require(ads, "na-cu001-adsorption-site-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    selected = ads["selected_hollow_minimum"]
    cell = selected["cell_angstrom"]
    atoms_a = selected["atoms"]
    ni = na_index(atoms_a)
    atoms_b0 = json.loads(json.dumps(atoms_a))
    translated = vec_add(atoms_b0[ni]["position_angstrom"], vec_scale(cell[0], 0.25))
    atoms_b0[ni]["position_angstrom"] = wrap_xy(translated, cell)
    mixed = na["selected_mixed_settings"]
    method = {
        "ecutwfc_ry": mixed["ecutwfc_ry"],
        "ecutrho_ry": mixed["ecutrho_ry"],
        "kmesh": selected["kmesh_inplane"],
    }
    na_filename = na["selected"]["installed_filename"]
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo = pseudo_identity(pseudo_dir, na_filename)
    pw = Path(args.pw).resolve()
    root = Path(args.out_dir).resolve()
    a_scf = scf_record(root=root / "endpoint_a_scf", name="endpoint_a", cell=cell, atoms=atoms_a,
                       method=method, na_filename=na_filename, pseudo_dir=pseudo_dir, pw=pw, np_count=args.np)
    b_relax = relax_record(root=root / "endpoint_b_relax", name="endpoint_b_relax", cell=cell, atoms=atoms_b0,
                           method=method, na_filename=na_filename, pseudo_dir=pseudo_dir, pw=pw, np_count=args.np)
    atoms_b = b_relax["atoms"]
    b_scf = scf_record(root=root / "endpoint_b_scf", name="endpoint_b", cell=cell, atoms=atoms_b,
                       method=method, na_filename=na_filename, pseudo_dir=pseudo_dir, pw=pw, np_count=args.np)
    energy_delta = None if a_scf["energy_ev"] is None or b_scf["energy_ev"] is None else abs(a_scf["energy_ev"] - b_scf["energy_ev"])
    a_force = max_unconstrained_force(a_scf["forces_ev_per_angstrom"], atoms_a)
    b_force = max_unconstrained_force(b_scf["forces_ev_per_angstrom"], atoms_b)
    class_a = classify_surface_site(atoms_a[ni]["position_angstrom"], cell)
    class_b = classify_surface_site(atoms_b[ni]["position_angstrom"], cell)
    displacement_frac = cart_to_frac(vec_sub(atoms_b[ni]["position_angstrom"], atoms_a[ni]["position_angstrom"]), cell)
    displacement_frac[:2] -= np.round(displacement_frac[:2] - np.array([0.25, 0.0]))
    translation_error = float(np.linalg.norm(frac_to_cart([displacement_frac[0] - 0.25, displacement_frac[1], 0.0], cell)[:2]))
    checks = {
        "endpoint_a_scf_pass": a_scf["returncode"] == 0 and a_scf["job_done"] and a_scf["energy_ev"] is not None,
        "endpoint_b_relax_pass": b_relax["returncode"] == 0 and b_relax["job_done"] and b_relax["energy_ev"] is not None,
        "endpoint_b_scf_pass": b_scf["returncode"] == 0 and b_scf["job_done"] and b_scf["energy_ev"] is not None,
        "endpoint_energy_difference_le_0p001_ev": energy_delta is not None and energy_delta <= 0.001,
        "endpoint_a_force_le_0p02": a_force is not None and a_force <= FORCE_TOL_EV_A,
        "endpoint_b_force_le_0p02": b_force is not None and b_force <= FORCE_TOL_EV_A,
        "both_hollow": class_a["site"] == "hollow" and class_b["site"] == "hollow",
        "translation_error_le_0p05_angstrom": translation_error <= 0.05,
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    handoff = {
        "schema": "na-cu001-endpoints-handoff-v0.1",
        "status": status,
        "system": "Na diffusion between nearest-neighbor hollow sites on Cu(001)",
        "cell_angstrom": cell,
        "method": method,
        "endpoint_a": {"atoms": atoms_a, "energy_ev": a_scf["energy_ev"], "site": class_a, "scf": a_scf},
        "endpoint_b": {"atoms": atoms_b, "energy_ev": b_scf["energy_ev"], "site": class_b, "relax": b_relax, "scf": b_scf},
        "energy_difference_ev": energy_delta,
        "primitive_translation_error_angstrom": translation_error,
        "pass_checks": checks,
        "pseudopotentials": pseudo,
        "input_artifacts": [artifact_link(ads_path), artifact_link(na_path)],
        "next_gate": "path_and_image_convergence",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def neb_input(*, prefix: str, outdir: Path, pseudo_dir: Path, cell: list[list[float]],
              atoms_a: list[dict[str, Any]], atoms_b: list[dict[str, Any]], method: dict[str, Any],
              na_filename: str, image_count: int, ci: bool, path_thr: float) -> str:
    ci_scheme = "auto" if ci else "no-CI"
    lines = [
        "BEGIN", "BEGIN_PATH_INPUT", "&PATH",
        "  restart_mode = 'from_scratch',", "  string_method = 'neb',",
        "  nstep_path = 250,", f"  num_of_images = {image_count},",
        "  opt_scheme = 'broyden',", f"  CI_scheme = '{ci_scheme}',",
        "  first_last_opt = .false.,", "  minimum_image = .true.,",
        f"  path_thr = {path_thr:.8f},", "/", "END_PATH_INPUT", "BEGIN_ENGINE_INPUT",
        "&CONTROL", "  calculation = 'scf',", f"  prefix = '{prefix}',",
        f"  outdir = '{outdir}',", f"  pseudo_dir = '{pseudo_dir}',",
        "  tprnfor = .true.,", "  verbosity = 'high',", "/",
        "&SYSTEM", "  ibrav = 0,", f"  nat = {len(atoms_a)},", "  ntyp = 2,",
        f"  ecutwfc = {float(method['ecutwfc_ry']):.8f},",
        f"  ecutrho = {float(method['ecutrho_ry']):.8f},",
        "  occupations = 'smearing',", "  smearing = 'mv',", "  degauss = 0.02,",
        "  nosym = .true.,", "  assume_isolated = 'esm',", "  esm_bc = 'bc1',", "/",
        "&ELECTRONS", "  conv_thr = 1.0d-9,", "  mixing_beta = 0.3,", "  electron_maxstep = 300,", "/",
        "&IONS", "/", "ATOMIC_SPECIES",
        f"Cu {CU_MASS_AMU:.10f} {CU_PSEUDO}", f"Na {NA_MASS_AMU:.10f} {na_filename}",
        "BEGIN_POSITIONS", "FIRST_IMAGE", "ATOMIC_POSITIONS angstrom",
    ]
    for atom in atoms_a:
        x, y, z = atom["position_angstrom"]
        f = atom.get("flags", [0, 0, 0])
        lines.append(f"{atom['symbol']} {x:.12f} {y:.12f} {z:.12f} {f[0]} {f[1]} {f[2]}")
    lines.extend(["LAST_IMAGE", "ATOMIC_POSITIONS angstrom"])
    for atom in atoms_b:
        x, y, z = atom["position_angstrom"]
        f = atom.get("flags", [0, 0, 0])
        lines.append(f"{atom['symbol']} {x:.12f} {y:.12f} {z:.12f} {f[0]} {f[1]} {f[2]}")
    lines.extend(["END_POSITIONS", "K_POINTS automatic", f"{int(method['kmesh'])} {int(method['kmesh'])} 1 0 0 0", "CELL_PARAMETERS angstrom"])
    lines.extend(" ".join(f"{x:.12f}" for x in vector) for vector in cell)
    lines.extend(["END_ENGINE_INPUT", "END", ""])
    return "\n".join(lines)


def run_neb_case(*, root: Path, endpoints: dict[str, Any], na: dict[str, Any], pseudo_dir: Path,
                 neb: Path, image_count: int, ci: bool, np_count: int) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    tag = f"na_cu001_{'ci' if ci else 'neb'}_{image_count}"
    inp = root / f"{tag}.in"
    out = root / f"{tag}.out"
    na_filename = na["selected"]["installed_filename"]
    inp.write_text(neb_input(
        prefix=tag, outdir=tmp, pseudo_dir=pseudo_dir, cell=endpoints["cell_angstrom"],
        atoms_a=endpoints["endpoint_a"]["atoms"], atoms_b=endpoints["endpoint_b"]["atoms"],
        method=endpoints["method"], na_filename=na_filename, image_count=image_count,
        ci=ci, path_thr=CI_NEB_TOL_EV_A if ci else NEB_TOL_EV_A,
    ))
    rc, elapsed = run_command(mpi_command(neb, np_count, ["-inp", str(inp)]), root, out)
    text = out.read_text(errors="replace")
    parsed = parse_neb_output(text, image_count)
    xyz = root / f"{tag}.xyz"
    frames = parse_xyz_frames(xyz) if xyz.is_file() else []
    result = {
        "schema": "na-cu001-neb-case-v0.1",
        "status": "PASS" if rc == 0 and parsed["job_done"] and parsed["converged"] and parsed["forward_barrier_ev"] is not None and len(parsed["images"]) == image_count else "HOLD",
        "ci": ci,
        "image_count": image_count,
        "path_threshold_ev_per_angstrom": CI_NEB_TOL_EV_A if ci else NEB_TOL_EV_A,
        **parsed,
        "frames": frames,
        "elapsed_s": elapsed,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out),
        "xyz_sha256": sha256(xyz) if xyz.is_file() else None,
    }
    write_json(root / "run_record.json", result)
    return result


def command_neb_run(args: argparse.Namespace) -> None:
    endpoints_path = Path(args.endpoints_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    endpoints = read_json(endpoints_path)
    na = read_json(na_path)
    require(endpoints, "na-cu001-endpoints-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    if args.images not in {5, 7, 9}:
        raise SystemExit("HOLD: unregistered ordinary NEB image count")
    pseudo_identity(Path(args.pseudo_dir).resolve(), na["selected"]["installed_filename"])
    result = run_neb_case(
        root=Path(args.out_dir).resolve(), endpoints=endpoints, na=na,
        pseudo_dir=Path(args.pseudo_dir).resolve(), neb=Path(args.neb).resolve(),
        image_count=args.images, ci=False, np_count=args.np,
    )
    result["input_artifacts"] = [artifact_link(endpoints_path), artifact_link(na_path)]
    write_json(Path(args.out_dir).resolve() / "run_record.json", result)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


def command_neb_analyze(args: argparse.Namespace) -> None:
    records = [read_json(p) for p in sorted(Path(args.records).resolve().rglob("run_record.json"))]
    input_links = []
    if getattr(args, "endpoints_handoff", None):
        endpoints_path = Path(args.endpoints_handoff).resolve()
        endpoints = read_json(endpoints_path)
        require(endpoints, "na-cu001-endpoints-handoff-v0.1")
        input_links.append(artifact_link(endpoints_path))
    if getattr(args, "na_handoff", None):
        na_path = Path(args.na_handoff).resolve()
        na = read_json(na_path)
        require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
        input_links.append(artifact_link(na_path))
    expected = {5, 7, 9}
    found = {int(r.get("image_count")) for r in records}
    if found != expected or len(records) != 3:
        raise SystemExit(f"HOLD: expected ordinary NEB records for {sorted(expected)}, found {sorted(found)}")
    if not all(r.get("schema") == "na-cu001-neb-case-v0.1" and r.get("status") == "PASS" and not r.get("ci") for r in records):
        raise SystemExit("HOLD: one or more ordinary NEB records failed")
    by_n = {int(r["image_count"]): r for r in records}
    barriers = {n: float(by_n[n]["forward_barrier_ev"]) for n in expected}
    selected_n = None
    for n in sorted(expected):
        larger = [barriers[m] for m in expected if m >= n]
        if max(abs(barriers[n] - value) for value in larger) <= 0.005:
            selected_n = n
            break
    status = "PASS" if selected_n is not None else "HOLD"
    handoff = {
        "schema": "na-cu001-path-convergence-handoff-v0.1",
        "status": status,
        "registered_image_counts": [5, 7, 9],
        "barrier_tolerance_ev": 0.005,
        "barriers_ev": barriers,
        "barrier_range_ev": max(barriers.values()) - min(barriers.values()),
        "selected_image_count": selected_n,
        "selected_record": by_n.get(selected_n) if selected_n else None,
        "all_records": by_n,
        "input_artifacts": input_links,
        "next_gate": "climbing_image_neb",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def command_ci_neb(args: argparse.Namespace) -> None:
    path_path = Path(args.path_handoff).resolve()
    endpoints_path = Path(args.endpoints_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    path = read_json(path_path)
    endpoints = read_json(endpoints_path)
    na = read_json(na_path)
    require(path, "na-cu001-path-convergence-handoff-v0.1")
    require(endpoints, "na-cu001-endpoints-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    image_count = int(path["selected_image_count"])
    result = run_neb_case(
        root=Path(args.out_dir).resolve(), endpoints=endpoints, na=na,
        pseudo_dir=Path(args.pseudo_dir).resolve(), neb=Path(args.neb).resolve(),
        image_count=image_count, ci=True, np_count=args.np,
    )
    images = result.get("images") or []
    internal = images[1:-1]
    max_row = max(internal, key=lambda row: row["energy_ev"]) if internal else None
    frames = result.get("frames") or []
    saddle_atoms = frames[max_row["index"] - 1] if max_row and len(frames) == image_count else None
    if saddle_atoms is not None:
        reference_flags = [atom.get("flags", [0, 0, 0]) for atom in endpoints["endpoint_a"]["atoms"]]
        if len(reference_flags) != len(saddle_atoms):
            saddle_atoms = None
        else:
            for atom, flags in zip(saddle_atoms, reference_flags):
                atom["flags"] = list(flags)
    endpoint_a = endpoints["endpoint_a"]["energy_ev"]
    endpoint_b = endpoints["endpoint_b"]["energy_ev"]
    checks = {
        "neb_pass": result["status"] == "PASS",
        "maximum_image_internal": max_row is not None and 1 < max_row["index"] < image_count,
        "saddle_frame_available": saddle_atoms is not None,
        "endpoint_forward_reproduction_le_0p001_ev": images and abs(images[0]["energy_ev"] - endpoint_a) <= 0.001,
        "endpoint_reverse_reproduction_le_0p001_ev": images and abs(images[-1]["energy_ev"] - endpoint_b) <= 0.001,
        "max_internal_error_le_0p03": result["max_internal_error_ev_per_angstrom"] is not None and result["max_internal_error_ev_per_angstrom"] <= CI_NEB_TOL_EV_A,
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    handoff = {
        "schema": "na-cu001-ci-neb-handoff-v0.1",
        "status": status,
        "image_count": image_count,
        "forward_barrier_ev": result["forward_barrier_ev"],
        "reverse_barrier_ev": result["reverse_barrier_ev"],
        "images": images,
        "maximum_energy_image": max_row,
        "saddle_atoms": saddle_atoms,
        "cell_angstrom": endpoints["cell_angstrom"],
        "method": endpoints["method"],
        "pass_checks": checks,
        "run_record": result,
        "input_artifacts": [artifact_link(path_path), artifact_link(endpoints_path), artifact_link(na_path)],
        "next_gate": "saddle_verification",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def periodic_xy_distance(a: Iterable[float], b: Iterable[float], cell: list[list[float]]) -> float:
    fa = cart_to_frac(a, cell)
    fb = cart_to_frac(b, cell)
    df = fa - fb
    df[0] -= round(float(df[0]))
    df[1] -= round(float(df[1]))
    df[2] = 0.0
    return float(np.linalg.norm(frac_to_cart(df, cell)[:2]))


def hessian_from_force_records(records: dict[tuple[int, int], list[float]], delta: float) -> np.ndarray:
    h = np.zeros((3, 3), dtype=float)
    for axis in range(3):
        fplus = np.asarray(records[(axis, 1)], dtype=float)
        fminus = np.asarray(records[(axis, -1)], dtype=float)
        h[:, axis] = -(fplus - fminus) / (2.0 * delta)
    return 0.5 * (h + h.T)


def frequencies_from_eigenvalues(eigenvalues: np.ndarray) -> np.ndarray:
    mass = NA_MASS_AMU * AMU_TO_KG
    vals = []
    for value in eigenvalues:
        hz = math.sqrt(abs(float(value)) * EV_ANG2_TO_N_M / mass) / (2.0 * math.pi)
        vals.append(-hz if value < 0 else hz)
    return np.asarray(vals)


def command_saddle(args: argparse.Namespace) -> None:
    endpoints_path = Path(args.endpoints_handoff).resolve()
    ci_path = Path(args.ci_handoff).resolve()
    na_path = Path(args.na_handoff).resolve()
    endpoints = read_json(endpoints_path)
    ci = read_json(ci_path)
    na = read_json(na_path)
    require(endpoints, "na-cu001-endpoints-handoff-v0.1")
    require(ci, "na-cu001-ci-neb-handoff-v0.1")
    require(na, "na-cu001-na-pseudopotential-handoff-v0.1")
    cell = ci["cell_angstrom"]
    atoms_min = json.loads(json.dumps(endpoints["endpoint_a"]["atoms"]))
    atoms_sad = json.loads(json.dumps(ci["saddle_atoms"]))
    if not atoms_sad:
        raise SystemExit("HOLD: CI-NEB handoff lacks saddle coordinates")
    ni_min = na_index(atoms_min)
    ni_sad = na_index(atoms_sad)
    mixed = na["selected_mixed_settings"]
    method = {
        "ecutwfc_ry": mixed["ecutwfc_ry"],
        "ecutrho_ry": mixed["ecutrho_ry"],
        "kmesh": endpoints["method"]["kmesh"],
    }
    na_filename = na["selected"]["installed_filename"]
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo = pseudo_identity(pseudo_dir, na_filename)
    pw = Path(args.pw).resolve()
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    centers = {"minimum": (atoms_min, ni_min), "saddle": (atoms_sad, ni_sad)}
    center_scf: dict[str, Any] = {}
    displacement_records: dict[str, dict[float, dict[tuple[int, int], list[float]]]] = {
        "minimum": {}, "saddle": {}
    }
    raw_cases = []
    for center_name, (center_atoms, ni) in centers.items():
        fixed_center = json.loads(json.dumps(center_atoms))
        for atom in fixed_center:
            atom["flags"] = [0, 0, 0]
        center_scf[center_name] = scf_record(
            root=root / center_name / "center", name=f"{center_name}_center", cell=cell,
            atoms=fixed_center, method=method, na_filename=na_filename,
            pseudo_dir=pseudo_dir, pw=pw, np_count=args.np,
        )
        for delta in (0.02, 0.04):
            displacement_records[center_name][delta] = {}
            for axis in range(3):
                for sign in (-1, 1):
                    atoms = json.loads(json.dumps(fixed_center))
                    atoms[ni]["position_angstrom"][axis] += sign * delta
                    tag = f"{center_name}_d{delta:.2f}_a{axis}_s{sign:+d}".replace(".", "p").replace("+", "p").replace("-", "m")
                    rec = scf_record(
                        root=root / center_name / tag, name=tag, cell=cell, atoms=atoms,
                        method=method, na_filename=na_filename, pseudo_dir=pseudo_dir,
                        pw=pw, np_count=args.np,
                    )
                    if rec["returncode"] != 0 or not rec["job_done"] or len(rec["forces_ev_per_angstrom"]) != len(atoms):
                        raise SystemExit(f"HOLD: failed finite-displacement SCF {tag}")
                    force_na = rec["forces_ev_per_angstrom"][ni]
                    displacement_records[center_name][delta][(axis, sign)] = force_na
                    raw_cases.append({
                        "center": center_name, "delta_angstrom": delta, "axis": axis,
                        "sign": sign, "na_force_ev_per_angstrom": force_na,
                        "run": {k: rec[k] for k in ("returncode", "job_done", "energy_ev", "elapsed_s", "input_sha256", "output_sha256")},
                    })

    analysis: dict[str, Any] = {}
    eigensystems: dict[str, dict[float, tuple[np.ndarray, np.ndarray]]] = {"minimum": {}, "saddle": {}}
    for center_name in ("minimum", "saddle"):
        analyses = {}
        for delta in (0.02, 0.04):
            h = hessian_from_force_records(displacement_records[center_name][delta], delta)
            evals, evecs = np.linalg.eigh(h)
            freqs = frequencies_from_eigenvalues(evals)
            eigensystems[center_name][delta] = (evals, evecs)
            analyses[str(delta)] = {
                "hessian_ev_per_angstrom2": h.tolist(),
                "eigenvalues_ev_per_angstrom2": evals.tolist(),
                "frequencies_hz": freqs.tolist(),
            }
        e02 = eigensystems[center_name][0.02][0]
        e04 = eigensystems[center_name][0.04][0]
        scale = np.maximum(np.maximum(np.abs(e02), np.abs(e04)), 1.0e-6)
        convergence = float(np.max(np.abs(e02 - e04) / scale))
        analyses["delta_relative_eigenvalue_difference_max"] = convergence
        analysis[center_name] = analyses

    min_evals, _ = eigensystems["minimum"][0.02]
    sad_evals, sad_evecs = eigensystems["saddle"][0.02]
    unstable_index = int(np.argmin(sad_evals))
    unstable_vector = sad_evecs[:, unstable_index]
    hop = np.asarray(vec_sub(
        endpoints["endpoint_b"]["atoms"][na_index(endpoints["endpoint_b"]["atoms"])]["position_angstrom"],
        endpoints["endpoint_a"]["atoms"][na_index(endpoints["endpoint_a"]["atoms"])]["position_angstrom"],
    ), dtype=float)
    hop_frac = cart_to_frac(hop, cell)
    hop_frac[0] -= round(float(hop_frac[0] - 0.25))
    hop_frac[1] -= round(float(hop_frac[1]))
    hop_frac[2] = 0.0
    hop_cart = frac_to_cart(hop_frac, cell)
    hop_unit = hop_cart / np.linalg.norm(hop_cart)
    alignment = abs(float(np.dot(unstable_vector, hop_unit)))

    prefactors = {}
    for delta in (0.02, 0.04):
        me, _ = eigensystems["minimum"][delta]
        se, _ = eigensystems["saddle"][delta]
        mf = frequencies_from_eigenvalues(me)
        sf = frequencies_from_eigenvalues(se)
        if np.any(me <= 0) or np.sum(se < 0) != 1:
            prefactors[str(delta)] = None
        else:
            prefactors[str(delta)] = float(np.prod(mf[mf > 0]) / np.prod(sf[sf > 0]))
    if prefactors["0.02"] is None or prefactors["0.04"] is None:
        prefactor_rel = None
    else:
        prefactor_rel = abs(prefactors["0.02"] - prefactors["0.04"]) / max(abs(prefactors["0.02"]), abs(prefactors["0.04"]), 1.0e-30)

    downhill = []
    endpoint_positions = {
        "A": endpoints["endpoint_a"]["atoms"][na_index(endpoints["endpoint_a"]["atoms"])]["position_angstrom"],
        "B": endpoints["endpoint_b"]["atoms"][na_index(endpoints["endpoint_b"]["atoms"])]["position_angstrom"],
    }
    for sign in (-1, 1):
        atoms0 = json.loads(json.dumps(atoms_sad))
        atoms0[ni_sad]["position_angstrom"] = vec_add(atoms0[ni_sad]["position_angstrom"], vec_scale(unstable_vector, sign * 0.05))
        rec = relax_record(
            root=root / f"downhill_{sign:+d}".replace("+", "p").replace("-", "m"),
            name=f"downhill_{sign:+d}".replace("+", "p").replace("-", "m"),
            cell=cell, atoms=atoms0, method=method, na_filename=na_filename,
            pseudo_dir=pseudo_dir, pw=pw, np_count=args.np,
        )
        ni = na_index(rec["atoms"])
        d_a = periodic_xy_distance(rec["atoms"][ni]["position_angstrom"], endpoint_positions["A"], cell)
        d_b = periodic_xy_distance(rec["atoms"][ni]["position_angstrom"], endpoint_positions["B"], cell)
        basin = "A" if d_a < d_b else "B"
        downhill.append({
            "sign": sign, "basin": basin, "distance_to_A_angstrom": d_a,
            "distance_to_B_angstrom": d_b, "run": rec,
        })

    saddle_center_forces = center_scf["saddle"]["forces_ev_per_angstrom"]
    saddle_force = norm(saddle_center_forces[ni_sad]) if len(saddle_center_forces) == len(atoms_sad) else None
    checks = {
        "minimum_positive_at_both_displacements": all(np.all(eigensystems["minimum"][d][0] > 0) for d in (0.02, 0.04)),
        "saddle_exactly_one_negative_at_both_displacements": all(np.sum(eigensystems["saddle"][d][0] < 0) == 1 for d in (0.02, 0.04)),
        "hessian_delta_convergence_le_20_percent": analysis["minimum"]["delta_relative_eigenvalue_difference_max"] <= 0.20 and analysis["saddle"]["delta_relative_eigenvalue_difference_max"] <= 0.20,
        "unstable_mode_alignment_ge_0p70": alignment >= 0.70,
        "partial_vineyard_prefactor_convergence_le_20_percent": prefactor_rel is not None and prefactor_rel <= 0.20,
        "saddle_na_force_le_0p03": saddle_force is not None and saddle_force <= CI_NEB_TOL_EV_A,
        "downhill_relaxations_converged": all(d["run"]["returncode"] == 0 and d["run"]["job_done"] and d["run"]["max_unconstrained_force_ev_per_angstrom"] is not None and d["run"]["max_unconstrained_force_ev_per_angstrom"] <= FORCE_TOL_EV_A for d in downhill),
        "downhill_reaches_distinct_endpoints": {d["basin"] for d in downhill} == {"A", "B"},
        "downhill_endpoint_distance_le_0p30_angstrom": all(min(d["distance_to_A_angstrom"], d["distance_to_B_angstrom"]) <= 0.30 for d in downhill),
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    handoff = {
        "schema": "na-cu001-saddle-handoff-v0.1",
        "status": status,
        "method": "Na-only partial Hessian at endpoint and CI-NEB saddle, central finite differences at 0.02 and 0.04 Angstrom, plus downhill relaxations",
        "cell_angstrom": cell,
        "saddle_atoms": atoms_sad,
        "minimum_atoms": atoms_min,
        "hessian_analysis": analysis,
        "unstable_mode": {
            "eigenvalue_ev_per_angstrom2": float(sad_evals[unstable_index]),
            "eigenvector_cartesian": unstable_vector.tolist(),
            "alignment_with_hop_direction": alignment,
        },
        "partial_vineyard_prefactor_hz": prefactors["0.02"],
        "partial_vineyard_prefactor_delta_check_hz": prefactors["0.04"],
        "partial_vineyard_prefactor_relative_difference": prefactor_rel,
        "saddle_na_force_ev_per_angstrom": saddle_force,
        "downhill_connectivity": downhill,
        "raw_finite_displacement_cases": raw_cases,
        "pass_checks": checks,
        "pseudopotentials": pseudo,
        "input_artifacts": [artifact_link(endpoints_path), artifact_link(ci_path), artifact_link(na_path)],
        "next_gate": "barrier_coordinate_extraction",
    }
    write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def command_barrier(args: argparse.Namespace) -> None:
    path_path = Path(args.path_handoff).resolve()
    ci_path = Path(args.ci_handoff).resolve()
    saddle_path = Path(args.saddle_handoff).resolve()
    path = read_json(path_path)
    ci = read_json(ci_path)
    saddle = read_json(saddle_path)
    require(path, "na-cu001-path-convergence-handoff-v0.1")
    require(ci, "na-cu001-ci-neb-handoff-v0.1")
    require(saddle, "na-cu001-saddle-handoff-v0.1")
    barrier = float(ci["forward_barrier_ev"])
    reverse = float(ci["reverse_barrier_ev"])
    selected_ordinary = float(path["selected_record"]["forward_barrier_ev"])
    image_unc = 0.5 * float(path["barrier_range_ev"])
    ci_shift = abs(barrier - selected_ordinary)
    endpoint_asym = abs(barrier - reverse)
    conservative_unc = image_unc + ci_shift + endpoint_asym
    prefactor = float(saddle["partial_vineyard_prefactor_hz"])
    temperatures = [100.0, 150.0, 200.0, 250.0, 300.0]
    rates = [
        {
            "temperature_k": t,
            "rate_s_minus_1": prefactor * math.exp(-barrier / (KB_EV_K * t)),
            "model": "partial-Hessian harmonic transition-state estimate",
        }
        for t in temperatures
    ]
    coordinate = {
        "schema": "na-cu001-barrier-coordinate-v0.1",
        "status": "PASS",
        "system": "Na diffusion on Cu(001)",
        "mechanism": "nearest-neighbor fourfold-hollow to fourfold-hollow hop through bridge region",
        "coverage_ml": 0.0625,
        "electronic_forward_barrier_ev": barrier,
        "electronic_reverse_barrier_ev": reverse,
        "electronic_barrier_conservative_uncertainty_ev": conservative_unc,
        "uncertainty_components_ev": {
            "half_registered_image_count_range": image_unc,
            "ci_refinement_shift": ci_shift,
            "endpoint_asymmetry": endpoint_asym,
        },
        "attempt_frequency": {
            "value_hz": prefactor,
            "method": "Na-only partial-Hessian Vineyard prefactor",
            "finite_difference_check_hz": saddle["partial_vineyard_prefactor_delta_check_hz"],
            "relative_difference": saddle["partial_vineyard_prefactor_relative_difference"],
            "limitation": "substrate vibrational determinants are not included",
        },
        "computed_rate_coordinates": rates,
        "zero_point_correction_ev": None,
        "thermal_free_energy_correction_ev": None,
        "friction_or_linewidth": None,
        "separation_rule": "electronic barrier, approximate harmonic prefactor, model rates, and experimental quantities remain distinct",
        "input_artifacts": [artifact_link(path_path), artifact_link(ci_path), artifact_link(saddle_path)],
        "next_gate": "computational_atlas_admission",
    }
    write_json(Path(args.out).resolve(), coordinate)
    print(json.dumps(coordinate, indent=2))


def command_atlas(args: argparse.Namespace) -> None:
    barrier_path = Path(args.barrier_coordinate).resolve()
    evidence_path = Path(args.public_evidence).resolve()
    barrier = read_json(barrier_path)
    evidence = read_json(evidence_path)
    require(barrier, "na-cu001-barrier-coordinate-v0.1")
    computational_rows = []
    for row in barrier["computed_rate_coordinates"]:
        computational_rows.append({
            "system": "Na/Cu(001)",
            "phase": "surface",
            "coverage_ml": barrier["coverage_ml"],
            "temperature_k": row["temperature_k"],
            "barrier_ev": barrier["electronic_forward_barrier_ev"],
            "barrier_uncertainty_ev": barrier["electronic_barrier_conservative_uncertainty_ev"],
            "rate_s_minus_1": row["rate_s_minus_1"],
            "rate_model": row["model"],
            "attempt_frequency_hz": barrier["attempt_frequency"]["value_hz"],
            "source_type": "first_principles_computational_model",
            "verification_tier": "COMPUTATIONAL_FULL",
            "experimental_rate": None,
            "experimental_barrier": None,
        })
    record = {
        "schema": "na-cu001-atlas-admission-v0.1",
        "status": "PASS",
        "admission_scope": "computational Barrier-Rate Atlas extension only",
        "computational_rows": computational_rows,
        "public_evidence_candidates": evidence,
        "experimental_admission_status": "HOLD_PENDING_EXACT_STATE_POINT_TABLE",
        "non_blending_rule": "The public 51 meV and 0.53 THz report is not substituted for the computed barrier or prefactor and is not joined to a temperature-specific row without the underlying state-point table.",
        "input_artifacts": [artifact_link(barrier_path), artifact_link(evidence_path)],
        "next_gate": "integration_readiness",
    }
    write_json(Path(args.out).resolve(), record)
    print(json.dumps(record, indent=2))


def command_manifest(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != Path(args.out).name):
        rows.append({"path": str(path.relative_to(root)), "sha256": sha256(path), "size_bytes": path.stat().st_size})
    output = {"schema": "na-cu001-computational-manifest-v0.1", "status": "PASS", "files": rows}
    write_json(Path(args.out).resolve(), output)
    print(json.dumps(output, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("slab-handoff")
    p.add_argument("--slab-result", required=True)
    p.add_argument("--bulk-handoff", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_slab_handoff)

    p = sub.add_parser("clean-relax")
    p.add_argument("--slab-handoff", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_clean_relax)

    p = sub.add_parser("resolve-na")
    p.add_argument("--na-probe", required=True)
    p.add_argument("--bulk-handoff", required=True)
    p.add_argument("--pseudo-root", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--np", type=int, default=1)
    p.set_defaults(func=command_resolve_na)

    p = sub.add_parser("adsorption-run")
    p.add_argument("--site", choices=["hollow", "bridge", "top"], required=True)
    p.add_argument("--height", type=float, required=True)
    p.add_argument("--clean-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_adsorption_run)

    p = sub.add_parser("adsorption-analyze")
    p.add_argument("--records", required=True)
    p.add_argument("--clean-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_adsorption_analyze)

    p = sub.add_parser("endpoints")
    p.add_argument("--adsorption-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_endpoints)

    p = sub.add_parser("neb-run")
    p.add_argument("--images", type=int, required=True)
    p.add_argument("--endpoints-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--neb", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_neb_run)

    p = sub.add_parser("neb-analyze")
    p.add_argument("--records", required=True)
    p.add_argument("--endpoints-handoff")
    p.add_argument("--na-handoff")
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_neb_analyze)

    p = sub.add_parser("ci-neb")
    p.add_argument("--path-handoff", required=True)
    p.add_argument("--endpoints-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--neb", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_ci_neb)

    p = sub.add_parser("saddle")
    p.add_argument("--endpoints-handoff", required=True)
    p.add_argument("--ci-handoff", required=True)
    p.add_argument("--na-handoff", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--np", type=int, default=2)
    p.set_defaults(func=command_saddle)

    p = sub.add_parser("barrier")
    p.add_argument("--path-handoff", required=True)
    p.add_argument("--ci-handoff", required=True)
    p.add_argument("--saddle-handoff", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_barrier)

    p = sub.add_parser("atlas")
    p.add_argument("--barrier-coordinate", required=True)
    p.add_argument("--public-evidence", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_atlas)

    p = sub.add_parser("manifest")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_manifest)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
