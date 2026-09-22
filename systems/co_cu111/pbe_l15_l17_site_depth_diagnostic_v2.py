#!/usr/bin/env python3
"""Resource-feasible L15-vs-L17 CO/Cu(111) site-depth diagnostic v0.2.

This is a mechanical/resource adaptation of the v0.1 matched-site screen after
all eight 4x4 segment-1 jobs failed before producing a scientific energy result
because the standard GitHub runner could not allocate the QE wavefunction
arrays.  The scientific bookkeeping remains fail-closed:

* the original L17 1 meV clean-surface failure remains a failure;
* the v0.1 4x4 resource failure remains a mechanical failure;
* this v0.2 test is explicitly a 2x2, 0.25 ML depth diagnostic only;
* the 5 meV/CO sensitivity ceiling is inherited unchanged;
* a PASS here cannot be relabeled as low-coverage 4x4 convergence.

The production SCF/restart machinery is reused from the already-tested v1
runner.  Only protocol validation and matched geometry construction are
specialized here.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
V1_PATH = HERE / "pbe_l15_l17_observable_sufficiency_v1.py"
spec = importlib.util.spec_from_file_location("l15l17_v1", V1_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("MECHANICAL_HOLD: cannot load v1 exact-restart runner")
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)

PROTOCOL_SCHEMA = "co-cu111-pbe-l15-l17-site-depth-diagnostic-v0.2"
PROTOCOL_STATUS = "FROZEN_AFTER_V0_1_RESOURCE_HOLD_BEFORE_V0_2_RESULTS"
STATE_SCHEMA = "co-cu111-l15-l17-site-depth-scf-state-v0.2"
RESULT_SCHEMA = "co-cu111-l15-l17-site-depth-diagnostic-result-v0.2"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def verify_protocol_v2(p: dict[str, Any]) -> None:
    if p.get("schema") != PROTOCOL_SCHEMA or p.get("status") != PROTOCOL_STATUS:
        raise SystemExit("SCIENTIFIC_HOLD: wrong or unfrozen v0.2 site-depth protocol")
    if p.get("scientific_scope") != "PROSPECTIVE_RESOURCE_FEASIBLE_SLAB_DEPTH_DIAGNOSTIC_AFTER_4X4_MEMORY_HOLD":
        raise SystemExit("SCIENTIFIC_HOLD: v0.2 diagnostic scope drift")

    parent = p["parent_v0_1_resource_hold"]
    if int(parent.get("workflow_run_id", -1)) != 34016668712:
        raise SystemExit("SCIENTIFIC_HOLD: v0.1 resource-hold provenance drift")
    if parent.get("preflight_passed") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: v0.1 preflight provenance drift")
    if parent.get("all_eight_segment1_cases_failed_before_scientific_energy_result") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: v0.1 failure scope drift")
    if parent.get("failure_class") != "MECHANICAL_RESOURCE_HOLD_MEMORY":
        raise SystemExit("SCIENTIFIC_HOLD: v0.1 failure class drift")
    if parent.get("scientific_result_consulted") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: v0.2 was contaminated by v0.1 scientific outcomes")

    s15 = p["source_l15"]
    s17 = p["source_l17"]
    if (s15.get("case_id"), int(s15.get("layers", -1)), float(s15.get("vacuum_angstrom", -1)), int(s15.get("kmesh", -1))) != (
        "L15-V32-K28-extension-audit", 15, 32.0, 28
    ):
        raise SystemExit("SCIENTIFIC_HOLD: L15 source drift")
    if (s17.get("case_id"), int(s17.get("layers", -1)), float(s17.get("vacuum_angstrom", -1)), int(s17.get("kmesh", -1))) != (
        "L17-V36-K32-extension-audit", 17, 36.0, 32
    ):
        raise SystemExit("SCIENTIFIC_HOLD: L17 source drift")
    if s17.get("required_result_status") != "NUMERICAL_HOLD_L17_TERMINAL_UNDER_CURRENT_CONTRACT":
        raise SystemExit("SCIENTIFIC_HOLD: original L17 HOLD not preserved")
    if s17.get("original_surface_excess_gate_pass") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: original L17 surface gate was reclassified")

    screen = p["matched_site_depth_diagnostic"]
    if screen.get("supercell") != [2, 2]:
        raise SystemExit("SCIENTIFIC_HOLD: v0.2 diagnostic supercell drift")
    if not close(screen.get("nominal_coverage_ML"), 0.25):
        raise SystemExit("SCIENTIFIC_HOLD: v0.2 coverage drift")
    if screen.get("intended_low_coverage_supercell_not_claimed") != [4, 4] or not close(screen.get("intended_low_coverage_ML_not_claimed"), 0.0625):
        raise SystemExit("SCIENTIFIC_HOLD: low-coverage non-claim removed")
    if screen.get("sites") != ["top", "bridge", "fcc_hollow", "hcp_hollow"]:
        raise SystemExit("SCIENTIFIC_HOLD: site set drift")
    if not close(screen.get("common_vacuum_angstrom"), 36.0):
        raise SystemExit("SCIENTIFIC_HOLD: common vacuum drift")
    if int(screen.get("kmesh", -1)) != 8:
        raise SystemExit("SCIENTIFIC_HOLD: reciprocal-density-preserving K8 drift")
    if not close(screen.get("slab_depth_sensitivity_max_ev_per_CO"), 0.005):
        raise SystemExit("SCIENTIFIC_HOLD: inherited 5 meV/CO sensitivity ceiling drift")
    if screen.get("same_global_minimum_required") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: same-global-minimum requirement disabled")

    ex = p["execution"]
    if ex.get("execution_mode") != "DIRECT_ONE_RANK" or int(ex.get("mpi_ranks", -1)) != 1:
        raise SystemExit("SCIENTIFIC_HOLD: execution rank drift")
    if ex.get("checkpoint_mode") != "QE_CLEAN_MAX_SECONDS_EXACT_RESTART":
        raise SystemExit("SCIENTIFIC_HOLD: exact-restart contract disabled")
    if int(ex.get("qe_max_seconds_per_segment", -1)) != 16200:
        raise SystemExit("SCIENTIFIC_HOLD: QE checkpoint cadence drift")
    if int(ex.get("maximum_scf_segments", -1)) != 6:
        raise SystemExit("SCIENTIFIC_HOLD: finite segment bound drift")

    decision = p["decision"]
    if decision.get("absolute_clean_surface_pass_claimed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: absolute clean-surface PASS was invented")
    if decision.get("low_coverage_4x4_sufficiency_claimed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: 4x4 low-coverage sufficiency was invented")
    if decision.get("l17_original_failure_preserved") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: original L17 failure not preserved")
    if decision.get("automatic_l19_dispatch") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: unauthorized L19 auto-dispatch enabled")

    prov = p["provenance"]
    required_false = (
        "original_1_mev_clean_surface_gate_changed",
        "original_l17_result_reclassified",
        "kinetic_inputs_used",
        "barrier_or_rate_inputs_used",
        "threshold_retuned_to_observed_l17_result",
        "coverage_reduced_for_resource_feasibility",
    )
    for key in required_false:
        if prov.get(key) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: provenance drift: {key}")
    if prov.get("coverage_increased_from_0p0625_to_0p25_for_resource_feasibility") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: coverage-change disclosure missing")
    if prov.get("coverage_change_explicitly_limits_interpretation") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: interpretation firewall missing")


def load_protocol_v2(path: Path) -> dict[str, Any]:
    p = v1.load_json(path)
    verify_protocol_v2(p)
    q = json.loads(json.dumps(p))
    # The v1 execution engine consumes this generic key.  The source protocol
    # retains the more explicit v0.2 name and interpretation limits.
    q["matched_site_screen"] = q["matched_site_depth_diagnostic"]
    return q


def matched_geometry_v2(source: dict[str, Any], depth: str, site: str, p: dict[str, Any]):
    screen = p["matched_site_screen"]
    layers = int(source["layers"])
    if site not in screen["sites"]:
        raise SystemExit("SCIENTIFIC_HOLD: requested site is outside frozen v0.2 diagnostic")
    n = int(screen["supercell"][0])
    if screen["supercell"] != [n, n] or n != 2:
        raise SystemExit("SCIENTIFIC_HOLD: only the frozen 2x2 v0.2 diagnostic is admissible")

    a0 = 3.632355796707377
    axy = a0 / math.sqrt(2.0)
    a1 = [n * axy, 0.0, 0.0]
    a2 = [0.5 * n * axy, 0.5 * n * math.sqrt(3.0) * axy, 0.0]
    base_cell = json.loads(json.dumps(source["cell_angstrom"]))
    source_vacuum = float(source["vacuum_angstrom"])
    common_vacuum = float(screen["common_vacuum_angstrom"])
    cell_z = float(base_cell[2][2]) + (common_vacuum - source_vacuum)
    cell = [a1, a2, [0.0, 0.0, cell_z]]

    z_by_layer: list[float | None] = [None] * layers
    for atom in source["final_atoms"]:
        idx = int(atom["layer"])
        z_by_layer[idx] = float(atom["position_angstrom"][2])
    if any(z is None for z in z_by_layer):
        raise SystemExit("MECHANICAL_HOLD: source clean geometry lacks layer z values")

    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        su, sv = v1.layer_shift(layer)
        for i in range(n):
            for j in range(n):
                u = (i + su) / n
                vv = (j + sv) / n
                x, y = v1.frac_to_cart(u, vv, a1, a2)
                atoms.append({
                    "symbol": "Cu",
                    "position_angstrom": [x, y, float(z_by_layer[layer])],
                    "flags": [0, 0, 0],
                    "layer": layer,
                })

    off = v1.site_offsets(layers)[site]
    u = (1.0 + off[0]) / n
    vv = (1.0 + off[1]) / n
    x, y = v1.frac_to_cart(u, vv, a1, a2)
    top_z = max(float(z) for z in z_by_layer if z is not None)
    c_z = top_z + float(screen["initial_carbon_height_above_top_Cu_plane_angstrom"])
    o_z = c_z + float(screen["initial_co_bond_angstrom"])
    if o_z >= cell_z / 2.0 - 2.0:
        raise SystemExit("SCIENTIFIC_HOLD: CO is too close to the ESM boundary")
    atoms.append({"symbol": "C", "position_angstrom": [x, y, c_z], "flags": [0, 0, 0], "layer": None})
    atoms.append({"symbol": "O", "position_angstrom": [x, y, o_z], "flags": [0, 0, 0], "layer": None})

    evidence = {
        "depth": depth,
        "source_case_id": source["case_id"],
        "source_layers": layers,
        "source_vacuum_angstrom": source_vacuum,
        "common_vacuum_angstrom": common_vacuum,
        "cell_z_adjustment_angstrom": common_vacuum - source_vacuum,
        "supercell": [n, n],
        "nominal_coverage_ML": 0.25,
        "site": site,
        "kmesh": int(screen["kmesh"]),
        "all_atomic_coordinates_fixed": True,
        "low_coverage_4x4_sufficiency_claimed": False,
    }
    return cell, atoms, evidence


def mem_total_gib() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal:"):
            kib = float(line.split()[1])
            return kib / 1024.0 / 1024.0
    raise SystemExit("MECHANICAL_HOLD: unable to read runner memory")


def command_preflight_v2(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = load_protocol_v2(pp)
    l15 = v1.load_l15(Path(args.l15_root).resolve(), p)
    l17 = v1.load_l17(Path(args.l17_root).resolve(), p)
    ram = mem_total_gib()
    minimum = float(p["execution"]["resource_preflight_requires_available_ram_gib_at_least"])
    if ram < minimum:
        raise SystemExit(f"MECHANICAL_HOLD: runner memory {ram:.3f} GiB below frozen v0.2 minimum {minimum:.3f} GiB")
    out = {
        "schema": "co-cu111-pbe-l15-l17-site-depth-diagnostic-preflight-v0.2",
        "status": "PASS",
        "runner_memtotal_gib": ram,
        "required_memtotal_gib_minimum": minimum,
        "l15_summary_sha256": p["source_l15"]["summary_sha256"],
        "l17_state_sha256": p["source_l17"]["relax_state_sha256"],
        "l15_layers": l15["layers"],
        "l17_layers": l17["layers"],
        "diagnostic_supercell": [2, 2],
        "diagnostic_coverage_ML": 0.25,
        "diagnostic_kmesh": 8,
        "original_l17_surface_gate_pass": False,
        "low_coverage_4x4_sufficiency_claimed": False,
        "absolute_clean_surface_pass_claimed": False,
    }
    if args.out:
        v1.write_json(Path(args.out).resolve(), out)
    print(json.dumps(out, indent=2, sort_keys=True))


# Patch only the protocol/geometry-facing hooks.  The exact-restart state
# machine, checkpoint hashing, QE invocation and adjudication implementation
# remain the tested v1 code path.
v1.PROTOCOL_SCHEMA = PROTOCOL_SCHEMA
v1.PROTOCOL_STATUS = PROTOCOL_STATUS
v1.STATE_SCHEMA = STATE_SCHEMA
v1.RESULT_SCHEMA = RESULT_SCHEMA
v1.load_protocol = load_protocol_v2
v1.matched_geometry = matched_geometry_v2
v1.command_preflight = command_preflight_v2

# Re-export useful pure functions for independent tests.
classify_sufficiency = v1.classify_sufficiency
site_offsets = v1.site_offsets
write_checkpoint_manifest = v1.write_checkpoint_manifest
verify_checkpoint_manifest = v1.verify_checkpoint_manifest
add_control_fields = v1.add_control_fields


def main() -> None:
    args = v1.parser().parse_args()
    if args.cmd == "scf-segment" and args.segment > 1 and not args.prior_root:
        raise SystemExit("MECHANICAL_HOLD: --prior-root required after segment 1")
    args.func(args)


if __name__ == "__main__":
    main()
