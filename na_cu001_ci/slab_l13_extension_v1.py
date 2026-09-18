#!/usr/bin/env python3
"""Preregistered 13-layer strict holdout extension for Na/Cu(001) C7.

This module does not alter the frozen 64-point source grid. It adds one
independent 13-layer holdout block over the same four vacuums and four in-plane
k meshes, then tests only the original source layers against that thicker
holdout at the source-selected vacuum/k pair.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

SOURCE_LAYERS = [5, 7, 9, 11]
EXTENSION_LAYER = 13
VACUUMS = [12.0, 16.0, 20.0, 24.0]
KMESHES = [16, 18, 20, 22]
ENERGY_TOL_MEV = 1.0
DOWNSTREAM_LAYER_FLOOR = 7
SOURCE_RUN_ID = 30949901790
SOURCE_COMMIT = "8ca3f708537886050ef18210315e79a43595d3f3"
RESULT_SCHEMA = "na-cu001-clean-slab-l13-extension-selection-v0.1"
AUDIT_SCHEMA = "na-cu001-clean-slab-l13-strict-holdout-audit-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def exact_grid(rows: Iterable[dict[str, Any]]) -> set[tuple[int, float, int]]:
    return {
        (
            int(row.get("layers", -1)),
            float(row.get("vacuum_angstrom", -1.0)),
            int(row.get("kmesh_inplane", -1)),
        )
        for row in rows
    }


def expected_source_grid() -> set[tuple[int, float, int]]:
    return {(layer, vacuum, kmesh) for layer in SOURCE_LAYERS for vacuum in VACUUMS for kmesh in KMESHES}


def expected_extension_grid() -> set[tuple[int, float, int]]:
    return {(EXTENSION_LAYER, vacuum, kmesh) for vacuum in VACUUMS for kmesh in KMESHES}


def parse_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or len(fields[0]) != 64:
            raise SystemExit(f"HOLD: malformed compact manifest line {path}:{number}")
        digest, recorded_path = fields
        entries[Path(recorded_path.strip()).name] = digest
    return entries


def audit_compact_case(record_path: Path, row: dict[str, Any]) -> dict[str, Any]:
    tag = str(row.get("tag") or "")
    if not tag:
        raise SystemExit(f"HOLD: record without tag at {record_path}")
    inp = record_path.parent / f"{tag}.in"
    out = record_path.parent / f"{tag}.out"
    manifest_candidates = [
        record_path.parent / "COMPACT_EVIDENCE.sha256",
        record_path.parent.parent / "COMPACT_EVIDENCE.sha256",
    ]
    manifest = next((candidate for candidate in manifest_candidates if candidate.is_file()), None)
    for required in (inp, out):
        if not required.is_file():
            raise SystemExit(f"HOLD: compact evidence missing for {tag}: {required.name}")
    if manifest is None:
        raise SystemExit(f"HOLD: compact evidence manifest missing for {tag}")
    actual = {
        "run_record.json": sha256(record_path),
        inp.name: sha256(inp),
        out.name: sha256(out),
    }
    listed = parse_manifest(manifest)
    missing = {name: digest for name, digest in actual.items() if listed.get(name) != digest}
    if missing:
        raise SystemExit(f"HOLD: compact manifest mismatch for {tag}: {json.dumps(missing, sort_keys=True)}")
    if row.get("input_sha256") != actual[inp.name] or row.get("output_sha256") != actual[out.name]:
        raise SystemExit(f"HOLD: input/output hash mismatch for {tag}")
    return {
        "tag": tag,
        "record_sha256": actual["run_record.json"],
        "input_sha256": actual[inp.name],
        "output_sha256": actual[out.name],
        "compact_manifest_sha256": sha256(manifest),
    }


def load_record_paths(root: Path) -> list[Path]:
    return sorted(root.rglob("run_record.json"))


def strict_layer_selection(
    by_key: dict[tuple[int, float, int], dict[str, Any]],
    selected_vacuum: float,
    selected_kmesh: int,
    tolerance_mev: float = ENERGY_TOL_MEV,
) -> dict[str, Any]:
    all_layers = SOURCE_LAYERS + [EXTENSION_LAYER]
    diagnostics: list[dict[str, Any]] = []
    eligible: list[int] = []
    for layer in SOURCE_LAYERS:
        key = (layer, selected_vacuum, selected_kmesh)
        if key not in by_key:
            raise SystemExit(f"HOLD: source record missing for {key}")
        value = float(by_key[key]["bulk_referenced_surface_excess_ev_per_surface_atom"])
        stricter = []
        for thicker in all_layers:
            if thicker <= layer:
                continue
            thicker_key = (thicker, selected_vacuum, selected_kmesh)
            if thicker_key not in by_key:
                raise SystemExit(f"HOLD: strict thicker holdout missing for {thicker_key}")
            thicker_value = float(by_key[thicker_key]["bulk_referenced_surface_excess_ev_per_surface_atom"])
            stricter.append((thicker, thicker_value))
        worst = max(abs(value - thicker_value) * 1000.0 for _, thicker_value in stricter)
        passed = bool(layer >= DOWNSTREAM_LAYER_FLOOR and worst <= tolerance_mev)
        diagnostics.append(
            {
                "layers": layer,
                "strictly_thicker_comparison_count": len(stricter),
                "strictly_thicker_layers": [item[0] for item in stricter],
                "worst_strict_difference_mev_per_surface_atom": worst,
                "meets_downstream_layer_floor": layer >= DOWNSTREAM_LAYER_FLOOR,
                "terminal_extension_eligible_for_selection": False,
                "pass": passed,
            }
        )
        if passed:
            eligible.append(layer)
    return {
        "diagnostics": diagnostics,
        "eligible_layers": eligible,
        "selected_layers": min(eligible) if eligible else None,
    }


def fixed_provenance_fields(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "a0_angstrom",
        "e0_ev_per_atom",
        "ecutwfc_ry",
        "ecutrho_ry",
        "bulk_kmesh",
        "handoff_sha256",
        "result_sha256",
        "v04_bridge_sha256",
        "pseudo_sha256",
    ]
    return {key: row.get(key) for key in keys}


def check_fixed_provenance(reference: dict[str, Any], row: dict[str, Any]) -> None:
    expected = fixed_provenance_fields(reference)
    actual = fixed_provenance_fields(row)
    mismatches: dict[str, Any] = {}
    for key, value in expected.items():
        other = actual.get(key)
        if key in {"a0_angstrom", "e0_ev_per_atom"}:
            if value is None or other is None or abs(float(value) - float(other)) > 1e-12:
                mismatches[key] = {"source": value, "extension": other}
        elif value != other:
            mismatches[key] = {"source": value, "extension": other}
    if mismatches:
        raise SystemExit(f"HOLD: frozen provenance/settings mismatch: {json.dumps(mismatches, sort_keys=True)}")


def audit_extension_records(root: Path, source_reference: dict[str, Any], v5: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = load_record_paths(root)
    if len(paths) != 16:
        raise SystemExit(f"HOLD: expected 16 L13 records, found {len(paths)}")
    rows = [read_json(path) for path in paths]
    if exact_grid(rows) != expected_extension_grid():
        raise SystemExit("HOLD: L13 extension grid differs from the preregistered 16-point holdout block")
    compact: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    for path, row in zip(paths, rows):
        tag = str(row.get("tag") or "")
        if row.get("schema") != "na-cu001-clean-slab-case-v0.3":
            raise SystemExit(f"HOLD: unsupported L13 record schema for {tag}")
        if int(row.get("layers", -1)) != EXTENSION_LAYER or int(row.get("nat", -1)) != EXTENSION_LAYER:
            raise SystemExit(f"HOLD: invalid L13 atom/layer identity for {tag}")
        if row.get("returncode") != 0 or not row.get("job_done") or not row.get("scf_converged"):
            raise SystemExit(f"HOLD: nonconverged L13 record for {tag}")
        electro = row.get("electrostatic_convention") or {}
        if electro.get("assume_isolated") != "esm" or electro.get("esm_bc") != "bc1":
            raise SystemExit(f"HOLD: ESM bc1 mismatch for {tag}")
        geometry = row.get("geometry_convention") or {}
        conditions = [
            geometry.get("schema") == v5.GEOMETRY_SCHEMA,
            geometry.get("atomic_position_card") == "angstrom",
            geometry.get("coordinate_origin") == "cartesian_z_zero",
            abs(float(geometry.get("slab_center_z_angstrom", 1.0))) <= 1e-12,
            abs(float(geometry.get("atomic_z_mean_angstrom", 1.0))) <= 1e-12,
            bool(geometry.get("symmetric_about_zero")),
            abs(float(geometry.get("vacuum_total_angstrom", -1.0)) - float(row["vacuum_angstrom"])) <= 1e-12,
            abs(2.0 * float(geometry.get("vacuum_each_side_angstrom", -1.0)) - float(row["vacuum_angstrom"])) <= 1e-12,
        ]
        if not all(conditions):
            raise SystemExit(f"HOLD: L13 geometry metadata mismatch for {tag}")
        check_fixed_provenance(source_reference, row)
        inputs.append(v5.audit_input_file(path, row))
        compact.append(audit_compact_case(path, row))
    return rows, {
        "schema": "na-cu001-esm-centered-l13-raw-audit-v0.1",
        "status": "PASS",
        "verified_record_count": 16,
        "verified_input_count": 16,
        "verified_output_count": 16,
        "geometry_schema": v5.GEOMETRY_SCHEMA,
        "atomic_position_card": "angstrom",
        "coordinate_origin": "cartesian_z_zero",
        "all_slabs_symmetric_about_zero": True,
        "vacuum_split_equally_between_open_boundaries": True,
        "all_inputs_set_esm_bc1": True,
        "input_records": sorted(inputs, key=lambda item: item["tag"]),
        "compact_evidence": sorted(compact, key=lambda item: item["tag"]),
    }


def run_case(args: argparse.Namespace) -> None:
    module_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(module_dir))
    import slab_runner_v2 as v2  # type: ignore
    import slab_runner_v5 as v5  # type: ignore

    if int(args.layers) != EXTENSION_LAYER:
        raise SystemExit("HOLD: this entrypoint is registered only for the 13-layer extension")
    if float(args.vacuum) not in VACUUMS or int(args.kmesh) not in KMESHES:
        raise SystemExit("HOLD: unregistered L13 vacuum or k mesh")
    original_layers = list(v2.LAYERS)
    try:
        v2.LAYERS = SOURCE_LAYERS + [EXTENSION_LAYER]
        v5.run_case(args)
    finally:
        v2.LAYERS = original_layers


def analyze(args: argparse.Namespace) -> None:
    module_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(module_dir))
    import slab_runner_v5 as v5  # type: ignore

    source_root = Path(args.source_records).resolve()
    extension_root = Path(args.extension_records).resolve()
    source_paths = load_record_paths(source_root)
    if len(source_paths) != 64:
        raise SystemExit(f"HOLD: expected 64 source records, found {len(source_paths)}")
    source_rows = [read_json(path) for path in source_paths]
    if exact_grid(source_rows) != expected_source_grid():
        raise SystemExit("HOLD: source records differ from the frozen 64-point grid")

    source_compact = [audit_compact_case(path, row) for path, row in zip(source_paths, source_rows)]
    with tempfile.TemporaryDirectory() as tmpdir:
        source_result_path = Path(tmpdir) / "SOURCE_64_RESULT.json"
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                v5.analyze(SimpleNamespace(records=str(source_root), out=str(source_result_path)))
            except SystemExit:
                if not source_result_path.is_file():
                    raise
        source_result = read_json(source_result_path)
        source_result_bytes = source_result_path.read_bytes()

    source_grid = source_result.get("registered_grid") or {}
    if (
        sorted(int(value) for value in source_grid.get("layers", [])) != SOURCE_LAYERS
        or sorted(float(value) for value in source_grid.get("vacuum_angstrom", [])) != VACUUMS
        or sorted(int(value) for value in source_grid.get("kmesh_inplane", [])) != KMESHES
    ):
        raise SystemExit("HOLD: source analysis changed the frozen 64-point grid")
    if float(source_result.get("energy_tolerance_mev_per_surface_atom", -1.0)) != ENERGY_TOL_MEV:
        raise SystemExit("HOLD: source analysis changed the 1.0 meV threshold")
    holdout = source_result.get("strict_holdout_audit") or {}
    selected_pair = holdout.get("selected_vacuum_k_pair")
    if not isinstance(selected_pair, list) or len(selected_pair) != 2:
        raise SystemExit("HOLD: source 64 analysis did not establish a strict vacuum/k pair")
    selected_vacuum = float(selected_pair[0])
    selected_kmesh = int(selected_pair[1])
    if selected_vacuum not in VACUUMS or selected_kmesh not in KMESHES:
        raise SystemExit("HOLD: source-selected vacuum/k pair lies outside the frozen grid")

    source_reference = source_rows[0]
    extension_rows, extension_audit = audit_extension_records(extension_root, source_reference, v5)
    by_key: dict[tuple[int, float, int], dict[str, Any]] = {}
    for row in source_rows + extension_rows:
        key = (int(row["layers"]), float(row["vacuum_angstrom"]), int(row["kmesh_inplane"]))
        if key in by_key:
            raise SystemExit(f"HOLD: duplicate combined slab record for {key}")
        by_key[key] = row

    layer = strict_layer_selection(by_key, selected_vacuum, selected_kmesh)
    selected_layers = layer["selected_layers"]
    selected_record = by_key[(selected_layers, selected_vacuum, selected_kmesh)] if selected_layers is not None else None
    gate = "PASS" if selected_layers is not None else "HOLD"
    reason = None if gate == "PASS" else "no original source slab at or above seven layers passes against the preregistered 13-layer holdout"
    audit = {
        "schema": AUDIT_SCHEMA,
        "status": gate,
        "source_terminal_layer": 11,
        "extension_terminal_layer": EXTENSION_LAYER,
        "extension_terminal_eligible_for_selection": False,
        "selection_candidates_are_source_layers_only": True,
        "selected_vacuum_k_pair": [selected_vacuum, selected_kmesh],
        "energy_tolerance_mev_per_surface_atom": ENERGY_TOL_MEV,
        "downstream_layer_floor": DOWNSTREAM_LAYER_FLOOR,
        "layer_diagnostics": layer["diagnostics"],
        "eligible_source_layers": layer["eligible_layers"],
        "selected_source_layers": selected_layers,
        "reason": reason,
    }
    result = {
        "schema": RESULT_SCHEMA,
        "registration_status": "preregistered_scientific_hold_resolution",
        "gate": gate,
        "next_gate": "definitive_independent_audit" if gate == "PASS" else None,
        "source_c7_run_id": SOURCE_RUN_ID,
        "source_c7_commit": SOURCE_COMMIT,
        "source_64_result_sha256": hashlib.sha256(source_result_bytes).hexdigest(),
        "source_64_gate": source_result.get("gate"),
        "frozen_source_grid": source_grid,
        "extension_grid": {
            "layers": [EXTENSION_LAYER],
            "vacuum_angstrom": VACUUMS,
            "kmesh_inplane": KMESHES,
            "calculation_count": 16,
            "eligible_for_selection": False,
        },
        "energy_tolerance_mev_per_surface_atom": ENERGY_TOL_MEV,
        "electrostatic_convention": {
            "assume_isolated": "esm",
            "esm_bc": "bc1",
            "applied_to_source_64_and_l13_extension": True,
        },
        "bulk_provenance": source_result.get("bulk_provenance"),
        "selected_vacuum_k_pair": [selected_vacuum, selected_kmesh],
        "recommended_smallest": (
            {
                "layers": selected_layers,
                "vacuum_angstrom": selected_vacuum,
                "kmesh_inplane": selected_kmesh,
                "source_record": selected_record,
            }
            if selected_record is not None
            else None
        ),
        "strict_l13_holdout_audit": audit,
        "source_esm_geometry_audit": source_result.get("esm_geometry_audit"),
        "extension_esm_geometry_audit": extension_audit,
        "source_compact_evidence": sorted(source_compact, key=lambda item: item["tag"]),
        "analysis_entrypoint": Path(__file__).name,
        "workflow_run_id": int(os.environ.get("GITHUB_RUN_ID", "0") or 0),
        "workflow_commit": os.environ.get("GITHUB_SHA"),
    }
    out = Path(args.out).resolve()
    write_json(out, result)
    if args.source_result_out:
        write_json(Path(args.source_result_out).resolve(), source_result)
    print(json.dumps(result, indent=2))
    if gate != "PASS":
        raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--layers", type=int, required=True)
    run.add_argument("--vacuum", type=float, required=True)
    run.add_argument("--kmesh", type=int, required=True)
    run.add_argument("--handoff", required=True)
    run.add_argument("--bulk-result", required=True)
    run.add_argument("--pw", required=True)
    run.add_argument("--pseudo-dir", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--np", type=int, default=2)
    ana = sub.add_parser("analyze")
    ana.add_argument("--source-records", required=True)
    ana.add_argument("--extension-records", required=True)
    ana.add_argument("--source-result-out")
    ana.add_argument("--out", required=True)
    args = parser.parse_args()
    run_case(args) if args.command == "run" else analyze(args)


if __name__ == "__main__":
    main()
