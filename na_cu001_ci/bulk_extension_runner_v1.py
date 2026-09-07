#!/usr/bin/env python3
"""Fail-closed post-HOLD Cu bulk convergence extension for Na/Cu(001).

The v0.3 route correctly stopped because no original candidate met the frozen
energy gate. This module does not relax that gate. It evaluates a preregistered
higher-cost candidate grid against a reference that must first reproduce an
independent still-higher audit point. Experimental Na/Cu(001) quantities are
absent from construction and selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import bulk_runner_v2 as legacy_bulk

RESULT_SCHEMA = "na-cu001-bulk-selection-v0.4"
HANDOFF_SCHEMA = "na-cu001-bulk-to-slab-handoff-v0.4"
PROTOCOL_SCHEMA = "na-cu001-bulk-extension-protocol-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_protocol(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get("schema") != PROTOCOL_SCHEMA:
        raise SystemExit("HOLD: unsupported bulk extension protocol schema")
    if data.get("status") != "FROZEN_AFTER_V0.3_HOLD_BEFORE_EXTENSION_RESULTS":
        raise SystemExit("HOLD: bulk extension protocol is not frozen")
    return data


def candidate_key(row: dict[str, Any]) -> tuple[int, int]:
    return int(row["ecutwfc_ry"]), int(row["kmesh"])


def cost_score(row: dict[str, Any]) -> float:
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


def expected_pairs(protocol: dict[str, Any]) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    hist = protocol["reused_historical_candidates"]
    ext = protocol["extension_candidates"]
    historical = {(int(e), int(k)) for e in hist["ecuts_ry"] for k in hist["kmeshes"]}
    extension = {(int(e), int(k)) for e in ext["ecuts_ry"] for k in ext["kmeshes"]}
    if len(historical) != int(hist["expected_count"]) or len(extension) != int(ext["expected_count"]):
        raise SystemExit("HOLD: protocol candidate cardinality is internally inconsistent")
    return historical, extension


def analyze(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve()
    protocol = load_protocol(protocol_path)
    rows = legacy_bulk.load_fit_rows(Path(args.summaries).resolve())
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    duplicates: list[tuple[int, int]] = []
    for row in rows:
        key = candidate_key(row)
        if key in by_key:
            duplicates.append(key)
        by_key[key] = row
    if duplicates:
        raise SystemExit(f"HOLD: duplicate EOS summaries for {sorted(set(duplicates))}")

    historical, extension = expected_pairs(protocol)
    reference_key = (int(protocol["reference"]["ecutwfc_ry"]), int(protocol["reference"]["kmesh"]))
    audit_key = (int(protocol["independent_reference_audit"]["ecutwfc_ry"]), int(protocol["independent_reference_audit"]["kmesh"]))
    required = historical | extension | {reference_key, audit_key}
    missing = sorted(required - set(by_key))
    unexpected = sorted(set(by_key) - required)
    if missing:
        raise SystemExit(f"HOLD: missing registered EOS summaries: {missing}")
    if unexpected:
        raise SystemExit(f"HOLD: unregistered EOS summaries present: {unexpected}")

    da_max = float(protocol["joint_gate"]["delta_a_max_angstrom"])
    de_max = float(protocol["joint_gate"]["delta_e_max_ev_per_atom"])
    reference = by_key[reference_key]
    audit = by_key[audit_key]
    reference_audit_gate = compare(reference, audit, da_max, de_max)

    candidates: list[dict[str, Any]] = []
    for key in sorted(historical | extension):
        row = by_key[key]
        row["candidate_origin"] = "historical_v0.3" if key in historical else "post_hold_extension_v0.4"
        row["estimated_cost_score"] = cost_score(row)
        row["joint_gate_against_audited_reference"] = compare(row, reference, da_max, de_max)
        candidates.append(row)

    admitted = [r for r in candidates if r["joint_gate_against_audited_reference"]["pass"]]
    admitted.sort(key=lambda r: (r["estimated_cost_score"], int(r["ecutwfc_ry"]), int(r["kmesh"])))
    selection = admitted[0] if reference_audit_gate["pass"] and admitted else None
    for index, row in enumerate(sorted(candidates, key=lambda r: (r["estimated_cost_score"], int(r["ecutwfc_ry"]), int(r["kmesh"]))), start=1):
        row["registered_cost_rank"] = index

    gate = "PASS" if selection is not None else "HOLD"
    hold_reasons: list[str] = []
    if not reference_audit_gate["pass"]:
        hold_reasons.append("reference_140Ry_22cubed_failed_independent_150Ry_24cubed_audit")
    if not admitted:
        hold_reasons.append("no_registered_candidate_passed_unchanged_joint_gate")

    result = {
        "schema": RESULT_SCHEMA,
        "status": gate,
        "registration_status": "extension_frozen_after_v0.3_hold_before_v0.4_results",
        "system_role": "construction_convergence_only_no_kinetic_targets",
        "triggering_hold": protocol["triggering_hold"],
        "protocol": {"path": protocol_path.name, "sha256": sha256(protocol_path), "schema": protocol["schema"]},
        "reference": reference,
        "independent_reference_audit": audit,
        "reference_audit_gate": reference_audit_gate,
        "candidates": candidates,
        "joint_criteria": {"delta_a_max_angstrom": da_max, "delta_e_max_ev_per_atom": de_max},
        "selection_rule": protocol["selection_order"],
        "recommended_smallest_cost_candidate": selection,
        "hold_reasons": hold_reasons,
        "gate": gate,
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if gate != "PASS":
        raise SystemExit(2)


def make_handoff(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve()
    protocol = load_protocol(protocol_path)
    result_path = Path(args.result).resolve()
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    if result.get("schema") != RESULT_SCHEMA or result.get("gate") != "PASS":
        raise SystemExit("HOLD: source bulk extension result is not v0.4 PASS")
    if not (result.get("reference_audit_gate") or {}).get("pass"):
        raise SystemExit("HOLD: v0.4 reference audit did not pass")
    selected = result.get("recommended_smallest_cost_candidate")
    if not selected:
        raise SystemExit("HOLD: v0.4 result lacks a selected candidate")
    fit = selected["fit"]
    all_rows = list(result["candidates"]) + [result["reference"], result["independent_reference_audit"]]
    handoff = {
        "schema": HANDOFF_SCHEMA,
        "scientific_status": "bulk_convergence_passed_slab_not_yet_run",
        "registration_status": result["registration_status"],
        "system_role": result["system_role"],
        "source_result": {
            "path": result_path.name,
            "sha256": hashlib.sha256(result_bytes).hexdigest(),
            "selection_rule": result["selection_rule"],
        },
        "protocol": {"path": protocol_path.name, "sha256": sha256(protocol_path), "schema": protocol["schema"]},
        "input_artifacts": ([
            {"path": result_path.name, "sha256": hashlib.sha256(result_bytes).hexdigest()},
            {"path": protocol_path.name, "sha256": sha256(protocol_path)},
        ] + [{"path": row["source_summary"], "sha256": row["source_sha256"]} for row in all_rows]),
        "selected_bulk_settings": {
            "ecutwfc_ry": int(selected["ecutwfc_ry"]),
            "ecutrho_ry": int(selected["ecutrho_ry"]),
            "kmesh_cubic": [int(selected["kmesh"])] * 3,
            "equilibrium_lattice_constant_angstrom": float(fit["a0_angstrom"]),
            "equilibrium_energy_ev_per_atom": float(fit["e0_ev_per_atom"]),
            "quadratic_fit_rms_residual_mev_per_atom": float(fit["rms_residual_mev_per_atom"]),
            "estimated_cost_score": float(selected["estimated_cost_score"]),
            "registered_cost_rank": int(selected["registered_cost_rank"]),
            "candidate_origin": selected["candidate_origin"],
        },
        "joint_gate": selected["joint_gate_against_audited_reference"],
        "reference_settings": {
            "ecutwfc_ry": int(result["reference"]["ecutwfc_ry"]),
            "ecutrho_ry": int(result["reference"]["ecutrho_ry"]),
            "kmesh_cubic": [int(result["reference"]["kmesh"])] * 3,
            "independent_audit": {
                "ecutwfc_ry": int(result["independent_reference_audit"]["ecutwfc_ry"]),
                "ecutrho_ry": int(result["independent_reference_audit"]["ecutrho_ry"]),
                "kmesh_cubic": [int(result["independent_reference_audit"]["kmesh"])] * 3,
                "gate": result["reference_audit_gate"],
            },
            "interpretation": "The 140 Ry/22^3 reference passed an unchanged-threshold reproduction audit against 150 Ry/24^3; this remains a finite numerical reference, not an absolute complete-basis proof.",
        },
        "frozen_method": {
            "code": "Quantum ESPRESSO PWscf",
            "code_version": "7.6",
            "exchange_correlation": "PBE",
            "pseudopotential": protocol["software_and_pseudopotential_identity"]["cu_upf_filename"],
            "historical_grid": protocol["reused_historical_candidates"],
            "extension_grid": protocol["extension_candidates"],
            "reference": protocol["reference"],
            "independent_reference_audit": protocol["independent_reference_audit"],
            "bulk_lattice_grid_angstrom": protocol["lattice_grid_angstrom"],
            "joint_gate": protocol["joint_gate"],
        },
        "run_provenance": {
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "commit_sha": os.environ.get("GITHUB_SHA"),
            "ref": os.environ.get("GITHUB_REF"),
        },
        "next_gate": "explicit_preregistered_cu001_slab_convergence",
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(handoff, indent=2) + "\n")
    print(json.dumps(handoff, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    ana = sub.add_parser("analyze")
    ana.add_argument("--protocol", required=True)
    ana.add_argument("--summaries", required=True)
    ana.add_argument("--out", required=True)
    hand = sub.add_parser("handoff")
    hand.add_argument("--protocol", required=True)
    hand.add_argument("--result", required=True)
    hand.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "analyze":
        analyze(args)
    else:
        make_handoff(args)


if __name__ == "__main__":
    main()
