#!/usr/bin/env python3
"""Prospective numerical extension for CO/Cu(111) PBE Stage A.

This controller is intentionally narrow. It responds only to the executed
Stage A NUMERICAL_HOLD by extending Cu bulk numerical convergence and, only if
required by the already-frozen post-combination rule, running a minimal
isolated-CO combination audit at the selected higher cutoff.

It does not inspect or use any CO/Cu(111) diffusion barrier, hopping rate,
kinetic prefactor, fitted friction, ChemSA target, or Atlas residual.
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

import numpy as np

RY_TO_EV = 13.605693122994
EV_A2_TO_N_M = 16.02176634
AMU_TO_KG = 1.66053906660e-27
C_CM_S = 2.99792458e10
MASS_C_AMU = 12.0
MASS_O_AMU = 15.99491461957
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
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


def verify_amendment(amendment: dict[str, Any]) -> None:
    if amendment.get("schema") != "co-cu111-pbe-stage-a-numerical-extension-v0.1":
        raise SystemExit("HOLD: wrong numerical-extension schema")
    if amendment.get("status") != "FROZEN_AFTER_STAGE_A_NUMERICAL_HOLD_BEFORE_EXTENSION_RESULTS":
        raise SystemExit("HOLD: numerical extension not frozen")
    trigger = amendment["triggering_stage_a_result"]
    if trigger["status"] != "NUMERICAL_HOLD" or trigger["next_gate"] != "STAGE_A_HOLD_REVIEW":
        raise SystemExit("HOLD: amendment is not bound to the executed Stage A numerical hold")
    gates = amendment["unchanged_gates"]
    if float(gates["bulk_delta_a0_max_angstrom"]) != 0.005:
        raise SystemExit("HOLD: bulk lattice gate changed")
    if float(gates["bulk_delta_e0_max_ev_per_atom"]) != 0.001:
        raise SystemExit("HOLD: bulk energy gate changed")
    if float(gates["co_bond_length_max_difference_angstrom"]) != 0.002:
        raise SystemExit("HOLD: CO bond numerical gate changed")
    if float(gates["co_stretch_max_difference_cm_minus_1"]) != 10.0:
        raise SystemExit("HOLD: CO stretch numerical gate changed")
    if float(gates["co_fit_discretization_max_cm_minus_1"]) != 10.0:
        raise SystemExit("HOLD: CO fit-discretization gate changed")
    if amendment["provenance"]["scientific_settings_changed"] is not False:
        raise SystemExit("HOLD: scientific settings changed")


def protocol_cutoff_map(protocol: dict[str, Any]) -> dict[str, tuple[int, int]]:
    return {
        str(row["id"]): (int(row["ecutwfc"]), int(row["ecutrho"]))
        for row in protocol["cutoff_pairs_ry"]
    }


def run_pw(pw: Path, inp: Path, out: Path, env: dict[str, str]) -> tuple[int, float, float | None, bool]:
    start = time.time()
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.run([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
    text = out.read_text(errors="replace")
    energies = [float(x) for x in ENERGY_RE.findall(text)]
    energy_ev = energies[-1] * RY_TO_EV if energies else None
    return proc.returncode, time.time() - start, energy_ev, "JOB DONE." in text


def bulk_input(
    a: float,
    ecutwfc: int,
    ecutrho: int,
    k: int,
    pseudo_dir: Path,
    outdir: Path,
    cu_name: str,
) -> str:
    pos = [(0, 0, 0), (0, 0.5, 0.5), (0.5, 0, 0.5), (0.5, 0.5, 0)]
    lines = [
        "&CONTROL",
        " calculation='scf',",
        " prefix='co_cu111_stageA_bulk_extension',",
        f" pseudo_dir='{pseudo_dir}',",
        f" outdir='{outdir}',",
        " tstress=.true.,",
        " verbosity='high',",
        "/",
        "&SYSTEM",
        " ibrav=0,",
        " nat=4,",
        " ntyp=1,",
        f" ecutwfc={ecutwfc},",
        f" ecutrho={ecutrho},",
        " input_dft='PBE',",
        " occupations='smearing',",
        " smearing='mv',",
        " degauss=0.02,",
        "/",
        "&ELECTRONS",
        " conv_thr=1.0d-10,",
        " mixing_beta=0.3,",
        " electron_maxstep=200,",
        "/",
        "ATOMIC_SPECIES",
        f"Cu 63.546 {cu_name}",
        "CELL_PARAMETERS angstrom",
        f"{a:.12f} 0 0",
        f"0 {a:.12f} 0",
        f"0 0 {a:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines += [f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in pos]
    lines += ["K_POINTS automatic", f"{k} {k} {k} 0 0 0"]
    return "\n".join(lines) + "\n"


def co_input(
    r: float,
    L: float,
    ecutwfc: int,
    ecutrho: int,
    pseudo_dir: Path,
    outdir: Path,
    c_name: str,
    o_name: str,
) -> str:
    zc = L / 2.0 - r / 2.0
    zo = L / 2.0 + r / 2.0
    x = y = L / 2.0
    return f"""&CONTROL
 calculation='scf',
 prefix='co_cu111_stageA_CO_extension',
 pseudo_dir='{pseudo_dir}',
 outdir='{outdir}',
 verbosity='high',
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=2,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 assume_isolated='martyna-tuckerman',
 nosym=.true.,
/
&ELECTRONS
 conv_thr=1.0d-10,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
C 12.000000 {c_name}
O 15.999000 {o_name}
CELL_PARAMETERS angstrom
{L:.12f} 0 0
0 {L:.12f} 0
0 0 {L:.12f}
ATOMIC_POSITIONS angstrom
C {x:.12f} {y:.12f} {zc:.12f}
O {x:.12f} {y:.12f} {zo:.12f}
K_POINTS gamma
"""


def clean_tmp(tmp: Path) -> None:
    import shutil

    if not tmp.exists():
        return
    for p in tmp.iterdir():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()


def write_manifest(root: Path, summary: Path) -> None:
    files = sorted(root.rglob("*.in")) + sorted(root.rglob("*.out")) + [summary]
    (root / "STAGE_TIME_MANIFEST.sha256").write_text(
        "\n".join(f"{sha256(p)}  {p.relative_to(root)}" for p in files) + "\n"
    )


def candidate_grid(amendment: dict[str, Any]) -> set[tuple[int, int, int]]:
    spec = amendment["bulk_extension"]
    return {
        (int(w), int(spec["ecutrho_by_ecutwfc"][str(w)]), int(k))
        for w in spec["candidate_ecutwfc_ry"]
        for k in spec["candidate_kmeshes"]
    }


def command_self_test(args: argparse.Namespace) -> None:
    amendment = load_json(Path(args.amendment))
    verify_amendment(amendment)
    grid = candidate_grid(amendment)
    if len(grid) != 25:
        raise SystemExit(f"HOLD: expected 25 candidate combinations, found {len(grid)}")
    reused = {
        (int(r["ecutwfc_ry"]), int(r["ecutrho_ry"]), int(r["kmesh"]))
        for r in amendment["bulk_extension"]["reused_existing_candidates"]
    }
    if reused != {(90, 900, 12), (90, 900, 14), (90, 900, 16)}:
        raise SystemExit("HOLD: reused-candidate set changed")
    new_candidates = grid - reused
    if len(new_candidates) != 22:
        raise SystemExit(f"HOLD: expected 22 new candidate EOS cases, found {len(new_candidates)}")
    ref = amendment["bulk_extension"]["terminal_reference"]
    audit = amendment["bulk_extension"]["independent_audit"]
    if (int(ref["ecutwfc_ry"]), int(ref["ecutrho_ry"]), int(ref["kmesh"])) != (140, 1400, 22):
        raise SystemExit("HOLD: terminal reference changed")
    if (int(audit["ecutwfc_ry"]), int(audit["ecutrho_ry"]), int(audit["kmesh"])) != (150, 1500, 24):
        raise SystemExit("HOLD: independent audit changed")
    if amendment["conditional_co_combination_check"]["boxes_angstrom"] != [18, 26]:
        raise SystemExit("HOLD: conditional CO boxes changed")
    print("EXTENSION_CONTRACT_SELF_TEST_PASS")
    print("CANDIDATE_GRID=25")
    print("REUSED_CANDIDATES=3")
    print("NEW_CANDIDATES=22")
    print("REFERENCE_AND_AUDIT=2")
    print("NEW_BULK_EOS_CASES=24")


def verify_solver_bundle(
    bundle: dict[str, Any], pseudo_dir: Path, pw: Path
) -> tuple[str, str, str]:
    if sha256(pw) != bundle["solver_bundle"]["pw_x_sha256"]:
        raise SystemExit("HOLD: pw.x hash mismatch")
    names = {}
    for symbol in ("Cu", "C", "O"):
        row = bundle["pseudopotentials"][symbol]
        path = pseudo_dir / row["filename"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            raise SystemExit(f"HOLD: pseudopotential mismatch for {symbol}")
        names[symbol] = row["filename"]
    return names["Cu"], names["C"], names["O"]


def command_bulk_run(args: argparse.Namespace) -> None:
    amendment_path = Path(args.amendment).resolve()
    bundle_path = Path(args.bundle).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pw = Path(args.pw).resolve()
    root = Path(args.out).resolve()

    amendment = load_json(amendment_path)
    bundle = load_json(bundle_path)
    verify_amendment(amendment)
    cu_name, _, _ = verify_solver_bundle(bundle, pseudo_dir, pw)

    role = str(args.role)
    triple = (int(args.ecutwfc), int(args.ecutrho), int(args.kmesh))
    if role == "candidate":
        if triple not in candidate_grid(amendment):
            raise SystemExit(f"HOLD: candidate not frozen: {triple}")
        reused = {
            (int(r["ecutwfc_ry"]), int(r["ecutrho_ry"]), int(r["kmesh"]))
            for r in amendment["bulk_extension"]["reused_existing_candidates"]
        }
        if triple in reused:
            raise SystemExit("HOLD: workflow attempted to recompute an archived reusable candidate")
    elif role == "reference":
        row = amendment["bulk_extension"]["terminal_reference"]
        allowed = (int(row["ecutwfc_ry"]), int(row["ecutrho_ry"]), int(row["kmesh"]))
        if triple != allowed:
            raise SystemExit("HOLD: wrong terminal-reference case")
    elif role == "audit":
        row = amendment["bulk_extension"]["independent_audit"]
        allowed = (int(row["ecutwfc_ry"]), int(row["ecutrho_ry"]), int(row["kmesh"]))
        if triple != allowed:
            raise SystemExit("HOLD: wrong independent-audit case")
    else:
        raise SystemExit(f"HOLD: unknown bulk role {role}")

    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"

    records: list[dict[str, Any]] = []
    root.mkdir(parents=True, exist_ok=True)
    lattice_grid = [float(x) for x in amendment["bulk_extension"]["lattice_grid_angstrom"]]
    for a in lattice_grid:
        tag = f"a{a:.3f}"
        d = root / tag
        d.mkdir(exist_ok=True)
        tmp = d / "tmp"
        tmp.mkdir(exist_ok=True)
        inp = d / f"{tag}.in"
        out = d / f"{tag}.out"
        inp.write_text(
            bulk_input(
                a,
                int(args.ecutwfc),
                int(args.ecutrho),
                int(args.kmesh),
                pseudo_dir,
                tmp,
                cu_name,
            )
        )
        rc, elapsed, energy, done = run_pw(pw, inp, out, env)
        rec = {
            "a_angstrom": a,
            "returncode": rc,
            "job_done": done,
            "energy_ev_total": energy,
            "energy_ev_per_atom": None if energy is None else energy / 4.0,
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
        }
        write_json(d / "run_record.json", rec)
        records.append(rec)
        if rc != 0 or not done or energy is None:
            raise SystemExit(f"HOLD: bulk extension QE failure {tag}")
        clean_tmp(tmp)

    summary = {
        "schema": "co-cu111-pbe-stage-a-bulk-extension-eos-v0.1",
        "status": "COMPLETE",
        "role": role,
        "ecutwfc_ry": int(args.ecutwfc),
        "ecutrho_ry": int(args.ecutrho),
        "kmesh": int(args.kmesh),
        "records": records,
        "provenance": {
            "amendment_sha256": sha256(amendment_path),
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "cu_pseudo_sha256": bundle["pseudopotentials"]["Cu"]["sha256"],
            "scientific_settings_changed": False,
        },
    }
    summary_path = root / "summary.json"
    write_json(summary_path, summary)
    write_manifest(root, summary_path)


def quadratic_fit(points: list[tuple[float, float]]) -> dict[str, float]:
    x = np.array([p[0] for p in points])
    y = np.array([p[1] for p in points])
    coeff = np.polyfit(x, y, 2)
    if coeff[0] <= 0:
        raise ValueError("non-convex bulk fit")
    a0 = float(-coeff[1] / (2 * coeff[0]))
    e0 = float(np.polyval(coeff, a0))
    rms = float(np.sqrt(np.mean((y - np.polyval(coeff, x)) ** 2)) * 1000)
    if not (min(x) <= a0 <= max(x)):
        raise ValueError("bulk fit minimum outside grid")
    return {"a0_angstrom": a0, "e0_ev_per_atom": e0, "rms_mev_per_atom": rms}


def verify_manifest(member: Path) -> None:
    manifest = member / "STAGE_TIME_MANIFEST.sha256"
    if not manifest.is_file():
        raise SystemExit(f"HOLD: missing manifest: {manifest}")
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        path = member / rel.strip()
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"HOLD: manifest mismatch: {path}")


def verify_records(member: Path, expected_count: int) -> None:
    paths = sorted(member.rglob("run_record.json"))
    if len(paths) != expected_count:
        raise SystemExit(f"HOLD: wrong record count in {member}: {len(paths)}")
    for rp in paths:
        rec = load_json(rp)
        if rec["returncode"] != 0 or rec["job_done"] is not True:
            raise SystemExit(f"HOLD: invalid run record: {rp}")
        if rec.get("energy_ev_per_atom") is None or not math.isfinite(float(rec["energy_ev_per_atom"])):
            raise SystemExit(f"HOLD: invalid energy: {rp}")
        ins = list(rp.parent.glob("*.in"))
        outs = list(rp.parent.glob("*.out"))
        if len(ins) != 1 or len(outs) != 1:
            raise SystemExit(f"HOLD: missing raw input/output: {rp.parent}")
        if sha256(ins[0]) != rec["input_sha256"] or sha256(outs[0]) != rec["output_sha256"]:
            raise SystemExit(f"HOLD: raw input/output hash mismatch: {rp.parent}")


def fit_bulk_summary(path: Path) -> dict[str, Any]:
    d = load_json(path)
    fit = quadratic_fit(
        [(float(r["a_angstrom"]), float(r["energy_ev_per_atom"])) for r in d["records"]]
    )
    if d["schema"] == "co-cu111-pbe-stage-a-bulk-matrix-v0.1":
        if d["cutoff_id"] != "C2":
            raise SystemExit(f"HOLD: only C2 archived candidates may be reused here: {path}")
        ecutwfc = 90
        ecutrho = 900
        role = "candidate"
    elif d["schema"] == "co-cu111-pbe-stage-a-bulk-extension-eos-v0.1":
        ecutwfc = int(d["ecutwfc_ry"])
        ecutrho = int(d["ecutrho_ry"])
        role = str(d["role"])
    else:
        raise SystemExit(f"HOLD: unexpected bulk summary schema: {path}")
    return {
        "ecutwfc_ry": ecutwfc,
        "ecutrho_ry": ecutrho,
        "kmesh": int(d["kmesh"]),
        "role": role,
        "fit": fit,
        "source": str(path),
        "source_sha256": sha256(path),
    }


def command_bulk_gate(args: argparse.Namespace) -> None:
    amendment_path = Path(args.amendment).resolve()
    decision_path = Path(args.stage_a_decision).resolve()
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()

    amendment = load_json(amendment_path)
    decision = load_json(decision_path)
    verify_amendment(amendment)
    if decision.get("schema") != "co-cu111-pbe-stage-a-result-v0.1" or decision.get("status") != "NUMERICAL_HOLD":
        raise SystemExit("HOLD: triggering Stage A result is not the executed NUMERICAL_HOLD")
    if decision.get("next_gate") != "STAGE_A_HOLD_REVIEW":
        raise SystemExit("HOLD: triggering Stage A result has wrong next gate")

    expected_trigger_sha = amendment["triggering_stage_a_result"]["result_json_sha256"]
    if sha256(decision_path) != expected_trigger_sha:
        raise SystemExit("HOLD: triggering Stage A result hash mismatch")

    summary_paths = sorted(root.rglob("summary.json"))
    rows: list[dict[str, Any]] = []
    for path in summary_paths:
        d = load_json(path)
        if d.get("schema") not in {
            "co-cu111-pbe-stage-a-bulk-matrix-v0.1",
            "co-cu111-pbe-stage-a-bulk-extension-eos-v0.1",
        }:
            continue
        if len(d.get("records", [])) != 6:
            raise SystemExit(f"HOLD: incomplete EOS summary: {path}")
        verify_manifest(path.parent)
        verify_records(path.parent, 6)
        rows.append(fit_bulk_summary(path))

    expected_candidates = candidate_grid(amendment)
    candidate_rows = [r for r in rows if r["role"] == "candidate"]
    seen_candidates = {(r["ecutwfc_ry"], r["ecutrho_ry"], r["kmesh"]) for r in candidate_rows}
    if seen_candidates != expected_candidates:
        raise SystemExit(
            f"HOLD: candidate cardinality mismatch: expected {len(expected_candidates)}, got {len(seen_candidates)}"
        )

    # Bind the three reused C2 cases to the archived scientific-decision summaries.
    prior_c2 = {
        (90, 900, int(r["kmesh"])): r["source_sha256"]
        for r in decision["bulk_candidates"]
        if r["cutoff_id"] == "C2" and int(r["kmesh"]) in {12, 14, 16}
    }
    if len(prior_c2) != 3:
        raise SystemExit("HOLD: triggering decision does not contain all three reusable C2 bulk cases")
    for row in candidate_rows:
        key = (row["ecutwfc_ry"], row["ecutrho_ry"], row["kmesh"])
        if key in prior_c2 and row["source_sha256"] != prior_c2[key]:
            raise SystemExit(f"HOLD: reused C2 summary changed: {key}")

    ref_spec = amendment["bulk_extension"]["terminal_reference"]
    audit_spec = amendment["bulk_extension"]["independent_audit"]
    ref_key = (int(ref_spec["ecutwfc_ry"]), int(ref_spec["ecutrho_ry"]), int(ref_spec["kmesh"]))
    audit_key = (int(audit_spec["ecutwfc_ry"]), int(audit_spec["ecutrho_ry"]), int(audit_spec["kmesh"]))
    reference = next(
        (r for r in rows if r["role"] == "reference" and (r["ecutwfc_ry"], r["ecutrho_ry"], r["kmesh"]) == ref_key),
        None,
    )
    audit = next(
        (r for r in rows if r["role"] == "audit" and (r["ecutwfc_ry"], r["ecutrho_ry"], r["kmesh"]) == audit_key),
        None,
    )
    if reference is None or audit is None:
        raise SystemExit("HOLD: reference or audit EOS missing")

    gates = amendment["unchanged_gates"]
    da_max = float(gates["bulk_delta_a0_max_angstrom"])
    de_max = float(gates["bulk_delta_e0_max_ev_per_atom"])
    expa = float(gates["bulk_reference_lattice_constant_angstrom"])
    maxrel = float(gates["bulk_reference_lattice_max_relative_error_fraction"])

    reference_audit = {
        "delta_a0_angstrom": abs(reference["fit"]["a0_angstrom"] - audit["fit"]["a0_angstrom"]),
        "delta_e0_ev_per_atom": abs(reference["fit"]["e0_ev_per_atom"] - audit["fit"]["e0_ev_per_atom"]),
    }
    reference_audit["pass"] = (
        reference_audit["delta_a0_angstrom"] <= da_max
        and reference_audit["delta_e0_ev_per_atom"] <= de_max
    )
    reference_physical_pass = abs(reference["fit"]["a0_angstrom"] - expa) / expa <= maxrel
    audit_physical_pass = abs(audit["fit"]["a0_angstrom"] - expa) / expa <= maxrel

    for row in candidate_rows:
        row["delta_a0_angstrom"] = abs(row["fit"]["a0_angstrom"] - reference["fit"]["a0_angstrom"])
        row["delta_e0_ev_per_atom"] = abs(row["fit"]["e0_ev_per_atom"] - reference["fit"]["e0_ev_per_atom"])
        row["numerical_pass"] = (
            row["delta_a0_angstrom"] <= da_max and row["delta_e0_ev_per_atom"] <= de_max
        )
        row["physical_pass"] = abs(row["fit"]["a0_angstrom"] - expa) / expa <= maxrel

    selected = None
    extension_reason = None
    if not reference_audit["pass"]:
        status = "NUMERICAL_HOLD"
        extension_reason = "TERMINAL_REFERENCE_FAILED_INDEPENDENT_AUDIT"
    elif not reference_physical_pass or not audit_physical_pass:
        status = "PBE_REJECT_BULK_STRUCTURE"
        extension_reason = "EXTENDED_REFERENCE_FAILED_BULK_PHYSICAL_GUARD"
    else:
        passing = [r for r in candidate_rows if r["numerical_pass"] and r["physical_pass"]]
        if passing:
            selected = min(passing, key=lambda r: (r["ecutwfc_ry"], r["kmesh"]))
            status = "BULK_EXTENSION_PASS"
            extension_reason = "LOWEST_FROZEN_EXTENSION_CANDIDATE_SELECTED"
        else:
            status = "NUMERICAL_HOLD"
            extension_reason = "NO_FROZEN_EXTENSION_CANDIDATE_PASSED"

    need_co_check = bool(selected and selected["ecutwfc_ry"] > 90)
    result = {
        "schema": "co-cu111-pbe-stage-a-bulk-extension-gate-v0.1",
        "status": status,
        "extension_reason": extension_reason,
        "reference": reference,
        "audit": audit,
        "reference_audit": reference_audit,
        "reference_physical_pass": reference_physical_pass,
        "audit_physical_pass": audit_physical_pass,
        "candidates": sorted(candidate_rows, key=lambda r: (r["ecutwfc_ry"], r["kmesh"])),
        "selected": selected,
        "conditional_co_combination_check_required": need_co_check,
        "provenance": {
            "amendment_sha256": sha256(amendment_path),
            "trigger_stage_a_result_sha256": sha256(decision_path),
            "scientific_settings_changed": False,
        },
    }
    write_json(out, result)
    print(json.dumps(result, indent=2))


def bond_grid(spec: dict[str, Any]) -> list[float]:
    start = float(spec["start"])
    stop = float(spec["stop"])
    step = float(spec["step"])
    n = int(round((stop - start) / step))
    vals = [round(start + i * step, 10) for i in range(n + 1)]
    if abs(vals[-1] - stop) > 1e-8:
        raise SystemExit("HOLD: malformed bond grid")
    return vals


def command_co_run(args: argparse.Namespace) -> None:
    amendment_path = Path(args.amendment).resolve()
    bundle_path = Path(args.bundle).resolve()
    gate_path = Path(args.bulk_gate).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pw = Path(args.pw).resolve()
    root = Path(args.out).resolve()

    amendment = load_json(amendment_path)
    bundle = load_json(bundle_path)
    gate = load_json(gate_path)
    verify_amendment(amendment)
    _, c_name, o_name = verify_solver_bundle(bundle, pseudo_dir, pw)
    if gate.get("schema") != "co-cu111-pbe-stage-a-bulk-extension-gate-v0.1":
        raise SystemExit("HOLD: wrong bulk-extension gate schema")
    if gate.get("status") != "BULK_EXTENSION_PASS" or gate.get("selected") is None:
        raise SystemExit("HOLD: CO combination check launched without a selected bulk extension")
    if gate.get("conditional_co_combination_check_required") is not True:
        raise SystemExit("HOLD: unnecessary CO recomputation attempted")

    selected = gate["selected"]
    ecutwfc = int(selected["ecutwfc_ry"])
    ecutrho = int(selected["ecutrho_ry"])
    if ecutwfc <= 90:
        raise SystemExit("HOLD: archived 90 Ry CO data must be reused rather than recomputed")
    L = int(args.box)
    if L not in [int(x) for x in amendment["conditional_co_combination_check"]["boxes_angstrom"]]:
        raise SystemExit("HOLD: CO combination box not frozen")

    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"

    records: list[dict[str, Any]] = []
    root.mkdir(parents=True, exist_ok=True)
    for r in bond_grid(amendment["conditional_co_combination_check"]["bond_scan_angstrom"]):
        tag = f"r{r:.2f}"
        d = root / tag
        d.mkdir(exist_ok=True)
        tmp = d / "tmp"
        tmp.mkdir(exist_ok=True)
        inp = d / f"{tag}.in"
        out = d / f"{tag}.out"
        inp.write_text(co_input(r, float(L), ecutwfc, ecutrho, pseudo_dir, tmp, c_name, o_name))
        rc, elapsed, energy, done = run_pw(pw, inp, out, env)
        rec = {
            "bond_angstrom": r,
            "returncode": rc,
            "job_done": done,
            "energy_ev_total": energy,
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
        }
        write_json(d / "run_record.json", rec)
        records.append(rec)
        if rc != 0 or not done or energy is None:
            raise SystemExit(f"HOLD: CO extension QE failure {tag}")
        clean_tmp(tmp)

    summary = {
        "schema": "co-cu111-pbe-stage-a-co-combination-extension-v0.1",
        "status": "COMPLETE",
        "ecutwfc_ry": ecutwfc,
        "ecutrho_ry": ecutrho,
        "box_angstrom": float(L),
        "records": records,
        "provenance": {
            "amendment_sha256": sha256(amendment_path),
            "bulk_gate_sha256": sha256(gate_path),
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "c_pseudo_sha256": bundle["pseudopotentials"]["C"]["sha256"],
            "o_pseudo_sha256": bundle["pseudopotentials"]["O"]["sha256"],
            "scientific_settings_changed": False,
        },
    }
    summary_path = root / "summary.json"
    write_json(summary_path, summary)
    write_manifest(root, summary_path)


def co_fit(records: list[dict[str, Any]], sparse: bool = False) -> dict[str, float]:
    rows = sorted((float(r["bond_angstrom"]), float(r["energy_ev_total"])) for r in records)
    if sparse:
        rows = rows[::2]
    imin = min(range(len(rows)), key=lambda i: rows[i][1])
    lo = max(0, min(imin - 3, len(rows) - 7))
    local = rows[lo : lo + 7]
    if len(local) < 5:
        raise ValueError("insufficient local CO points")
    x = np.array([p[0] for p in local])
    y = np.array([p[1] for p in local])
    coeff = np.polyfit(x, y, 4)
    roots = np.roots(np.polyder(coeff))
    candidates = []
    for root in roots:
        if abs(root.imag) < 1e-8:
            rr = float(root.real)
            if min(x) <= rr <= max(x):
                second = float(np.polyval(np.polyder(coeff, 2), rr))
                if second > 0:
                    candidates.append((float(np.polyval(coeff, rr)), rr, second))
    if not candidates:
        raise ValueError("no valid quartic minimum")
    _, r0, curvature = min(candidates)
    mu_amu = MASS_C_AMU * MASS_O_AMU / (MASS_C_AMU + MASS_O_AMU)
    omega = math.sqrt(curvature * EV_A2_TO_N_M / (mu_amu * AMU_TO_KG))
    cm1 = omega / (2 * math.pi * C_CM_S)
    rms = float(np.sqrt(np.mean((y - np.polyval(coeff, x)) ** 2)) * 1000)
    return {
        "bond_angstrom": r0,
        "harmonic_stretch_cm_minus_1": cm1,
        "curvature_ev_per_angstrom2": curvature,
        "fit_rms_mev": rms,
        "fit_min_angstrom": float(min(x)),
        "fit_max_angstrom": float(max(x)),
    }


def load_extension_co_summary(path: Path) -> dict[str, Any]:
    d = load_json(path)
    if d.get("schema") != "co-cu111-pbe-stage-a-co-combination-extension-v0.1":
        raise SystemExit(f"HOLD: wrong CO extension summary schema: {path}")
    if d.get("status") != "COMPLETE" or len(d.get("records", [])) != 23:
        raise SystemExit(f"HOLD: incomplete CO extension summary: {path}")
    verify_manifest(path.parent)
    # CO records have total energy rather than per-atom energy.
    rec_paths = sorted(path.parent.rglob("run_record.json"))
    if len(rec_paths) != 23:
        raise SystemExit(f"HOLD: wrong CO record count: {path.parent}")
    for rp in rec_paths:
        rec = load_json(rp)
        if rec["returncode"] != 0 or rec["job_done"] is not True:
            raise SystemExit(f"HOLD: invalid CO run record: {rp}")
        if rec.get("energy_ev_total") is None or not math.isfinite(float(rec["energy_ev_total"])):
            raise SystemExit(f"HOLD: invalid CO energy: {rp}")
        ins = list(rp.parent.glob("*.in"))
        outs = list(rp.parent.glob("*.out"))
        if len(ins) != 1 or len(outs) != 1:
            raise SystemExit(f"HOLD: missing CO raw files: {rp.parent}")
        if sha256(ins[0]) != rec["input_sha256"] or sha256(outs[0]) != rec["output_sha256"]:
            raise SystemExit(f"HOLD: CO raw hash mismatch: {rp.parent}")
    fit = co_fit(d["records"], False)
    sparse = co_fit(d["records"], True)
    return {
        "ecutwfc_ry": int(d["ecutwfc_ry"]),
        "ecutrho_ry": int(d["ecutrho_ry"]),
        "box_angstrom": float(d["box_angstrom"]),
        "fit": fit,
        "sparse_fit": sparse,
        "discretization_delta_cm_minus_1": abs(
            fit["harmonic_stretch_cm_minus_1"] - sparse["harmonic_stretch_cm_minus_1"]
        ),
        "source": str(path),
        "source_sha256": sha256(path),
    }


def command_finalize(args: argparse.Namespace) -> None:
    amendment_path = Path(args.amendment).resolve()
    decision_path = Path(args.stage_a_decision).resolve()
    bulk_gate_path = Path(args.bulk_gate).resolve()
    out = Path(args.out).resolve()
    co_root = Path(args.co_root).resolve() if args.co_root else None

    amendment = load_json(amendment_path)
    decision = load_json(decision_path)
    bulk_gate = load_json(bulk_gate_path)
    verify_amendment(amendment)
    if sha256(decision_path) != amendment["triggering_stage_a_result"]["result_json_sha256"]:
        raise SystemExit("HOLD: triggering Stage A result changed")
    if decision.get("status") != "NUMERICAL_HOLD":
        raise SystemExit("HOLD: Stage A base result is not NUMERICAL_HOLD")
    if bulk_gate.get("schema") != "co-cu111-pbe-stage-a-bulk-extension-gate-v0.1":
        raise SystemExit("HOLD: wrong bulk gate schema")

    final_status: str
    next_gate: str
    extension_reason = str(bulk_gate.get("extension_reason"))
    selected = bulk_gate.get("selected")
    co_combination: dict[str, Any] | None = None

    if bulk_gate["status"] == "PBE_REJECT_BULK_STRUCTURE":
        final_status = "PBE_REJECT_BULK_STRUCTURE"
    elif bulk_gate["status"] != "BULK_EXTENSION_PASS" or selected is None:
        final_status = "NUMERICAL_HOLD"
    else:
        selected_w = int(selected["ecutwfc_ry"])
        selected_rho = int(selected["ecutrho_ry"])
        if selected_w == 90:
            # Reuse the already-validated C2/L18 and C2/L26 records. This is the
            # exact post-combination cutoff that the original frozen analyzer
            # could not select only because C2 was its terminal holdout.
            c2_l18 = next(
                (
                    r
                    for r in decision["co_candidates"]
                    if r["cutoff_id"] == "C2" and abs(float(r["box_angstrom"]) - 18.0) < 1e-9
                ),
                None,
            )
            c2_l26 = next(
                (
                    r
                    for r in decision["co_candidates"]
                    if r["cutoff_id"] == "C2" and abs(float(r["box_angstrom"]) - 26.0) < 1e-9
                ),
                None,
            )
            if c2_l18 is None or c2_l26 is None:
                raise SystemExit("HOLD: archived 90 Ry CO combination records missing")
            co_combination = {
                "mode": "REUSED_ARCHIVED_C2_CO_COMBINATION_CHECK",
                "selected_box": c2_l18,
                "terminal_box": c2_l26,
            }
            if not c2_l26["bond_physical_pass"]:
                final_status = "PBE_REJECT_CO_STRUCTURE"
            elif not c2_l26["frequency_physical_pass"]:
                final_status = "PBE_REJECT_CO_VIBRATION"
            elif not c2_l18["discretization_pass"] or not c2_l26["discretization_pass"]:
                final_status = "FIT_HOLD"
            elif not c2_l18["numerical_pass"]:
                final_status = "NUMERICAL_HOLD"
            else:
                final_status = "PASS"
        else:
            if co_root is None:
                raise SystemExit("HOLD: higher-cutoff CO combination audit required but absent")
            paths = sorted(co_root.rglob("summary.json"))
            rows = [load_extension_co_summary(p) for p in paths]
            rows = [r for r in rows if r["ecutwfc_ry"] == selected_w and r["ecutrho_ry"] == selected_rho]
            if {r["box_angstrom"] for r in rows} != {18.0, 26.0}:
                raise SystemExit("HOLD: expected exactly L18 and L26 CO combination audits")
            l18 = next(r for r in rows if r["box_angstrom"] == 18.0)
            l26 = next(r for r in rows if r["box_angstrom"] == 26.0)
            gates = amendment["unchanged_gates"]
            bond_ref = float(gates["co_equilibrium_bond_reference_angstrom"])
            bond_rel = float(gates["co_bond_reference_max_relative_error_fraction"])
            freq_ref = float(gates["co_fundamental_vibration_reference_cm_minus_1"])
            freq_rel = float(gates["co_vibration_reference_max_relative_error_fraction"])
            disc_max = float(gates["co_fit_discretization_max_cm_minus_1"])
            dbond_max = float(gates["co_bond_length_max_difference_angstrom"])
            dfreq_max = float(gates["co_stretch_max_difference_cm_minus_1"])

            for r in (l18, l26):
                r["bond_physical_pass"] = (
                    abs(r["fit"]["bond_angstrom"] - bond_ref) / bond_ref <= bond_rel
                )
                r["frequency_physical_pass"] = (
                    abs(r["fit"]["harmonic_stretch_cm_minus_1"] - freq_ref) / freq_ref <= freq_rel
                )
                r["discretization_pass"] = r["discretization_delta_cm_minus_1"] <= disc_max
            l18["delta_bond_angstrom_to_L26"] = abs(
                l18["fit"]["bond_angstrom"] - l26["fit"]["bond_angstrom"]
            )
            l18["delta_stretch_cm_minus_1_to_L26"] = abs(
                l18["fit"]["harmonic_stretch_cm_minus_1"]
                - l26["fit"]["harmonic_stretch_cm_minus_1"]
            )
            l18["numerical_pass"] = (
                l18["delta_bond_angstrom_to_L26"] <= dbond_max
                and l18["delta_stretch_cm_minus_1_to_L26"] <= dfreq_max
            )
            co_combination = {
                "mode": "CONDITIONAL_HIGHER_CUTOFF_CO_COMBINATION_AUDIT",
                "selected_box": l18,
                "terminal_box": l26,
            }
            if not l26["bond_physical_pass"]:
                final_status = "PBE_REJECT_CO_STRUCTURE"
            elif not l26["frequency_physical_pass"]:
                final_status = "PBE_REJECT_CO_VIBRATION"
            elif not l18["discretization_pass"] or not l26["discretization_pass"]:
                final_status = "FIT_HOLD"
            elif not l18["numerical_pass"]:
                final_status = "NUMERICAL_HOLD"
            else:
                final_status = "PASS"

    if final_status == "PASS":
        next_gate = "PBE_CU111_CLEAN_SURFACE_AND_SITE_ORDERING_SCREEN"
    elif final_status.startswith("PBE_REJECT"):
        next_gate = "BLYP_PP_PROVENANCE_GATE"
    else:
        next_gate = "STAGE_A_HOLD_REVIEW"

    combined = None
    if final_status == "PASS" and selected is not None:
        combined = {
            "ecutwfc_ry": int(selected["ecutwfc_ry"]),
            "ecutrho_ry": int(selected["ecutrho_ry"]),
            "bulk_kmesh": int(selected["kmesh"]),
            "gas_box_angstrom": 18.0,
            "selection_origin": "PROSPECTIVE_STAGE_A_NUMERICAL_EXTENSION_v0.1",
        }

    result = {
        "schema": "co-cu111-pbe-stage-a-numerical-extension-result-v0.1",
        "base_stage_a_status": decision["status"],
        "status": final_status,
        "extension_reason": extension_reason,
        "bulk_extension_gate": bulk_gate,
        "co_base_selection": decision["co_selected"],
        "co_combination_check": co_combination,
        "combined_selected_settings": combined,
        "next_gate": next_gate,
        "provenance": {
            "amendment_sha256": sha256(amendment_path),
            "base_stage_a_result_sha256": sha256(decision_path),
            "bulk_gate_sha256": sha256(bulk_gate_path),
            "scientific_settings_changed": False,
            "kinetic_inputs_used": False,
        },
    }
    write_json(out, result)
    print(json.dumps(result, indent=2))
    print(f"PBE_STAGE_A_EXTENSION_STATUS={final_status}")
    print(f"NEXT_GATE={next_gate}")
    print("SCIENTIFIC_SETTINGS_CHANGED=false")
    print("KINETIC_INPUTS_USED=false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("self-test")
    p.add_argument("--amendment", required=True)
    p.set_defaults(func=command_self_test)

    p = sub.add_parser("bulk-run")
    p.add_argument("--amendment", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--ecutwfc", type=int, required=True)
    p.add_argument("--ecutrho", type=int, required=True)
    p.add_argument("--kmesh", type=int, required=True)
    p.add_argument("--role", choices=["candidate", "reference", "audit"], required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_bulk_run)

    p = sub.add_parser("bulk-gate")
    p.add_argument("--amendment", required=True)
    p.add_argument("--stage-a-decision", required=True)
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_bulk_gate)

    p = sub.add_parser("co-run")
    p.add_argument("--amendment", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--bulk-gate", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--box", type=int, required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_co_run)

    p = sub.add_parser("finalize")
    p.add_argument("--amendment", required=True)
    p.add_argument("--stage-a-decision", required=True)
    p.add_argument("--bulk-gate", required=True)
    p.add_argument("--co-root")
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_finalize)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
