#!/usr/bin/env python3
"""Preregistered clean Cu(001) slab convergence for Na/Cu(001) closure.

Consumes the compact bulk handoff and full bulk selection result. This stage
contains no Na geometries, adsorption energies, barriers, rates, or kinetic
targets. It fails closed on schema, provenance, or bulk-gate disagreement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time

RY_TO_EV = 13.605693122994
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
PSEUDO_NAME = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"
LAYERS = [5, 7, 9, 11]
VACUUM = [12.0, 16.0, 20.0, 24.0]
ENERGY_TOL_MEV = 1.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def solve2(a00: float, a01: float, a11: float, b0: float, b1: float) -> tuple[float, float]:
    det = a00 * a11 - a01 * a01
    if abs(det) < 1e-20:
        raise ValueError("singular linear fit")
    return ((b0 * a11 - b1 * a01) / det, (a00 * b1 - a01 * b0) / det)


def linear_fit(points: list[tuple[float, float]]) -> dict:
    n = float(len(points))
    sx = sum(x for x, _ in points)
    sy = sum(y for _, y in points)
    sxx = sum(x * x for x, _ in points)
    sxy = sum(x * y for x, y in points)
    intercept, slope = solve2(n, sx, sxx, sy, sxy)
    residuals = [y - (intercept + slope * x) for x, y in points]
    return {
        "intercept_ev": intercept,
        "slope_ev_per_atom": slope,
        "rms_residual_mev": 1000.0 * math.sqrt(sum(r * r for r in residuals) / len(residuals)),
    }


def load_bulk(handoff_path: Path, result_path: Path) -> dict:
    handoff_bytes = handoff_path.read_bytes()
    handoff = json.loads(handoff_bytes)
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    if handoff.get("schema") != "na-cu001-bulk-to-slab-handoff-v0.3":
        raise SystemExit("HOLD: unsupported bulk handoff schema")
    if handoff.get("scientific_status") != "bulk_convergence_passed_slab_not_yet_run":
        raise SystemExit("HOLD: bulk handoff is not a published PASS handoff")
    source = handoff.get("source_result") or {}
    if source.get("sha256") != hashlib.sha256(result_bytes).hexdigest():
        raise SystemExit("HOLD: bulk result hash disagrees with handoff")
    if result.get("gate") != "PASS" or not result.get("recommended_smallest"):
        raise SystemExit("HOLD: source bulk result is not PASS")
    selected_result = result["recommended_smallest"]
    selected_handoff = handoff.get("selected_bulk_settings") or {}
    required = [
        "ecutwfc_ry", "ecutrho_ry", "kmesh_cubic",
        "equilibrium_lattice_constant_angstrom", "equilibrium_energy_ev_per_atom",
    ]
    missing = [k for k in required if selected_handoff.get(k) is None]
    if missing:
        raise SystemExit(f"HOLD: bulk handoff missing {missing}")
    kcube = selected_handoff["kmesh_cubic"]
    if not isinstance(kcube, list) or len(kcube) != 3 or len(set(kcube)) != 1:
        raise SystemExit("HOLD: invalid cubic bulk k mesh")
    fit = selected_result.get("fit") or {}
    comparisons = {
        "ecutwfc": (int(selected_handoff["ecutwfc_ry"]), int(selected_result["ecutwfc_ry"])),
        "ecutrho": (int(selected_handoff["ecutrho_ry"]), int(selected_result["ecutrho_ry"])),
        "kmesh": (int(kcube[0]), int(selected_result["kmesh"])),
    }
    for name, (a, b) in comparisons.items():
        if a != b:
            raise SystemExit(f"HOLD: {name} disagreement between handoff and source result")
    a0 = float(selected_handoff["equilibrium_lattice_constant_angstrom"])
    e0 = float(selected_handoff["equilibrium_energy_ev_per_atom"])
    if abs(a0 - float(fit["a0_angstrom"])) > 1e-10 or abs(e0 - float(fit["e0_ev_per_atom"])) > 1e-10:
        raise SystemExit("HOLD: fitted bulk values disagree between handoff and source result")
    ref = result["reference"]
    delta_a = abs(a0 - float(ref["fit"]["a0_angstrom"]))
    delta_e = abs(e0 - float(ref["fit"]["e0_ev_per_atom"]))
    bulk_gate = {
        "delta_a_from_reference_angstrom": delta_a,
        "delta_e_from_reference_ev_per_atom": delta_e,
        "required_delta_a_max_angstrom": 0.005,
        "required_delta_e_max_ev_per_atom": 0.001,
        "pass": delta_a <= 0.005 and delta_e <= 0.001,
    }
    if not bulk_gate["pass"]:
        raise SystemExit("HOLD: selected bulk pair fails the registered joint lattice-and-energy criterion")
    return {
        "a0_angstrom": a0,
        "e0_ev_per_atom": e0,
        "ecutwfc_ry": int(selected_handoff["ecutwfc_ry"]),
        "ecutrho_ry": int(selected_handoff["ecutrho_ry"]),
        "bulk_kmesh": int(kcube[0]),
        "bulk_gate_revalidation": bulk_gate,
        "handoff_sha256": hashlib.sha256(handoff_bytes).hexdigest(),
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
    }


def registered_kmeshes(bulk_kmesh: int) -> list[int]:
    equivalent = int(math.ceil(math.sqrt(2.0) * bulk_kmesh))
    if equivalent % 2:
        equivalent += 1
    return sorted({max(4, equivalent + d) for d in (-4, -2, 0, 2)})


def fcc001_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[tuple[float, float, float]], float, float]:
    if layers not in LAYERS:
        raise ValueError(f"layers must be one of {LAYERS}")
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    z0 = 0.5 * (cell_z - slab_height)
    atoms = []
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        atoms.append((shift, shift, (z0 + layer * dz) / cell_z))
    area = a0 * a0 / 2.0
    return atoms, cell_z, area


def qe_input(*, bulk: dict, layers: int, vacuum: float, kmesh: int, pseudo_dir: Path, outdir: Path, tag: str) -> str:
    atoms, cell_z, _ = fcc001_geometry(bulk["a0_angstrom"], layers, vacuum)
    h = bulk["a0_angstrom"] / 2.0
    lines = [
        "&CONTROL", "  calculation = 'scf',", f"  prefix = '{tag}',",
        f"  pseudo_dir = '{pseudo_dir}',", f"  outdir = '{outdir}',",
        "  tprnfor = .true.,", "  tstress = .true.,", "  verbosity = 'high',", "/",
        "&SYSTEM", "  ibrav = 0,", f"  nat = {len(atoms)},", "  ntyp = 1,",
        f"  ecutwfc = {bulk['ecutwfc_ry']},", f"  ecutrho = {bulk['ecutrho_ry']},",
        "  occupations = 'smearing',", "  smearing = 'mv',", "  degauss = 0.02,",
        "  nosym = .true.,", "  assume_isolated = 'esm',", "  esm_bc = 'bc1',", "/",
        "&ELECTRONS", "  conv_thr = 1.0d-10,", "  mixing_beta = 0.3,",
        "  electron_maxstep = 250,", "/", "ATOMIC_SPECIES",
        f"Cu 63.54600000 {PSEUDO_NAME}", "CELL_PARAMETERS angstrom",
        f" {h:.12f} {h:.12f} 0.0", f" {-h:.12f} {h:.12f} 0.0", f" 0.0 0.0 {cell_z:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in atoms)
    lines.extend(["K_POINTS automatic", f"{kmesh} {kmesh} 1 0 0 0"])
    return "\n".join(lines) + "\n"


def run_case(args: argparse.Namespace) -> None:
    handoff_path = Path(args.handoff).resolve()
    result_path = Path(args.bulk_result).resolve()
    bulk = load_bulk(handoff_path, result_path)
    allowed_k = registered_kmeshes(bulk["bulk_kmesh"])
    if args.layers not in LAYERS or args.vacuum not in VACUUM or args.kmesh not in allowed_k:
        raise SystemExit(f"HOLD: unregistered slab case; allowed layers={LAYERS}, vacuum={VACUUM}, kmesh={allowed_k}")
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve(); pseudo = pseudo_dir / PSEUDO_NAME
    pw = Path(args.pw).resolve()
    if not pw.exists() or not pseudo.exists():
        raise SystemExit("HOLD: pw.x or pseudopotential missing")
    tag = f"cu001_L{args.layers}_V{args.vacuum:g}_K{args.kmesh}"
    job = out / tag; job.mkdir(exist_ok=True)
    inp = job / f"{tag}.in"; stdout = job / f"{tag}.out"; tmp = job / "tmp"; tmp.mkdir(exist_ok=True)
    inp.write_text(qe_input(bulk=bulk, layers=args.layers, vacuum=args.vacuum,
                            kmesh=args.kmesh, pseudo_dir=pseudo_dir, outdir=tmp, tag=tag))
    cmd = ["mpirun", "-np", str(args.np), str(pw)] if args.np > 1 else [str(pw)]
    start = time.time()
    with inp.open("rb") as fi, stdout.open("wb") as fo:
        proc = subprocess.run(cmd, stdin=fi, stdout=fo, stderr=subprocess.STDOUT)
    text = stdout.read_text(errors="replace")
    energies = [float(x) for x in ENERGY_RE.findall(text)]
    _, cell_z, area = fcc001_geometry(bulk["a0_angstrom"], args.layers, args.vacuum)
    energy_ev = energies[-1] * RY_TO_EV if energies else None
    record = {
        "schema": "na-cu001-clean-slab-case-v0.3", "tag": tag,
        "electrostatic_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
        "layers": args.layers, "nat": args.layers, "vacuum_angstrom": args.vacuum,
        "cell_z_angstrom": cell_z, "kmesh_inplane": args.kmesh,
        "area_angstrom2": area, **bulk,
        "returncode": proc.returncode, "job_done": "JOB DONE." in text,
        "scf_converged": "convergence has been achieved" in text.lower(),
        "final_energy_ry": energies[-1] if energies else None,
        "final_energy_ev": energy_ev,
        "bulk_referenced_surface_excess_ev_per_surface_atom":
            (energy_ev - args.layers * bulk["e0_ev_per_atom"]) / 2.0 if energy_ev is not None else None,
        "elapsed_s": time.time() - start, "input_sha256": sha256(inp),
        "output_sha256": sha256(stdout), "pseudo_sha256": sha256(pseudo), "command": cmd,
    }
    (job / "run_record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    if proc.returncode or not record["job_done"] or not record["scf_converged"] or energy_ev is None:
        raise SystemExit(f"HOLD: QE failure for {tag}")


def analyze(args: argparse.Namespace) -> None:
    root = Path(args.records).resolve()
    rows = [json.loads(p.read_text()) for p in root.rglob("run_record.json")]
    if not rows:
        raise SystemExit("HOLD: no slab records")
    bulk_k = int(rows[0]["bulk_kmesh"])
    kmeshes = registered_kmeshes(bulk_k)
    expected = {(l, v, k) for l in LAYERS for v in VACUUM for k in kmeshes}
    found = {(int(r["layers"]), float(r["vacuum_angstrom"]), int(r["kmesh_inplane"])) for r in rows}
    if found != expected:
        raise SystemExit(f"HOLD: expected {len(expected)} cases, found {len(found)}")
    if any(r.get("schema") != "na-cu001-clean-slab-case-v0.3" for r in rows):
        raise SystemExit("HOLD: mixed or unsupported slab record schema")
    if any(not r.get("scf_converged") or not r.get("job_done") or r.get("returncode") != 0 for r in rows):
        raise SystemExit("HOLD: one or more slab SCFs did not converge")
    invariant = (rows[0]["a0_angstrom"], rows[0]["e0_ev_per_atom"], rows[0]["ecutwfc_ry"],
                 rows[0]["ecutrho_ry"], rows[0]["handoff_sha256"], rows[0]["result_sha256"],
                 json.dumps(rows[0].get("electrostatic_convention"), sort_keys=True))
    for r in rows:
        check = (r["a0_angstrom"], r["e0_ev_per_atom"], r["ecutwfc_ry"], r["ecutrho_ry"],
                 r["handoff_sha256"], r["result_sha256"], json.dumps(r.get("electrostatic_convention"), sort_keys=True))
        if check != invariant:
            raise SystemExit("HOLD: slab records do not share one frozen bulk provenance")
    fits = []
    by_key = {(int(r["layers"]), float(r["vacuum_angstrom"]), int(r["kmesh_inplane"])): r for r in rows}
    for v in VACUUM:
        for k in kmeshes:
            points = [(float(l), float(by_key[(l, v, k)]["final_energy_ev"])) for l in LAYERS]
            fit = linear_fit(points)
            fits.append({
                "vacuum_angstrom": v,
                "kmesh_inplane": k,
                "surface_excess_ev_per_surface_atom": fit["intercept_ev"] / 2.0,
                "fitted_slab_bulk_energy_ev_per_atom": fit["slope_ev_per_atom"],
                "independent_bulk_energy_ev_per_atom": rows[0]["e0_ev_per_atom"],
                "slope_difference_mev_per_atom": 1000.0 * abs(fit["slope_ev_per_atom"] - rows[0]["e0_ev_per_atom"]),
                "fit_rms_residual_mev": fit["rms_residual_mev"],
            })
    fit_map = {(f["vacuum_angstrom"], f["kmesh_inplane"]): f for f in fits}
    accepted_vk = []
    for v in VACUUM:
        for k in kmeshes:
            value = fit_map[(v, k)]["surface_excess_ev_per_surface_atom"]
            dominating = [fit_map[(vv, kk)]["surface_excess_ev_per_surface_atom"]
                          for vv in VACUUM if vv >= v for kk in kmeshes if kk >= k]
            worst = max(abs(value - x) * 1000.0 for x in dominating)
            fit_map[(v, k)]["worst_dominating_difference_mev_per_surface_atom"] = worst
            if worst <= ENERGY_TOL_MEV:
                accepted_vk.append((v, k))
    accepted_vk.sort()
    selected_vk = accepted_vk[0] if accepted_vk else None
    layer_diagnostics = []
    selected_layers = []
    if selected_vk:
        v, k = selected_vk
        for l in LAYERS:
            value = by_key[(l, v, k)]["bulk_referenced_surface_excess_ev_per_surface_atom"]
            thicker = [by_key[(ll, v, k)]["bulk_referenced_surface_excess_ev_per_surface_atom"] for ll in LAYERS if ll >= l]
            worst = max(abs(value - x) * 1000.0 for x in thicker)
            layer_diagnostics.append({"layers": l, "worst_thicker_difference_mev_per_surface_atom": worst})
            if worst <= ENERGY_TOL_MEV:
                selected_layers.append(l)
    selected = None
    if selected_vk and selected_layers:
        selected = {
            "layers": min(selected_layers),
            "vacuum_angstrom": selected_vk[0],
            "kmesh_inplane": selected_vk[1],
            "source_record": by_key[(min(selected_layers), selected_vk[0], selected_vk[1])],
        }
    result = {
        "schema": "na-cu001-clean-slab-selection-v0.3",
        "registration_status": "preregistered_clean_surface_no_na",
        "bulk_provenance": {
            "handoff_sha256": rows[0]["handoff_sha256"],
            "result_sha256": rows[0]["result_sha256"],
            "bulk_gate_revalidation": rows[0]["bulk_gate_revalidation"],
        },
        "registered_grid": {"layers": LAYERS, "vacuum_angstrom": VACUUM, "kmesh_inplane": kmeshes},
        "energy_tolerance_mev_per_surface_atom": ENERGY_TOL_MEV,
        "electrostatic_convention": {"assume_isolated": "esm", "esm_bc": "bc1", "applied_to_all_64_cases": True},
        "surface_fit_diagnostics": sorted(fits, key=lambda f: (f["vacuum_angstrom"], f["kmesh_inplane"])),
        "layer_diagnostics_at_selected_vacuum_kmesh": layer_diagnostics,
        "recommended_smallest": selected,
        "gate": "PASS" if selected else "HOLD",
        "next_gate": "clean_surface_relaxation",
    }
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not selected:
        raise SystemExit(2)


def main() -> None:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--layers", type=int, required=True); run.add_argument("--vacuum", type=float, required=True)
    run.add_argument("--kmesh", type=int, required=True); run.add_argument("--handoff", required=True)
    run.add_argument("--bulk-result", required=True); run.add_argument("--pw", required=True)
    run.add_argument("--pseudo-dir", required=True); run.add_argument("--out", required=True)
    run.add_argument("--np", type=int, default=2)
    ana = sub.add_parser("analyze"); ana.add_argument("--records", required=True); ana.add_argument("--out", required=True)
    args = p.parse_args(); run_case(args) if args.command == "run" else analyze(args)


if __name__ == "__main__":
    main()
