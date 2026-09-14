#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RY_TO_EV = 13.605693122994
E_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(path: str | Path):
    return json.loads(Path(path).read_text())


def write(path: str | Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def hcp_bulk_input(a, c, ecutwfc, ecutrho, kmesh, pseudo_dir, outdir, prefix):
    kx, ky, kz = kmesh
    return f"""&CONTROL
 calculation='scf',
 prefix='{prefix}',
 pseudo_dir='{pseudo_dir}',
 outdir='{outdir}',
 tprnfor=.true.,
 tstress=.true.,
 verbosity='high',
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=1,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 occupations='smearing',
 smearing='mv',
 degauss=0.02,
/
&ELECTRONS
 conv_thr=1.0d-10,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
Ru 101.07 Ru.nc.pbe.z_16.oncvpsp4.sg15.v0.upf
CELL_PARAMETERS angstrom
{a:.12f} 0.0 0.0
{-0.5*a:.12f} {math.sqrt(3.0)*0.5*a:.12f} 0.0
0.0 0.0 {c:.12f}
ATOMIC_POSITIONS crystal
Ru 0.0 0.0 0.0
Ru 0.666666666666667 0.333333333333333 0.5
K_POINTS automatic
{kx} {ky} {kz} 0 0 0
"""


def slab_geometry(a: float, c: float, layers: int, total_vacuum: float):
    if layers < 3 or layers % 2 != 1:
        raise ValueError("slab layers must be odd and >=3")
    dz = c / 2.0
    slab_thickness = (layers - 1) * dz
    cell_z = slab_thickness + total_vacuum
    rows = []
    mid = (layers - 1) / 2.0
    for j in range(layers):
        if j % 2 == 0:
            x, y = 0.0, 0.0
        else:
            x, y = 2.0 / 3.0, 1.0 / 3.0
        z_ang = (j - mid) * dz
        z_frac = 0.5 + z_ang / cell_z
        rows.append((x, y, z_frac))
    return cell_z, rows


def slab_input(a, c, layers, total_vacuum, ecutwfc, ecutrho, kmesh, pseudo_dir, outdir, prefix):
    kx, ky, kz = kmesh
    cell_z, positions = slab_geometry(a, c, layers, total_vacuum)
    atoms = "\n".join(f"Ru {x:.15f} {y:.15f} {z:.15f}" for x, y, z in positions)
    return f"""&CONTROL
 calculation='scf',
 prefix='{prefix}',
 pseudo_dir='{pseudo_dir}',
 outdir='{outdir}',
 tprnfor=.true.,
 tstress=.true.,
 verbosity='high',
/
&SYSTEM
 ibrav=0,
 nat={layers},
 ntyp=1,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 occupations='smearing',
 smearing='mv',
 degauss=0.02,
/
&ELECTRONS
 conv_thr=1.0d-10,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
Ru 101.07 Ru.nc.pbe.z_16.oncvpsp4.sg15.v0.upf
CELL_PARAMETERS angstrom
{a:.12f} 0.0 0.0
{-0.5*a:.12f} {math.sqrt(3.0)*0.5*a:.12f} 0.0
0.0 0.0 {cell_z:.12f}
ATOMIC_POSITIONS crystal
{atoms}
K_POINTS automatic
{kx} {ky} {kz} 0 0 0
"""


def execute_qe(case_dir: Path, pw: Path, input_text: str, timeout_s: int, tag: str):
    case_dir.mkdir(parents=True, exist_ok=True)
    tmp = case_dir / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = case_dir / "pw.in"
    out = case_dir / "pw.out"
    inp.write_text(input_text.replace("__OUTDIR__", str(tmp.resolve())))
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    start = time.time()
    timed_out = False
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        try:
            rc = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                rc = proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait(timeout=10)
    elapsed = time.time() - start
    text = out.read_text(errors="replace")
    energies = [float(x) * RY_TO_EV for x in E_RE.findall(text)]
    ok = (not timed_out) and rc == 0 and "JOB DONE." in text and bool(energies)
    record = {
        "tag": tag,
        "execution_state": {
            "PLANNED": True,
            "EXECUTED": True,
            "MEASURED": bool(energies),
            "VALID": bool(ok),
            "ADJUDICATED": False
        },
        "return_code": int(rc),
        "timeout": bool(timed_out),
        "job_done": bool("JOB DONE." in text),
        "energy_count": len(energies),
        "elapsed_s": elapsed,
        "input_sha256": sha256(inp),
        "output_sha256": sha256(out)
    }
    if ok:
        record["energy_ev"] = energies[-1]
        shutil.rmtree(tmp, ignore_errors=True)
        return record
    record["mechanical_failure"] = "timeout, nonzero return, missing JOB DONE, or missing total energy"
    raise RuntimeError(json.dumps(record, sort_keys=True))


def suffix_selection(rows, tolerance: float, eligible=lambda row: True):
    ref = rows[-1]["surface_excess_ev_per_surface_atom"]
    deltas = [abs(r["surface_excess_ev_per_surface_atom"] - ref) for r in rows]
    for i in range(0, len(rows) - 1):
        if not eligible(rows[i]):
            continue
        if all(d <= tolerance for d in deltas[i:]):
            return i, deltas
    return None, deltas


def validate_contract(protocol, bulk_protocol, adjudication, pw: Path, ru_pseudo: Path):
    if protocol["status"] != "FROZEN_BEFORE_SYSTEM3_CLEAN_SURFACE_RESULTS":
        raise SystemExit("SCIENTIFIC_HOLD: clean-surface protocol is not frozen")
    if adjudication["status"] != protocol["entry_gate"]["required_bulk_status"]:
        raise SystemExit("SCIENTIFIC_HOLD: required bulk PASS adjudication missing")
    source = adjudication["source"]
    if source["original_run_id"] != protocol["entry_gate"]["required_original_run_id"]:
        raise SystemExit("MECHANICAL_HOLD: bulk source run identity mismatch")
    if source["original_artifact_id"] != protocol["entry_gate"]["required_original_artifact_id"]:
        raise SystemExit("MECHANICAL_HOLD: bulk source artifact identity mismatch")
    if source["original_artifact_digest"] != protocol["entry_gate"]["required_original_artifact_digest"]:
        raise SystemExit("MECHANICAL_HOLD: bulk source artifact digest mismatch")
    if source["recovery_run_id"] != protocol["entry_gate"]["required_recovery_run_id"]:
        raise SystemExit("MECHANICAL_HOLD: bulk recovery identity mismatch")
    if sha256(pw) != bulk_protocol["provenance"]["pw_x_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pw.x hash mismatch")
    if sha256(ru_pseudo) != bulk_protocol["pseudopotentials"]["Ru"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: Ru pseudopotential hash mismatch")
    if protocol["fresh_bulk_reference"]["kmesh"] != bulk_protocol["kmesh_grid"][-1]:
        raise SystemExit("SCIENTIFIC_HOLD: fresh bulk reference is not the frozen bulk-grid endpoint")
    fw = protocol["evidence_firewall"]
    if any(bool(v) for v in fw.values()):
        raise SystemExit("SCIENTIFIC_HOLD: prospective firewall not closed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--bulk-protocol", required=True)
    ap.add_argument("--bulk-adjudication", required=True)
    ap.add_argument("--pw", required=True)
    ap.add_argument("--pseudo-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    protocol_path = Path(args.protocol)
    bulk_protocol_path = Path(args.bulk_protocol)
    adjudication_path = Path(args.bulk_adjudication)
    protocol = load(protocol_path)
    bulk_protocol = load(bulk_protocol_path)
    adjudication = load(adjudication_path)
    outroot = Path(args.out)
    outroot.mkdir(parents=True, exist_ok=True)
    rawroot = outroot / "raw"
    rawroot.mkdir(exist_ok=True)

    pw = Path(args.pw).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve()
    ru_pseudo = pseudo_dir / bulk_protocol["pseudopotentials"]["Ru"]["filename"]
    validate_contract(protocol, bulk_protocol, adjudication, pw, ru_pseudo)

    selected = adjudication["selected_numerical_settings"]
    fit = adjudication["structural_fit"]
    ecutwfc = int(selected["ecutwfc_ry"])
    ecutrho = int(selected["ecutrho_ry"])
    a = float(fit["a_angstrom"])
    c = float(fit["c_angstrom"])
    timeout_s = int(protocol["execution"]["per_scf_timeout_seconds"])
    tol = float(protocol["numerical_gate"]["absolute_surface_excess_tolerance_ev_per_surface_atom"])

    all_rows = []
    cache = {}

    def run_bulk_ref():
        tag = "bulk_reference_fitted_highk"
        case = rawroot / tag
        txt = hcp_bulk_input(a, c, ecutwfc, ecutrho, tuple(protocol["fresh_bulk_reference"]["kmesh"]), pseudo_dir, "__OUTDIR__", tag)
        row = execute_qe(case, pw, txt, timeout_s, tag)
        row.update({
            "kind": "bulk_reference",
            "a_angstrom": a,
            "c_angstrom": c,
            "ecutwfc_ry": ecutwfc,
            "ecutrho_ry": ecutrho,
            "kmesh": list(protocol["fresh_bulk_reference"]["kmesh"]),
            "energy_ev_per_atom": row["energy_ev"] / 2.0
        })
        all_rows.append(row)
        return row

    try:
        bulk_ref = run_bulk_ref()
        ebulk = bulk_ref["energy_ev_per_atom"]

        def run_slab(layers: int, vacuum: float, kmesh, stage: str):
            key = (int(layers), float(vacuum), tuple(int(x) for x in kmesh))
            if key in cache:
                return cache[key]
            tag = f"slab_L{layers}_V{vacuum:g}_K{kmesh[0]}_{kmesh[1]}_{kmesh[2]}"
            case = rawroot / tag
            txt = slab_input(a, c, int(layers), float(vacuum), ecutwfc, ecutrho, tuple(kmesh), pseudo_dir, "__OUTDIR__", tag)
            row = execute_qe(case, pw, txt, timeout_s, tag)
            gamma = (row["energy_ev"] - int(layers) * ebulk) / 2.0
            cell_z, _ = slab_geometry(a, c, int(layers), float(vacuum))
            row.update({
                "kind": "slab_scf",
                "first_stage_requested": stage,
                "layers": int(layers),
                "total_vacuum_angstrom": float(vacuum),
                "cell_z_angstrom": cell_z,
                "kmesh": [int(x) for x in kmesh],
                "ecutwfc_ry": ecutwfc,
                "ecutrho_ry": ecutrho,
                "surface_excess_ev_per_surface_atom": gamma
            })
            all_rows.append(row)
            cache[key] = row
            return row

        ng = protocol["numerical_gate"]
        kcfg = ng["kmesh_stage"]
        k_rows = [run_slab(kcfg["layers"], kcfg["total_vacuum_angstrom"], k, "kmesh") for k in kcfg["surface_kmeshes"]]
        ki, k_deltas = suffix_selection(k_rows, tol)
        if ki is None:
            result = build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, "CLEAN_SURFACE_NUMERICAL_HOLD", "kmesh_stage", {"kmesh_deltas_to_terminal": k_deltas})
            write(outroot / "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json", result)
            raise SystemExit("SCIENTIFIC_HOLD: kmesh stage did not demonstrate non-terminal convergence")
        selected_k = k_rows[ki]["kmesh"]

        vcfg = ng["vacuum_stage"]
        v_rows = [run_slab(vcfg["layers"], v, selected_k, "vacuum") for v in vcfg["total_vacuum_angstrom"]]
        vi, v_deltas = suffix_selection(v_rows, tol)
        if vi is None:
            result = build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, "CLEAN_SURFACE_NUMERICAL_HOLD", "vacuum_stage", {"selected_kmesh": selected_k, "vacuum_deltas_to_terminal": v_deltas})
            write(outroot / "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json", result)
            raise SystemExit("SCIENTIFIC_HOLD: vacuum stage did not demonstrate non-terminal convergence")
        selected_v = v_rows[vi]["total_vacuum_angstrom"]

        lcfg = ng["layer_stage"]
        l_rows = [run_slab(L, selected_v, selected_k, "layers") for L in lcfg["layers"]]
        li, l_deltas = suffix_selection(l_rows, tol, eligible=lambda r: r["layers"] >= lcfg["minimum_eligible_layers"])
        if li is None:
            result = build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, "CLEAN_SURFACE_NUMERICAL_HOLD", "layer_stage", {"selected_kmesh": selected_k, "selected_total_vacuum_angstrom": selected_v, "layer_deltas_to_terminal": l_deltas})
            write(outroot / "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json", result)
            raise SystemExit("SCIENTIFIC_HOLD: layer stage did not demonstrate eligible non-terminal convergence")
        selected_l = l_rows[li]["layers"]

        base = run_slab(selected_l, selected_v, selected_k, "joint_base")
        high_k = list(kcfg["terminal_reference"])
        high_v = float(vcfg["terminal_reference_angstrom"])
        high_l = int(lcfg["terminal_reference_layers"])
        rk = run_slab(selected_l, selected_v, high_k, "joint_high_k")
        rv = run_slab(selected_l, high_v, selected_k, "joint_high_vacuum")
        rl = run_slab(high_l, selected_v, selected_k, "joint_high_layers")
        joint = {
            "kmesh_endpoint_delta_ev_per_surface_atom": abs(rk["surface_excess_ev_per_surface_atom"] - base["surface_excess_ev_per_surface_atom"]),
            "vacuum_endpoint_delta_ev_per_surface_atom": abs(rv["surface_excess_ev_per_surface_atom"] - base["surface_excess_ev_per_surface_atom"]),
            "layer_endpoint_delta_ev_per_surface_atom": abs(rl["surface_excess_ev_per_surface_atom"] - base["surface_excess_ev_per_surface_atom"])
        }
        if any(v > tol for v in joint.values()):
            result = build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, "CLEAN_SURFACE_COUPLED_CONVERGENCE_HOLD", "joint_endpoint_recheck", {"selected_layers": selected_l, "selected_total_vacuum_angstrom": selected_v, "selected_kmesh": selected_k, "joint_endpoint_recheck": joint, "kmesh_deltas_to_terminal": k_deltas, "vacuum_deltas_to_terminal": v_deltas, "layer_deltas_to_terminal": l_deltas})
            write(outroot / "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json", result)
            raise SystemExit("SCIENTIFIC_HOLD: coupled endpoint recheck failed")

        extra = {
            "selected_layers": selected_l,
            "selected_total_vacuum_angstrom": selected_v,
            "selected_kmesh": selected_k,
            "selected_surface_excess_ev_per_surface_atom": base["surface_excess_ev_per_surface_atom"],
            "kmesh_deltas_to_terminal": k_deltas,
            "vacuum_deltas_to_terminal": v_deltas,
            "layer_deltas_to_terminal": l_deltas,
            "joint_endpoint_recheck": joint
        }
        result = build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, "CLEAN_SURFACE_FIXED_GRID_PASS", None, extra)
        write(outroot / "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json", result)
        print(json.dumps(result, indent=2, sort_keys=True))

    except RuntimeError as exc:
        hold = {
            "schema": "h-ru0001-clean-surface-mechanical-hold-v0.1",
            "status": "MECHANICAL_SURFACE_HOLD",
            "execution_state": "EXECUTED_NOT_VALID",
            "error": str(exc),
            "protocol_sha256": sha256(protocol_path),
            "bulk_adjudication_sha256": sha256(adjudication_path),
            "completed_valid_case_count": sum(1 for r in all_rows if r.get("execution_state", {}).get("VALID")),
            "scientific_settings_changed": False,
            "thresholds_changed": False
        }
        write(outroot / "SYSTEM3_CLEAN_SURFACE_MECHANICAL_HOLD.json", hold)
        print(json.dumps(hold, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)


def build_result(protocol_path, bulk_protocol_path, adjudication_path, protocol, adjudication, bulk_ref, all_rows, status, failed_gate, extra):
    elapsed = sum(float(r.get("elapsed_s", 0.0)) for r in all_rows)
    for row in all_rows:
        if row.get("execution_state", {}).get("VALID"):
            row["execution_state"]["ADJUDICATED"] = True
    result = {
        "schema": "h-ru0001-clean-surface-numerical-result-v0.1",
        "status": status,
        "system": "H/Ru(0001)",
        "scope": "NON_KINETIC_CLEAN_SURFACE_QUALIFICATION",
        "execution_state": "ADJUDICATED",
        "failed_gate": failed_gate,
        "tolerance_ev_per_surface_atom": protocol["numerical_gate"]["absolute_surface_excess_tolerance_ev_per_surface_atom"],
        "fresh_bulk_reference": {
            "energy_ev_per_atom": bulk_ref["energy_ev_per_atom"],
            "kmesh": bulk_ref["kmesh"],
            "a_angstrom": bulk_ref["a_angstrom"],
            "c_angstrom": bulk_ref["c_angstrom"]
        },
        "compute": {
            "valid_qe_case_count": sum(1 for r in all_rows if r.get("execution_state", {}).get("VALID")),
            "measured_qe_wall_seconds": elapsed
        },
        "provenance": {
            "protocol_sha256": sha256(Path(protocol_path)),
            "bulk_protocol_sha256": sha256(Path(bulk_protocol_path)),
            "bulk_adjudication_sha256": sha256(Path(adjudication_path)),
            "original_bulk_run_id": adjudication["source"]["original_run_id"],
            "recovery_bulk_run_id": adjudication["source"]["recovery_run_id"],
            "scientific_settings_changed": False,
            "thresholds_changed": False,
            "kinetic_inputs_used": False,
            "published_site_ordering_used": False,
            "chi_used": False,
            "System2_result_used": False
        },
        "next_gate": protocol["decision"]["pass_next_gate"] if status == protocol["decision"]["pass_status"] else "STOP_SCIENTIFIC_PROGRESSION_AND_ADJUDICATE_HOLD",
        "raw_records": all_rows
    }
    result.update(extra)
    return result


if __name__ == "__main__":
    main()
