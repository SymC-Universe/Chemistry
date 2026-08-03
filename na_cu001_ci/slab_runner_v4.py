#!/usr/bin/env python3
"""Versioned clean-slab analyzer enforcing the frozen downstream layer floor.

The 64 registered slab calculations and the 1 meV/surface-atom convergence
criterion are unchanged. This wrapper delegates the physical analysis to
slab_runner_v2, then enforces the preregistered requirement that a downstream
slab contain at least seven Cu layers. It can therefore reuse an already
completed raw matrix without rerunning any SCF.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import slab_runner_v2 as v2

DOWNSTREAM_LAYER_FLOOR = 7
RESULT_SCHEMA = "na-cu001-clean-slab-selection-v0.3"


def read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def enforce_floor(result: dict[str, Any], records_root: Path) -> dict[str, Any]:
    if result.get("schema") != RESULT_SCHEMA:
        raise SystemExit("HOLD: unsupported clean-slab result schema")
    if float(result.get("energy_tolerance_mev_per_surface_atom", -1.0)) != float(v2.ENERGY_TOL_MEV):
        raise SystemExit("HOLD: clean-slab tolerance differs from the frozen 1 meV criterion")

    selected = result.get("recommended_smallest")
    if result.get("gate") != "PASS" or not isinstance(selected, dict):
        result["downstream_layer_floor"] = DOWNSTREAM_LAYER_FLOOR
        result["layer_floor_audit"] = {
            "status": "HOLD",
            "reason": "base clean-slab analysis did not produce a PASS selection",
        }
        return result

    diagnostics = result.get("layer_diagnostics_at_selected_vacuum_kmesh") or []
    eligible = sorted(
        int(row["layers"])
        for row in diagnostics
        if int(row.get("layers", -1)) >= DOWNSTREAM_LAYER_FLOOR
        and float(row.get("worst_thicker_difference_mev_per_surface_atom", float("inf")))
        <= float(v2.ENERGY_TOL_MEV)
    )
    if not eligible:
        result["recommended_smallest"] = None
        result["gate"] = "HOLD"
        result["downstream_layer_floor"] = DOWNSTREAM_LAYER_FLOOR
        result["layer_floor_audit"] = {
            "status": "HOLD",
            "reason": "no converged registered slab satisfies the frozen downstream layer floor",
            "eligible_layers_at_or_above_floor": [],
        }
        return result

    chosen_layer = eligible[0]
    selected_vacuum = float(selected["vacuum_angstrom"])
    selected_kmesh = int(selected["kmesh_inplane"])
    rows = [read(path) for path in records_root.rglob("run_record.json")]
    matches = [
        row for row in rows
        if int(row.get("layers", -1)) == chosen_layer
        and float(row.get("vacuum_angstrom", -1.0)) == selected_vacuum
        and int(row.get("kmesh_inplane", -1)) == selected_kmesh
    ]
    if len(matches) != 1:
        raise SystemExit(
            "HOLD: could not resolve exactly one raw source record for the floor-compliant slab"
        )

    original_layer = int(selected["layers"])
    result["recommended_smallest"] = {
        "layers": chosen_layer,
        "vacuum_angstrom": selected_vacuum,
        "kmesh_inplane": selected_kmesh,
        "source_record": matches[0],
    }
    result["downstream_layer_floor"] = DOWNSTREAM_LAYER_FLOOR
    result["layer_floor_audit"] = {
        "status": "PASS",
        "frozen_minimum_layers": DOWNSTREAM_LAYER_FLOOR,
        "base_analyzer_selected_layers": original_layer,
        "final_selected_layers": chosen_layer,
        "selection_changed_only_to_enforce_frozen_floor": original_layer != chosen_layer,
        "energy_tolerance_mev_per_surface_atom": float(v2.ENERGY_TOL_MEV),
        "eligible_layers_at_or_above_floor": eligible,
    }
    result["analysis_entrypoint"] = "slab_runner_v4.py"
    return result


def analyze(args: argparse.Namespace) -> None:
    records_root = Path(args.records).resolve()
    out = Path(args.out).resolve()
    with tempfile.TemporaryDirectory() as tmpdir:
        base_out = Path(tmpdir) / "BASE_CLEAN_SLAB_CONVERGENCE_RESULT.json"
        try:
            v2.analyze(SimpleNamespace(records=str(records_root), out=str(base_out)))
        except SystemExit as exc:
            if not base_out.is_file():
                raise
            base = read(base_out)
            audited = enforce_floor(base, records_root)
            write(out, audited)
            raise SystemExit(exc.code)
        base = read(base_out)
    audited = enforce_floor(base, records_root)
    write(out, audited)
    print(json.dumps(audited, indent=2))
    if audited.get("gate") != "PASS":
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    analyze(args)


if __name__ == "__main__":
    main()
