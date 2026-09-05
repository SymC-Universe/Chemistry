#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import closure_engine_v4 as v4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def fixture(root: Path):
    bulk_result_path = root / "BULK_CONVERGENCE_RESULT.json"
    bulk_handoff_path = root / "BULK_HANDOFF.json"
    bridge_path = root / "BULK_V04_DOWNSTREAM_BRIDGE.json"
    slab_result_path = root / "CLEAN_SLAB_CONVERGENCE_RESULT.json"
    out_path = root / "SLAB_HANDOFF.json"

    bulk_settings = {
        "ecutwfc_ry": 90,
        "ecutrho_ry": 270,
        "kmesh_cubic": [14, 14, 14],
        "equilibrium_lattice_constant_angstrom": 3.62,
        "equilibrium_energy_ev_per_atom": -3.7,
    }
    bulk_result = {
        "schema": "na-cu001-bulk-selection-v0.4",
        "gate": "PASS",
        "status": "PASS",
        "recommended_smallest_cost_candidate": {
            "ecutwfc_ry": 90,
            "ecutrho_ry": 270,
            "kmesh": 14,
            "fit": {"a0_angstrom": 3.62, "e0_ev_per_atom": -3.7},
        },
    }
    write(bulk_result_path, bulk_result)
    bulk_handoff = {
        "schema": "na-cu001-bulk-to-slab-handoff-v0.4",
        "scientific_status": "bulk_convergence_passed_slab_not_yet_run",
        "source_result": {"sha256": sha(bulk_result_path)},
        "selected_bulk_settings": bulk_settings,
    }
    write(bulk_handoff_path, bulk_handoff)
    bridge = {
        "schema": "na-cu001-audited-bulk-downstream-bridge-v0.1",
        "status": "PASS",
        "source_artifacts": [
            {
                "schema": "na-cu001-bulk-selection-v0.4",
                "path": bulk_result_path.name,
                "sha256": sha(bulk_result_path),
            },
            {
                "schema": "na-cu001-bulk-to-slab-handoff-v0.4",
                "path": bulk_handoff_path.name,
                "sha256": sha(bulk_handoff_path),
            },
        ],
        "reference_audit_gate": {"pass": True},
        "verified_eos_count": 46,
        "verified_scf_count": 276,
        "selected_candidate_gate": {"pass": True},
        "selection_verification": {"selected_pair": [90, 14]},
        "selected_bulk_settings": bulk_settings,
    }
    write(bridge_path, bridge)

    geometry = {
        "schema": "na-cu001-esm-centered-slab-v0.2",
        "atomic_position_card": "angstrom",
        "coordinate_origin": "cartesian_z_zero",
        "slab_center_z_angstrom": 0.0,
        "atomic_z_mean_angstrom": 0.0,
        "symmetric_about_zero": True,
        "vacuum_total_angstrom": 20.0,
        "vacuum_each_side_angstrom": 10.0,
    }
    source = {
        "schema": "na-cu001-clean-slab-case-v0.3",
        "tag": "cu001_L7_V20_K20",
        "layers": 7,
        "vacuum_angstrom": 20.0,
        "kmesh_inplane": 20,
        "a0_angstrom": 3.62,
        "ecutwfc_ry": 90,
        "ecutrho_ry": 270,
        "bulk_kmesh": 14,
        "e0_ev_per_atom": -3.7,
        "geometry_convention": geometry,
    }
    strict = {
        "schema": "na-cu001-clean-slab-strict-holdout-audit-v0.1",
        "status": "PASS",
        "terminal_holdouts": {
            "layers": 11,
            "vacuum_angstrom": 24.0,
            "kmesh_inplane": 22,
            "eligible_for_selection": False,
        },
        "selected_vacuum_k_pair": [20.0, 20],
        "selected_layers": 7,
    }
    raw_audit = {
        "schema": "na-cu001-esm-centered-raw-audit-v0.3",
        "status": "PASS",
        "verified_record_count": 64,
        "verified_input_count": 64,
        "geometry_schema": "na-cu001-esm-centered-slab-v0.2",
        "atomic_position_card": "angstrom",
        "all_slabs_symmetric_about_zero": True,
        "vacuum_split_equally_between_open_boundaries": True,
        "all_input_hashes_match_run_records": True,
        "all_inputs_set_esm_bc1": True,
    }
    slab_result = {
        "schema": "na-cu001-clean-slab-selection-v0.3",
        "gate": "PASS",
        "energy_tolerance_mev_per_surface_atom": 1.0,
        "electrostatic_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
        "recommended_smallest": {
            "layers": 7,
            "vacuum_angstrom": 20.0,
            "kmesh_inplane": 20,
            "source_record": source,
        },
        "layer_floor_audit": {"status": "PASS", "frozen_minimum_layers": 7},
        "strict_holdout_audit": strict,
        "esm_geometry_audit": raw_audit,
    }
    write(slab_result_path, slab_result)
    return slab_result_path, bulk_handoff_path, out_path


def run(paths):
    slab, bulk, out = paths
    v4.command_slab_handoff(
        SimpleNamespace(slab_result=str(slab), bulk_handoff=str(bulk), out=str(out))
    )
    return json.loads(out.read_text())


def rejects(fn) -> None:
    try:
        fn()
    except SystemExit:
        return
    raise AssertionError("expected HOLD")


def mutate_slab(path: Path, fn) -> None:
    data = json.loads(path.read_text())
    fn(data)
    write(path, data)


def test_valid_handoff_carries_full_proof_bundle():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        out = run(paths)
        assert out["status"] == "PASS"
        assert out["selected_slab_settings"]["layers"] == 7
        assert out["selected_slab_settings"]["coordinate_convention"]["origin"] == "cartesian_z_zero"
        proof = out["slab_convergence_provenance"]
        assert proof["strict_holdout_audit"]["status"] == "PASS"
        assert proof["esm_geometry_audit"]["verified_input_count"] == 64
        assert out["convergence_rule"]["terminal_points_ineligible"] is True


def test_rejects_terminal_self_selection():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        mutate_slab(paths[0], lambda x: x["recommended_smallest"].update({"layers": 11}))
        rejects(lambda: run(paths))


def test_rejects_failed_strict_holdout_audit():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        mutate_slab(paths[0], lambda x: x["strict_holdout_audit"].update({"status": "HOLD"}))
        rejects(lambda: run(paths))


def test_rejects_incomplete_qe_input_inventory():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        mutate_slab(paths[0], lambda x: x["esm_geometry_audit"].update({"verified_input_count": 63}))
        rejects(lambda: run(paths))


def test_rejects_selected_source_without_definitive_geometry():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        mutate_slab(
            paths[0],
            lambda x: x["recommended_smallest"]["source_record"]["geometry_convention"].update(
                {"coordinate_origin": "fractional_z_half"}
            ),
        )
        rejects(lambda: run(paths))


def test_rejects_nonpass_slab_result():
    with tempfile.TemporaryDirectory() as d:
        paths = fixture(Path(d))
        mutate_slab(paths[0], lambda x: x.update({"gate": "HOLD"}))
        rejects(lambda: run(paths))


if __name__ == "__main__":
    tests = [
        test_valid_handoff_carries_full_proof_bundle,
        test_rejects_terminal_self_selection,
        test_rejects_failed_strict_holdout_audit,
        test_rejects_incomplete_qe_input_inventory,
        test_rejects_selected_source_without_definitive_geometry,
        test_rejects_nonpass_slab_result,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"PASS {len(tests)} proof-carrying slab handoff tests")
