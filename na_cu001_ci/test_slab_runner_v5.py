#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import slab_runner_v2 as v2
import slab_runner_v5 as v5


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol


def test_five_layer_geometry_centered_at_zero():
    a0 = 3.6
    atoms, cell_z, area = v5.fcc001_geometry_esm_centered(a0, 5, 12.0)
    z = [row[2] * cell_z for row in atoms]
    assert close(sum(z) / len(z), 0.0)
    assert close(min(z), -a0)
    assert close(max(z), a0)
    assert close(min(z) + max(z), 0.0)
    assert close(cell_z, 4 * a0 / 2 + 12.0)
    assert close(area, a0 * a0 / 2)
    assert all(-0.5 < row[2] < 0.5 for row in atoms)


def test_all_registered_layers_have_equal_vacuum_halves():
    a0 = 3.61
    for layers in v2.LAYERS:
        for vacuum in v2.VACUUM:
            atoms, cell_z, _ = v5.fcc001_geometry_esm_centered(a0, layers, vacuum)
            z = [row[2] * cell_z for row in atoms]
            left = min(z) - (-cell_z / 2)
            right = cell_z / 2 - max(z)
            assert close(left, vacuum / 2)
            assert close(right, vacuum / 2)
            assert close(left, right)


def test_layer_spacing_and_fcc_shift_preserved():
    a0 = 3.63
    atoms, cell_z, _ = v5.fcc001_geometry_esm_centered(a0, 11, 24.0)
    z = [row[2] * cell_z for row in atoms]
    assert all(close(z[i + 1] - z[i], a0 / 2) for i in range(len(z) - 1))
    assert [(x, y) for x, y, _ in atoms[:4]] == [(0.0, 0.0), (0.5, 0.5), (0.0, 0.0), (0.5, 0.5)]


def test_geometry_record_is_explicit_and_symmetric():
    record = v5.geometry_record(3.6, 7, 16.0)
    assert record["schema"] == v5.GEOMETRY_SCHEMA
    assert record["coordinate_origin"] == "cartesian_z_zero"
    assert record["symmetric_about_zero"] is True
    assert close(record["atomic_z_mean_angstrom"], 0.0)
    assert close(record["vacuum_each_side_angstrom"], 8.0)


def test_raw_geometry_audit_rejects_old_fractional_half_centering():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        for idx in range(64):
            path = root / str(idx) / "run_record.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                "tag": f"bad-{idx}",
                "layers": 5,
                "vacuum_angstrom": 12.0,
                "geometry_convention": {
                    "schema": v5.GEOMETRY_SCHEMA,
                    "coordinate_origin": "fractional_z_half",
                    "slab_center_z_angstrom": 9.0,
                    "atomic_z_mean_angstrom": 9.0,
                    "symmetric_about_zero": False,
                    "vacuum_total_angstrom": 12.0,
                    "vacuum_each_side_angstrom": 6.0,
                },
            }) + "\n")
        try:
            v5.audit_raw_geometry(root)
        except SystemExit:
            return
        raise AssertionError("miscentered raw matrix was accepted")


def test_raw_geometry_audit_accepts_complete_centered_inventory():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        idx = 0
        for layers in v2.LAYERS:
            for vacuum in v2.VACUUM:
                for kmesh in (16, 18, 20, 22):
                    path = root / str(idx) / "run_record.json"
                    path.parent.mkdir(parents=True)
                    path.write_text(json.dumps({
                        "tag": f"L{layers}-V{vacuum}-K{kmesh}",
                        "layers": layers,
                        "vacuum_angstrom": vacuum,
                        "kmesh_inplane": kmesh,
                        "geometry_convention": v5.geometry_record(3.6, layers, vacuum),
                    }) + "\n")
                    idx += 1
        out = v5.audit_raw_geometry(root)
        assert out["status"] == "PASS"
        assert out["verified_record_count"] == 64


if __name__ == "__main__":
    tests = [
        test_five_layer_geometry_centered_at_zero,
        test_all_registered_layers_have_equal_vacuum_halves,
        test_layer_spacing_and_fcc_shift_preserved,
        test_geometry_record_is_explicit_and_symmetric,
        test_raw_geometry_audit_rejects_old_fractional_half_centering,
        test_raw_geometry_audit_accepts_complete_centered_inventory,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"PASS {len(tests)} ESM-centered slab geometry tests")
