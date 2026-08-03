#!/usr/bin/env python3
"""Versioned closure entrypoint for the audited v0.4 bulk chain.

Only the two commands that directly consume the bulk handoff are replaced:
`slab-handoff` and `resolve-na`. Every later physical calculation delegates to
closure_engine_v2.py unchanged. This preserves the corrected V2 adsorption,
NEB, Hessian, connectivity, sensitivity, rate, and admission behavior while
requiring the independently verified v0.4 bulk bridge.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import closure_engine_v2 as v2

RESULT_SCHEMA = "na-cu001-bulk-selection-v0.4"
HANDOFF_SCHEMA = "na-cu001-bulk-to-slab-handoff-v0.4"
BRIDGE_SCHEMA = "na-cu001-audited-bulk-downstream-bridge-v0.1"
RESULT_FILENAME = "BULK_CONVERGENCE_RESULT.json"
BRIDGE_FILENAME = "BULK_V04_DOWNSTREAM_BRIDGE.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def bridge_source_hash(bridge: dict[str, Any], schema: str) -> str | None:
    rows = [x for x in bridge.get("source_artifacts", []) if x.get("schema") == schema]
    return str(rows[0].get("sha256")) if len(rows) == 1 else None


def load_v04_bundle(bulk_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path, Path]:
    bulk_path = bulk_path.resolve()
    result_path = bulk_path.parent / RESULT_FILENAME
    bridge_path = bulk_path.parent / BRIDGE_FILENAME
    if not result_path.is_file() or not bridge_path.is_file():
        raise SystemExit("HOLD: v0.4 result or audited bridge is missing beside bulk handoff")
    bulk = read(bulk_path)
    result = read(result_path)
    bridge = read(bridge_path)
    if bulk.get("schema") != HANDOFF_SCHEMA or bulk.get("scientific_status") != "bulk_convergence_passed_slab_not_yet_run":
        raise SystemExit("HOLD: bulk handoff is not v0.4 PASS")
    if result.get("schema") != RESULT_SCHEMA or result.get("gate") != "PASS" or result.get("status") != "PASS":
        raise SystemExit("HOLD: bulk result is not v0.4 PASS")
    if bridge.get("schema") != BRIDGE_SCHEMA or bridge.get("status") != "PASS":
        raise SystemExit("HOLD: audited v0.4 bridge is not PASS")
    if bulk.get("source_result", {}).get("sha256") != sha256(result_path):
        raise SystemExit("HOLD: v0.4 handoff/result hash mismatch")
    if bridge_source_hash(bridge, HANDOFF_SCHEMA) != sha256(bulk_path):
        raise SystemExit("HOLD: bridge/handoff hash mismatch")
    if bridge_source_hash(bridge, RESULT_SCHEMA) != sha256(result_path):
        raise SystemExit("HOLD: bridge/result hash mismatch")
    if not (bridge.get("reference_audit_gate") or {}).get("pass"):
        raise SystemExit("HOLD: independent v0.4 reference audit did not pass")
    if int(bridge.get("verified_eos_count", -1)) != 46 or int(bridge.get("verified_scf_count", -1)) != 276:
        raise SystemExit("HOLD: v0.4 bridge inventory is incomplete")
    if not (bridge.get("selected_candidate_gate") or {}).get("pass"):
        raise SystemExit("HOLD: selected v0.4 candidate did not pass independent revalidation")
    return bulk, result, bridge, result_path, bridge_path


def command_slab_handoff(args: Any) -> None:
    result_path = Path(args.slab_result).resolve()
    bulk_path = Path(args.bulk_handoff).resolve()
    result = v2.read_json(result_path)
    v2.require(result, "na-cu001-clean-slab-selection-v0.3")
    bulk, _, bridge, bulk_result_path, bridge_path = load_v04_bundle(bulk_path)
    selected = result.get("recommended_smallest")
    if not isinstance(selected, dict):
        raise SystemExit("HOLD: slab result lacks selection")
    source = selected.get("source_record") or {}
    bridge_selected = bridge.get("selected_bulk_settings") or {}
    if int(source.get("ecutwfc_ry", -1)) != int(bridge_selected.get("ecutwfc_ry", -2)):
        raise SystemExit("HOLD: slab records do not use audited v0.4 cutoff")
    if int(source.get("bulk_kmesh", -1)) != int((bridge_selected.get("kmesh_cubic") or [-2])[0]):
        raise SystemExit("HOLD: slab records do not use audited v0.4 bulk mesh provenance")
    handoff = {
        "schema": "na-cu001-clean-slab-to-relaxation-handoff-v0.3",
        "status": "PASS",
        "system": "clean Cu(001)",
        "selected_slab_settings": {
            "layers": max(7, int(selected["layers"])),
            "convergence_selected_layers": int(selected["layers"]),
            "vacuum_angstrom": float(selected["vacuum_angstrom"]),
            "kmesh_inplane": int(selected["kmesh_inplane"]),
            "a0_angstrom": float(source["a0_angstrom"]),
            "ecutwfc_ry": float(source["ecutwfc_ry"]),
            "ecutrho_ry": float(source["ecutrho_ry"]),
            "bulk_kmesh": int(source["bulk_kmesh"]),
            "bulk_energy_ev_per_atom": float(source["e0_ev_per_atom"]),
            "surface_cell": "primitive Cu(001), area a0^2/2",
            "electrostatic_convention": result.get("electrostatic_convention") or {"assume_isolated": "esm", "esm_bc": "bc1"},
        },
        "bulk_v04_provenance": {
            "bulk_handoff": v2.artifact(bulk_path),
            "bulk_result": v2.artifact(bulk_result_path),
            "audited_bridge": v2.artifact(bridge_path),
            "reference_audit_gate": bridge["reference_audit_gate"],
            "selection_verification": bridge.get("selection_verification"),
        },
        "convergence_rule": {
            "surface_excess_tolerance_mev_per_surface_atom": result["energy_tolerance_mev_per_surface_atom"],
            "selected_vacuum_kmesh": [selected["vacuum_angstrom"], selected["kmesh_inplane"]],
            "convergence_selected_layers": selected["layers"],
            "downstream_layers": max(7, int(selected["layers"])),
            "downstream_layer_rule": "use at least 7 layers so the expanded one-sided mobility model retains a fixed bottom surface",
        },
        "input_artifacts": [v2.artifact(result_path), v2.artifact(bulk_path), v2.artifact(bulk_result_path), v2.artifact(bridge_path)],
        "next_gate": "electrostatic_parity",
    }
    v2.write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))


def command_resolve_na(args: Any) -> None:
    protocol = v2.load_protocol(args.protocol)
    probe_path = Path(args.probe).resolve()
    bulk_path = Path(args.bulk_handoff).resolve()
    probe = v2.read_json(probe_path)
    v2.require(probe, "na-cu001-na-pseudo-probe-v0.2")
    bulk, _, bridge, result_path, bridge_path = load_v04_bundle(bulk_path)
    selected = probe["selected"]
    cut = probe["authoritative_cutoffs"]
    wfc = max(float(bulk["selected_bulk_settings"]["ecutwfc_ry"]), float(cut["recommended_ecutwfc_ry"]))
    rho = max(float(bulk["selected_bulk_settings"]["ecutrho_ry"]), float(cut["recommended_ecutrho_ry"]))
    source = Path(args.pseudo_root).resolve() / selected["path"]
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pseudo_dir.mkdir(parents=True, exist_ok=True)
    dest = pseudo_dir / selected["filename"]
    shutil.copy2(source, dest)
    if sha256(dest) != selected["sha256"]:
        raise SystemExit("HOLD: Na UPF copy hash mismatch")
    root = Path(args.out_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = root / "na_atom.in"
    out = root / "na_atom.out"
    inp.write_text(v2.legacy.na_atom_input(prefix="na_isolated", outdir=tmp, pseudo_dir=pseudo_dir,
                                           na_filename=dest.name, ecutwfc=wfc, ecutrho=rho))
    rc, elapsed = v2.legacy.run_command(v2.legacy.mpi_command(Path(args.pw).resolve(), args.np), root, out, inp)
    text = out.read_text(errors="replace")
    energy = v2.legacy.parse_qe_energy(text)
    checks = {
        "returncode_zero": rc == 0,
        "job_done": "JOB DONE." in text,
        "energy_present": energy is not None,
        "archive_hash_verified": probe["archive"]["sha256"] == protocol["immutable_sources"]["sssp_pbe_efficiency_v2_archive_sha256"],
        "upf_hash_verified": selected["sha256"] == protocol["immutable_sources"]["na_upf_sha256"],
        "bulk_reference_audit_passed": bool(bridge["reference_audit_gate"]["pass"]),
    }
    handoff = {
        "schema": "na-cu001-na-pseudopotential-handoff-v0.2",
        "status": "PASS" if all(checks.values()) else "HOLD",
        "selected": {**selected, "installed_filename": dest.name, "installed_sha256": sha256(dest)},
        "authoritative_cutoffs": cut,
        "selected_mixed_settings": {
            "ecutwfc_ry": wfc,
            "ecutrho_ry": rho,
            "rule": "componentwise maximum of audited v0.4 bulk PASS and authoritative SSSP v2 metadata",
        },
        "bulk_v04_provenance": {
            "bulk_handoff": v2.artifact(bulk_path),
            "bulk_result": v2.artifact(result_path),
            "audited_bridge": v2.artifact(bridge_path),
        },
        "isolated_atom_reference": {
            "energy_ev": energy,
            "elapsed_s": elapsed,
            "input_sha256": sha256(inp),
            "output_sha256": sha256(out),
        },
        "pass_checks": checks,
        "input_artifacts": [v2.artifact(probe_path), v2.artifact(bulk_path), v2.artifact(result_path), v2.artifact(bridge_path)],
        "next_gate": "adsorption_site_screening",
    }
    v2.write_json(Path(args.out).resolve(), handoff)
    print(json.dumps(handoff, indent=2))
    if handoff["status"] != "PASS":
        raise SystemExit(2)


def main() -> None:
    v2.command_slab_handoff = command_slab_handoff
    v2.command_resolve_na = command_resolve_na
    args = v2.build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
