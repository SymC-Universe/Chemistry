#!/usr/bin/env python3
"""Mechanical proposal relay for the frozen CO/Cu(111) L13 audit.

This runner changes no scientific setting. It exists because the first bounded
recovery evaluated the same seed geometry in every segment: each segment then
printed a BFGS trial geometry but timed out during that trial's SCF. Here the
printed trial is explicitly labelled unevaluated and is used only as the input
geometry of the next unchanged pw.x relaxation segment, where it is evaluated
from scratch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import pbe_surface_timeout_recovery_v1 as v1  # noqa: E402

base = v1.base
PROTOCOL_SCHEMA = "co-cu111-pbe-surface-audit-proposal-relay-v0.1"
RELAY_SCHEMA = "co-cu111-pbe-surface-audit-proposal-relay-segment-v0.1"


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


def find_one(root: Path, name: str) -> Path | None:
    rows = [p for p in root.rglob(name) if p.is_file()]
    if len(rows) > 1:
        raise SystemExit(f"MECHANICAL_HOLD: multiple {name} files under {root}")
    return rows[0] if rows else None


def protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != PROTOCOL_SCHEMA:
        raise SystemExit("MECHANICAL_HOLD: wrong proposal-relay protocol schema")
    if p.get("status") != "FROZEN_MECHANICAL_RELAY_AFTER_V1_AUDIT_SEGMENT_EXHAUSTION_BEFORE_RELAY_RESULTS":
        raise SystemExit("MECHANICAL_HOLD: proposal-relay protocol is not frozen")
    if p.get("scientific_scope") != "NO_SCIENTIFIC_CONFIGURATION_CHANGE":
        raise SystemExit("MECHANICAL_HOLD: proposal relay changes scientific scope")
    prov = p.get("provenance", {})
    if prov.get("scientific_settings_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: proposal-relay provenance is not clean")
    if prov.get("surface_energies_or_kinetic_results_used_to_choose_relay") is not False:
        raise SystemExit("MECHANICAL_HOLD: result-directed relay design is forbidden")
    c = p.get("relay_contract", {})
    if c.get("target") != "audit" or c.get("case_id") != "L13-V28-K24-audit":
        raise SystemExit("MECHANICAL_HOLD: relay target is not exactly the frozen L13 audit")
    if c.get("restart_claim") != "NOT_EXACT_QE_RESTART":
        raise SystemExit("MECHANICAL_HOLD: false exact-restart claim")
    if c.get("continuation_mode") != "EVALUATE_PRIOR_BFGS_PROPOSED_TRIAL_FROM_SCRATCH":
        raise SystemExit("MECHANICAL_HOLD: wrong relay continuation mode")
    if c.get("qe_restart_mode_added") is not False or c.get("qe_max_seconds_added") is not False:
        raise SystemExit("MECHANICAL_HOLD: forbidden QE runtime directive enabled")
    if int(c.get("segment_runtime_cap_seconds", -1)) != 16200:
        raise SystemExit("MECHANICAL_HOLD: relay runtime cap changed")
    if int(c.get("maximum_relay_segments", -1)) != 4 or c.get("logical_segment_numbers") != [5, 6, 7, 8]:
        raise SystemExit("MECHANICAL_HOLD: relay segment bound changed")
    return p


def repo_root() -> Path:
    return HERE.parent.parent


def verify_frozen_sources(p: dict[str, Any]) -> None:
    root = repo_root()
    checks = {
        p["parent_recovery"]["original_recovery_protocol_path"]: p["parent_recovery"]["original_recovery_protocol_sha256"],
        p["parent_recovery"]["original_recovery_runner_path"]: p["parent_recovery"]["original_recovery_runner_sha256"],
        p["frozen_sources"]["surface_protocol"]["path"]: p["frozen_sources"]["surface_protocol"]["sha256"],
        p["frozen_sources"]["surface_runner"]["path"]: p["frozen_sources"]["surface_runner"]["sha256"],
        p["frozen_sources"]["surface_test"]["path"]: p["frozen_sources"]["surface_test"]["sha256"],
    }
    for rel, expected in checks.items():
        path = root / rel
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source mismatch: {rel}")


def original_context(p: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = repo_root()
    original = v1.recovery_protocol(root / p["parent_recovery"]["original_recovery_protocol_path"])
    surface = base.load_json(root / p["frozen_sources"]["surface_protocol"]["path"])
    base.verify_protocol(surface)
    target = original["recovery_targets"]["audit"]
    v1.verify_target_against_surface(surface, target)
    rc = p["relay_contract"]
    exact = {
        "layers": int(target["layers"]),
        "vacuum_angstrom": float(target["vacuum_angstrom"]),
        "kmesh": int(target["kmesh"]),
        "role": target["role"],
        "case_id": target["case_id"],
    }
    for key, value in exact.items():
        got = rc.get(key)
        if isinstance(value, float):
            if abs(float(got) - value) > 1e-12:
                raise SystemExit(f"MECHANICAL_HOLD: relay target differs from frozen audit: {key}")
        elif got != value:
            raise SystemExit(f"MECHANICAL_HOLD: relay target differs from frozen audit: {key}")
    return original, surface, target


def apply_template(rows: list[dict[str, Any]], template: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) != len(template):
        raise SystemExit("MECHANICAL_HOLD: geometry atom count mismatch")
    out: list[dict[str, Any]] = []
    for row, tmpl in zip(rows, template):
        if row.get("symbol") != tmpl.get("symbol"):
            raise SystemExit("MECHANICAL_HOLD: geometry symbol order mismatch")
        item = dict(tmpl)
        item["position_angstrom"] = [float(x) for x in row["position_angstrom"]]
        out.append(item)
    return out


def parse_position_block(lines: list[str], start: int, nat: int, template: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    rows: list[dict[str, Any]] = []
    for j in range(start + 1, min(start + 1 + nat, len(lines))):
        parts = lines[j].split()
        if len(parts) < 4 or parts[0] not in {"Cu", "C", "O"}:
            return None
        try:
            xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
        except ValueError:
            return None
        idx = len(rows)
        row = dict(template[idx])
        row["symbol"] = parts[0]
        row["position_angstrom"] = xyz
        rows.append(row)
    return rows if len(rows) == nat else None


def last_bfgs_proposed_trial(text: str, nat: int, template: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    """Return the final BFGS trial whose parent geometry was demonstrably evaluated.

    The returned trial itself is NOT claimed to be evaluated. Its parent section
    must contain a completed QE total-energy marker, a Total force record and the
    BFGS geometry-optimization step that emitted the trial coordinates.
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().upper().startswith("ATOMIC_POSITIONS") and "angstrom" in line.lower()]
    accepted: list[tuple[list[dict[str, Any]], dict[str, Any]]] = []
    for pos, start in enumerate(starts):
        rows = parse_position_block(lines, start, nat, template)
        if rows is None:
            continue
        parent_start = 0 if pos == 0 else starts[pos - 1] + 1 + nat
        parent = "\n".join(lines[parent_start:start])
        energies = [float(x) * base.RY_TO_EV for x in base.ENERGY_RE.findall(parent)]
        if not energies or "Total force =" not in parent or "BFGS Geometry Optimization" not in parent:
            continue
        total_force_rows = []
        for line in parent.splitlines():
            if "Total force =" in line:
                total_force_rows.append(line.strip())
        accepted.append((rows, {
            "parent_energy_ev": energies[-1],
            "parent_total_force_line": total_force_rows[-1] if total_force_rows else None,
            "trial_semantics": "PROPOSED_NOT_YET_EVALUATED",
        }))
    return accepted[-1] if accepted else None


def max_displacement_angstrom(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> float:
    if len(a) != len(b):
        return math.inf
    return max(
        math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(ra["position_angstrom"], rb["position_angstrom"])))
        for ra, rb in zip(a, b)
    )


def same_geometry(a: list[dict[str, Any]], b: list[dict[str, Any]], tol: float = 1e-10) -> bool:
    return max_displacement_angstrom(a, b) <= tol


def load_parent_v1_seed(root: Path, p: dict[str, Any], target: dict[str, Any], template: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seg_path = find_one(root, "RECOVERY_SEGMENT.json")
    out_path = find_one(root, "clean_relax.out")
    if seg_path is None or out_path is None:
        raise SystemExit("MECHANICAL_HOLD: v1 audit segment-4 seed files missing")
    seed = p["audit_seed"]
    if sha256(seg_path) != seed["recovery_segment_sha256"] or sha256(out_path) != seed["relax_output_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: immutable v1 audit segment-4 hash mismatch")
    row = load_json(seg_path)
    if row.get("schema") != v1.SEGMENT_SCHEMA or row.get("case_id") != target["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: v1 audit segment identity mismatch")
    if int(row.get("segment", -1)) != int(seed["required_parent_segment"]):
        raise SystemExit("MECHANICAL_HOLD: wrong v1 parent segment")
    if row.get("status") != seed["required_parent_status"] or row.get("timed_out_by_wrapper") is not True:
        raise SystemExit("MECHANICAL_HOLD: v1 parent is not the frozen timed-out CONTINUE state")
    if row.get("recovery_protocol_sha256") != p["parent_recovery"]["original_recovery_protocol_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: v1 parent recovery protocol mismatch")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: v1 parent provenance mismatch")
    current = apply_template(row.get("latest_atoms") or [], template)
    proposed = last_bfgs_proposed_trial(out_path.read_text(errors="replace"), int(target["layers"]), template)
    if proposed is None:
        raise SystemExit("MECHANICAL_HOLD: no provable BFGS trial geometry in v1 segment 4")
    trial, evidence = proposed
    trial = apply_template(trial, template)
    delta = max_displacement_angstrom(current, trial)
    if delta <= 1e-10:
        raise SystemExit("MECHANICAL_HOLD: v1 proposed trial does not advance geometry")
    evidence.update({
        "prior_kind": "v1_audit_segment_4",
        "prior_segment_sha256": sha256(seg_path),
        "prior_relax_output_sha256": sha256(out_path),
        "input_to_trial_max_displacement_angstrom": delta,
    })
    return trial, evidence


def load_relay_prior(root: Path, p: dict[str, Any], target: dict[str, Any], template: list[dict[str, Any]], expected_relay_segment: int) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    seg_path = find_one(root, "RELAY_SEGMENT.json")
    if seg_path is None:
        raise SystemExit("MECHANICAL_HOLD: prior relay segment missing")
    row = load_json(seg_path)
    if row.get("schema") != RELAY_SCHEMA or row.get("case_id") != target["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: prior relay identity mismatch")
    if int(row.get("relay_segment", -1)) != expected_relay_segment:
        raise SystemExit("MECHANICAL_HOLD: relay prior is not the immediate predecessor")
    if row.get("relay_protocol_sha256") != p["_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: relay prior protocol mismatch")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: relay prior provenance mismatch")
    status = row.get("status")
    if status == "RELAX_COMPLETE":
        atoms = apply_template(row.get("final_atoms") or [], template)
        return status, atoms, {"prior_kind": "relay_complete", "prior_segment_sha256": sha256(seg_path), "prior_row": row}
    if status != "CONTINUE":
        raise SystemExit("MECHANICAL_HOLD: unexpected relay-prior status")
    out_path = find_one(root, "clean_relax.out")
    if out_path is None or sha256(out_path) != row.get("raw_hashes", {}).get("relax_output_sha256"):
        raise SystemExit("MECHANICAL_HOLD: relay prior relax-output hash mismatch")
    proposed = last_bfgs_proposed_trial(out_path.read_text(errors="replace"), int(target["layers"]), template)
    if proposed is None:
        raise SystemExit("MECHANICAL_HOLD: relay prior has no provable next trial")
    parsed_trial, evidence = proposed
    parsed_trial = apply_template(parsed_trial, template)
    stored = apply_template(row.get("next_trial_atoms") or [], template)
    if not same_geometry(parsed_trial, stored, 1e-9):
        raise SystemExit("MECHANICAL_HOLD: stored relay trial does not match raw QE output")
    evidence.update({"prior_kind": "relay_continue", "prior_segment_sha256": sha256(seg_path), "prior_row": row})
    return status, stored, evidence


def verify_runtime_context(p: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    verify_frozen_sources(p)
    original, surface, target = original_context(p)
    surface_path = Path(args.surface_protocol).resolve()
    if sha256(surface_path) != p["frozen_sources"]["surface_protocol"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: supplied surface protocol hash mismatch")
    base.verify_stage_a(surface, Path(args.stage_a_result).resolve())
    bundle = base.verify_bundle(surface, Path(args.bundle).resolve(), Path(args.pseudo_dir).resolve(), Path(args.pw).resolve())
    if sha256(Path(args.pw).resolve()) != p["frozen_sources"]["pw_x_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: exact pw.x SHA256 mismatch")
    return original, surface, target, bundle


def command_self_test(args: argparse.Namespace) -> None:
    rp = Path(args.relay_protocol).resolve()
    p = protocol(rp); p["_sha256"] = sha256(rp)
    verify_frozen_sources(p)
    original, surface, target = original_context(p)
    unchanged = p["unchanged_science"]
    inherited = surface["inherited_stage_a_settings"]
    exact = {
        "ecutwfc_ry": inherited["ecutwfc_ry"],
        "ecutrho_ry": inherited["ecutrho_ry"],
        "degauss_ry": inherited["degauss_ry"],
        "electron_conv_thr": inherited["electron_conv_thr"],
        "mixing_beta": inherited["mixing_beta"],
        "electron_maxstep": inherited["electron_maxstep"],
    }
    for key, value in exact.items():
        if unchanged.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: relay changes frozen value {key}")
    if int(unchanged["mpi_rank_count"]) != 1 or unchanged["thread_caps"] != {"OMP_NUM_THREADS": 1, "OPENBLAS_NUM_THREADS": 1, "MKL_NUM_THREADS": 1}:
        raise SystemExit("MECHANICAL_HOLD: process/thread contract changed")
    if target["case_id"] != p["relay_contract"]["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: audit target mismatch")
    print("AUDIT_PROPOSAL_RELAY_SELF_TEST_PASS")
    print("SCIENTIFIC_SETTINGS_CHANGED=false")
    print("KINETIC_INPUTS_USED=false")


def command_verify_seed(args: argparse.Namespace) -> None:
    rp = Path(args.relay_protocol).resolve()
    p = protocol(rp); p["_sha256"] = sha256(rp)
    verify_frozen_sources(p)
    _, surface, target = original_context(p)
    _, template = v1.cell_and_template(surface, target)
    trial, evidence = load_parent_v1_seed(Path(args.parent_root).resolve(), p, target, template)
    print(json.dumps({
        "status": "PROPOSAL_RELAY_SEED_VERIFIED",
        "case_id": target["case_id"],
        "trial_semantics": "PROPOSED_NOT_YET_EVALUATED",
        "atom_count": len(trial),
        **evidence,
    }, indent=2, sort_keys=True))


def command_relay(args: argparse.Namespace) -> None:
    rp = Path(args.relay_protocol).resolve()
    p = protocol(rp); p["_sha256"] = sha256(rp)
    _, surface, target, bundle = verify_runtime_context(p, args)
    relay_segment = int(args.relay_segment)
    maximum = int(p["relay_contract"]["maximum_relay_segments"])
    if relay_segment < 1 or relay_segment > maximum:
        raise SystemExit("MECHANICAL_HOLD: relay segment outside frozen bound")
    cell, template = v1.cell_and_template(surface, target)

    prior_root = Path(args.prior_root).resolve()
    if relay_segment == 1:
        seed, evidence = load_parent_v1_seed(prior_root, p, target, template)
        prior_status = "CONTINUE"
    else:
        prior_status, seed, evidence = load_relay_prior(prior_root, p, target, template, relay_segment - 1)
        if prior_status == "RELAX_COMPLETE":
            prior_row = evidence["prior_row"]
            root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
            adopted = dict(prior_row)
            adopted["relay_segment"] = relay_segment
            adopted["logical_segment"] = int(p["relay_contract"]["logical_segment_numbers"][relay_segment - 1])
            adopted["adopted_from_complete_relay_segment"] = relay_segment - 1
            write_json(root / "RELAY_SEGMENT.json", adopted)
            base.stage_manifest(root, [root / "RELAY_SEGMENT.json"])
            print(json.dumps(adopted, indent=2, sort_keys=True))
            return

    seed = apply_template(seed, template)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "relax"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_relax.in"; out = run_dir / "clean_relax.out"
    inp.write_text(base.qe_input(
        calculation="relax",
        prefix="co_cu111_clean",
        cell=cell,
        atoms=seed,
        kmesh=int(target["kmesh"]),
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    ))
    v1.validate_no_runtime_directives(inp)
    cap = int(args.runtime_cap_s or p["relay_contract"]["segment_runtime_cap_seconds"])
    if cap != int(p["relay_contract"]["segment_runtime_cap_seconds"]):
        raise SystemExit("MECHANICAL_HOLD: relay runtime cap differs from frozen value")
    result = v1.run_pw_capped(Path(args.pw).resolve(), inp, out, cap)
    if result["returncode"] != 0 and not result["timed_out_by_wrapper"]:
        raise SystemExit(f"MECHANICAL_HOLD: pw.x failed before relay checkpoint, rc={result['returncode']}")

    complete = bool(result["job_done"] and result["energy_ev"] is not None)
    row: dict[str, Any] = {
        "schema": RELAY_SCHEMA,
        "status": "RELAX_COMPLETE" if complete else "CONTINUE",
        "case_id": target["case_id"],
        "target": "audit",
        "relay_segment": relay_segment,
        "logical_segment": int(p["relay_contract"]["logical_segment_numbers"][relay_segment - 1]),
        "continuation_mode": p["relay_contract"]["continuation_mode"],
        "restart_claim": p["relay_contract"]["restart_claim"],
        "input_trial_semantics": "PROPOSED_NOT_YET_EVALUATED",
        "input_atoms": seed,
        "input_source_evidence": {k: v for k, v in evidence.items() if k != "prior_row"},
        "cell_angstrom": cell,
        "layers": int(target["layers"]),
        "vacuum_angstrom": float(target["vacuum_angstrom"]),
        "kmesh": int(target["kmesh"]),
        "role": target["role"],
        "elapsed_s": result["elapsed_s"],
        "timed_out_by_wrapper": result["timed_out_by_wrapper"],
        "pw_returncode": result["returncode"],
        "relay_protocol_sha256": p["_sha256"],
        "surface_protocol_sha256": sha256(Path(args.surface_protocol).resolve()),
        "pw_sha256": sha256(Path(args.pw).resolve()),
        "bundle_sha256": sha256(Path(args.bundle).resolve()),
        "scientific_settings_changed": False,
        "kinetic_inputs_used": False,
        "raw_hashes": {
            "relax_input_sha256": sha256(inp),
            "relax_output_sha256": sha256(out),
        },
    }

    if complete:
        final_atoms = base.parse_positions(result["text"], int(target["layers"]), seed)
        if final_atoms is None:
            raise SystemExit("MECHANICAL_HOLD: completed relay relaxation lacks final geometry")
        final_atoms = apply_template(final_atoms, template)
        forces = base.parse_forces(result["text"], int(target["layers"]))
        max_force = base.max_movable_force_ev_a(forces, final_atoms)
        row.update({
            "final_atoms": final_atoms,
            "relax_energy_ev": float(result["energy_ev"]),
            "max_movable_force_ev_per_angstrom": max_force,
            "next_trial_atoms": None,
        })
    else:
        proposed = last_bfgs_proposed_trial(result["text"], int(target["layers"]), template)
        if proposed is None:
            raise SystemExit("MECHANICAL_HOLD: timed-out relay did not reach a provable next BFGS trial")
        next_trial, proposal_evidence = proposed
        next_trial = apply_template(next_trial, template)
        delta = max_displacement_angstrom(seed, next_trial)
        if delta <= 1e-10:
            raise SystemExit("MECHANICAL_HOLD: timed-out relay would repeat the same input geometry")
        forces = base.parse_forces(result["text"], int(target["layers"]))
        evaluated_seed_force = base.max_movable_force_ev_a(forces, seed)
        row.update({
            "evaluated_input_energy_ev": result["energy_ev"],
            "evaluated_input_max_movable_force_ev_per_angstrom": evaluated_seed_force,
            "next_trial_atoms": next_trial,
            "next_trial_semantics": "PROPOSED_NOT_YET_EVALUATED",
            "next_trial_max_displacement_from_input_angstrom": delta,
            "next_trial_parent_evidence": proposal_evidence,
        })

    # Electronic scratch is not a continuation source in this relay. Preserve the
    # raw input/output and explicit geometry record, then discard scratch to avoid
    # treating partial wavefunctions or charge density as an implicit restart.
    base.cleanup_tmp(tmp)
    row["scratch_retained"] = False
    row["scratch_used_for_continuation"] = False
    write_json(root / "RELAY_SEGMENT.json", row)
    base.stage_manifest(root, [root / "RELAY_SEGMENT.json"])
    print(json.dumps(row, indent=2, sort_keys=True))


def command_reproduce(args: argparse.Namespace) -> None:
    rp = Path(args.relay_protocol).resolve()
    p = protocol(rp); p["_sha256"] = sha256(rp)
    _, surface, target, bundle = verify_runtime_context(p, args)
    cell, template = v1.cell_and_template(surface, target)
    seg_path = find_one(Path(args.relax_root).resolve(), "RELAY_SEGMENT.json")
    if seg_path is None:
        raise SystemExit("MECHANICAL_HOLD: final relay segment missing")
    seg = load_json(seg_path)
    if seg.get("schema") != RELAY_SCHEMA or seg.get("case_id") != target["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: final relay identity mismatch")
    if seg.get("relay_protocol_sha256") != p["_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: final relay protocol mismatch")
    if seg.get("status") != "RELAX_COMPLETE":
        raise SystemExit("MECHANICAL_INCOMPLETE: L13 audit relaxation did not complete within frozen proposal-relay segments")
    atoms = apply_template(seg.get("final_atoms") or [], template)
    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]

    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    repro = root / "reproduce"; repro.mkdir(exist_ok=True)
    tmp = repro / "tmp"; tmp.mkdir(exist_ok=True)
    inp = repro / "clean_reproduce.in"; out = repro / "clean_reproduce.out"
    inp.write_text(base.qe_input(
        calculation="scf",
        prefix="co_cu111_clean_repro",
        cell=cell,
        atoms=fixed,
        kmesh=int(target["kmesh"]),
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    ))
    v1.validate_no_runtime_directives(inp)
    cap = int(args.runtime_cap_s or p["relay_contract"]["segment_runtime_cap_seconds"])
    if cap != int(p["relay_contract"]["segment_runtime_cap_seconds"]):
        raise SystemExit("MECHANICAL_HOLD: reproduction cap differs from frozen relay value")
    result = v1.run_pw_capped(Path(args.pw).resolve(), inp, out, cap)
    if result["timed_out_by_wrapper"]:
        raise SystemExit("MECHANICAL_INCOMPLETE: L13 audit independent reproduction SCF exceeded frozen relay cap")
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit("MECHANICAL_HOLD: L13 audit independent reproduction SCF failed")

    relax_energy = seg.get("relax_energy_ev")
    max_force = seg.get("max_movable_force_ev_per_angstrom")
    if relax_energy is None or max_force is None:
        raise SystemExit("MECHANICAL_HOLD: completed relay lacks relaxation energy/force")
    delta = abs(float(relax_energy) - float(result["energy_ev"]))
    spec = surface["clean_surface"]
    mechanical_pass = (
        float(max_force) <= float(spec["relaxation"]["force_gate_ev_per_angstrom"])
        and delta <= float(spec["independent_scf_reproduction_gate_ev"])
    )
    bulk_e0 = float(surface["inherited_stage_a_settings"]["bulk_e0_ev_per_atom"])
    excess = (float(result["energy_ev"]) - int(target["layers"]) * bulk_e0) / 2.0
    layer_z = sorted(float(a["position_angstrom"][2]) for a in atoms)
    surface_path = Path(args.surface_protocol).resolve()
    stage_path = Path(args.stage_a_result).resolve()
    bundle_path = Path(args.bundle).resolve()
    pw = Path(args.pw).resolve()
    summary = {
        "schema": "co-cu111-pbe-clean-surface-case-v0.1",
        "status": "COMPLETE" if mechanical_pass else "NUMERICAL_HOLD",
        "case_id": target["case_id"],
        "role": target["role"],
        "layers": int(target["layers"]),
        "vacuum_angstrom": float(target["vacuum_angstrom"]),
        "kmesh": int(target["kmesh"]),
        "cell_angstrom": cell,
        "layer_z_angstrom": layer_z,
        "final_atoms": atoms,
        "relax_energy_ev": float(relax_energy),
        "fixed_geometry_scf_energy_ev": float(result["energy_ev"]),
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": float(max_force),
        "surface_excess_ev_per_surface_atom": excess,
        "mechanical_pass": mechanical_pass,
        "provenance": {
            "protocol_sha256": sha256(surface_path),
            "stage_a_result_sha256": sha256(stage_path),
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "proposal_relay_protocol_sha256": p["_sha256"],
            "parent_recovery_run_id": p["parent_recovery"]["run_id"],
            "continuation_mode": p["relay_contract"]["continuation_mode"],
            "restart_claim": p["relay_contract"]["restart_claim"],
            "kinetic_inputs_used": False,
            "stage_a_scientific_settings_modified": False,
            "scientific_settings_changed": False,
        },
        "raw_hashes": {
            "final_relay_segment_sha256": sha256(seg_path),
            "reproduce_input_sha256": sha256(inp),
            "reproduce_output_sha256": sha256(out),
        },
    }
    summary_path = root / "summary.json"
    write_json(summary_path, summary)
    base.stage_manifest(root, [summary_path])
    print(json.dumps(summary, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("self-test")
    s.add_argument("--relay-protocol", required=True)
    s.set_defaults(func=command_self_test)

    v = sub.add_parser("verify-seed")
    v.add_argument("--relay-protocol", required=True)
    v.add_argument("--parent-root", required=True)
    v.set_defaults(func=command_verify_seed)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--relay-protocol", required=True)
    common.add_argument("--surface-protocol", required=True)
    common.add_argument("--stage-a-result", required=True)
    common.add_argument("--bundle", required=True)
    common.add_argument("--pseudo-dir", required=True)
    common.add_argument("--pw", required=True)
    common.add_argument("--runtime-cap-s", type=int)

    r = sub.add_parser("relay", parents=[common])
    r.add_argument("--prior-root", required=True)
    r.add_argument("--relay-segment", type=int, required=True)
    r.add_argument("--out", required=True)
    r.set_defaults(func=command_relay)

    q = sub.add_parser("reproduce", parents=[common])
    q.add_argument("--relax-root", required=True)
    q.add_argument("--out", required=True)
    q.set_defaults(func=command_reproduce)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
