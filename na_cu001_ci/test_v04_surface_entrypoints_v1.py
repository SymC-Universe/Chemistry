#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import closure_engine_v3 as engine
import slab_runner_v3 as slab


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def fixture(root: Path):
    result_path = root / engine.RESULT_FILENAME
    handoff_path = root / "BULK_HANDOFF.json"
    bridge_path = root / engine.BRIDGE_FILENAME
    selected = {
        "ecutwfc_ry": 80,
        "ecutrho_ry": 240,
        "kmesh": 14,
        "fit": {"a0_angstrom": 3.61, "e0_ev_per_atom": -100.0},
    }
    result = {
        "schema": engine.RESULT_SCHEMA,
        "status": "PASS",
        "gate": "PASS",
        "recommended_smallest_cost_candidate": selected,
    }
    write(result_path, result)
    settings = {
        "ecutwfc_ry": 80,
        "ecutrho_ry": 240,
        "kmesh_cubic": [14, 14, 14],
        "equilibrium_lattice_constant_angstrom": 3.61,
        "equilibrium_energy_ev_per_atom": -100.0,
    }
    handoff = {
        "schema": engine.HANDOFF_SCHEMA,
        "scientific_status": "bulk_convergence_passed_slab_not_yet_run",
        "source_result": {"sha256": sha(result_path)},
        "selected_bulk_settings": settings,
    }
    write(handoff_path, handoff)
    bridge = {
        "schema": engine.BRIDGE_SCHEMA,
        "status": "PASS",
        "source_artifacts": [
            {"schema": engine.RESULT_SCHEMA, "path": result_path.name, "sha256": sha(result_path)},
            {"schema": engine.HANDOFF_SCHEMA, "path": handoff_path.name, "sha256": sha(handoff_path)},
        ],
        "reference_audit_gate": {"pass": True, "delta_a_angstrom": 0.0002, "delta_e_ev_per_atom": 0.0002},
        "verified_eos_count": 46,
        "verified_scf_count": 276,
        "selected_bulk_settings": settings,
        "selected_candidate_gate": {"pass": True, "delta_a_angstrom": 0.0001, "delta_e_ev_per_atom": 0.0008},
        "selection_verification": {"selected_pair": [80, 14], "passing_candidate_count": 3},
    }
    write(bridge_path, bridge)
    return result_path, handoff_path, bridge_path


def test_loaders_accept_valid_bundle():
    with tempfile.TemporaryDirectory() as d:
        result_path, handoff_path, _ = fixture(Path(d))
        out = slab.load_bulk_v04(handoff_path, result_path)
        assert out["ecutwfc_ry"] == 80 and out["bulk_kmesh"] == 14
        bulk, result, bridge, rp, bp = engine.load_v04_bundle(handoff_path)
        assert bulk["schema"] == engine.HANDOFF_SCHEMA
        assert result["schema"] == engine.RESULT_SCHEMA
        assert bridge["verified_scf_count"] == 276
        assert rp == result_path.resolve() and bp.name == engine.BRIDGE_FILENAME


def test_slab_handoff_records_v04_provenance():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _, handoff_path, _ = fixture(root)
        slab_result_path = root / "SLAB_RESULT.json"
        write(slab_result_path, {
            "schema": "na-cu001-clean-slab-selection-v0.3",
            "gate": "PASS",
            "energy_tolerance_mev_per_surface_atom": 1.0,
            "electrostatic_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
            "recommended_smallest": {
                "layers": 7,
                "vacuum_angstrom": 20.0,
                "kmesh_inplane": 10,
                "source_record": {
                    "a0_angstrom": 3.61,
                    "e0_ev_per_atom": -100.0,
                    "ecutwfc_ry": 80,
                    "ecutrho_ry": 240,
                    "bulk_kmesh": 14,
                },
            },
        })
        out = root / "SLAB_HANDOFF.json"
        engine.command_slab_handoff(SimpleNamespace(slab_result=str(slab_result_path), bulk_handoff=str(handoff_path), out=str(out)))
        data = json.loads(out.read_text())
        assert data["status"] == "PASS"
        assert data["bulk_v04_provenance"]["reference_audit_gate"]["pass"] is True
        assert len(data["input_artifacts"]) == 4


def test_reject_failed_reference_audit():
    with tempfile.TemporaryDirectory() as d:
        result_path, handoff_path, bridge_path = fixture(Path(d))
        bridge = json.loads(bridge_path.read_text())
        bridge["reference_audit_gate"]["pass"] = False
        write(bridge_path, bridge)
        for fn in (lambda: slab.load_bulk_v04(handoff_path, result_path), lambda: engine.load_v04_bundle(handoff_path)):
            try:
                fn()
                raise AssertionError("failed reference audit accepted")
            except SystemExit:
                pass


def test_reject_incomplete_inventory():
    with tempfile.TemporaryDirectory() as d:
        result_path, handoff_path, bridge_path = fixture(Path(d))
        bridge = json.loads(bridge_path.read_text())
        bridge["verified_scf_count"] = 270
        write(bridge_path, bridge)
        try:
            slab.load_bulk_v04(handoff_path, result_path)
            raise AssertionError("incomplete SCF inventory accepted")
        except SystemExit:
            pass


def test_reject_hash_mismatch():
    with tempfile.TemporaryDirectory() as d:
        result_path, handoff_path, _ = fixture(Path(d))
        result = json.loads(result_path.read_text())
        result["unexpected"] = "mutation"
        write(result_path, result)
        for fn in (lambda: slab.load_bulk_v04(handoff_path, result_path), lambda: engine.load_v04_bundle(handoff_path)):
            try:
                fn()
                raise AssertionError("mutated result accepted")
            except SystemExit:
                pass


if __name__ == "__main__":
    tests = [
        test_loaders_accept_valid_bundle,
        test_slab_handoff_records_v04_provenance,
        test_reject_failed_reference_audit,
        test_reject_incomplete_inventory,
        test_reject_hash_mismatch,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} v0.4 surface entrypoint tests")
