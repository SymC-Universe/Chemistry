#!/usr/bin/env python3
"""Definitive v0.4-aware clean-slab entrypoint for ESM calculations.

This version preserves the registered 64-case matrix and the V2 energy
analysis, while correcting the ESM geometry convention: the slab is centered
around Cartesian z=0, atomic positions are emitted explicitly in angstrom, and
the open boundaries lie at +/- Lz/2. Analysis verifies the actual QE input
files and is then passed through the V4 enforcement of the frozen seven-layer
downstream floor.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import slab_runner_v2 as v2
import slab_runner_v3 as v3
import slab_runner_v4 as v4

GEOMETRY_SCHEMA = "na-cu001-esm-centered-slab-v0.2"


def fcc001_geometry_esm_centered(
    a0: float, layers: int, vacuum: float
) -> tuple[list[tuple[float, float, float]], float, float]:
    """Return primitive-cell fractional coordinates with z measured from zero."""
    if layers not in v2.LAYERS:
        raise ValueError(f"layers must be one of {v2.LAYERS}")
    dz = a0 / 2.0
    slab_height = (layers - 1) * dz
    cell_z = slab_height + vacuum
    atoms: list[tuple[float, float, float]] = []
    midpoint = (layers - 1) / 2.0
    for layer in range(layers):
        shift = 0.5 if layer % 2 else 0.0
        z_cart = (layer - midpoint) * dz
        atoms.append((shift, shift, z_cart / cell_z))
    area = a0 * a0 / 2.0
    return atoms, cell_z, area


def fcc001_cartesian_atoms_esm_centered(
    a0: float, layers: int, vacuum: float
) -> tuple[list[tuple[float, float, float]], float, float]:
    """Return explicit Cartesian atomic positions in angstrom around z=0."""
    fractional, cell_z, area = fcc001_geometry_esm_centered(a0, layers, vacuum)
    h = a0 / 2.0
    atoms = []
    for f1, f2, f3 in fractional:
        x = f1 * h + f2 * (-h)
        y = f1 * h + f2 * h
        z = f3 * cell_z
        atoms.append((x, y, z))
    return atoms, cell_z, area


def geometry_record(a0: float, layers: int, vacuum: float) -> dict[str, Any]:
    atoms, cell_z, _ = fcc001_cartesian_atoms_esm_centered(a0, layers, vacuum)
    z_cart = [z for _, _, z in atoms]
    return {
        "schema": GEOMETRY_SCHEMA,
        "atomic_position_card": "angstrom",
        "coordinate_origin": "cartesian_z_zero",
        "slab_center_z_angstrom": 0.0,
        "cell_boundaries_z_angstrom": [-cell_z / 2.0, cell_z / 2.0],
        "atomic_z_min_angstrom": min(z_cart),
        "atomic_z_max_angstrom": max(z_cart),
        "atomic_z_mean_angstrom": sum(z_cart) / len(z_cart),
        "vacuum_total_angstrom": vacuum,
        "vacuum_each_side_angstrom": vacuum / 2.0,
        "symmetric_about_zero": abs(min(z_cart) + max(z_cart)) <= 1e-12,
    }


def qe_input_esm_centered(
    *,
    bulk: dict,
    layers: int,
    vacuum: float,
    kmesh: int,
    pseudo_dir: Path,
    outdir: Path,
    tag: str,
) -> str:
    """Build an ESM input with explicit real-space coordinates around z=0."""
    atoms, cell_z, _ = fcc001_cartesian_atoms_esm_centered(
        float(bulk["a0_angstrom"]), layers, vacuum
    )
    h = float(bulk["a0_angstrom"]) / 2.0
    lines = [
        "&CONTROL",
        "  calculation = 'scf',",
        f"  prefix = '{tag}',",
        f"  pseudo_dir = '{pseudo_dir}',",
        f"  outdir = '{outdir}',",
        "  tprnfor = .true.,",
        "  tstress = .true.,",
        "  verbosity = 'high',",
        "/",
        "&SYSTEM",
        "  ibrav = 0,",
        f"  nat = {len(atoms)},",
        "  ntyp = 1,",
        f"  ecutwfc = {bulk['ecutwfc_ry']},",
        f"  ecutrho = {bulk['ecutrho_ry']},",
        "  occupations = 'smearing',",
        "  smearing = 'mv',",
        "  degauss = 0.02,",
        "  nosym = .true.,",
        "  assume_isolated = 'esm',",
        "  esm_bc = 'bc1',",
        "/",
        "&ELECTRONS",
        "  conv_thr = 1.0d-10,",
        "  mixing_beta = 0.3,",
        "  electron_maxstep = 250,",
        "/",
        "ATOMIC_SPECIES",
        f"Cu 63.54600000 {v2.PSEUDO_NAME}",
        "CELL_PARAMETERS angstrom",
        f" {h:.12f} {h:.12f} 0.0",
        f" {-h:.12f} {h:.12f} 0.0",
        f" 0.0 0.0 {cell_z:.12f}",
        "ATOMIC_POSITIONS angstrom",
    ]
    lines.extend(f"Cu {x:.12f} {y:.12f} {z:.12f}" for x, y, z in atoms)
    lines.extend(["K_POINTS automatic", f"{kmesh} {kmesh} 1 0 0 0"])
    return "\n".join(lines) + "\n"


def case_tag(layers: int, vacuum: float, kmesh: int) -> str:
    return f"cu001_L{layers}_V{vacuum:g}_K{kmesh}"


def case_record_path(out: Path, layers: int, vacuum: float, kmesh: int) -> Path:
    tag = case_tag(layers, vacuum, kmesh)
    return out.resolve() / tag / "run_record.json"


def attach_geometry_to_case_record(
    out: Path, layers: int, vacuum: float, kmesh: int
) -> Path:
    path = case_record_path(out, layers, vacuum, kmesh)
    if not path.is_file():
        raise SystemExit(f"HOLD: current slab record missing: {path}")
    row = json.loads(path.read_text())
    expected_tag = case_tag(layers, vacuum, kmesh)
    identity = {
        "tag": row.get("tag") == expected_tag,
        "layers": int(row.get("layers", -1)) == int(layers),
        "vacuum": abs(float(row.get("vacuum_angstrom", -1.0)) - float(vacuum)) <= 1e-12,
        "kmesh": int(row.get("kmesh_inplane", -1)) == int(kmesh),
    }
    if not all(identity.values()):
        raise SystemExit(f"HOLD: current slab record identity mismatch: {identity}")
    row["geometry_convention"] = geometry_record(
        float(row["a0_angstrom"]), int(row["layers"]), float(row["vacuum_angstrom"])
    )
    path.write_text(json.dumps(row, indent=2) + "\n")
    return path


def run_case(args: argparse.Namespace) -> None:
    v2.load_bulk = v3.load_bulk_v04
    v2.fcc001_geometry = fcc001_geometry_esm_centered
    v2.qe_input = qe_input_esm_centered
    v2.run_case(args)
    attach_geometry_to_case_record(
        Path(args.out), int(args.layers), float(args.vacuum), int(args.kmesh)
    )


def audit_input_file(record_path: Path, row: dict[str, Any]) -> dict[str, Any]:
    tag = str(row.get("tag") or "")
    if not tag:
        raise SystemExit("missing record tag")
    input_path = record_path.parent / f"{tag}.in"
    if not input_path.is_file():
        raise SystemExit(f"missing QE input file {input_path.name}")
    actual_hash = v2.sha256(input_path)
    if row.get("input_sha256") != actual_hash:
        raise SystemExit("QE input SHA-256 does not match the run record")

    text = input_path.read_text()
    lines = [line.strip() for line in text.splitlines()]
    if "assume_isolated = 'esm'," not in lines:
        raise SystemExit("QE input does not set assume_isolated='esm'")
    if "esm_bc = 'bc1'," not in lines:
        raise SystemExit("QE input does not set esm_bc='bc1'")
    if "ATOMIC_POSITIONS angstrom" not in lines or "ATOMIC_POSITIONS crystal" in lines:
        raise SystemExit("QE input does not use the explicit angstrom atomic-position card")

    nat = int(row.get("nat", -1))
    if nat != int(row.get("layers", -2)) or nat <= 0:
        raise SystemExit("QE input atom count cannot be reconciled with the layer count")
    atom_start = lines.index("ATOMIC_POSITIONS angstrom") + 1
    atom_lines = lines[atom_start : atom_start + nat]
    if len(atom_lines) != nat:
        raise SystemExit("QE input atomic-position block is incomplete")
    coords = []
    for line in atom_lines:
        fields = line.split()
        if len(fields) != 4 or fields[0] != "Cu":
            raise SystemExit("QE input atomic-position line is malformed")
        coords.append(tuple(float(value) for value in fields[1:4]))
    z = [value[2] for value in coords]
    if abs(sum(z) / len(z)) > 1e-9 or abs(min(z) + max(z)) > 1e-9:
        raise SystemExit("QE input atoms are not symmetric around Cartesian z=0")

    cell_start = lines.index("CELL_PARAMETERS angstrom") + 1
    cell_lines = lines[cell_start : cell_start + 3]
    if len(cell_lines) != 3:
        raise SystemExit("QE input cell block is incomplete")
    cell = [tuple(float(value) for value in line.split()) for line in cell_lines]
    if any(len(vector) != 3 for vector in cell):
        raise SystemExit("QE input cell vector is malformed")
    if abs(cell[2][2] - float(row.get("cell_z_angstrom", -1.0))) > 1e-9:
        raise SystemExit("QE input cell height disagrees with the run record")

    k_start = lines.index("K_POINTS automatic") + 1
    k_values = tuple(int(value) for value in lines[k_start].split())
    kmesh = int(row.get("kmesh_inplane", -1))
    if k_values != (kmesh, kmesh, 1, 0, 0, 0):
        raise SystemExit("QE input k mesh disagrees with the run record")

    return {
        "tag": tag,
        "input_file": input_path.name,
        "input_sha256": actual_hash,
        "nat": nat,
        "atomic_position_card": "angstrom",
        "z_mean_angstrom": sum(z) / len(z),
        "z_min_plus_max_angstrom": min(z) + max(z),
        "cell_z_angstrom": cell[2][2],
        "kmesh_inplane": kmesh,
        "assume_isolated": "esm",
        "esm_bc": "bc1",
    }


def audit_raw_geometry(records_root: Path) -> dict[str, Any]:
    paths = sorted(records_root.rglob("run_record.json"))
    if len(paths) != 64:
        raise SystemExit(f"HOLD: expected 64 raw slab records, found {len(paths)}")
    rows = [json.loads(path.read_text()) for path in paths]
    bad: list[dict[str, str]] = []
    input_records: list[dict[str, Any]] = []
    for path, row in zip(paths, rows):
        geom = row.get("geometry_convention") or {}
        conditions = [
            geom.get("schema") == GEOMETRY_SCHEMA,
            geom.get("atomic_position_card") == "angstrom",
            geom.get("coordinate_origin") == "cartesian_z_zero",
            abs(float(geom.get("slab_center_z_angstrom", 1.0))) <= 1e-12,
            abs(float(geom.get("atomic_z_mean_angstrom", 1.0))) <= 1e-12,
            bool(geom.get("symmetric_about_zero")),
            abs(float(geom.get("vacuum_total_angstrom", -1.0)) - float(row["vacuum_angstrom"])) <= 1e-12,
            abs(2.0 * float(geom.get("vacuum_each_side_angstrom", -1.0)) - float(row["vacuum_angstrom"])) <= 1e-12,
        ]
        if not all(conditions):
            bad.append({"tag": str(row.get("tag")), "reason": "geometry metadata mismatch"})
            continue
        try:
            input_records.append(audit_input_file(path, row))
        except (SystemExit, ValueError, IndexError) as exc:
            bad.append({"tag": str(row.get("tag")), "reason": str(exc)})
    if bad:
        raise SystemExit(f"HOLD: ESM-centered raw/input audit failed: {json.dumps(bad, sort_keys=True)}")
    return {
        "schema": "na-cu001-esm-centered-raw-audit-v0.3",
        "status": "PASS",
        "verified_record_count": len(rows),
        "verified_input_count": len(input_records),
        "geometry_schema": GEOMETRY_SCHEMA,
        "atomic_position_card": "angstrom",
        "coordinate_origin": "cartesian_z_zero",
        "all_slabs_symmetric_about_zero": True,
        "vacuum_split_equally_between_open_boundaries": True,
        "all_input_hashes_match_run_records": True,
        "all_inputs_set_esm_bc1": True,
        "input_records": sorted(input_records, key=lambda item: item["tag"]),
    }


def analyze(args: argparse.Namespace) -> None:
    records_root = Path(args.records).resolve()
    geometry_audit = audit_raw_geometry(records_root)
    out = Path(args.out).resolve()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpout = Path(tmpdir) / "FLOOR_AUDITED_RESULT.json"
        try:
            v4.analyze(SimpleNamespace(records=str(records_root), out=str(tmpout)))
        except SystemExit as exc:
            if not tmpout.is_file():
                raise
            result = json.loads(tmpout.read_text())
            result["esm_geometry_audit"] = geometry_audit
            result["analysis_entrypoint"] = "slab_runner_v5.py"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(result, indent=2) + "\n")
            raise SystemExit(exc.code)
        result = json.loads(tmpout.read_text())
    result["esm_geometry_audit"] = geometry_audit
    result["analysis_entrypoint"] = "slab_runner_v5.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result.get("gate") != "PASS":
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
    ana.add_argument("--records", required=True)
    ana.add_argument("--out", required=True)
    args = parser.parse_args()
    run_case(args) if args.command == "run" else analyze(args)


if __name__ == "__main__":
    main()
