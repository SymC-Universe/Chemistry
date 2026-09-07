#!/usr/bin/env python3
"""Prospective v0.4 bulk-to-surface bridge verifier for Na/Cu(001).

Frozen before the audited v0.4 bulk result exists. The verifier does not choose
or alter a bulk setting. It independently checks the published v0.4 decision,
handoff, protocol, and all 46 EOS summaries before emitting the compact bridge
record consumed by the corrected surface workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RESULT_SCHEMA = "na-cu001-bulk-selection-v0.4"
HANDOFF_SCHEMA = "na-cu001-bulk-to-slab-handoff-v0.4"
PROTOCOL_SCHEMA = "na-cu001-bulk-extension-protocol-v0.1"
BRIDGE_SCHEMA = "na-cu001-audited-bulk-downstream-bridge-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def pair(row: dict[str, Any]) -> tuple[int, int]:
    return int(row["ecutwfc_ry"]), int(row["kmesh"])


def cost(row: dict[str, Any]) -> float:
    return float(row["ecutwfc_ry"]) ** 1.5 * float(row["kmesh"]) ** 3


def compare(row: dict[str, Any], reference: dict[str, Any], da_max: float, de_max: float) -> dict[str, Any]:
    da = abs(float(row["fit"]["a0_angstrom"]) - float(reference["fit"]["a0_angstrom"]))
    de = abs(float(row["fit"]["e0_ev_per_atom"]) - float(reference["fit"]["e0_ev_per_atom"]))
    return {
        "delta_a_angstrom": da,
        "delta_e_ev_per_atom": de,
        "delta_a_pass": da <= da_max,
        "delta_e_pass": de <= de_max,
        "pass": da <= da_max and de <= de_max,
    }


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def expected_pairs(protocol: dict[str, Any]) -> tuple[set[tuple[int, int]], tuple[int, int], tuple[int, int]]:
    hist = protocol["reused_historical_candidates"]
    ext = protocol["extension_candidates"]
    candidates = {(int(e), int(k)) for e in hist["ecuts_ry"] for k in hist["kmeshes"]}
    candidates |= {(int(e), int(k)) for e in ext["ecuts_ry"] for k in ext["kmeshes"]}
    reference = (int(protocol["reference"]["ecutwfc_ry"]), int(protocol["reference"]["kmesh"]))
    audit = (int(protocol["independent_reference_audit"]["ecutwfc_ry"]), int(protocol["independent_reference_audit"]["kmesh"]))
    if len(candidates) != int(hist["expected_count"]) + int(ext["expected_count"]):
        raise SystemExit("HOLD: protocol candidate cardinality mismatch")
    if reference in candidates or audit in candidates or reference == audit:
        raise SystemExit("HOLD: reference or audit is eligible as a candidate")
    return candidates, reference, audit


def verify_summary_files(rows: list[dict[str, Any]], summaries: Path) -> list[dict[str, str]]:
    expected_names: set[str] = set()
    verified: list[dict[str, str]] = []
    for row in rows:
        source = Path(str(row.get("source_summary", ""))).name
        expected_hash = str(row.get("source_sha256", ""))
        if not source or len(expected_hash) != 64:
            raise SystemExit("HOLD: result row lacks a registered summary path/hash")
        if source in expected_names:
            raise SystemExit(f"HOLD: duplicate summary basename {source}")
        expected_names.add(source)
        path = summaries / source
        if not path.is_file():
            raise SystemExit(f"HOLD: missing EOS summary {source}")
        actual = sha256(path)
        if actual != expected_hash:
            raise SystemExit(f"HOLD: EOS summary hash mismatch {source}")
        data = load(path)
        if int(data.get("ecutwfc_ry", -1)) != int(row["ecutwfc_ry"]) or int(data.get("kmesh", -1)) != int(row["kmesh"]):
            raise SystemExit(f"HOLD: EOS summary identity mismatch {source}")
        records = data.get("records") or []
        if len(records) != 6:
            raise SystemExit(f"HOLD: incomplete six-point EOS {source}")
        for record in records:
            if record.get("returncode") != 0 or not record.get("job_done") or not record.get("scf_converged"):
                raise SystemExit(f"HOLD: failed or unconverged SCF retained in {source}")
            if record.get("final_energy_ev_per_atom") is None:
                raise SystemExit(f"HOLD: missing final energy in {source}")
            if len(str(record.get("input_sha256", ""))) != 64 or len(str(record.get("output_sha256", ""))) != 64:
                raise SystemExit(f"HOLD: missing SCF input/output hash in {source}")
        verified.append({"path": source, "sha256": actual})
    actual_names = {p.name for p in summaries.glob("summary_e*_k*.json")}
    unexpected = sorted(actual_names - expected_names)
    missing = sorted(expected_names - actual_names)
    if unexpected or missing:
        raise SystemExit(f"HOLD: summary directory mismatch missing={missing} unexpected={unexpected}")
    return sorted(verified, key=lambda x: x["path"])


def verify(args: argparse.Namespace) -> None:
    result_path = Path(args.result).resolve()
    handoff_path = Path(args.handoff).resolve()
    protocol_path = Path(args.protocol).resolve()
    summaries = Path(args.summaries).resolve()
    result = load(result_path)
    handoff = load(handoff_path)
    protocol = load(protocol_path)

    if result.get("schema") != RESULT_SCHEMA or result.get("gate") != "PASS" or result.get("status") != "PASS":
        raise SystemExit("HOLD: source bulk result is not v0.4 PASS")
    if handoff.get("schema") != HANDOFF_SCHEMA or handoff.get("scientific_status") != "bulk_convergence_passed_slab_not_yet_run":
        raise SystemExit("HOLD: source bulk handoff is not v0.4 PASS")
    if protocol.get("schema") != PROTOCOL_SCHEMA or protocol.get("status") != "FROZEN_AFTER_V0.3_HOLD_BEFORE_EXTENSION_RESULTS":
        raise SystemExit("HOLD: source bulk extension protocol is not frozen")
    if handoff.get("source_result", {}).get("sha256") != sha256(result_path):
        raise SystemExit("HOLD: handoff/result hash mismatch")
    if result.get("protocol", {}).get("sha256") != sha256(protocol_path) or handoff.get("protocol", {}).get("sha256") != sha256(protocol_path):
        raise SystemExit("HOLD: protocol hash mismatch")

    candidates_expected, reference_key, audit_key = expected_pairs(protocol)
    reference = result.get("reference") or {}
    audit = result.get("independent_reference_audit") or {}
    if pair(reference) != reference_key or pair(audit) != audit_key:
        raise SystemExit("HOLD: reference/audit identity mismatch")

    da_max = float(protocol["joint_gate"]["delta_a_max_angstrom"])
    de_max = float(protocol["joint_gate"]["delta_e_max_ev_per_atom"])
    audit_check = compare(reference, audit, da_max, de_max)
    reported_audit = result.get("reference_audit_gate") or {}
    for key in ("delta_a_angstrom", "delta_e_ev_per_atom"):
        if not close(audit_check[key], reported_audit.get(key, float("nan"))):
            raise SystemExit(f"HOLD: reference audit {key} mismatch")
    if audit_check["pass"] is not True or reported_audit.get("pass") is not True:
        raise SystemExit("HOLD: independent reference audit did not pass")

    candidates = result.get("candidates") or []
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    for row in candidates:
        key = pair(row)
        if key in by_key:
            raise SystemExit(f"HOLD: duplicate candidate {key}")
        by_key[key] = row
    if set(by_key) != candidates_expected:
        raise SystemExit("HOLD: v0.4 candidate universe differs from frozen protocol")

    passing: list[dict[str, Any]] = []
    for row in candidates:
        check = compare(row, reference, da_max, de_max)
        reported = row.get("joint_gate_against_audited_reference") or {}
        for key in ("delta_a_angstrom", "delta_e_ev_per_atom"):
            if not close(check[key], reported.get(key, float("nan"))):
                raise SystemExit(f"HOLD: candidate {pair(row)} {key} mismatch")
        if bool(check["pass"]) != bool(reported.get("pass")):
            raise SystemExit(f"HOLD: candidate {pair(row)} gate mismatch")
        expected_cost = cost(row)
        if not close(expected_cost, row.get("estimated_cost_score", float("nan")), tol=max(1e-9, expected_cost * 1e-12)):
            raise SystemExit(f"HOLD: candidate {pair(row)} cost mismatch")
        if check["pass"]:
            passing.append(row)
    if not passing:
        raise SystemExit("HOLD: no candidate passes independently recomputed joint gate")
    passing.sort(key=lambda r: (cost(r), int(r["ecutwfc_ry"]), int(r["kmesh"])))
    expected_selected = passing[0]
    selected = result.get("recommended_smallest_cost_candidate") or {}
    if pair(selected) != pair(expected_selected):
        raise SystemExit("HOLD: selected candidate is not the frozen minimum-cost joint pass")
    if pair(selected) in {reference_key, audit_key}:
        raise SystemExit("HOLD: reference or audit selected itself")

    hs = handoff.get("selected_bulk_settings") or {}
    if int(hs.get("ecutwfc_ry", -1)) != int(selected["ecutwfc_ry"]) or int((hs.get("kmesh_cubic") or [-1])[0]) != int(selected["kmesh"]):
        raise SystemExit("HOLD: selected settings disagree between result and handoff")
    if not close(hs.get("equilibrium_lattice_constant_angstrom", float("nan")), selected["fit"]["a0_angstrom"]):
        raise SystemExit("HOLD: selected lattice constant disagrees between result and handoff")
    if not close(hs.get("equilibrium_energy_ev_per_atom", float("nan")), selected["fit"]["e0_ev_per_atom"]):
        raise SystemExit("HOLD: selected energy disagrees between result and handoff")

    all_rows = candidates + [reference, audit]
    if len(all_rows) != 46:
        raise SystemExit(f"HOLD: expected 46 EOS rows, found {len(all_rows)}")
    verified_summaries = verify_summary_files(all_rows, summaries)

    output = {
        "schema": BRIDGE_SCHEMA,
        "status": "PASS",
        "scientific_status": "audited_v0.4_bulk_passed_surface_not_yet_run",
        "source_artifacts": [
            {"path": result_path.name, "sha256": sha256(result_path), "schema": RESULT_SCHEMA},
            {"path": handoff_path.name, "sha256": sha256(handoff_path), "schema": HANDOFF_SCHEMA},
            {"path": protocol_path.name, "sha256": sha256(protocol_path), "schema": PROTOCOL_SCHEMA},
        ],
        "verified_eos_summaries": verified_summaries,
        "verified_eos_count": len(verified_summaries),
        "verified_scf_count": 6 * len(verified_summaries),
        "reference_audit_gate": audit_check,
        "selected_bulk_settings": hs,
        "selected_candidate_gate": compare(selected, reference, da_max, de_max),
        "selection_verification": {
            "candidate_count": len(candidates),
            "passing_candidate_count": len(passing),
            "selected_pair": list(pair(selected)),
            "selected_cost_score": cost(selected),
            "rule": "minimum frozen estimated cost among independently recomputed joint-pass candidates",
        },
        "frozen_criteria": {"delta_a_max_angstrom": da_max, "delta_e_max_ev_per_atom": de_max},
        "next_gate": "registered_esm_bc1_clean_cu001_slab_matrix",
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True)
    p.add_argument("--handoff", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--summaries", required=True)
    p.add_argument("--out", required=True)
    verify(p.parse_args())


if __name__ == "__main__":
    main()
