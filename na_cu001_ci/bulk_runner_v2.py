#!/usr/bin/env python3
"""Prospective Cu bulk convergence and holdout validation for Na/Cu(001).

The production selector is joint and fail-closed. A candidate is admitted only
when both its equilibrium lattice constant and equilibrium energy agree with an
independently registered higher-cost reference. The original 120-SCF matrix is
reused; the holdout adds only the six EOS points at 80 Ry / 16^3.
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
import time
from typing import Any

RY_TO_EV = 13.605693122994
LATTICES = [3.55, 3.58, 3.61, 3.64, 3.67, 3.70]
REGISTERED_ECUTS = [50, 55, 60, 65, 70]
REGISTERED_KMESHES = [8, 10, 12, 14]
HOLDOUT_ECUT = 80
HOLDOUT_KMESH = 16
DELTA_A_MAX_ANGSTROM = 0.005
DELTA_E_MAX_EV_PER_ATOM = 0.001
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
PSEUDO_NAME = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def qe_input(a: float, ecut: int, kmesh: int, pseudo_dir: Path, outdir: Path) -> str:
    positions = [(0.0, 0.0, 0.0), (0.0, 0.5, 0.5), (0.5, 0.0, 0.5), (0.5, 0.5, 0.0)]
    lines = [
        "&CONTROL", "  calculation = 'scf',",
        f"  prefix = 'bulk_a{a:.3f}_e{ecut}_k{kmesh}',",
        f"  pseudo_dir = '{pseudo_dir}',", f"  outdir = '{outdir}',",
        "  tprnfor = .true.,", "  tstress = .true.,", "  verbosity = 'high',", "/",
        "&SYSTEM", "  ibrav = 0,", "  nat = 4,", "  ntyp = 1,",
        f"  ecutwfc = {ecut},", f"  ecutrho = {3 * ecut},",
        "  occupations = 'smearing',", "  smearing = 'mv',", "  degauss = 0.02,", "/",
        "&ELECTRONS", "  conv_thr = 1.0d-10,", "  mixing_beta = 0.3,",
        "  electron_maxstep = 200,", "/", "ATOMIC_SPECIES",
        f"Cu 63.54600000 {PSEUDO_NAME}", "CELL_PARAMETERS angstrom",
        f" {a:.12f} 0.0 0.0", f" 0.0 {a:.12f} 0.0", f" 0.0 0.0 {a:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in positions)
    lines.extend(["K_POINTS automatic", f"{kmesh} {kmesh} {kmesh} 0 0 0"])
    return "\n".join(lines) + "\n"


def run_grid(args: argparse.Namespace) -> None:
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    pseudo_dir = Path(args.pseudo_dir).resolve(); pseudo = pseudo_dir / PSEUDO_NAME
    pw = Path(args.pw).resolve()
    if not pw.exists() or not pseudo.exists():
        raise SystemExit("HOLD: pw.x or Cu pseudopotential missing")
    records: list[dict[str, Any]] = []
    env = dict(os.environ); env.setdefault("OMP_NUM_THREADS", "1")
    for a in LATTICES:
        tag = f"bulk_a{a:.3f}_e{args.ecut}_k{args.kmesh}"
        job = out / tag; job.mkdir(exist_ok=True)
        inp = job / f"{tag}.in"; stdout = job / f"{tag}.out"; tmp = job / "tmp"; tmp.mkdir(exist_ok=True)
        inp.write_text(qe_input(a, args.ecut, args.kmesh, pseudo_dir, tmp))
        cmd = ["mpirun", "-np", str(args.np), str(pw)] if args.np > 1 else [str(pw)]
        start = time.time()
        with inp.open("rb") as fi, stdout.open("wb") as fo:
            proc = subprocess.run(cmd, stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        text = stdout.read_text(errors="replace")
        energies = [float(x) for x in ENERGY_RE.findall(text)]
        record = {
            "tag": tag, "a_angstrom": a, "ecutwfc_ry": args.ecut,
            "ecutrho_ry": 3 * args.ecut, "kmesh": args.kmesh,
            "returncode": proc.returncode, "job_done": "JOB DONE." in text,
            "scf_converged": "convergence has been achieved" in text.lower(),
            "final_energy_ry": energies[-1] if energies else None,
            "final_energy_ev_per_atom": energies[-1] * RY_TO_EV / 4.0 if energies else None,
            "elapsed_s": time.time() - start, "input_sha256": sha256(inp),
            "output_sha256": sha256(stdout), "pseudo_sha256": sha256(pseudo), "command": cmd,
        }
        (job / "run_record.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record); print(json.dumps(record), flush=True)
        if proc.returncode != 0 or not record["job_done"] or not record["scf_converged"] or record["final_energy_ry"] is None:
            raise SystemExit(f"HOLD: QE failure or unconverged SCF for {tag}")
    summary = {
        "schema": "na-cu001-bulk-matrix-v0.3",
        "registration_status": "construction_only_no_kinetic_targets",
        "qe_version_requested": "7.6", "xc": "PBE",
        "pseudopotential": PSEUDO_NAME, "pseudopotential_sha256": sha256(pseudo),
        "ecutwfc_ry": args.ecut, "ecutrho_ry": 3 * args.ecut,
        "kmesh": args.kmesh, "lattice_grid_angstrom": LATTICES, "records": records,
    }
    path = out / f"summary_e{args.ecut}_k{args.kmesh}.json"
    path.write_text(json.dumps(summary, indent=2) + "\n"); print(path)


def solve3(a: list[list[float]], b: list[float]) -> list[float]:
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-20:
            raise ValueError("singular quadratic fit")
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]; m[col] = [x / p for x in m[col]]
        for r in range(3):
            if r == col: continue
            f = m[r][col]; m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][3] for i in range(3)]


def quadratic_fit(points: list[tuple[float, float]]) -> dict[str, Any]:
    n = float(len(points)); sx = sum(x for x, _ in points); sx2 = sum(x*x for x, _ in points)
    sx3 = sum(x*x*x for x, _ in points); sx4 = sum(x*x*x*x for x, _ in points)
    sy = sum(y for _, y in points); sxy = sum(x*y for x, y in points); sx2y = sum(x*x*y for x, y in points)
    c0, c1, c2 = solve3([[n, sx, sx2], [sx, sx2, sx3], [sx2, sx3, sx4]], [sy, sxy, sx2y])
    if c2 <= 0: raise ValueError("non-convex energy-lattice fit")
    a0 = -c1 / (2.0 * c2); e0 = c0 + c1 * a0 + c2 * a0 * a0
    residuals = [y - (c0 + c1*x + c2*x*x) for x, y in points]
    return {"a0_angstrom": a0, "e0_ev_per_atom": e0,
            "coefficients_constant_linear_quadratic": [c0, c1, c2],
            "rms_residual_mev_per_atom": 1000.0 * math.sqrt(sum(r*r for r in residuals) / len(residuals))}


def load_fit_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("summary_e*_k*.json")):
        data = json.loads(path.read_text())
        records = data.get("records") or []
        if len(records) != len(LATTICES):
            raise SystemExit(f"HOLD: incomplete EOS summary {path}")
        if not all(r.get("returncode") == 0 and r.get("job_done") and r.get("scf_converged") and r.get("final_energy_ev_per_atom") is not None for r in records):
            raise SystemExit(f"HOLD: failed or unconverged record in {path}")
        points = sorted((float(r["a_angstrom"]), float(r["final_energy_ev_per_atom"])) for r in records)
        rows.append({"ecutwfc_ry": int(data["ecutwfc_ry"]), "ecutrho_ry": int(data["ecutrho_ry"]),
                     "kmesh": int(data["kmesh"]), "fit": quadratic_fit(points),
                     "source_summary": f"bulk_summaries/{path.name}", "source_sha256": sha256(path)})
    rows.sort(key=lambda r: (r["ecutwfc_ry"], r["kmesh"]))
    return rows


def analyze(args: argparse.Namespace) -> None:
    root = Path(args.summaries).resolve(); rows = load_fit_rows(root)
    ref_ecut = int(args.reference_ecut); ref_kmesh = int(args.reference_kmesh)
    ref_matches = [r for r in rows if r["ecutwfc_ry"] == ref_ecut and r["kmesh"] == ref_kmesh]
    if len(ref_matches) != 1:
        raise SystemExit(f"HOLD: expected one reference {ref_ecut} Ry/{ref_kmesh}^3, found {len(ref_matches)}")
    ref = ref_matches[0]
    candidates = [r for r in rows if r["ecutwfc_ry"] in REGISTERED_ECUTS and r["kmesh"] in REGISTERED_KMESHES]
    expected = len(REGISTERED_ECUTS) * len(REGISTERED_KMESHES)
    if len(candidates) != expected:
        raise SystemExit(f"HOLD: expected {expected} registered candidates, found {len(candidates)}")
    for r in rows:
        da = abs(r["fit"]["a0_angstrom"] - ref["fit"]["a0_angstrom"])
        de = abs(r["fit"]["e0_ev_per_atom"] - ref["fit"]["e0_ev_per_atom"])
        r["delta_a_from_reference_angstrom"] = da
        r["delta_e_from_reference_ev_per_atom"] = de
        r["joint_gate"] = {
            "delta_a_pass": da <= DELTA_A_MAX_ANGSTROM,
            "delta_e_pass": de <= DELTA_E_MAX_EV_PER_ATOM,
            "pass": da <= DELTA_A_MAX_ANGSTROM and de <= DELTA_E_MAX_EV_PER_ATOM,
        }
    admitted = [r for r in candidates if r["joint_gate"]["pass"]]
    selection = sorted(admitted, key=lambda r: (r["ecutwfc_ry"], r["kmesh"]))[0] if admitted else None
    result = {
        "schema": "na-cu001-bulk-selection-v0.3",
        "registration_status": "construction_only_no_kinetic_targets",
        "reference_interpretation": "converged relative to the separately executed higher-cost holdout EOS; not an absolute complete-basis proof",
        "reference": ref, "candidates": rows,
        "joint_criteria": {"delta_a_max_angstrom": DELTA_A_MAX_ANGSTROM,
                           "delta_e_max_ev_per_atom": DELTA_E_MAX_EV_PER_ATOM},
        "selection_rule": "smallest registered (ecutwfc,kmesh) satisfying both |delta a0| <= 0.005 A and |delta E0| <= 0.001 eV/atom against the 80 Ry/16^3 holdout",
        "recommended_smallest": selection, "gate": "PASS" if selection else "HOLD",
    }
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n"); print(json.dumps(result, indent=2))
    if not selection: raise SystemExit(2)


def make_handoff(args: argparse.Namespace) -> None:
    result_path = Path(args.result).resolve(); result_bytes = result_path.read_bytes(); result = json.loads(result_bytes)
    if result.get("schema") != "na-cu001-bulk-selection-v0.3" or result.get("gate") != "PASS":
        raise SystemExit("HOLD: source bulk result is not v0.3 PASS")
    selected = result["recommended_smallest"]; fit = selected["fit"]
    handoff = {
        "schema": "na-cu001-bulk-to-slab-handoff-v0.3",
        "scientific_status": "bulk_convergence_passed_slab_not_yet_run",
        "source_result": {"path": result_path.name, "sha256": hashlib.sha256(result_bytes).hexdigest(),
                          "selection_rule": result["selection_rule"]},
        "input_artifacts": ([{"path": result_path.name, "sha256": hashlib.sha256(result_bytes).hexdigest()}] +
            [{"path": row["source_summary"], "sha256": row["source_sha256"]} for row in result["candidates"]]),
        "selected_bulk_settings": {
            "ecutwfc_ry": selected["ecutwfc_ry"], "ecutrho_ry": selected["ecutrho_ry"],
            "kmesh_cubic": [selected["kmesh"]] * 3,
            "equilibrium_lattice_constant_angstrom": fit["a0_angstrom"],
            "equilibrium_energy_ev_per_atom": fit["e0_ev_per_atom"],
            "quadratic_fit_rms_residual_mev_per_atom": fit["rms_residual_mev_per_atom"],
        },
        "joint_gate": selected["joint_gate"],
        "reference_settings": {"ecutwfc_ry": result["reference"]["ecutwfc_ry"],
                               "ecutrho_ry": result["reference"]["ecutrho_ry"],
                               "kmesh_cubic": [result["reference"]["kmesh"]] * 3,
                               "interpretation": result["reference_interpretation"]},
        "frozen_method": {"code": "Quantum ESPRESSO PWscf", "code_version": "7.6",
                          "exchange_correlation": "PBE", "pseudopotential": PSEUDO_NAME,
                          "ecutrho_multiplier": 3, "occupations": "smearing", "smearing": "mv",
                          "degauss_ry": 0.02, "bulk_lattice_grid_angstrom": LATTICES,
                          "candidate_cutoff_grid_ry": REGISTERED_ECUTS,
                          "candidate_kmesh_grid": REGISTERED_KMESHES,
                          "holdout": {"ecutwfc_ry": HOLDOUT_ECUT, "kmesh": HOLDOUT_KMESH}},
        "run_provenance": {"repository": os.environ.get("GITHUB_REPOSITORY"),
                           "workflow": os.environ.get("GITHUB_WORKFLOW"),
                           "run_id": os.environ.get("GITHUB_RUN_ID"),
                           "commit_sha": os.environ.get("GITHUB_SHA"), "ref": os.environ.get("GITHUB_REF")},
        "next_gate": "explicit_preregistered_cu001_slab_convergence",
    }
    out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(handoff, indent=2) + "\n"); print(json.dumps(handoff, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run"); run.add_argument("--ecut", type=int, required=True); run.add_argument("--kmesh", type=int, required=True)
    run.add_argument("--pw", required=True); run.add_argument("--pseudo-dir", required=True); run.add_argument("--out", required=True); run.add_argument("--np", type=int, default=2)
    ana = sub.add_parser("analyze"); ana.add_argument("--summaries", required=True); ana.add_argument("--out", required=True)
    ana.add_argument("--reference-ecut", type=int, default=HOLDOUT_ECUT); ana.add_argument("--reference-kmesh", type=int, default=HOLDOUT_KMESH)
    hand = sub.add_parser("handoff"); hand.add_argument("--result", required=True); hand.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "run": run_grid(args)
    elif args.command == "analyze": analyze(args)
    else: make_handoff(args)


if __name__ == "__main__":
    main()
