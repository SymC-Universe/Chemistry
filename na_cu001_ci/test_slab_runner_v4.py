#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import slab_runner_v4 as v4


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def base_result(selected_layer: int = 5, seven_passes: bool = True) -> dict:
    return {
        "schema": v4.RESULT_SCHEMA,
        "gate": "PASS",
        "energy_tolerance_mev_per_surface_atom": 1.0,
        "recommended_smallest": {
            "layers": selected_layer,
            "vacuum_angstrom": 16.0,
            "kmesh_inplane": 18,
            "source_record": {"layers": selected_layer},
        },
        "layer_diagnostics_at_selected_vacuum_kmesh": [
            {"layers": 5, "worst_thicker_difference_mev_per_surface_atom": 0.2},
            {"layers": 7, "worst_thicker_difference_mev_per_surface_atom": 0.5 if seven_passes else 1.5},
            {"layers": 9, "worst_thicker_difference_mev_per_surface_atom": 0.4 if seven_passes else 1.4},
            {"layers": 11, "worst_thicker_difference_mev_per_surface_atom": 0.0},
        ],
    }


def records(root: Path) -> None:
    for layer in (5, 7, 9, 11):
        write(root / f"L{layer}" / "run_record.json", {
            "schema": "na-cu001-clean-slab-case-v0.3",
            "layers": layer,
            "vacuum_angstrom": 16.0,
            "kmesh_inplane": 18,
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


def test_promotes_five_to_frozen_floor():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        out = v4.enforce_floor(base_result(5), root)
        assert out["gate"] == "PASS"
        assert out["recommended_smallest"]["layers"] == 7
        assert out["layer_floor_audit"]["selection_changed_only_to_enforce_frozen_floor"] is True
        assert out["energy_tolerance_mev_per_surface_atom"] == 1.0


def test_keeps_existing_floor_compliant_selection():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        out = v4.enforce_floor(base_result(7), root)
        assert out["recommended_smallest"]["layers"] == 7
        assert out["layer_floor_audit"]["selection_changed_only_to_enforce_frozen_floor"] is False


def test_selects_next_registered_layer_when_seven_fails():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        result = base_result(5, seven_passes=False)
        result["layer_diagnostics_at_selected_vacuum_kmesh"][2]["worst_thicker_difference_mev_per_surface_atom"] = 0.7
        out = v4.enforce_floor(result, root)
        assert out["recommended_smallest"]["layers"] == 9


def test_holds_when_no_layer_at_floor_converges():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        result = base_result(5, seven_passes=False)
        result["layer_diagnostics_at_selected_vacuum_kmesh"][2]["worst_thicker_difference_mev_per_surface_atom"] = 1.4
        result["layer_diagnostics_at_selected_vacuum_kmesh"][3]["worst_thicker_difference_mev_per_surface_atom"] = 1.1
        out = v4.enforce_floor(result, root)
        assert out["gate"] == "HOLD"
        assert out["recommended_smallest"] is None


def test_rejects_changed_tolerance():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); records(root)
        result = base_result(5); result["energy_tolerance_mev_per_surface_atom"] = 2.0
        rejects(lambda: v4.enforce_floor(result, root))


def test_rejects_missing_source_record():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        result = base_result(5)
        rejects(lambda: v4.enforce_floor(result, root))


if __name__ == "__main__":
    tests = [
        test_promotes_five_to_frozen_floor,
        test_keeps_existing_floor_compliant_selection,
        test_selects_next_registered_layer_when_seven_fails,
        test_holds_when_no_layer_at_floor_converges,
        test_rejects_changed_tolerance,
        test_rejects_missing_source_record,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"PASS {len(tests)} slab layer-floor tests")
