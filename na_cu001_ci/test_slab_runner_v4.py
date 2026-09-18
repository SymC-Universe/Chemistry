#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import slab_runner_v4 as v4

LAYERS = [5, 7, 9, 11]
VACUUMS = [12.0, 16.0, 20.0, 24.0]
KMESHES = [16, 18, 20, 22]


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def base_result(*, terminal_only_vk: bool = False) -> dict:
    fits = []
    for vacuum in VACUUMS:
        for kmesh in KMESHES:
            if terminal_only_vk:
                value = 0.01 * vacuum + 0.001 * kmesh
            else:
                value = 1.0 if vacuum >= 16.0 and kmesh >= 18 else 1.01
            fits.append({
                "vacuum_angstrom": vacuum,
                "kmesh_inplane": kmesh,
                "surface_excess_ev_per_surface_atom": value,
                "fitted_slab_bulk_energy_ev_per_atom": -3.0,
                "independent_bulk_energy_ev_per_atom": -3.0,
                "slope_difference_mev_per_atom": 0.0,
                "fit_rms_residual_mev": 0.0,
            })
    return {
        "schema": v4.RESULT_SCHEMA,
        "gate": "PASS",
        "next_gate": "clean_surface_relaxation",
        "energy_tolerance_mev_per_surface_atom": 1.0,
        "registered_grid": {
            "layers": LAYERS,
            "vacuum_angstrom": VACUUMS,
            "kmesh_inplane": KMESHES,
        },
        "surface_fit_diagnostics": fits,
        "recommended_smallest": {
            "layers": 11,
            "vacuum_angstrom": 24.0,
            "kmesh_inplane": 22,
            "source_record": {"terminal_self_selection": True},
        },
    }


def records(root: Path, *, layer_mode: str = "seven_passes") -> None:
    values = {
        "seven_passes": {5: 1.01, 7: 1.0004, 9: 1.0002, 11: 1.0},
        "nine_passes": {5: 1.01, 7: 1.003, 9: 1.0004, 11: 1.0},
        "terminal_only": {5: 1.01, 7: 1.004, 9: 1.002, 11: 1.0},
    }[layer_mode]
    for layer in LAYERS:
        write(root / f"L{layer}" / "run_record.json", {
            "schema": "na-cu001-clean-slab-case-v0.3",
            "tag": f"L{layer}-V16-K18",
            "layers": layer,
            "vacuum_angstrom": 16.0,
            "kmesh_inplane": 18,
            "bulk_referenced_surface_excess_ev_per_surface_atom": values[layer],
            "scf_converged": True,
            "job_done": True,
            "returncode": 0,
        })


def rejects(fn) -> None:
    try:
        fn()
    except SystemExit:
        return
    raise AssertionError("expected HOLD")


def test_selects_nonterminal_vacuum_k_and_seven_layers():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        out = v4.enforce_strict_holdouts(base_result(), root)
        selected = out["recommended_smallest"]
        assert out["gate"] == "PASS"
        assert selected["vacuum_angstrom"] == 16.0
        assert selected["kmesh_inplane"] == 18
        assert selected["layers"] == 7
        assert selected["vacuum_angstrom"] < max(VACUUMS)
        assert selected["kmesh_inplane"] < max(KMESHES)
        assert selected["layers"] < max(LAYERS)
        assert out["strict_holdout_audit"]["status"] == "PASS"
        assert out["strict_holdout_audit"]["schema"] == v4.HOLDOUT_AUDIT_SCHEMA


def test_selects_nine_when_seven_fails_strict_holdout():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root, layer_mode="nine_passes")
        out = v4.enforce_strict_holdouts(base_result(), root)
        assert out["gate"] == "PASS"
        assert out["recommended_smallest"]["layers"] == 9
        assert out["layer_floor_audit"]["eligible_nonterminal_layers_at_or_above_floor"] == [9]


def test_terminal_vacuum_k_cannot_validate_itself():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        out = v4.enforce_strict_holdouts(base_result(terminal_only_vk=True), root)
        assert out["gate"] == "HOLD"
        assert out["recommended_smallest"] is None
        assert out["strict_holdout_audit"]["eligible_vacuum_k_pairs"] == []
        terminal = [
            row for row in out["strict_holdout_audit"]["vacuum_k_diagnostics"]
            if row["vacuum_angstrom"] == 24.0 and row["kmesh_inplane"] == 22
        ][0]
        assert terminal["pass"] is False
        assert terminal["terminal_self_selection_excluded"] is True


def test_eleven_layers_cannot_validate_itself():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root, layer_mode="terminal_only")
        out = v4.enforce_strict_holdouts(base_result(), root)
        assert out["gate"] == "HOLD"
        assert out["recommended_smallest"] is None
        terminal = [
            row for row in out["strict_holdout_audit"]["layer_diagnostics"]
            if row["layers"] == 11
        ][0]
        assert terminal["pass"] is False
        assert terminal["terminal_self_selection_excluded"] is True


def test_each_selected_vacuum_k_has_both_axis_holdouts():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        out = v4.enforce_strict_holdouts(base_result(), root)
        selected_v, selected_k = out["strict_holdout_audit"]["selected_vacuum_k_pair"]
        row = [
            item for item in out["strict_holdout_audit"]["vacuum_k_diagnostics"]
            if item["vacuum_angstrom"] == selected_v and item["kmesh_inplane"] == selected_k
        ][0]
        assert row["same_k_larger_vacuum_count"] > 0
        assert row["same_vacuum_denser_k_count"] > 0
        assert row["strictly_larger_comparison_count"] > 0


def test_rejects_changed_tolerance():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        result = base_result(); result["energy_tolerance_mev_per_surface_atom"] = 2.0
        rejects(lambda: v4.enforce_strict_holdouts(result, root))


def test_rejects_changed_registered_grid():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        result = base_result(); result["registered_grid"]["layers"] = [5, 7, 9]
        rejects(lambda: v4.enforce_strict_holdouts(result, root))


def test_rejects_missing_source_record():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rejects(lambda: v4.enforce_strict_holdouts(base_result(), root))


if __name__ == "__main__":
    tests = [
        test_selects_nonterminal_vacuum_k_and_seven_layers,
        test_selects_nine_when_seven_fails_strict_holdout,
        test_terminal_vacuum_k_cannot_validate_itself,
        test_eleven_layers_cannot_validate_itself,
        test_each_selected_vacuum_k_has_both_axis_holdouts,
        test_rejects_changed_tolerance,
        test_rejects_changed_registered_grid,
        test_rejects_missing_source_record,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"PASS {len(tests)} strict slab holdout tests")
