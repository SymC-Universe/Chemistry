#!/usr/bin/env python3
"""Mechanical recovery for the definitive Na/Cu(001) electrostatic gate.

The original three-SCF gate timed out after the selected 12 A ESM case completed.
This runner changes no scientific setting. It executes only one registered missing
case at a time and can later aggregate the completed 12 A ESM checkpoint with the
recovered 16 A ESM and periodic diagnostic records under the frozen v0.2 gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import electrostatic_consistency_v1 as base

CASES = {
    "esm_selected": {"vacuum": 12.0, "esm": True},
    "esm_next_vacuum": {"vacuum": 16.0, "esm": True},
    "periodic_diagnostic": {"vacuum": 12.0, "esm": False},
}


def common_values(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    slab, audit, protocol, provenance = base.verify_inputs(args)
    s = slab["selected_slab_settings"]
    values = {
        "a0": float(s["a0_angstrom"]),
        "layers": int(s["layers"]),
        "kmesh": int(s["kmesh_inplane"]),
        "ecutwfc": float(s["ecutwfc_ry"]),
        "ecutrho": float(s["ecutrho_ry"]),
        "bulk_energy": float(s["bulk_energy_ev_per_atom"]),
    }
    if values["layers"] != 11 or values["kmesh"] != 16 or values["ecutwfc"] != 90.0 or values["ecutrho"] != 270.0:
        raise SystemExit("HOLD: recovery inputs differ from frozen definitive settings")
    provenance["recovery_from_run_id"] = int(args.recovery_from_run_id)
    provenance["recovery_mechanical_reason"] = "original three-case wrapper reached GitHub timeout after completed selected ESM checkpoint"
    provenance["scientific_settings_changed"] = False
    return slab, audit, protocol, provenance, values


def run_case(args: argparse.Namespace) -> None:
    _, _, _, provenance, values = common_values(args)
    if args.tag not in {"esm_next_vacuum", "periodic_diagnostic"}:
        raise SystemExit("HOLD: recovery may execute only the two missing registered cases")
    spec = CASES[args.tag]
    record = base.run_case(
        root=Path(args.out_dir).resolve(),
        tag=args.tag,
        pw=Path(args.pw),
        pseudo_dir=Path(args.pseudo_dir),
        np_count=args.np,
        a0=float(values["a0"]),
        layers=int(values["layers"]),
        vacuum=float(spec["vacuum"]),
        kmesh=int(values["kmesh"]),
        ecutwfc=float(values["ecutwfc"]),
        ecutrho=float(values["ecutrho"]),
        bulk_energy_ev_per_atom=float(values["bulk_energy"]),
        esm=bool(spec["esm"]),
    )
    record["recovery_provenance"] = provenance
    base.write_json(Path(args.out_dir).resolve() / args.tag / "run_record.json", record)
    print(json.dumps(record, indent=2))
    if not record.get("complete"):
        raise SystemExit(2)


def verify_case(path: Path, tag: str) -> dict[str, Any]:
    row = base.read_json(path.resolve())
    spec = CASES[tag]
    if row.get("schema") != "na-cu001-electrostatic-consistency-case-v0.1" or row.get("tag") != tag:
        raise SystemExit(f"HOLD: malformed case record for {tag}")
    expected = [11, float(spec["vacuum"]), 16, 90.0, 270.0]
    actual = [int(row.get("layers", -1)), float(row.get("vacuum_angstrom", -1)), int(row.get("kmesh_inplane", -1)), float(row.get("ecutwfc_ry", -1)), float(row.get("ecutrho_ry", -1))]
    if actual != expected:
        raise SystemExit(f"HOLD: recovered case settings changed for {tag}: {actual}")
    if not bool(row.get("complete")) or row.get("returncode") != 0 or not row.get("job_done") or not row.get("scf_converged") or row.get("energy_ev") is None:
        raise SystemExit(f"HOLD: case is not complete: {tag}")
    geom = row.get("geometry_convention") or {}
    if geom.get("schema") != "na-cu001-esm-centered-slab-v0.2" or geom.get("coordinate_origin") != "cartesian_z_zero" or geom.get("atomic_position_card") != "angstrom" or not geom.get("symmetric_about_zero"):
        raise SystemExit(f"HOLD: centered geometry not proven for {tag}")
    electro = row.get("electrostatic_convention") or {}
    if bool(spec["esm"]):
        if electro.get("assume_isolated") != "esm" or electro.get("esm_bc") != "bc1":
            raise SystemExit(f"HOLD: ESM convention mismatch for {tag}")
    else:
        if electro.get("role") != "periodic_diagnostic_only":
            raise SystemExit("HOLD: periodic case lost diagnostic-only role")
    inp = path.parent / f"{tag}.in"
    out = path.parent / f"{tag}.out"
    if not inp.is_file() or not out.is_file():
        raise SystemExit(f"HOLD: raw input/output missing for {tag}")
    if base.sha256(inp) != row.get("input_sha256") or base.sha256(out) != row.get("output_sha256"):
        raise SystemExit(f"HOLD: raw hash mismatch for {tag}")
    return row


def analyze(args: argparse.Namespace) -> None:
    slab, audit, protocol, provenance, _ = common_values(args)
    selected = verify_case(Path(args.selected_record), "esm_selected")
    next_v = verify_case(Path(args.next_record), "esm_next_vacuum")
    periodic = verify_case(Path(args.periodic_record), "periodic_diagnostic")
    records = [selected, next_v, periodic]
    esm_delta = abs(float(selected["surface_excess_ev_per_surface_atom"]) - float(next_v["surface_excess_ev_per_surface_atom"]))
    boundary_delta = abs(float(selected["surface_excess_ev_per_surface_atom"]) - float(periodic["surface_excess_ev_per_surface_atom"]))
    tol_mev = float(protocol["surface"]["esm_vacuum_stability_tolerance_mev_per_surface_atom"])
    tol_ev = tol_mev / 1000.0
    checks = {
        "definitive_audit_pass": audit.get("status") == "PASS",
        "frozen_selected_setting_11L_12A_K16": True,
        "explicit_cartesian_z_zero_preserved": all(bool(row["geometry_convention"]["symmetric_about_zero"]) for row in records),
        "selected_esm_scf_completed": True,
        "next_vacuum_esm_scf_completed": True,
        "periodic_diagnostic_completed": True,
        "esm_next_vacuum_change_le_1mev_per_surface_atom": esm_delta <= tol_ev,
        "periodic_diagnostic_nonselecting": True,
    }
    status = "PASS" if all(checks.values()) else "HOLD"
    provenance["selected_esm_checkpoint_origin_run_id"] = int(args.recovery_from_run_id)
    provenance["recovery_run_id"] = int(args.recovery_run_id)
    payload = {
        "schema": "na-cu001-electrostatic-consistency-v0.3",
        "status": status,
        "selected_convention": {"assume_isolated": "esm", "esm_bc": "bc1"},
        "coordinate_convention": {"atomic_position_card": "angstrom", "origin": "cartesian_z_zero"},
        "selected_slab": {"layers": 11, "vacuum_angstrom": 12.0, "kmesh_inplane": 16},
        "comparison_vacuum_angstrom": 16.0,
        "tolerance_mev_per_surface_atom": tol_mev,
        "tolerance_ev_per_surface_atom": tol_ev,
        "esm_vacuum_delta_ev_per_surface_atom": esm_delta,
        "periodic_vs_esm_diagnostic_ev_per_surface_atom": boundary_delta,
        "periodic_diagnostic_role": "reported only; cannot select, reject, or retune the registered ESM bc1 route",
        "records": records,
        "pass_checks": checks,
        "provenance": provenance,
        "input_artifacts": {
            "slab_handoff_sha256": base.sha256(Path(args.slab_handoff).resolve()),
            "audit_record_sha256": base.sha256(Path(args.audit_record).resolve()),
            "protocol_sha256": base.sha256(Path(args.protocol).resolve()),
            "selected_record_sha256": base.sha256(Path(args.selected_record).resolve()),
            "next_record_sha256": base.sha256(Path(args.next_record).resolve()),
            "periodic_record_sha256": base.sha256(Path(args.periodic_record).resolve()),
        },
        "next_gate": "clean_surface_relaxation",
    }
    base.write_json(Path(args.out).resolve(), payload)
    print(json.dumps(payload, indent=2))
    if status != "PASS":
        raise SystemExit(2)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--slab-handoff", required=True)
    parser.add_argument("--audit-record", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--pw", required=False, default="/bin/true")
    parser.add_argument("--pseudo-dir", required=False, default=".")
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--audit-run-id", required=True)
    parser.add_argument("--audit-commit", required=True)
    parser.add_argument("--control-commit", required=True)
    parser.add_argument("--recovery-from-run-id", required=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("case")
    add_common(run)
    run.add_argument("--tag", required=True, choices=["esm_next_vacuum", "periodic_diagnostic"])
    run.add_argument("--out-dir", required=True)
    run.add_argument("--np", type=int, default=2)
    run.set_defaults(func=run_case)
    agg = sub.add_parser("analyze")
    add_common(agg)
    agg.add_argument("--selected-record", required=True)
    agg.add_argument("--next-record", required=True)
    agg.add_argument("--periodic-record", required=True)
    agg.add_argument("--recovery-run-id", required=True)
    agg.add_argument("--out", required=True)
    agg.set_defaults(func=analyze)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
