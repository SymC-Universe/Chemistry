#!/usr/bin/env python3
"""Fail-closed slab handoff carrying the definitive C7 proof bundle.

This version preserves every later V2/V3 physical command. It replaces only
`slab-handoff`, requiring the strict nonterminal holdout audit, the frozen
seven-layer floor, and the complete ESM raw/input audit before C8 can begin.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import closure_engine_v2 as v2
import closure_engine_v3 as v3

SLAB_RESULT_SCHEMA = "na-cu001-clean-slab-selection-v0.3"
SLAB_HANDOFF_SCHEMA = "na-cu001-clean-slab-to-relaxation-handoff-v0.3"
STRICT_HOLDOUT_SCHEMA = "na-cu001-clean-slab-strict-holdout-audit-v0.1"
RAW_INPUT_AUDIT_SCHEMA = "na-cu001-esm-centered-raw-audit-v0.3"
GEOMETRY_SCHEMA = "na-cu001-esm-centered-slab-v0.2"


def require_slab_proof(result: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    floor = result.get("layer_floor_audit") or {}
    holdout = result.get("strict_holdout_audit") or {}
    geometry = result.get("esm_geometry_audit") or {}
    source = selected.get("source_record") or {}
    source_geometry = source.get("geometry_convention") or {}

    if floor.get("status") != "PASS" or int(selected.get("layers", 0)) < 7:
        raise SystemExit("HOLD: frozen seven-layer floor is not proven")
    if holdout.get("schema") != STRICT_HOLDOUT_SCHEMA or holdout.get("status") != "PASS":
        raise SystemExit("HOLD: strict terminal-holdout audit is not PASS")
    terminal = holdout.get("terminal_holdouts") or {}
    if bool(terminal.get("eligible_for_selection", True)):
        raise SystemExit("HOLD: terminal holdouts were marked selectable")
    try:
        nonterminal = (
            int(selected["layers"]) < int(terminal["layers"])
            and float(selected["vacuum_angstrom"]) < float(terminal["vacuum_angstrom"])
            and int(selected["kmesh_inplane"]) < int(terminal["kmesh_inplane"])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"HOLD: malformed strict holdout selection: {exc}") from exc
    if not nonterminal:
        raise SystemExit("HOLD: a terminal slab setting selected itself")
    if [float(selected["vacuum_angstrom"]), int(selected["kmesh_inplane"])] != holdout.get(
        "selected_vacuum_k_pair"
    ):
        raise SystemExit("HOLD: selected vacuum/k pair disagrees with strict holdout audit")
    if int(selected["layers"]) != int(holdout.get("selected_layers", -1)):
        raise SystemExit("HOLD: selected layer disagrees with strict holdout audit")

    if geometry.get("schema") != RAW_INPUT_AUDIT_SCHEMA or geometry.get("status") != "PASS":
        raise SystemExit("HOLD: ESM raw/input audit is not PASS")
    if geometry.get("geometry_schema") != GEOMETRY_SCHEMA:
        raise SystemExit("HOLD: ESM geometry schema is not definitive")
    if int(geometry.get("verified_record_count", -1)) != 64:
        raise SystemExit("HOLD: clean-slab raw-record inventory is incomplete")
    if int(geometry.get("verified_input_count", -1)) != 64:
        raise SystemExit("HOLD: clean-slab QE-input inventory is incomplete")
    if geometry.get("atomic_position_card") != "angstrom":
        raise SystemExit("HOLD: slab positions were not explicitly emitted in angstrom")
    if not geometry.get("all_slabs_symmetric_about_zero"):
        raise SystemExit("HOLD: slab z=0 symmetry was not proven")
    if not geometry.get("vacuum_split_equally_between_open_boundaries"):
        raise SystemExit("HOLD: equal ESM vacuum halves were not proven")
    if not geometry.get("all_input_hashes_match_run_records"):
        raise SystemExit("HOLD: QE input hashes do not match run records")
    if not geometry.get("all_inputs_set_esm_bc1"):
        raise SystemExit("HOLD: ESM bc1 was not proven for every QE input")

    if source_geometry.get("schema") != GEOMETRY_SCHEMA:
        raise SystemExit("HOLD: selected raw source record lacks definitive geometry metadata")
    if source_geometry.get("atomic_position_card") != "angstrom":
        raise SystemExit("HOLD: selected raw source record did not use angstrom positions")
    if source_geometry.get("coordinate_origin") != "cartesian_z_zero":
        raise SystemExit("HOLD: selected raw source record is not centered at Cartesian z=0")
    if not source_geometry.get("symmetric_about_zero"):
        raise SystemExit("HOLD: selected raw source record is not symmetric about z=0")

    return {
        "layer_floor_audit": floor,
        "strict_holdout_audit": holdout,
        "esm_geometry_audit": geometry,
        "selected_source_geometry": source_geometry,
    }


def command_slab_handoff(args: Any) -> None:
    result_path = Path(args.slab_result).resolve()
    bulk_path = Path(args.bulk_handoff).resolve()
    result = v2.read_json(result_path)
    v2.require(result, SLAB_RESULT_SCHEMA)
    selected = result.get("recommended_smallest")
    if not isinstance(selected, dict):
        raise SystemExit("HOLD: slab result lacks a selected nonterminal setting")
    proof = require_slab_proof(result, selected)

    bulk, _, bridge, bulk_result_path, bridge_path = v3.load_v04_bundle(bulk_path)
    source = selected.get("source_record") or {}
    bridge_selected = bridge.get("selected_bulk_settings") or {}
    if int(source.get("ecutwfc_ry", -1)) != int(bridge_selected.get("ecutwfc_ry", -2)):
        raise SystemExit("HOLD: slab records do not use audited v0.4 cutoff")
    if int(source.get("ecutrho_ry", -1)) != int(bridge_selected.get("ecutrho_ry", -2)):
        raise SystemExit("HOLD: slab records do not use audited v0.4 density cutoff")
    if int(source.get("bulk_kmesh", -1)) != int((bridge_selected.get("kmesh_cubic") or [-2])[0]):
        raise SystemExit("HOLD: slab records do not use audited v0.4 bulk mesh provenance")

    selected_layers = int(selected["layers"])
    selected_vacuum = float(selected["vacuum_angstrom"])
    selected_kmesh = int(selected["kmesh_inplane"])
    handoff = {
        "schema": SLAB_HANDOFF_SCHEMA,
        "status": "PASS",
        "system": "clean Cu(001)",
        "selected_slab_settings": {
            "layers": selected_layers,
            "convergence_selected_layers": selected_layers,
            "vacuum_angstrom": selected_vacuum,
            "kmesh_inplane": selected_kmesh,
            "a0_angstrom": float(source["a0_angstrom"]),
            "ecutwfc_ry": float(source["ecutwfc_ry"]),
            "ecutrho_ry": float(source["ecutrho_ry"]),
            "bulk_kmesh": int(source["bulk_kmesh"]),
            "bulk_energy_ev_per_atom": float(source["e0_ev_per_atom"]),
            "surface_cell": "primitive Cu(001), area a0^2/2",
            "electrostatic_convention": result.get("electrostatic_convention")
            or {"assume_isolated": "esm", "esm_bc": "bc1"},
            "coordinate_convention": {
                "atomic_position_card": "angstrom",
                "origin": "cartesian_z_zero",
                "vacuum_distribution": "equal halves at +/-Lz/2",
            },
        },
        "bulk_v04_provenance": {
            "bulk_handoff": v2.artifact(bulk_path),
            "bulk_result": v2.artifact(bulk_result_path),
            "audited_bridge": v2.artifact(bridge_path),
            "reference_audit_gate": bridge["reference_audit_gate"],
            "selection_verification": bridge.get("selection_verification"),
        },
        "slab_convergence_provenance": {
            "slab_result": v2.artifact(result_path),
            **proof,
        },
        "convergence_rule": {
            "surface_excess_tolerance_mev_per_surface_atom": float(
                result["energy_tolerance_mev_per_surface_atom"]
            ),
            "selected_vacuum_kmesh": [selected_vacuum, selected_kmesh],
            "selected_layers": selected_layers,
            "terminal_holdouts": proof["strict_holdout_audit"]["terminal_holdouts"],
            "terminal_points_ineligible": True,
            "downstream_layer_rule": "selected slab is at least 7 layers and strictly thinner than the terminal holdout",
        },
        "input_artifacts": [
            v2.artifact(result_path),
            v2.artifact(bulk_path),
            v2.artifact(bulk_result_path),
            v2.artifact(bridge_path),
        ],
        "next_gate": "electrostatic_parity",
    }
    v2.write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))


def main() -> None:
    v2.command_slab_handoff = command_slab_handoff
    v2.command_resolve_na = v3.command_resolve_na
    args = v2.build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
