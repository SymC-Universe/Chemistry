#!/usr/bin/env python3
"""Fail-closed prospective L15 clean-Cu(111) convergence extension.

This runner does not relax any frozen acceptance threshold. It consumes the
previously failed L11<->L13 clean-surface gate as immutable evidence, promotes
the independently reproduced L13 case only to an extension reference, and
executes one prospectively frozen deeper audit rung L15/V32/K28.

The L13 result is used only to seed the two movable surface-depth z offsets of
L15. It is never used to change a threshold or to predetermine L15 acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

SCHEMA = "co-cu111-pbe-surface-convergence-extension-v0.1"
STATUS = "FROZEN_BEFORE_L15_RESULTS"
SEG_SCHEMA = "co-cu111-pbe-surface-convergence-extension-segment-v0.1"
GATE_SCHEMA = "co-cu111-pbe-surface-convergence-extension-gate-v0.1"
CLEAN_SCHEMA = "co-cu111-pbe-clean-surface-case-v0.1"
SOURCE_GATE_SCHEMA = "co-cu111-pbe-clean-surface-gate-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"MECHANICAL_HOLD: JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def find_one(root: Path, name: str) -> Path:
    found = [p for p in root.rglob(name) if p.is_file()]
    if len(found) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name} under {root}, found {len(found)}")
    return found[0]


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def verify_manifest(root: Path) -> None:
    manifest = root / "STAGE_TIME_MANIFEST.sha256"
    if not manifest.is_file():
        raise SystemExit(f"MECHANICAL_HOLD: missing stage-time manifest under {root}")
    for raw in manifest.read_text().splitlines():
        if not raw.strip():
            continue
        parts = raw.split("  ", 1)
        if len(parts) != 2:
            raise SystemExit("MECHANICAL_HOLD: malformed stage-time manifest line")
        expected, rel = parts
        target = root / rel
        if not target.is_file() or sha256(target) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: stage-time manifest mismatch: {rel}")


def protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != SCHEMA or p.get("status") != STATUS:
        raise SystemExit("SCIENTIFIC_HOLD: wrong or unfrozen surface-convergence extension protocol")
    if p.get("scientific_scope") != "PROSPECTIVE_NUMERICAL_CONVERGENCE_EXTENSION_AFTER_PREREGISTERED_HOLD":
        raise SystemExit("SCIENTIFIC_HOLD: extension scope drift")

    hold = p["source_hold"]
    if hold.get("required_status") != "NUMERICAL_HOLD" or hold.get("threshold_was_not_met") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: source failure is not preserved")
    if not close(hold["frozen_threshold_ev_per_surface_atom"], 0.001, 0.0):
        raise SystemExit("SCIENTIFIC_HOLD: source convergence threshold changed")
    if float(hold["observed_l11_l13_delta_ev_per_surface_atom"]) <= 0.001:
        raise SystemExit("SCIENTIFIC_HOLD: source HOLD no longer represents a failure")

    ref = p["extension_reference"]
    if (ref.get("case_id"), int(ref.get("layers", -1)), float(ref.get("vacuum_angstrom", -1)), int(ref.get("kmesh", -1))) != (
        "L13-V28-K24-audit", 13, 28.0, 24
    ):
        raise SystemExit("SCIENTIFIC_HOLD: extension reference changed")
    if ref.get("required_status") != "COMPLETE" or ref.get("required_mechanical_pass") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: extension reference is not independently closed")

    aud = p["extension_audit"]
    if (aud.get("case_id"), int(aud.get("layers", -1)), float(aud.get("vacuum_angstrom", -1)), int(aud.get("kmesh", -1))) != (
        "L15-V32-K28-extension-audit", 15, 32.0, 28
    ):
        raise SystemExit("SCIENTIFIC_HOLD: prospective L15 audit rung changed")

    method = p["frozen_method"]
    frozen = {
        "exchange_correlation": "PBE",
        "ecutwfc_ry": 90,
        "ecutrho_ry": 900,
        "bulk_lattice_constant_angstrom": 3.632355796707377,
        "bulk_e0_ev_per_atom": -2899.3351868909526,
        "degauss_ry": 0.02,
        "electron_conv_thr": 1e-10,
        "mixing_beta": 0.3,
        "electron_maxstep": 200,
        "assume_isolated": "esm",
        "esm_bc": "bc1",
        "ion_dynamics": "bfgs",
        "force_gate_ev_per_angstrom": 0.02,
        "independent_scf_reproduction_gate_ev": 0.001,
        "surface_excess_convergence_max_ev_per_surface_atom": 0.001,
    }
    for key, value in frozen.items():
        if method.get(key) != value:
            raise SystemExit(f"SCIENTIFIC_HOLD: frozen method drift: {key}")

    ex = p["execution"]
    if ex.get("execution_mode") != "DIRECT_ONE_RANK" or int(ex.get("mpi_ranks", -1)) != 1:
        raise SystemExit("MECHANICAL_HOLD: direct-one-rank execution changed")
    if int(ex.get("maximum_continuation_segments", -1)) != 36 or ex.get("logical_segment_numbers") != list(range(1, 37)):
        raise SystemExit("MECHANICAL_HOLD: bounded continuation runway changed")
    if int(ex.get("continuation_segment_runtime_cap_seconds", -1)) != 19800:
        raise SystemExit("MECHANICAL_HOLD: continuation runtime cap changed")
    if int(ex.get("reproduction_runtime_cap_seconds", -1)) != 19200:
        raise SystemExit("MECHANICAL_HOLD: reproduction runtime cap changed")
    if ex.get("four_rank_reselection_forbidden") is not True or ex.get("new_rank_qualification_forbidden") is not True:
        raise SystemExit("MECHANICAL_HOLD: forbidden MPI reselection changed")

    init = p["initialization"]
    if init.get("rule") != "L13_SURFACE_RELAXATION_OFFSETS_ONLY" or init.get("initialization_only") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: L15 initialization rule changed")
    if init.get("energy_or_surface_excess_used_to_seed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: forbidden energy-dependent seed")

    dec = p["decision"]
    if dec.get("no_threshold_retuning_after_results") is not True or dec.get("no_additional_scientific_rung_authorized") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: anti-retuning firewall disabled")
    if dec.get("automatic_site_ordering_dispatch") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: downstream auto-dispatch changed")

    prov = p["provenance"]
    for key in (
        "scientific_settings_changed_from_original_method",
        "force_gate_changed",
        "reproduction_gate_changed",
        "surface_excess_gate_changed",
        "candidate_selection_rule_changed",
        "kinetic_inputs_used",
        "surface_or_kinetic_result_used_to_relax_acceptance_threshold",
    ):
        if prov.get(key) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: provenance firewall changed: {key}")
    if prov.get("prior_failure_preserved_as_failure") is not True or prov.get("numerical_grid_extended") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: extension provenance incomplete")
    return p


def import_runtime():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_site_ordering_v1 as base  # type: ignore
    import pbe_surface_audit_rank_fallback_recovery_v1 as old  # type: ignore
    import pbe_surface_audit_proposal_relay_v1 as relay  # type: ignore
    return base, old, relay


def verify_repo_sources(p: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    for key in ("surface_protocol", "surface_runner", "rank_fallback_runner", "proposal_relay_runner"):
        row = p["frozen_sources"][key]
        target = repo / row["path"]
        if not target.is_file() or sha256(target) != row["sha256"]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source mismatch: {row['path']}")


def ideal_geometry(a0: float, layers: int, vacuum: float) -> tuple[list[list[float]], list[dict[str, Any]]]:
    if layers < 5 or layers % 2 == 0:
        raise ValueError("clean Cu(111) slab requires odd layers >= 5")
    axy = a0 / math.sqrt(2.0)
    d111 = a0 / math.sqrt(3.0)
    slab_height = (layers - 1) * d111
    cell_z = slab_height + vacuum
    a1 = [axy, 0.0, 0.0]
    a2 = [0.5 * axy, math.sqrt(3.0) * 0.5 * axy, 0.0]
    cell = [a1, a2, [0.0, 0.0, cell_z]]
    midpoint = (layers - 1) / 2.0
    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        shift = (layer % 3) / 3.0
        x = shift * a1[0] + shift * a2[0]
        y = shift * a1[1] + shift * a2[1]
        z = (layer - midpoint) * d111
        movable = layer < 2 or layer >= layers - 2
        atoms.append({"symbol": "Cu", "position_angstrom": [x, y, z], "flags": [0, 0, 1 if movable else 0], "layer": layer})
    return cell, atoms


def verify_source_hold(root: Path, p: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    path = find_one(root, "CLEAN_SURFACE_GATE.json")
    expected = p["source_hold"]
    if sha256(path) != expected["gate_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: source clean-gate hash mismatch")
    row = load_json(path)
    if row.get("schema") != SOURCE_GATE_SCHEMA or row.get("status") != expected["required_status"]:
        raise SystemExit("SCIENTIFIC_HOLD: wrong source clean-gate state")
    if row.get("next_gate") != expected["required_next_gate"]:
        raise SystemExit("SCIENTIFIC_HOLD: source HOLD next-gate drift")
    if not close(row.get("reference_audit_delta_ev_per_surface_atom", math.inf), expected["observed_l11_l13_delta_ev_per_surface_atom"], 1e-15):
        raise SystemExit("SCIENTIFIC_HOLD: source L11-L13 delta drift")
    if row.get("reference_audit_pass") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: source failure was rewritten as pass")
    return row, path


def verify_l13_reference(root: Path, p: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    verify_manifest(root)
    path = find_one(root, "summary.json")
    ref = p["extension_reference"]
    if sha256(path) != ref["summary_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: L13 extension-reference summary hash mismatch")
    row = load_json(path)
    checks = {
        "schema": CLEAN_SCHEMA,
        "status": ref["required_status"],
        "case_id": ref["case_id"],
        "layers": ref["layers"],
        "vacuum_angstrom": ref["vacuum_angstrom"],
        "kmesh": ref["kmesh"],
        "mechanical_pass": ref["required_mechanical_pass"],
    }
    for key, value in checks.items():
        if row.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: L13 reference mismatch: {key}")
    numeric = (
        ("max_movable_force_ev_per_angstrom", "max_movable_force_ev_per_angstrom", 1e-15),
        ("energy_reproduction_delta_ev", "energy_reproduction_delta_ev", 1e-15),
        ("surface_excess_ev_per_surface_atom", "surface_excess_ev_per_surface_atom", 1e-15),
        ("fixed_geometry_scf_energy_ev", "fixed_geometry_scf_energy_ev", 1e-10),
    )
    for row_key, ref_key, tol in numeric:
        if not close(row[row_key], ref[ref_key], tol):
            raise SystemExit(f"MECHANICAL_HOLD: L13 reference numeric drift: {row_key}")
    prov = row.get("provenance", {})
    if prov.get("pw_sha256") != ref["pw_sha256"] or prov.get("rank_selection_sha256") != ref["rank_selection_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: L13 reference engine/rank provenance drift")
    if prov.get("scientific_settings_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: L13 reference provenance contaminated")
    if len(row.get("final_atoms", [])) != 13:
        raise SystemExit("MECHANICAL_HOLD: L13 reference geometry length mismatch")
    return row, path


def seed_from_l13(l13: dict[str, Any], p: dict[str, Any]) -> tuple[list[list[float]], list[dict[str, Any]], dict[str, Any]]:
    a0 = float(p["frozen_method"]["bulk_lattice_constant_angstrom"])
    _, ideal13 = ideal_geometry(a0, 13, 28.0)
    cell15, ideal15 = ideal_geometry(a0, 15, 32.0)
    actual = l13["final_atoms"]
    source_layers = [0, 1, 11, 12]
    offsets = [
        float(actual[i]["position_angstrom"][2]) - float(ideal13[i]["position_angstrom"][2])
        for i in source_layers
    ]
    expected = p["initialization"]["l13_offsets_angstrom"]
    expected_values = [
        expected["bottom_outermost"], expected["bottom_subsurface"],
        expected["top_subsurface"], expected["top_outermost"],
    ]
    for got, exp in zip(offsets, expected_values):
        if not close(got, exp, 1e-12):
            raise SystemExit("MECHANICAL_HOLD: L13 seed offset drift")
    if not close(offsets[0], -offsets[3], 1e-12) or not close(offsets[1], -offsets[2], 1e-12):
        raise SystemExit("MECHANICAL_HOLD: L13 seed offsets lost surface symmetry")
    seed = json.loads(json.dumps(ideal15))
    target_layers = [0, 1, 13, 14]
    for target, delta in zip(target_layers, offsets):
        seed[target]["position_angstrom"][2] = float(seed[target]["position_angstrom"][2]) + float(delta)
    expected_seed = p["initialization"]["expected_l15_seed_outer_z_angstrom"]
    for layer in target_layers:
        if not close(seed[layer]["position_angstrom"][2], expected_seed[str(layer)], 1e-12):
            raise SystemExit("MECHANICAL_HOLD: L15 seed geometry drift")
    evidence = {
        "source": "L13_RELAXED_SURFACE_OFFSETS_ONLY",
        "source_case_id": l13["case_id"],
        "source_summary_sha256": p["extension_reference"]["summary_sha256"],
        "source_layers": source_layers,
        "target_layers": target_layers,
        "z_offsets_angstrom": offsets,
        "energy_or_surface_excess_used_to_seed": False,
        "initialization_only": True,
    }
    return cell15, seed, evidence


def verify_prior_segment(root: Path, p: dict[str, Any], expected_segment: int) -> tuple[dict[str, Any], Path]:
    verify_manifest(root)
    path = find_one(root, "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json")
    row = load_json(path)
    checks = {
        "schema": SEG_SCHEMA,
        "segment": expected_segment,
        "case_id": p["extension_audit"]["case_id"],
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "mpi_ranks": 1,
        "execution_mode": "DIRECT_ONE_RANK",
    }
    for key, value in checks.items():
        if row.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: prior L15 segment mismatch: {key}")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: prior L15 segment provenance contaminated")
    if row.get("surface_convergence_extension_protocol_sha256") != sha256(Path(p["_protocol_path"])):
        raise SystemExit("MECHANICAL_HOLD: prior L15 protocol hash drift")
    if row.get("status") not in {"CONTINUE", "RELAX_COMPLETE"}:
        raise SystemExit("MECHANICAL_HOLD: invalid prior L15 segment status")
    if row["status"] == "CONTINUE" and not row.get("next_trial_atoms"):
        raise SystemExit("MECHANICAL_HOLD: CONTINUE segment lacks next BFGS trial")
    if row["status"] == "RELAX_COMPLETE" and not row.get("final_atoms"):
        raise SystemExit("MECHANICAL_HOLD: RELAX_COMPLETE segment lacks final geometry")
    return row, path


def runtime_context(args: argparse.Namespace, p: dict[str, Any]):
    base, old, relay = import_runtime()
    verify_repo_sources(p)
    surface_path = Path(args.surface_protocol).resolve()
    if sha256(surface_path) != p["frozen_sources"]["surface_protocol"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: surface protocol hash mismatch")
    surface = base.load_json(surface_path)
    base.verify_protocol(surface)
    stage_path = Path(args.stage_a_result).resolve()
    if sha256(stage_path) != p["frozen_sources"]["stage_a_result_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: Stage A result hash mismatch")
    base.verify_stage_a(surface, stage_path)
    bundle_path = Path(args.bundle).resolve()
    if sha256(bundle_path) != p["frozen_sources"]["pseudopotential_bundle_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pseudopotential bundle hash mismatch")
    bundle = base.verify_bundle(surface, bundle_path, Path(args.pseudo_dir).resolve(), Path(args.pw).resolve())
    if sha256(Path(args.pw).resolve()) != p["frozen_sources"]["pw_x_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pw.x hash mismatch")
    sel_path = Path(args.selection).resolve()
    if sha256(sel_path) != p["frozen_sources"]["rank_selection_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: rank-selection record hash mismatch")
    sel = load_json(sel_path)
    if sel.get("selected_execution_mode") != "DIRECT_ONE_RANK" or int(sel.get("selected_mpi_ranks", -1)) != 1:
        raise SystemExit("MECHANICAL_HOLD: direct-one-rank selection drift")
    return base, old, relay, surface, bundle, sel


def command_self_test(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    a0 = p["frozen_method"]["bulk_lattice_constant_angstrom"]
    cell, atoms = ideal_geometry(a0, 15, 32.0)
    if len(atoms) != 15 or sum(int(a["flags"][2]) for a in atoms) != 4:
        raise SystemExit("SELF_TEST_FAIL: L15 geometry/constraints")
    if not close(cell[2][2], 61.359982358301025, 1e-12):
        raise SystemExit("SELF_TEST_FAIL: L15 cell-z")
    print("SURFACE_CONVERGENCE_EXTENSION_SELF_TEST_PASS")
    print("L15_V32_K28_FROZEN=true")
    print("FORCE_GATE_EV_A=0.020000000000")
    print("REPRO_GATE_EV=0.001000000000")
    print("SURFACE_EXCESS_GATE_EV_PER_SURFACE_ATOM=0.001000000000")
    print("DIRECT_ONE_RANK_FROZEN=true")
    print("KINETIC_INPUTS_USED=false")


def command_verify_sources(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    hold, hold_path = verify_source_hold(Path(args.hold_root).resolve(), p)
    l13, l13_path = verify_l13_reference(Path(args.l13_root).resolve(), p)
    _, seed, evidence = seed_from_l13(l13, p)
    print(json.dumps({
        "status": "SOURCE_EVIDENCE_VERIFIED",
        "source_hold_sha256": sha256(hold_path),
        "source_hold_delta_ev_per_surface_atom": hold["reference_audit_delta_ev_per_surface_atom"],
        "l13_summary_sha256": sha256(l13_path),
        "l13_surface_excess_ev_per_surface_atom": l13["surface_excess_ev_per_surface_atom"],
        "l15_seed_outer_z_angstrom": {str(i): seed[i]["position_angstrom"][2] for i in (0, 1, 13, 14)},
        "seed_evidence": evidence,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
    }, indent=2, sort_keys=True))


def command_inspect_prior(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    segment = int(args.segment)
    if segment == 1:
        l13, _ = verify_l13_reference(Path(args.prior_root).resolve(), p)
        seed_from_l13(l13, p)
        print("CARRY=false")
        print("PRIOR_STATUS=L13_EXTENSION_REFERENCE")
        return
    row, _ = verify_prior_segment(Path(args.prior_root).resolve(), p, segment - 1)
    print("CARRY=" + ("true" if row["status"] == "RELAX_COMPLETE" else "false"))
    print("PRIOR_STATUS=" + row["status"])
    print("PRIOR_SEGMENT=" + str(row["segment"]))


def command_continue(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    segment = int(args.segment)
    max_seg = int(p["execution"]["maximum_continuation_segments"])
    if segment < 1 or segment > max_seg:
        raise SystemExit("MECHANICAL_HOLD: L15 continuation segment outside frozen bound")
    prior_root = Path(args.prior_root).resolve()
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=True)

    if segment == 1:
        l13, _ = verify_l13_reference(prior_root, p)
        cell, seed, source_evidence = seed_from_l13(l13, p)
        already_complete = False
        completion_segment = None
    else:
        prior, prior_path = verify_prior_segment(prior_root, p, segment - 1)
        if prior["status"] == "RELAX_COMPLETE":
            carried = dict(prior)
            carried.update({
                "segment": segment,
                "logical_segment": segment,
                "carried_forward_without_recomputation": True,
                "source_evidence": {
                    "source": "PRIOR_RELAX_COMPLETE",
                    "source_record_sha256": sha256(prior_path),
                    "source_segment": segment - 1,
                },
            })
            write_json(root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json", carried)
            base, _, _ = import_runtime()
            base.stage_manifest(root, [root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json"])
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        seed = prior["next_trial_atoms"]
        source_evidence = {
            "source": "PRIOR_NEXT_BFGS_TRIAL",
            "source_record_sha256": sha256(prior_path),
            "source_segment": segment - 1,
            "source_raw_output_sha256": prior.get("raw_hashes", {}).get("relax_output_sha256"),
        }
        cell, template = ideal_geometry(float(p["frozen_method"]["bulk_lattice_constant_angstrom"]), 15, 32.0)
        if len(seed) != len(template):
            raise SystemExit("MECHANICAL_HOLD: prior L15 seed length drift")
        already_complete = False
        completion_segment = None

    if already_complete:
        raise SystemExit("MECHANICAL_HOLD: unreachable carry-forward state")
    required = (args.surface_protocol, args.stage_a_result, args.bundle, args.pseudo_dir, args.pw, args.selection)
    if any(x is None for x in required):
        raise SystemExit("MECHANICAL_HOLD: QE runtime inputs missing for active L15 segment")
    base, old, relay, surface, bundle, _sel = runtime_context(args, p)
    cell2, template = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 15, 32.0)
    if any(abs(float(a) - float(b)) > 1e-12 for ra, rb in zip(cell, cell2) for a, b in zip(ra, rb)):
        raise SystemExit("MECHANICAL_HOLD: independent L15 cell construction mismatch")
    seed = old.apply_template(seed, template)

    rd = root / "relax"
    rd.mkdir(exist_ok=True)
    tmp = rd / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = rd / "clean_relax.in"
    out = rd / "clean_relax.out"
    inp.write_text(base.qe_input(
        calculation="relax",
        prefix="co_cu111_clean_l15_extension",
        cell=cell2,
        atoms=seed,
        kmesh=28,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    ))
    result = old.run_pw(Path(args.pw).resolve(), inp, out, 1, int(args.runtime_cap_s))
    if result["returncode"] != 0 and not result["timed_out_by_wrapper"]:
        raise SystemExit(f"MECHANICAL_HOLD: direct one-rank L15 pw.x failed, rc={result['returncode']}")

    blocks = old.authoritative_force_blocks(result["text"], 15)
    latest = old.max_movable_force_ev_a(blocks[-1], seed) if blocks else None
    complete = bool(result["job_done"] and result["bfgs_finished"] and result["energy_ev"] is not None)
    final_atoms = None
    next_trial = None
    completion_segment = None
    if complete:
        final_atoms = base.parse_positions(result["text"], 15, seed)
        if final_atoms is None or not blocks:
            raise SystemExit("MECHANICAL_HOLD: completed L15 relaxation lacks final geometry/forces")
        final_atoms = old.apply_template(final_atoms, template)
        final_force = old.max_movable_force_ev_a(blocks[-1], final_atoms)
        if final_force > float(p["frozen_method"]["force_gate_ev_per_angstrom"]):
            raise SystemExit("SCIENTIFIC_HOLD: QE completed L15 but corrected movable-force gate failed")
        latest = final_force
        completion_segment = segment
    else:
        proposal = relay.last_bfgs_proposed_trial(result["text"], 15, seed)
        if proposal is None:
            raise SystemExit("MECHANICAL_HOLD: bounded L15 segment emitted no admissible next BFGS trial")
        next_trial, proposal_evidence = proposal
        next_trial = old.apply_template(next_trial, template)
        displacement = relay.max_displacement_angstrom(seed, next_trial)
        if displacement <= 1e-10:
            raise SystemExit("MECHANICAL_HOLD: L15 continuation would repeat the same geometry")
        source_evidence["next_trial_parent_evidence"] = proposal_evidence
        source_evidence["next_trial_displacement_angstrom"] = displacement

    row = {
        "schema": SEG_SCHEMA,
        "status": "RELAX_COMPLETE" if complete else "CONTINUE",
        "segment": segment,
        "logical_segment": segment,
        "completion_segment": completion_segment,
        "case_id": p["extension_audit"]["case_id"],
        "role": p["extension_audit"]["role"],
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "cell_angstrom": cell2,
        "mpi_ranks": 1,
        "execution_mode": "DIRECT_ONE_RANK",
        "runner_label": p["execution"]["runner_label"],
        "thread_caps": p["execution"]["thread_caps"],
        "timed_out_by_wrapper": result["timed_out_by_wrapper"],
        "pw_returncode": result["returncode"],
        "job_done": result["job_done"],
        "bfgs_finished": result["bfgs_finished"],
        "energy_ev": result["energy_ev"],
        "latest_authoritative_max_movable_force_ev_per_angstrom": latest,
        "input_atoms": seed,
        "final_atoms": final_atoms,
        "next_trial_atoms": next_trial,
        "source_evidence": source_evidence,
        "carried_forward_without_recomputation": False,
        "scientific_settings_changed": False,
        "scientific_settings_changed_after_extension_freeze": False,
        "numerical_grid_extended_from_original_protocol": True,
        "parallelization_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "raw_hashes": {
            "relax_input_sha256": sha256(inp),
            "relax_output_sha256": sha256(out),
        },
        "surface_convergence_extension_protocol_sha256": sha256(pp),
        "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
        "rank_selection_sha256": p["frozen_sources"]["rank_selection_sha256"],
        "pw_sha256": p["frozen_sources"]["pw_x_sha256"],
        "elapsed_s": result["elapsed_s"],
    }
    base.cleanup_tmp(tmp)
    record = root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json"
    write_json(record, row)
    base.stage_manifest(root, [record])
    print(json.dumps(row, indent=2, sort_keys=True))


def command_reproduce(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    max_seg = int(p["execution"]["maximum_continuation_segments"])
    seg, seg_path = verify_prior_segment(Path(args.prior_root).resolve(), p, max_seg)
    if seg.get("status") != "RELAX_COMPLETE" or not seg.get("final_atoms"):
        raise SystemExit(f"MECHANICAL_INCOMPLETE: L15 audit relaxation did not complete within {max_seg} frozen segments")
    required = (args.surface_protocol, args.stage_a_result, args.bundle, args.pseudo_dir, args.pw, args.selection)
    if any(x is None for x in required):
        raise SystemExit("MECHANICAL_HOLD: reproduction runtime inputs missing")
    base, old, _relay, surface, bundle, _sel = runtime_context(args, p)
    atoms = json.loads(json.dumps(seg["final_atoms"]))
    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]
    cell, _template = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 15, 32.0)
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=True)
    rd = root / "reproduce"
    rd.mkdir(exist_ok=True)
    tmp = rd / "tmp"
    tmp.mkdir(exist_ok=True)
    inp = rd / "clean_reproduce.in"
    out = rd / "clean_reproduce.out"
    inp.write_text(base.qe_input(
        calculation="scf",
        prefix="co_cu111_clean_l15_extension_repro",
        cell=cell,
        atoms=fixed,
        kmesh=28,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    ))
    result = old.run_pw(Path(args.pw).resolve(), inp, out, 1, int(args.runtime_cap_s))
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit("MECHANICAL_HOLD: independent direct-one-rank L15 SCF did not complete")
    force = float(seg["latest_authoritative_max_movable_force_ev_per_angstrom"])
    relax_energy = float(seg["energy_ev"])
    repro_energy = float(result["energy_ev"])
    delta = abs(relax_energy - repro_energy)
    fg = float(p["frozen_method"]["force_gate_ev_per_angstrom"])
    rg = float(p["frozen_method"]["independent_scf_reproduction_gate_ev"])
    passed = force <= fg and delta <= rg
    bulk_e0 = float(p["frozen_method"]["bulk_e0_ev_per_atom"])
    excess = (repro_energy - 15.0 * bulk_e0) / 2.0
    summary = {
        "schema": CLEAN_SCHEMA,
        "status": "COMPLETE" if passed else "NUMERICAL_HOLD",
        "case_id": p["extension_audit"]["case_id"],
        "role": "extension_audit",
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "cell_angstrom": cell,
        "final_atoms": atoms,
        "layer_z_angstrom": [float(a["position_angstrom"][2]) for a in atoms],
        "relax_energy_ev": relax_energy,
        "fixed_geometry_scf_energy_ev": repro_energy,
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": force,
        "mechanical_pass": passed,
        "surface_excess_ev_per_surface_atom": excess,
        "completion_segment": seg.get("completion_segment"),
        "provenance": {
            "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
            "surface_convergence_extension_protocol_sha256": sha256(pp),
            "stage_a_result_sha256": p["frozen_sources"]["stage_a_result_sha256"],
            "pw_sha256": p["frozen_sources"]["pw_x_sha256"],
            "bundle_sha256": p["frozen_sources"]["pseudopotential_bundle_sha256"],
            "rank_selection_sha256": p["frozen_sources"]["rank_selection_sha256"],
            "execution_mode": "DIRECT_ONE_RANK",
            "execution_resource_changed": False,
            "scientific_settings_changed": False,
            "scientific_settings_changed_after_extension_freeze": False,
            "numerical_grid_extended_from_original_protocol": True,
            "thresholds_changed": False,
            "kinetic_inputs_used": False,
            "authoritative_total_force_parser": True,
        },
        "raw_hashes": {
            "relax_segment_record_sha256": sha256(seg_path),
            "reproduce_input_sha256": sha256(inp),
            "reproduce_output_sha256": sha256(out),
        },
    }
    base.cleanup_tmp(tmp)
    sp = root / "summary.json"
    write_json(sp, summary)
    base.stage_manifest(root, [sp])
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("SCIENTIFIC_HOLD: L15 force or independent reproduction gate failed")


def candidate_ids(surface: dict[str, Any], base) -> list[str]:
    spec = surface["clean_surface"]
    ids: list[str] = []
    for layers in spec["candidate_layers"]:
        for vacuum in spec["candidate_vacuum_angstrom"]:
            for kmesh in spec["candidate_kmeshes"]:
                ids.append(base.clean_case_id(int(layers), float(vacuum), int(kmesh), "candidate"))
    return ids


def command_gate(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    p["_protocol_path"] = str(pp)
    hold, hold_path = verify_source_hold(Path(args.hold_root).resolve(), p)
    l13, l13_path = verify_l13_reference(Path(args.l13_root).resolve(), p)
    verify_manifest(Path(args.l15_root).resolve())
    l15_path = find_one(Path(args.l15_root).resolve(), "summary.json")
    l15 = load_json(l15_path)
    expected = p["extension_audit"]
    checks = {
        "schema": CLEAN_SCHEMA,
        "status": "COMPLETE",
        "case_id": expected["case_id"],
        "role": "extension_audit",
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "mechanical_pass": True,
    }
    for key, value in checks.items():
        if l15.get(key) != value:
            raise SystemExit(f"SCIENTIFIC_HOLD: L15 reproduced audit mismatch: {key}")
    if float(l15["max_movable_force_ev_per_angstrom"]) > 0.02 or float(l15["energy_reproduction_delta_ev"]) > 0.001:
        raise SystemExit("SCIENTIFIC_HOLD: L15 mechanics/reproduction gates not closed")
    prov = l15.get("provenance", {})
    if prov.get("scientific_settings_changed") is not False or prov.get("thresholds_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: L15 provenance contaminated")

    reference_audit_delta = abs(float(l13["surface_excess_ev_per_surface_atom"]) - float(l15["surface_excess_ev_per_surface_atom"]))
    tol = float(p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"])
    reference_audit_pass = reference_audit_delta <= tol

    base, old, _relay = import_runtime()
    verify_repo_sources(p)
    surface_path = Path(args.surface_protocol).resolve()
    if sha256(surface_path) != p["frozen_sources"]["surface_protocol"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: surface protocol hash mismatch at gate")
    surface = base.load_json(surface_path)
    base.verify_protocol(surface)
    stage_path = Path(args.stage_a_result).resolve()
    if sha256(stage_path) != p["frozen_sources"]["stage_a_result_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: Stage A hash mismatch at gate")
    base.verify_stage_a(surface, stage_path)

    candidates: list[dict[str, Any]] = []
    selected = None
    candidate_force_reaudit: dict[str, float] = {}
    if reference_audit_pass:
        rows = base.find_summaries(Path(args.candidate_root).resolve(), CLEAN_SCHEMA)
        expected_ids = candidate_ids(surface, base)
        by_id = {row["case_id"]: row for row in rows if row.get("case_id") in expected_ids}
        missing = [cid for cid in expected_ids if cid not in by_id]
        if missing:
            raise SystemExit("MECHANICAL_HOLD: missing frozen candidates: " + ",".join(missing))
        a0 = float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"])
        d111 = a0 / math.sqrt(3.0)
        for cid in expected_ids:
            row = by_id[cid]
            if row.get("status") != "COMPLETE" or row.get("mechanical_pass") is not True:
                raise SystemExit(f"SCIENTIFIC_HOLD: frozen candidate mechanics no longer closed: {cid}")
            if float(row.get("energy_reproduction_delta_ev", math.inf)) > 0.001:
                raise SystemExit(f"SCIENTIFIC_HOLD: frozen candidate reproduction gate failed: {cid}")
            summary_path = Path(row["_source_path"])
            outs = list(summary_path.parent.rglob("clean_relax.out"))
            if len(outs) != 1:
                raise SystemExit(f"MECHANICAL_HOLD: expected one raw candidate relax output for {cid}, found {len(outs)}")
            blocks = old.authoritative_force_blocks(outs[0].read_text(errors="replace"), int(row["layers"]))
            if not blocks:
                raise SystemExit(f"MECHANICAL_HOLD: no authoritative force block for {cid}")
            corrected_force = old.max_movable_force_ev_a(blocks[-1], row["final_atoms"])
            candidate_force_reaudit[cid] = corrected_force
            if corrected_force > 0.02:
                raise SystemExit(f"SCIENTIFIC_HOLD: candidate authoritative force re-audit failed: {cid}")
            delta = abs(float(row["surface_excess_ev_per_surface_atom"]) - float(l13["surface_excess_ev_per_surface_atom"]))
            cell_z = (int(row["layers"]) - 1) * d111 + float(row["vacuum_angstrom"])
            cost = int(row["layers"]) * int(row["kmesh"]) ** 2 * cell_z
            item = {k: v for k, v in row.items() if not k.startswith("_")}
            item.update({
                "surface_excess_delta_to_extension_reference_ev_per_surface_atom": delta,
                "surface_convergence_pass": corrected_force <= 0.02 and float(row["energy_reproduction_delta_ev"]) <= 0.001 and delta <= tol,
                "authoritative_force_reaudit_ev_per_angstrom": corrected_force,
                "estimated_cost_score": cost,
                "source_sha256": row["_source_sha256"],
            })
            candidates.append(item)
        passing = [x for x in candidates if x["surface_convergence_pass"]]
        passing.sort(key=lambda x: (x["estimated_cost_score"], x["layers"], x["vacuum_angstrom"], x["kmesh"]))
        selected = passing[0] if passing else None

    if not reference_audit_pass:
        status = "NUMERICAL_HOLD_EXTENSION_AUDIT"
        next_gate = p["decision"]["extension_audit_hold_next_gate"]
    elif selected is None:
        status = "NUMERICAL_HOLD_CANDIDATE_GRID"
        next_gate = p["decision"]["candidate_grid_hold_next_gate"]
    else:
        status = "CLEAN_SURFACE_PASS"
        next_gate = p["decision"]["pass_next_gate"]

    result = {
        "schema": GATE_SCHEMA,
        "status": status,
        "prior_failure": {
            "status": hold["status"],
            "l11_l13_delta_ev_per_surface_atom": hold["reference_audit_delta_ev_per_surface_atom"],
            "threshold_ev_per_surface_atom": p["source_hold"]["frozen_threshold_ev_per_surface_atom"],
            "preserved_as_failure": True,
        },
        "extension_reference": l13,
        "extension_audit": l15,
        "extension_reference_audit_delta_ev_per_surface_atom": reference_audit_delta,
        "extension_reference_audit_threshold_ev_per_surface_atom": tol,
        "extension_reference_audit_pass": reference_audit_pass,
        "candidates_adjudicated": reference_audit_pass,
        "candidate_force_reaudit_ev_per_angstrom": candidate_force_reaudit,
        "candidates": candidates,
        "selected": selected,
        "next_gate": next_gate,
        "automatic_site_ordering_dispatch": False,
        "provenance": {
            "source_hold_gate_sha256": sha256(hold_path),
            "l13_reference_summary_sha256": sha256(l13_path),
            "l15_audit_summary_sha256": sha256(l15_path),
            "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
            "surface_convergence_extension_protocol_sha256": sha256(pp),
            "stage_a_result_sha256": p["frozen_sources"]["stage_a_result_sha256"],
            "force_gate_changed": False,
            "reproduction_gate_changed": False,
            "surface_excess_gate_changed": False,
            "candidate_selection_rule_changed": False,
            "scientific_settings_changed": False,
            "scientific_settings_changed_after_extension_freeze": False,
            "numerical_grid_extended_from_original_protocol": True,
            "kinetic_inputs_used": False,
            "prior_failure_preserved_as_failure": True,
        },
    }
    out = Path(args.out).resolve()
    write_json(out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if status != "CLEAN_SURFACE_PASS":
        raise SystemExit(f"SCIENTIFIC_HOLD: {status}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("self-test")
    sp.add_argument("--protocol", required=True)
    sp.set_defaults(func=command_self_test)

    sp = sub.add_parser("verify-sources")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--hold-root", required=True)
    sp.add_argument("--l13-root", required=True)
    sp.set_defaults(func=command_verify_sources)

    sp = sub.add_parser("inspect-prior")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--prior-root", required=True)
    sp.add_argument("--segment", type=int, required=True)
    sp.set_defaults(func=command_inspect_prior)

    for name, func in (("continue", command_continue), ("reproduce", command_reproduce)):
        sp = sub.add_parser(name)
        sp.add_argument("--protocol", required=True)
        sp.add_argument("--prior-root", required=True)
        if name == "continue":
            sp.add_argument("--segment", type=int, required=True)
        sp.add_argument("--surface-protocol")
        sp.add_argument("--stage-a-result")
        sp.add_argument("--bundle")
        sp.add_argument("--pseudo-dir")
        sp.add_argument("--pw")
        sp.add_argument("--selection")
        sp.add_argument("--runtime-cap-s", type=int, required=True)
        sp.add_argument("--out", required=True)
        sp.set_defaults(func=func)

    sp = sub.add_parser("gate")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--hold-root", required=True)
    sp.add_argument("--l13-root", required=True)
    sp.add_argument("--l15-root", required=True)
    sp.add_argument("--candidate-root", required=True)
    sp.add_argument("--surface-protocol", required=True)
    sp.add_argument("--stage-a-result", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=command_gate)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
