#!/usr/bin/env python3
"""Versioned clean-slab analyzer with strict terminal holdouts.

The registered 64 calculations and the 1 meV/surface-atom criterion are
unchanged. The largest vacuum, densest k mesh, and thickest slab are treated as
holdouts and may never select themselves. A downstream slab must contain at
least seven Cu layers and must remain converged against strictly larger
registered settings.
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
HOLDOUT_AUDIT_SCHEMA = "na-cu001-clean-slab-strict-holdout-audit-v0.1"


def read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def hold(result: dict[str, Any], reason: str, audit: dict[str, Any]) -> dict[str, Any]:
    result["recommended_smallest"] = None
    result["gate"] = "HOLD"
    result["next_gate"] = None
    result["downstream_layer_floor"] = DOWNSTREAM_LAYER_FLOOR
    audit["status"] = "HOLD"
    audit["reason"] = reason
    result["strict_holdout_audit"] = audit
    result["layer_floor_audit"] = {
        "status": "HOLD",
        "frozen_minimum_layers": DOWNSTREAM_LAYER_FLOOR,
        "reason": reason,
    }
    result["analysis_entrypoint"] = "slab_runner_v4.py"
    return result


def enforce_strict_holdouts(
    result: dict[str, Any], records_root: Path
) -> dict[str, Any]:
    if result.get("schema") != RESULT_SCHEMA:
        raise SystemExit("HOLD: unsupported clean-slab result schema")
    tolerance = float(result.get("energy_tolerance_mev_per_surface_atom", -1.0))
    if tolerance != float(v2.ENERGY_TOL_MEV):
        raise SystemExit("HOLD: clean-slab tolerance differs from the frozen 1 meV criterion")

    grid = result.get("registered_grid") or {}
    layers = sorted(int(value) for value in grid.get("layers", []))
    vacuums = sorted(float(value) for value in grid.get("vacuum_angstrom", []))
    kmeshes = sorted(int(value) for value in grid.get("kmesh_inplane", []))
    if layers != sorted(v2.LAYERS) or vacuums != sorted(float(v) for v in v2.VACUUM):
        raise SystemExit("HOLD: registered layer or vacuum grid differs from the frozen matrix")
    if len(kmeshes) != 4 or len(set(kmeshes)) != 4:
        raise SystemExit("HOLD: registered k-mesh grid is not the frozen four-point matrix")

    max_layer = max(layers)
    max_vacuum = max(vacuums)
    max_kmesh = max(kmeshes)
    audit: dict[str, Any] = {
        "schema": HOLDOUT_AUDIT_SCHEMA,
        "status": "PENDING",
        "energy_tolerance_mev_per_surface_atom": tolerance,
        "terminal_holdouts": {
            "layers": max_layer,
            "vacuum_angstrom": max_vacuum,
            "kmesh_inplane": max_kmesh,
            "eligible_for_selection": False,
        },
        "selection_requires_strictly_larger_layer": True,
        "selection_requires_strictly_larger_vacuum": True,
        "selection_requires_strictly_denser_kmesh": True,
    }

    fits = result.get("surface_fit_diagnostics") or []
    fit_map: dict[tuple[float, int], dict[str, Any]] = {}
    for row in fits:
        key = (float(row["vacuum_angstrom"]), int(row["kmesh_inplane"]))
        if key in fit_map:
            raise SystemExit(f"HOLD: duplicate surface-fit diagnostic for {key}")
        fit_map[key] = row
    expected_vk = {(v, k) for v in vacuums for k in kmeshes}
    if set(fit_map) != expected_vk:
        raise SystemExit("HOLD: surface-fit diagnostics do not cover the frozen vacuum/k grid")

    vk_diagnostics: list[dict[str, Any]] = []
    eligible_vk: list[tuple[float, int]] = []
    for vacuum in vacuums:
        for kmesh in kmeshes:
            value = float(fit_map[(vacuum, kmesh)]["surface_excess_ev_per_surface_atom"])
            strict_rows = [
                (vv, kk, float(fit_map[(vv, kk)]["surface_excess_ev_per_surface_atom"]))
                for vv in vacuums
                for kk in kmeshes
                if vv >= vacuum
                and kk >= kmesh
                and (vv > vacuum or kk > kmesh)
            ]
            same_k_larger_vacuum = [row for row in strict_rows if row[1] == kmesh and row[0] > vacuum]
            same_vacuum_denser_k = [row for row in strict_rows if row[0] == vacuum and row[1] > kmesh]
            nonterminal = vacuum < max_vacuum and kmesh < max_kmesh
            worst = (
                max(abs(value - row[2]) * 1000.0 for row in strict_rows)
                if strict_rows
                else None
            )
            passed = bool(
                nonterminal
                and same_k_larger_vacuum
                and same_vacuum_denser_k
                and worst is not None
                and worst <= tolerance
            )
            diagnostic = {
                "vacuum_angstrom": vacuum,
                "kmesh_inplane": kmesh,
                "strictly_larger_comparison_count": len(strict_rows),
                "same_k_larger_vacuum_count": len(same_k_larger_vacuum),
                "same_vacuum_denser_k_count": len(same_vacuum_denser_k),
                "worst_strict_difference_mev_per_surface_atom": worst,
                "terminal_self_selection_excluded": not nonterminal,
                "pass": passed,
            }
            vk_diagnostics.append(diagnostic)
            if passed:
                eligible_vk.append((vacuum, kmesh))

    audit["vacuum_k_diagnostics"] = vk_diagnostics
    if not eligible_vk:
        audit["eligible_vacuum_k_pairs"] = []
        return hold(
            result,
            "no nonterminal vacuum/k pair passes against stricter registered holdouts",
            audit,
        )

    eligible_vk.sort(key=lambda pair: (pair[0], pair[1]))
    selected_vacuum, selected_kmesh = eligible_vk[0]
    audit["eligible_vacuum_k_pairs"] = [list(pair) for pair in eligible_vk]
    audit["selected_vacuum_k_pair"] = [selected_vacuum, selected_kmesh]

    rows = [read(path) for path in records_root.rglob("run_record.json")]
    by_key: dict[tuple[int, float, int], dict[str, Any]] = {}
    for row in rows:
        key = (
            int(row.get("layers", -1)),
            float(row.get("vacuum_angstrom", -1.0)),
            int(row.get("kmesh_inplane", -1)),
        )
        if key in by_key:
            raise SystemExit(f"HOLD: duplicate raw slab record for {key}")
        by_key[key] = row

    layer_diagnostics: list[dict[str, Any]] = []
    eligible_layers: list[int] = []
    for layer in layers:
        key = (layer, selected_vacuum, selected_kmesh)
        if key not in by_key:
            raise SystemExit(f"HOLD: raw source record missing for {key}")
        value = float(by_key[key]["bulk_referenced_surface_excess_ev_per_surface_atom"])
        stricter = [
            (
                thicker,
                float(
                    by_key[(thicker, selected_vacuum, selected_kmesh)][
                        "bulk_referenced_surface_excess_ev_per_surface_atom"
                    ]
                ),
            )
            for thicker in layers
            if thicker > layer
        ]
        worst = (
            max(abs(value - stricter_value) * 1000.0 for _, stricter_value in stricter)
            if stricter
            else None
        )
        nonterminal = layer < max_layer
        passed = bool(
            layer >= DOWNSTREAM_LAYER_FLOOR
            and nonterminal
            and stricter
            and worst is not None
            and worst <= tolerance
        )
        layer_diagnostics.append(
            {
                "layers": layer,
                "strictly_thicker_comparison_count": len(stricter),
                "worst_strict_difference_mev_per_surface_atom": worst,
                "meets_downstream_layer_floor": layer >= DOWNSTREAM_LAYER_FLOOR,
                "terminal_self_selection_excluded": not nonterminal,
                "pass": passed,
            }
        )
        if passed:
            eligible_layers.append(layer)

    result["layer_diagnostics_at_selected_vacuum_kmesh"] = layer_diagnostics
    audit["layer_diagnostics"] = layer_diagnostics
    audit["eligible_layers"] = eligible_layers
    if not eligible_layers:
        return hold(
            result,
            "no nonterminal slab at or above seven layers passes against a strictly thicker holdout",
            audit,
        )

    chosen_layer = min(eligible_layers)
    selected_key = (chosen_layer, selected_vacuum, selected_kmesh)
    selected_record = by_key[selected_key]
    result["recommended_smallest"] = {
        "layers": chosen_layer,
        "vacuum_angstrom": selected_vacuum,
        "kmesh_inplane": selected_kmesh,
        "source_record": selected_record,
    }
    result["gate"] = "PASS"
    result["next_gate"] = "clean_surface_relaxation"
    result["downstream_layer_floor"] = DOWNSTREAM_LAYER_FLOOR
    audit["status"] = "PASS"
    audit["selected_layers"] = chosen_layer
    result["strict_holdout_audit"] = audit
    result["layer_floor_audit"] = {
        "status": "PASS",
        "frozen_minimum_layers": DOWNSTREAM_LAYER_FLOOR,
        "terminal_holdout_layers": max_layer,
        "final_selected_layers": chosen_layer,
        "energy_tolerance_mev_per_surface_atom": tolerance,
        "eligible_nonterminal_layers_at_or_above_floor": eligible_layers,
    }
    result["analysis_entrypoint"] = "slab_runner_v4.py"
    return result


def enforce_floor(result: dict[str, Any], records_root: Path) -> dict[str, Any]:
    """Backward-compatible name for the strict holdout audit."""
    return enforce_strict_holdouts(result, records_root)


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
            audited = enforce_strict_holdouts(base, records_root)
            write(out, audited)
            raise SystemExit(exc.code)
        base = read(base_out)
    audited = enforce_strict_holdouts(base, records_root)
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
