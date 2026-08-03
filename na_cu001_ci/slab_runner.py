#!/usr/bin/env python3
"""Preregistered clean Cu(001) slab convergence for Na/Cu(001) closure.

Consumes a verified bulk handoff. It does not contain Na adsorption geometries,
barriers, experimental rates, or post-hoc threshold tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

RY_TO_EV = 13.605693122994
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
PSEUDO_NAME = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_handoff(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("schema") != "na-cu001-bulk-to-slab-handoff-v0.1":
        raise SystemExit("HOLD: unsupported bulk handoff schema")
    if data.get("scientific_status") != "PASS":
        raise SystemExit("HOLD: bulk handoff is not PASS")
    selected = data.get("selected") or {}
    required = ["ecutwfc_ry", "ecutrho_ry", "kmesh_cubic", "a0_angstrom"]
    missing = [key for key in required if selected.get(key) is None]
    if missing:
        raise SystemExit(f"HOLD: bulk handoff missing {missing}")
    return data


def fcc001_atoms(a0: float, layers: int, vacuum: float):
    if layers < 3:
        raise ValueError("layers must be >=3")
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    z0 = 0.5 * (cell_z - slab_height)
    atoms = []
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        atoms.append((shift, shift, (z0 + layer * dz) / cell_z))
    return atoms, cell_z


def qe_input(*, a0, layers, vacuum, kmesh, ecutwfc, ecutrho, pseudo_dir, outdir, tag):
    atoms, cell_z = fcc001_atoms(a0, layers, vacuum)
    lines = [
        "&CONTROL", "  calculation = 'scf',", f"  prefix = '{tag}',",
        f"  pseudo_dir = '{pseudo_dir}',", f"  outdir = '{outdir}',",
        "  tprnfor = .true.,", "  tstress = .true.,", "  verbosity = 'high',", "/",
        "&SYSTEM", "  ibrav = 0,", f"  nat = {len(atoms)},", "  ntyp = 1,",
        f"  ecutwfc = {ecutwfc},", f"  ecutrho = {ecutrho},",
        "  occupations = 'smearing',", "  smearing = 'mv',", "  degauss = 0.02,", "/",
        "&ELECTRONS", "  conv_thr = 1.0d-10,", "  mixing_beta = 0.3,",
        "  electron_maxstep = 250,", "/", "ATOMIC_SPECIES",
        f"Cu 63.54600000 {PSEUDO_NAME}", "CELL_PARAMETERS angstrom",
        f" {a0:.12f} 0.0 0.0", f" 0.0 {a0:.12f} 0.0", f" 0.0 0.0 {cell_z:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in atoms)
    lines.extend(["K_POINTS automatic", f"{kmesh} {kmesh} 1 0 0 0"])
    return "\n".join(lines) + "\n"


def run_case(args):
    handoff_path = Path(args.handoff).resolve()
    handoff = load_handoff(handoff_path)
    selected = handoff["selected"]
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve(); pseudo = pseudo_dir / PSEUDO_NAME
    pw = Path(args.pw).resolve()
    if not pw.exists() or not pseudo.exists():
        raise SystemExit("HOLD: pw.x or pseudopotential missing")
    tag = f"cu001_L{args.layers}_V{args.vacuum:g}_K{args.kmesh}"
    job = out / tag; job.mkdir(exist_ok=True)
    inp = job / f"{tag}.in"; stdout = job / f"{tag}.out"; tmp = job / "tmp"; tmp.mkdir(exist_ok=True)
    inp.write_text(qe_input(a0=float(selected["a0_angstrom"]), layers=args.layers,
                            vacuum=args.vacuum, kmesh=args.kmesh,
                            ecutwfc=int(selected["ecutwfc_ry"]), ecutrho=int(selected["ecutrho_ry"]),
                            pseudo_dir=pseudo_dir, outdir=tmp, tag=tag))
    cmd = ["mpirun", "-np", str(args.np), str(pw)] if args.np > 1 else [str(pw)]
    start = time.time()
    with inp.open("rb") as fi, stdout.open("wb") as fo:
        proc = subprocess.run(cmd, stdin=fi, stdout=fo, stderr=subprocess.STDOUT)
    text = stdout.read_text(errors="replace")
    energies = [float(x) for x in ENERGY_RE.findall(text)]
    area = float(selected["a0_angstrom"]) ** 2
    record = {
        "schema": "na-cu001-clean-slab-case-v0.1", "tag": tag,
        "layers": args.layers, "vacuum_angstrom": args.vacuum,
        "kmesh_inplane": args.kmesh, "area_angstrom2": area,
        "a0_angstrom": float(selected["a0_angstrom"]),
        "ecutwfc_ry": int(selected["ecutwfc_ry"]), "ecutrho_ry": int(selected["ecutrho_ry"]),
        "returncode": proc.returncode, "job_done": "JOB DONE." in text,
        "scf_converged": "convergence has been achieved" in text.lower(),
        "final_energy_ry": energies[-1] if energies else None,
        "final_energy_ev": energies[-1] * RY_TO_EV if energies else None,
        "elapsed_s": time.time() - start, "input_sha256": sha256(inp),
        "output_sha256": sha256(stdout), "pseudo_sha256": sha256(pseudo),
        "bulk_handoff_sha256": sha256(handoff_path), "command": cmd,
    }
    (job / "run_record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    if proc.returncode or not record["job_done"] or record["final_energy_ev"] is None:
        raise SystemExit(f"HOLD: QE failure for {tag}")


def analyze(args):
    root = Path(args.records).resolve()
    rows = [json.loads(p.read_text()) for p in root.rglob("run_record.json")]
    expected = {(l, v, k) for l in args.layers for v in args.vacuum for k in args.kmesh}
    found = {(int(r["layers"]), float(r["vacuum_angstrom"]), int(r["kmesh_inplane"])) for r in rows}
    if found != expected:
        raise SystemExit(f"HOLD: expected {len(expected)} cases, found {len(found)}")
    ref_key = (max(args.layers), max(args.vacuum), max(args.kmesh))
    ref = next(r for r in rows if (r["layers"], r["vacuum_angstrom"], r["kmesh_inplane"]) == ref_key)
    for r in rows:
        r["delta_energy_mev_per_surface_atom"] = abs(r["final_energy_ev"] - ref["final_energy_ev"]) * 1000.0 / 2.0
    admitted = [r for r in rows if r["delta_energy_mev_per_surface_atom"] <= args.energy_tol]
    admitted.sort(key=lambda r: (r["layers"], r["vacuum_angstrom"], r["kmesh_inplane"]))
    result = {
        "schema": "na-cu001-clean-slab-selection-v0.1",
        "registration_status": "preregistered_clean_surface_no_na",
        "reference": ref,
        "selection_rule": f"smallest (layers,vacuum,kmesh) with |E-E_ref|/2 <= {args.energy_tol} meV per surface atom",
        "recommended_smallest": admitted[0] if admitted else None,
        "candidates": sorted(rows, key=lambda r: (r["layers"], r["vacuum_angstrom"], r["kmesh_inplane"])),
        "gate": "PASS" if admitted else "HOLD",
        "next_gate": "clean_surface_relaxation_then_na_adsorption_preregistration",
    }
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not admitted: raise SystemExit(2)


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    for name, typ in [("--layers", int), ("--vacuum", float), ("--kmesh", int)]: run.add_argument(name, type=typ, required=True)
    run.add_argument("--handoff", required=True); run.add_argument("--pw", required=True)
    run.add_argument("--pseudo-dir", required=True); run.add_argument("--out", required=True); run.add_argument("--np", type=int, default=2)
    ana = sub.add_parser("analyze")
    ana.add_argument("--records", required=True); ana.add_argument("--out", required=True)
    ana.add_argument("--layers", nargs="+", type=int, required=True); ana.add_argument("--vacuum", nargs="+", type=float, required=True)
    ana.add_argument("--kmesh", nargs="+", type=int, required=True); ana.add_argument("--energy-tol", type=float, default=1.0)
    a = p.parse_args(); run_case(a) if a.command == "run" else analyze(a)

if __name__ == "__main__": main()
