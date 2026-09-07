#!/usr/bin/env python3
"""Versioned slab entrypoint for an independently verified v0.4 bulk bridge.

This module leaves slab_runner_v2.py unchanged. It substitutes only the bulk
loader used by V2 slab cases, requiring the prospectively frozen bridge record
and the original v0.4 result/handoff hashes. Slab geometry, ESM convention,
registered matrix, analysis, and numerical thresholds remain V2 behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import slab_runner_v2 as v2

RESULT_SCHEMA = "na-cu001-bulk-selection-v0.4"
HANDOFF_SCHEMA = "na-cu001-bulk-to-slab-handoff-v0.4"
BRIDGE_SCHEMA = "na-cu001-audited-bulk-downstream-bridge-v0.1"
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


def close(a: Any, b: Any, tol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def bridge_path(handoff_path: Path) -> Path:
    path = handoff_path.parent / BRIDGE_FILENAME
    if not path.is_file():
        raise SystemExit(f"HOLD: missing audited v0.4 bridge {path}")
    return path


def source_hash(bridge: dict[str, Any], schema: str) -> str | None:
    matches = [x for x in bridge.get("source_artifacts", []) if x.get("schema") == schema]
    if len(matches) != 1:
        return None
    return str(matches[0].get("sha256"))


def load_bulk_v04(handoff_path: Path, result_path: Path) -> dict[str, Any]:
    handoff_path = handoff_path.resolve()
    result_path = result_path.resolve()
    bp = bridge_path(handoff_path)
    handoff = read(handoff_path)
    result = read(result_path)
    bridge = read(bp)

    if handoff.get("schema") != HANDOFF_SCHEMA or handoff.get("scientific_status") != "bulk_convergence_passed_slab_not_yet_run":
        raise SystemExit("HOLD: unsupported or non-PASS v0.4 bulk handoff")
    if result.get("schema") != RESULT_SCHEMA or result.get("gate") != "PASS" or result.get("status") != "PASS":
        raise SystemExit("HOLD: unsupported or non-PASS v0.4 bulk result")
    if bridge.get("schema") != BRIDGE_SCHEMA or bridge.get("status") != "PASS":
        raise SystemExit("HOLD: audited v0.4 downstream bridge is not PASS")
    if source_hash(bridge, RESULT_SCHEMA) != sha256(result_path):
        raise SystemExit("HOLD: bridge/result hash mismatch")
    if source_hash(bridge, HANDOFF_SCHEMA) != sha256(handoff_path):
        raise SystemExit("HOLD: bridge/handoff hash mismatch")
    if handoff.get("source_result", {}).get("sha256") != sha256(result_path):
        raise SystemExit("HOLD: handoff/result hash mismatch")
    if not (bridge.get("reference_audit_gate") or {}).get("pass"):
        raise SystemExit("HOLD: v0.4 reference audit did not pass")
    if int(bridge.get("verified_eos_count", -1)) != 46 or int(bridge.get("verified_scf_count", -1)) != 276:
        raise SystemExit("HOLD: audited v0.4 bridge lacks the complete EOS/SCF inventory")

    hs = handoff.get("selected_bulk_settings") or {}
    bs = bridge.get("selected_bulk_settings") or {}
    selected = result.get("recommended_smallest_cost_candidate") or {}
    kcube = hs.get("kmesh_cubic")
    if not isinstance(kcube, list) or len(kcube) != 3 or len(set(int(x) for x in kcube)) != 1:
        raise SystemExit("HOLD: invalid v0.4 cubic bulk mesh")
    checks = {
        "ecutwfc": int(hs.get("ecutwfc_ry", -1)) == int(bs.get("ecutwfc_ry", -2)) == int(selected.get("ecutwfc_ry", -3)),
        "ecutrho": int(hs.get("ecutrho_ry", -1)) == int(bs.get("ecutrho_ry", -2)) == int(selected.get("ecutrho_ry", -3)),
        "kmesh": int(kcube[0]) == int((bs.get("kmesh_cubic") or [-2])[0]) == int(selected.get("kmesh", -3)),
        "a0": close(hs.get("equilibrium_lattice_constant_angstrom"), selected.get("fit", {}).get("a0_angstrom")),
        "e0": close(hs.get("equilibrium_energy_ev_per_atom"), selected.get("fit", {}).get("e0_ev_per_atom")),
    }
    if not all(checks.values()):
        raise SystemExit(f"HOLD: v0.4 selected settings disagree across result/handoff/bridge: {checks}")
    gate = bridge.get("selected_candidate_gate") or {}
    if not gate.get("pass"):
        raise SystemExit("HOLD: independently recomputed selected candidate gate is not PASS")

    return {
        "a0_angstrom": float(hs["equilibrium_lattice_constant_angstrom"]),
        "e0_ev_per_atom": float(hs["equilibrium_energy_ev_per_atom"]),
        "ecutwfc_ry": int(hs["ecutwfc_ry"]),
        "ecutrho_ry": int(hs["ecutrho_ry"]),
        "bulk_kmesh": int(kcube[0]),
        "bulk_gate_revalidation": gate,
        "handoff_sha256": sha256(handoff_path),
        "result_sha256": sha256(result_path),
        "v04_bridge_sha256": sha256(bp),
        "v04_reference_audit_gate": bridge["reference_audit_gate"],
        "v04_selection_verification": bridge.get("selection_verification"),
    }


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
    if args.command == "run":
        v2.load_bulk = load_bulk_v04
        v2.run_case(args)
    else:
        v2.analyze(args)


if __name__ == "__main__":
    main()
