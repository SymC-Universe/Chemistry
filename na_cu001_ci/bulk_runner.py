#!/usr/bin/env python3
"""Prospective Cu bulk convergence runner for Na/Cu(001) joined closure.

Construction-only: contains no Na/Cu(001) experimental kinetic targets.
Uses the locked v0.2 grid: six lattice constants, five cutoffs, four k meshes,
PBE, SSSP v2 PBE-efficiency Cu PAW, ecutrho=3*ecutwfc, MV smearing 0.02 Ry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

RY_TO_EV = 13.605693122994
LATTICES = [3.55, 3.58, 3.61, 3.64, 3.67, 3.70]
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
PSEUDO_NAME = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def qe_input(a: float, ecut: int, kmesh: int, pseudo_dir: Path, outdir: Path) -> str:
    positions = [
        (0.0, 0.0, 0.0),
        (0.0, 0.5, 0.5),
        (0.5, 0.0, 0.5),
        (0.5, 0.5, 0.0),
    ]
    lines = [
        "&CONTROL",
        "  calculation = 'scf',",
        f"  prefix = 'bulk_a{a:.3f}_e{ecut}_k{kmesh}',",
        f"  pseudo_dir = '{pseudo_dir}',",
        f"  outdir = '{outdir}',",
        "  tprnfor = .true.,",
        "  tstress = .true.,",
        "  verbosity = 'high',",
        "/",
        "&SYSTEM",
        "  ibrav = 0,",
        "  nat = 4,",
        "  ntyp = 1,",
        f"  ecutwfc = {ecut},",
        f"  ecutrho = {3 * ecut},",
        "  occupations = 'smearing',",
        "  smearing = 'mv',",
        "  degauss = 0.02,",
        "/",
        "&ELECTRONS",
        "  conv_thr = 1.0d-10,",
        "  mixing_beta = 0.3,",
        "  electron_maxstep = 200,",
        "/",
        "ATOMIC_SPECIES",
        f"Cu 63.54600000 {PSEUDO_NAME}",
        "CELL_PARAMETERS angstrom",
        f" {a:.12f} 0.0 0.0",
        f" 0.0 {a:.12f} 0.0",
        f" 0.0 0.0 {a:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in positions)
    lines.extend([
        "K_POINTS automatic",
        f"{kmesh} {kmesh} {kmesh} 0 0 0",
    ])
    return "\n".join(lines) + "\n"


def run_grid(args: argparse.Namespace) -> None:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo = pseudo_dir / PSEUDO_NAME
    pw = Path(args.pw).resolve()
    if not pw.exists():
        raise SystemExit(f"pw.x missing: {pw}")
    if not pseudo.exists():
        raise SystemExit(f"pseudopotential missing: {pseudo}")
    records = []
    env = dict(os.environ)
    env.setdefault("OMP_NUM_THREADS", "1")
    for a in LATTICES:
        tag = f"bulk_a{a:.3f}_e{args.ecut}_k{args.kmesh}"
        job = out / tag
        job.mkdir(exist_ok=True)
        inp = job / f"{tag}.in"
        stdout = job / f"{tag}.out"
        tmp = job / "tmp"
        tmp.mkdir(exist_ok=True)
        inp.write_text(qe_input(a, args.ecut, args.kmesh, pseudo_dir, tmp))
        cmd = ["mpirun", "-np", str(args.np), str(pw)] if args.np > 1 else [str(pw)]
        start = time.time()
        with inp.open("rb") as fi, stdout.open("wb") as fo:
            proc = subprocess.run(cmd, stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        text = stdout.read_text(errors="replace")
        energies = [float(x) for x in ENERGY_RE.findall(text)]
        record = {
            "tag": tag,
            "a_angstrom": a,
            "ecutwfc_ry": args.ecut,
            "ecutrho_ry": 3 * args.ecut,
            "kmesh": args.kmesh,
            "returncode": proc.returncode,
            "job_done": "JOB DONE." in text,
            "scf_converged": "convergence has been achieved" in text.lower(),
            "final_energy_ry": energies[-1] if energies else None,
            "final_energy_ev_per_atom": energies[-1] * RY_TO_EV / 4.0 if energies else None,
            "elapsed_s": time.time() - start,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(stdout),
            "pseudo_sha256": sha256(pseudo),
            "command": cmd,
        }
        (job / "run_record.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)
        print(json.dumps(record), flush=True)
        if proc.returncode != 0 or not record["job_done"] or record["final_energy_ry"] is None:
            raise SystemExit(f"HOLD: QE failure for {tag}")
    summary = {
        "schema": "na-cu001-bulk-matrix-v0.2",
        "registration_status": "construction_only_no_kinetic_targets",
        "qe_version_requested": "7.6",
        "xc": "PBE",
        "pseudopotential": PSEUDO_NAME,
        "pseudopotential_sha256": sha256(pseudo),
        "ecutwfc_ry": args.ecut,
        "ecutrho_ry": 3 * args.ecut,
        "kmesh": args.kmesh,
        "records": records,
    }
    path = out / f"summary_e{args.ecut}_k{args.kmesh}.json"
    path.write_text(json.dumps(summary, indent=2) + "\n")
    print(path)


def solve3(a: list[list[float]], b: list[float]) -> list[float]:
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-20:
            raise ValueError("singular quadratic fit")
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        m[col] = [x / p for x in m[col]]
        for r in range(3):
            if r == col:
                continue
            f = m[r][col]
            m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][3] for i in range(3)]


def quadratic_fit(points: list[tuple[float, float]]) -> dict:
    n = float(len(points))
    sx = sum(x for x, _ in points)
    sx2 = sum(x*x for x, _ in points)
    sx3 = sum(x*x*x for x, _ in points)
    sx4 = sum(x*x*x*x for x, _ in points)
    sy = sum(y for _, y in points)
    sxy = sum(x*y for x, y in points)
    sx2y = sum(x*x*y for x, y in points)
    c0, c1, c2 = solve3(
        [[n, sx, sx2], [sx, sx2, sx3], [sx2, sx3, sx4]],
        [sy, sxy, sx2y],
    )
    if c2 <= 0:
        raise ValueError("non-convex energy-volume fit")
    a0 = -c1 / (2.0 * c2)
    e0 = c0 + c1 * a0 + c2 * a0 * a0
    residuals = [y - (c0 + c1*x + c2*x*x) for x, y in points]
    return {
        "a0_angstrom": a0,
        "e0_ev_per_atom": e0,
        "coefficients_constant_linear_quadratic": [c0, c1, c2],
        "rms_residual_mev_per_atom": 1000.0 * math.sqrt(sum(r*r for r in residuals) / len(residuals)),
    }


def analyze(args: argparse.Namespace) -> None:
    root = Path(args.summaries).resolve()
    rows = []
    for path in root.rglob("summary_e*_k*.json"):
        data = json.loads(path.read_text())
        pts = [(float(r["a_angstrom"]), float(r["final_energy_ev_per_atom"])) for r in data["records"]]
        fit = quadratic_fit(sorted(pts))
        rows.append({
            "ecutwfc_ry": int(data["ecutwfc_ry"]),
            "ecutrho_ry": int(data["ecutrho_ry"]),
            "kmesh": int(data["kmesh"]),
            "fit": fit,
            "source_summary": str(path),
            "source_sha256": sha256(path),
        })
    if len(rows) != 20:
        raise SystemExit(f"HOLD: expected 20 completed matrix summaries, found {len(rows)}")
    rows.sort(key=lambda r: (r["ecutwfc_ry"], r["kmesh"]))
    ref = next(r for r in rows if r["ecutwfc_ry"] == 70 and r["kmesh"] == 14)
    for r in rows:
        r["delta_a_from_reference_angstrom"] = abs(r["fit"]["a0_angstrom"] - ref["fit"]["a0_angstrom"])
    admitted = [r for r in rows if r["delta_a_from_reference_angstrom"] <= 0.005]
    selection = admitted[0] if admitted else None
    result = {
        "schema": "na-cu001-bulk-selection-v0.2",
        "registration_status": "construction_only_no_kinetic_targets",
        "reference": ref,
        "candidates": rows,
        "selection_rule": "smallest (ecutwfc,kmesh) with |a0-a0_ref| <= 0.005 A",
        "recommended_smallest": selection,
        "gate": "PASS" if selection else "HOLD",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not selection:
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--ecut", type=int, required=True)
    run.add_argument("--kmesh", type=int, required=True)
    run.add_argument("--pw", required=True)
    run.add_argument("--pseudo-dir", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--np", type=int, default=2)
    ana = sub.add_parser("analyze")
    ana.add_argument("--summaries", required=True)
    ana.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "run":
        run_grid(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
