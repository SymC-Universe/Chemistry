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
            atoms, cell_z, _ = v5.fcc001_cartesian_atoms_esm_centered(a0, layers, vacuum)
            z = [row[2] for row in atoms]
            left = min(z) - (-cell_z / 2)
            right = cell_z / 2 - max(z)
            assert close(left, vacuum / 2)
            assert close(right, vacuum / 2)
            assert close(left, right)


def test_layer_spacing_and_fcc_shift_preserved():
    a0 = 3.63
    atoms, _, _ = v5.fcc001_cartesian_atoms_esm_centered(a0, 11, 24.0)
    z = [row[2] for row in atoms]
    assert all(close(z[i + 1] - z[i], a0 / 2) for i in range(len(z) - 1))
    assert [(x, y) for x, y, _ in atoms[:4]] == [(0.0, 0.0), (0.0, a0 / 2), (0.0, 0.0), (0.0, a0 / 2)]


def test_geometry_record_is_explicit_and_symmetric():
    record = v5.geometry_record(3.6, 7, 16.0)
    assert record["schema"] == v5.GEOMETRY_SCHEMA
    assert record["atomic_position_card"] == "angstrom"
    assert record["coordinate_origin"] == "cartesian_z_zero"
    assert record["symmetric_about_zero"] is True
    assert close(record["atomic_z_mean_angstrom"], 0.0)
    assert close(record["vacuum_each_side_angstrom"], 8.0)


def test_qe_input_uses_explicit_angstrom_coordinates_at_zero():
    a0 = 3.6
    bulk = {"a0_angstrom": a0, "ecutwfc_ry": 90, "ecutrho_ry": 270}
    text = v5.qe_input_esm_centered(
        bulk=bulk,
        layers=7,
        vacuum=16.0,
        kmesh=18,
        pseudo_dir=Path("/tmp/pseudo"),
        outdir=Path("/tmp/out"),
        tag="test",
    )
    assert "ATOMIC_POSITIONS angstrom" in text
    assert "ATOMIC_POSITIONS crystal" not in text
    assert "assume_isolated = 'esm'" in text
    assert "esm_bc = 'bc1'" in text
    lines = text.splitlines()
    start = lines.index("ATOMIC_POSITIONS angstrom") + 1
    atom_lines = lines[start : start + 7]
    coords = [[float(value) for value in line.split()[1:4]] for line in atom_lines]
    x = [row[0] for row in coords]
    y = [row[1] for row in coords]
    z = [row[2] for row in coords]
    assert all(close(value, 0.0) for value in x)
    assert y == [0.0, a0 / 2, 0.0, a0 / 2, 0.0, a0 / 2, 0.0]
    assert close(sum(z) / len(z), 0.0)
    assert close(min(z) + max(z), 0.0)
    assert min(z) < 0.0 < max(z)
    assert lines[start + 7] == "K_POINTS automatic"


def write_case_record(root: Path, layers: int, vacuum: float, kmesh: int) -> Path:
    tag = v5.case_tag(layers, vacuum, kmesh)
    path = root / tag / "run_record.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "tag": tag,
        "layers": layers,
        "vacuum_angstrom": vacuum,
        "kmesh_inplane": kmesh,
        "a0_angstrom": 3.6,
    }) + "\n")
    return path


def test_sequential_four_kmesh_updates_target_only_current_record():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        meshes = (16, 18, 20, 22)
        paths = {k: write_case_record(root, 7, 16.0, k) for k in meshes}
        for index, kmesh in enumerate(meshes, start=1):
            updated = v5.attach_geometry_to_case_record(root, 7, 16.0, kmesh)
            assert updated == paths[kmesh]
            for candidate_k, path in paths.items():
                row = json.loads(path.read_text())
                assert ("geometry_convention" in row) is (candidate_k in meshes[:index])


def test_record_identity_mismatch_rejected():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        path = write_case_record(root, 7, 16.0, 16)
        row = json.loads(path.read_text())
        row["kmesh_inplane"] = 18
        path.write_text(json.dumps(row) + "\n")
        try:
            v5.attach_geometry_to_case_record(root, 7, 16.0, 16)
        except SystemExit:
            return
        raise AssertionError("mismatched current record identity was accepted")


def write_complete_inventory(root: Path, tamper_index: int | None = None) -> None:
    bulk = {"a0_angstrom": 3.6, "ecutwfc_ry": 90, "ecutrho_ry": 270}
    index = 0
    for layers in v2.LAYERS:
        for vacuum in v2.VACUUM:
            for kmesh in (16, 18, 20, 22):
                tag = v5.case_tag(layers, vacuum, kmesh)
                directory = root / str(index)
                directory.mkdir(parents=True)
                input_path = directory / f"{tag}.in"
                input_text = v5.qe_input_esm_centered(
                    bulk=bulk,
                    layers=layers,
                    vacuum=vacuum,
                    kmesh=kmesh,
                    pseudo_dir=Path("/tmp/pseudo"),
                    outdir=Path("/tmp/out"),
                    tag=tag,
                )
                input_path.write_text(input_text)
                _, cell_z, _ = v5.fcc001_geometry_esm_centered(3.6, layers, vacuum)
                record = {
                    "tag": tag,
                    "layers": layers,
                    "nat": layers,
                    "vacuum_angstrom": vacuum,
                    "kmesh_inplane": kmesh,
                    "a0_angstrom": 3.6,
                    "cell_z_angstrom": cell_z,
                    "input_sha256": v2.sha256(input_path),
                    "geometry_convention": v5.geometry_record(3.6, layers, vacuum),
                }
                (directory / "run_record.json").write_text(json.dumps(record) + "\n")
                if tamper_index == index:
                    input_path.write_text(input_text + "! tampered after hashing\n")
                index += 1


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
                    "atomic_position_card": "crystal",
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


def test_raw_geometry_audit_rejects_tampered_input():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        write_complete_inventory(root, tamper_index=37)
        try:
            v5.audit_raw_geometry(root)
        except SystemExit:
            return
        raise AssertionError("tampered QE input was accepted")


def test_raw_geometry_audit_accepts_complete_centered_inventory():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        write_complete_inventory(root)
        out = v5.audit_raw_geometry(root)
        assert out["status"] == "PASS"
        assert out["verified_record_count"] == 64
        assert out["verified_input_count"] == 64
        assert out["atomic_position_card"] == "angstrom"
        assert out["all_input_hashes_match_run_records"] is True
        assert len(out["input_records"]) == 64


if __name__ == "__main__":
    tests = [
        test_five_layer_geometry_centered_at_zero,
        test_all_registered_layers_have_equal_vacuum_halves,
        test_layer_spacing_and_fcc_shift_preserved,
        test_geometry_record_is_explicit_and_symmetric,
        test_qe_input_uses_explicit_angstrom_coordinates_at_zero,
        test_sequential_four_kmesh_updates_target_only_current_record,
        test_record_identity_mismatch_rejected,
        test_raw_geometry_audit_rejects_old_fractional_half_centering,
        test_raw_geometry_audit_rejects_tampered_input,
        test_raw_geometry_audit_accepts_complete_centered_inventory,
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"PASS {len(tests)} ESM-centered slab/input tests")
