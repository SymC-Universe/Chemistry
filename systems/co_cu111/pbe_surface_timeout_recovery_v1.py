#!/usr/bin/env python3
"""Mechanical timeout recovery for the frozen CO/Cu(111) PBE clean-surface gate.

This module does not define new scientific settings. It imports the frozen
surface/site runner and uses its geometry and QE-input constructors. The only
recovery operation is to seed a fresh BFGS invocation from the last evaluated
ionic geometry preserved in the timed-out output. This is explicitly
not represented as an exact Quantum ESPRESSO restart.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import pbe_surface_site_ordering_v1 as base  # noqa: E402

SEGMENT_SCHEMA = "co-cu111-pbe-surface-timeout-recovery-segment-v0.1"
REPRO_SCHEMA = "co-cu111-pbe-surface-timeout-recovery-reproduction-v0.1"
PROTOCOL_SCHEMA = "co-cu111-pbe-surface-timeout-recovery-v0.1"


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


def recovery_protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != PROTOCOL_SCHEMA:
        raise SystemExit("MECHANICAL_HOLD: wrong recovery protocol schema")
    if p.get("status") != "FROZEN_MECHANICAL_RECOVERY_AFTER_SOURCE_TIMEOUTS_BEFORE_RECOVERY_RESULTS":
        raise SystemExit("MECHANICAL_HOLD: recovery protocol is not frozen")
    if p.get("scientific_scope") != "NO_SCIENTIFIC_CONFIGURATION_CHANGE":
        raise SystemExit("MECHANICAL_HOLD: recovery protocol changes scientific scope")
    prov = p.get("provenance", {})
    if prov.get("scientific_settings_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: recovery provenance is not clean")
    contract = p.get("continuation_contract", {})
    if contract.get("restart_claim") != "NOT_EXACT_QE_RESTART":
        raise SystemExit("MECHANICAL_HOLD: false exact-restart claim")
    if contract.get("continuation_mode") != "FROM_SCRATCH_FROM_LAST_EVALUATED_GEOMETRY":
        raise SystemExit("MECHANICAL_HOLD: wrong continuation mode")
    if contract.get("qe_restart_mode_added") is not False or contract.get("qe_max_seconds_added") is not False:
        raise SystemExit("MECHANICAL_HOLD: QE runtime controls may not be inserted")
    targets = p.get("recovery_targets", {})
    if set(targets) != {"reference", "audit"}:
        raise SystemExit("MECHANICAL_HOLD: recovery targets are not exactly reference+audit")
    return p


def verify_frozen_repo_sources(p: dict[str, Any]) -> None:
    frozen = p["frozen_sources"]
    for key in ("surface_protocol", "surface_runner", "surface_test"):
        row = frozen[key]
        # Paths are repository-relative. HERE is <repo>/systems/co_cu111.
        repo = HERE.parent.parent
        candidate = repo / row["path"]
        if not candidate.is_file():
            raise SystemExit(f"MECHANICAL_HOLD: missing frozen source {row['path']}")
        if sha256(candidate) != row["sha256"]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source SHA256 mismatch: {row['path']}")


def get_target(p: dict[str, Any], key: str) -> dict[str, Any]:
    if key not in {"reference", "audit"}:
        raise SystemExit("MECHANICAL_HOLD: target must be reference or audit")
    return p["recovery_targets"][key]


def verify_target_against_surface(surface: dict[str, Any], t: dict[str, Any]) -> None:
    cs = surface["clean_surface"]
    expected = cs["terminal_reference" if t["role"] == "reference" else "independent_audit"]
    checks = (
        int(t["layers"]) == int(expected["layers"]),
        abs(float(t["vacuum_angstrom"]) - float(expected["vacuum_angstrom"])) < 1e-12,
        int(t["kmesh"]) == int(expected["kmesh"]),
        expected.get("selectable") is False,
    )
    if not all(checks):
        raise SystemExit("MECHANICAL_HOLD: recovery target differs from frozen surface protocol")
    if t["case_id"] != base.clean_case_id(int(t["layers"]), float(t["vacuum_angstrom"]), int(t["kmesh"]), t["role"]):
        raise SystemExit("MECHANICAL_HOLD: target case_id mismatch")


def verify_source_artifact(root: Path, t: dict[str, Any]) -> None:
    for rel, expected in t["source_files"].items():
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"MECHANICAL_HOLD: source artifact missing {rel}")
        if sha256(path) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: immutable source hash mismatch for {rel}")


def cell_and_template(surface: dict[str, Any], t: dict[str, Any]) -> tuple[list[list[float]], list[dict[str, Any]]]:
    return base.clean_geometry(
        float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]),
        int(t["layers"]),
        float(t["vacuum_angstrom"]),
    )



def position_blocks(text: str, nat: int, template: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], str]]:
    """Return complete ATOMIC_POSITIONS blocks paired with text until the next block.

    A BFGS block is considered evaluated only if the following section contains
    both a completed total-energy record and a Total force record. This prevents
    a timeout during the SCF of a newly proposed geometry from being mistaken for
    an accepted/evaluated checkpoint.
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().upper().startswith("ATOMIC_POSITIONS") and "angstrom" in line.lower()]
    found: list[tuple[list[dict[str, Any]], str]] = []
    for pos, i in enumerate(starts):
        rows: list[dict[str, Any]] = []
        for j in range(i + 1, min(i + 1 + nat, len(lines))):
            parts = lines[j].split()
            if len(parts) < 4 or parts[0] not in {"Cu", "C", "O"}:
                rows = []
                break
            try:
                xyz = [float(parts[1]), float(parts[2]), float(parts[3])]
            except ValueError:
                rows = []
                break
            idx = len(rows)
            row = dict(template[idx])
            row["symbol"] = parts[0]
            row["position_angstrom"] = xyz
            rows.append(row)
        if len(rows) != nat:
            continue
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        follow = "\n".join(lines[i + 1 + nat:end])
        found.append((rows, follow))
    return found


def last_evaluated_positions(text: str, nat: int, template: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    evaluated: list[list[dict[str, Any]]] = []
    for rows, follow in position_blocks(text, nat, template):
        if base.ENERGY_RE.search(follow) and "Total force =" in follow:
            evaluated.append(rows)
    return evaluated[-1] if evaluated else None

def positions_from_source(root: Path, surface: dict[str, Any], t: dict[str, Any]) -> list[dict[str, Any]]:
    verify_source_artifact(root, t)
    _, template = cell_and_template(surface, t)
    text = (root / "relax/clean_relax.out").read_text(errors="replace")
    atoms = last_evaluated_positions(text, int(t["layers"]), template)
    if atoms is None:
        raise SystemExit("MECHANICAL_HOLD: no evaluated checkpoint geometry in source output")
    return atoms


def find_one(root: Path, name: str) -> Path | None:
    matches = [p for p in root.rglob(name) if p.is_file()]
    if len(matches) > 1:
        raise SystemExit(f"MECHANICAL_HOLD: multiple {name} files found under {root}")
    return matches[0] if matches else None


def positions_from_prior(root: Path, p: dict[str, Any], t: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = find_one(root, "RECOVERY_SEGMENT.json")
    if path is None:
        raise SystemExit("MECHANICAL_HOLD: prior recovery segment missing")
    row = load_json(path)
    if row.get("schema") != SEGMENT_SCHEMA or row.get("case_id") != t["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: prior segment identity mismatch")
    if row.get("recovery_protocol_sha256") != p["_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: prior segment recovery protocol mismatch")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: prior segment provenance mismatch")
    atoms = row.get("latest_atoms")
    if not isinstance(atoms, list) or len(atoms) != int(t["layers"]):
        raise SystemExit("MECHANICAL_HOLD: prior segment lacks a complete geometry")
    return atoms, row


def run_pw_capped(pw: Path, inp: Path, out: Path, cap_s: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    start = time.time()
    timed_out = False
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        try:
            rc = proc.wait(timeout=cap_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                rc = proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait(timeout=30)
    text = out.read_text(errors="replace")
    energies = [float(x) * base.RY_TO_EV for x in base.ENERGY_RE.findall(text)]
    return {
        "returncode": int(rc),
        "elapsed_s": time.time() - start,
        "timed_out_by_wrapper": timed_out,
        "job_done": "JOB DONE." in text,
        "energy_ev": energies[-1] if energies else None,
        "text": text,
    }


def validate_no_runtime_directives(inp: Path) -> None:
    low = inp.read_text().lower()
    forbidden = ("restart_mode", "max_seconds", "nstep")
    for token in forbidden:
        if token in low:
            raise SystemExit(f"MECHANICAL_HOLD: recovery inserted forbidden runtime/science directive {token}")


def command_self_test(args: argparse.Namespace) -> None:
    rp = Path(args.recovery_protocol).resolve()
    p = recovery_protocol(rp)
    p["_sha256"] = sha256(rp)
    verify_frozen_repo_sources(p)
    surface_path = Path(p["frozen_sources"]["surface_protocol"]["path"]).resolve()
    surface = base.load_json(surface_path)
    base.verify_protocol(surface)
    for key in ("reference", "audit"):
        verify_target_against_surface(surface, get_target(p, key))
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
            raise SystemExit(f"MECHANICAL_HOLD: recovery changed frozen value {key}")
    print("RECOVERY_SELF_TEST_PASS")
    print("SCIENTIFIC_SETTINGS_CHANGED=false")
    print("KINETIC_INPUTS_USED=false")


def command_verify_source(args: argparse.Namespace) -> None:
    rp = Path(args.recovery_protocol).resolve()
    p = recovery_protocol(rp); p["_sha256"] = sha256(rp)
    surface = base.load_json(Path(p["frozen_sources"]["surface_protocol"]["path"]).resolve())
    base.verify_protocol(surface)
    t = get_target(p, args.target)
    verify_target_against_surface(surface, t)
    root = Path(args.source_root).resolve()
    atoms = positions_from_source(root, surface, t)
    print(json.dumps({
        "status": "SOURCE_VERIFIED",
        "case_id": t["case_id"],
        "evaluated_geometry_atom_count": len(atoms),
        "source_output_sha256": sha256(root / "relax/clean_relax.out"),
        "restart_claim": p["continuation_contract"]["restart_claim"],
    }, sort_keys=True))


def command_recover_relax(args: argparse.Namespace) -> None:
    rp = Path(args.recovery_protocol).resolve()
    p = recovery_protocol(rp); p["_sha256"] = sha256(rp)
    verify_frozen_repo_sources(p)
    surface_path = Path(args.surface_protocol).resolve()
    surface = base.load_json(surface_path); base.verify_protocol(surface)
    if sha256(surface_path) != p["frozen_sources"]["surface_protocol"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: surface protocol SHA256 mismatch")
    base.verify_stage_a(surface, Path(args.stage_a_result).resolve())
    bundle = base.verify_bundle(surface, Path(args.bundle).resolve(), Path(args.pseudo_dir).resolve(), Path(args.pw).resolve())
    t = get_target(p, args.target); verify_target_against_surface(surface, t)
    source_root = Path(args.source_root).resolve(); verify_source_artifact(source_root, t)
    cell, template = cell_and_template(surface, t)

    segment = int(args.segment)
    maximum_segments = int(p["continuation_contract"]["maximum_relax_segments"])
    if segment < 1 or segment > maximum_segments:
        raise SystemExit("MECHANICAL_HOLD: recovery segment outside frozen range")
    if segment == 1 and args.prior_root:
        raise SystemExit("MECHANICAL_HOLD: segment 1 may not consume a prior recovery segment")
    if segment > 1 and not args.prior_root:
        raise SystemExit("MECHANICAL_HOLD: later recovery segment requires the immediately preceding segment")

    previous: dict[str, Any] | None = None
    if args.prior_root:
        prior_root = Path(args.prior_root).resolve()
        seed, previous = positions_from_prior(prior_root, p, t)
        if int(previous.get("segment", -1)) != segment - 1:
            raise SystemExit("MECHANICAL_HOLD: prior recovery segment is not the immediate predecessor")
        if previous.get("status") == "RELAX_COMPLETE":
            root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(prior_root, root, dirs_exist_ok=True)
            adopted = dict(previous)
            adopted["segment"] = segment
            adopted["adopted_from_previous_complete_segment"] = True
            adopted["adopted_from_segment"] = segment - 1
            write_json(root / "RECOVERY_SEGMENT.json", adopted)
            base.stage_manifest(root, [root / "RECOVERY_SEGMENT.json"])
            print(json.dumps(adopted, sort_keys=True))
            return
    else:
        seed = positions_from_source(source_root, surface, t)

    if len(seed) != int(t["layers"]):
        raise SystemExit("MECHANICAL_HOLD: seed geometry atom count mismatch")
    for atom, tmpl in zip(seed, template):
        atom["flags"] = list(tmpl["flags"])
        atom["layer"] = tmpl.get("layer")
        atom["symbol"] = tmpl["symbol"]

    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "relax"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_relax.in"; out = run_dir / "clean_relax.out"
    inp.write_text(base.qe_input(
        calculation="relax",
        prefix="co_cu111_clean",
        cell=cell,
        atoms=seed,
        kmesh=int(t["kmesh"]),
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    ))
    validate_no_runtime_directives(inp)
    frozen_cap = int(p["continuation_contract"]["segment_runtime_cap_seconds"])
    cap = int(args.runtime_cap_s or frozen_cap)
    if cap != frozen_cap:
        raise SystemExit("MECHANICAL_HOLD: runtime cap differs from frozen mechanical recovery value")
    result = run_pw_capped(Path(args.pw).resolve(), inp, out, cap)
    latest = last_evaluated_positions(result["text"], int(t["layers"]), seed) or seed
    for atom, tmpl in zip(latest, template):
        atom["flags"] = list(tmpl["flags"])
        atom["layer"] = tmpl.get("layer")
        atom["symbol"] = tmpl["symbol"]

    if result["returncode"] != 0 and not result["timed_out_by_wrapper"]:
        raise SystemExit(f"MECHANICAL_HOLD: pw.x failed before wrapper checkpoint, rc={result['returncode']}")

    relax_complete = bool(result["job_done"] and result["energy_ev"] is not None)
    forces = base.parse_forces(result["text"], int(t["layers"])) if relax_complete else None
    max_force = base.max_movable_force_ev_a(forces, latest) if relax_complete else None
    row = {
        "schema": SEGMENT_SCHEMA,
        "status": "RELAX_COMPLETE" if relax_complete else "CONTINUE",
        "case_id": t["case_id"],
        "target": args.target,
        "segment": int(args.segment),
        "continuation_mode": p["continuation_contract"]["continuation_mode"],
        "restart_claim": p["continuation_contract"]["restart_claim"],
        "latest_atoms": latest,
        "cell_angstrom": cell,
        "layers": int(t["layers"]),
        "vacuum_angstrom": float(t["vacuum_angstrom"]),
        "kmesh": int(t["kmesh"]),
        "role": t["role"],
        "relax_energy_ev": result["energy_ev"],
        "max_movable_force_ev_per_angstrom": max_force,
        "timed_out_by_wrapper": result["timed_out_by_wrapper"],
        "elapsed_s": result["elapsed_s"],
        "pw_returncode": result["returncode"],
        "source_artifact_id": t["source_artifact_id"],
        "source_artifact_digest": t["source_artifact_digest"],
        "source_output_sha256": t["source_files"]["relax/clean_relax.out"],
        "seed_source": "prior_recovery_segment" if previous else "immutable_source_timeout_output",
        "recovery_protocol_sha256": p["_sha256"],
        "surface_protocol_sha256": sha256(surface_path),
        "pw_sha256": sha256(Path(args.pw).resolve()),
        "bundle_sha256": sha256(Path(args.bundle).resolve()),
        "scientific_settings_changed": False,
        "kinetic_inputs_used": False,
        "raw_hashes": {
            "relax_input_sha256": sha256(inp),
            "relax_output_sha256": sha256(out),
        },
    }
    write_json(root / "RECOVERY_SEGMENT.json", row)
    base.stage_manifest(root, [root / "RECOVERY_SEGMENT.json"])
    print(json.dumps(row, indent=2, sort_keys=True))


def command_reproduce(args: argparse.Namespace) -> None:
    rp = Path(args.recovery_protocol).resolve()
    p = recovery_protocol(rp); p["_sha256"] = sha256(rp)
    verify_frozen_repo_sources(p)
    surface_path = Path(args.surface_protocol).resolve()
    surface = base.load_json(surface_path); base.verify_protocol(surface)
    base.verify_stage_a(surface, Path(args.stage_a_result).resolve())
    bundle_path = Path(args.bundle).resolve(); pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve()
    bundle = base.verify_bundle(surface, bundle_path, pseudo_dir, pw)
    t = get_target(p, args.target); verify_target_against_surface(surface, t)

    seg_path = find_one(Path(args.relax_root).resolve(), "RECOVERY_SEGMENT.json")
    if seg_path is None:
        raise SystemExit("MECHANICAL_HOLD: final recovery segment missing")
    seg = load_json(seg_path)
    if seg.get("schema") != SEGMENT_SCHEMA or seg.get("case_id") != t["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: final recovery segment identity mismatch")
    if seg.get("status") != "RELAX_COMPLETE":
        raise SystemExit("MECHANICAL_INCOMPLETE: relaxation did not complete within frozen recovery segments")
    if seg.get("recovery_protocol_sha256") != p["_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: recovery segment protocol mismatch")
    atoms = seg["latest_atoms"]
    cell = seg["cell_angstrom"]
    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]

    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    repro = root / "reproduce"; repro.mkdir(exist_ok=True); tmp = repro / "tmp"; tmp.mkdir(exist_ok=True)
    inp = repro / "clean_reproduce.in"; out = repro / "clean_reproduce.out"
    inp.write_text(base.qe_input(
        calculation="scf",
        prefix="co_cu111_clean_repro",
        cell=cell,
        atoms=fixed,
        kmesh=int(t["kmesh"]),
        protocol=surface,
        bundle=bundle,
        pseudo_dir=pseudo_dir,
        outdir=tmp,
    ))
    validate_no_runtime_directives(inp)
    frozen_cap = int(p["continuation_contract"]["segment_runtime_cap_seconds"])
    cap = int(args.runtime_cap_s or frozen_cap)
    if cap != frozen_cap:
        raise SystemExit("MECHANICAL_HOLD: reproduction runtime cap differs from frozen mechanical recovery value")
    result = run_pw_capped(pw, inp, out, cap)
    if result["timed_out_by_wrapper"]:
        row = {
            "schema": REPRO_SCHEMA,
            "status": "CONTINUE",
            "case_id": t["case_id"],
            "target": args.target,
            "timed_out_by_wrapper": True,
            "recovery_protocol_sha256": p["_sha256"],
            "scientific_settings_changed": False,
            "kinetic_inputs_used": False,
            "raw_hashes": {"reproduce_input_sha256": sha256(inp), "reproduce_output_sha256": sha256(out)},
        }
        write_json(root / "REPRODUCTION_CHECKPOINT.json", row)
        base.stage_manifest(root, [root / "REPRODUCTION_CHECKPOINT.json"])
        print(json.dumps(row, indent=2, sort_keys=True))
        return
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit("MECHANICAL_HOLD: independent reproduction SCF failed")

    relax_energy = seg.get("relax_energy_ev")
    if relax_energy is None:
        raise SystemExit("MECHANICAL_HOLD: completed relaxation energy missing")
    delta = abs(float(relax_energy) - float(result["energy_ev"]))
    max_force = seg.get("max_movable_force_ev_per_angstrom")
    spec = surface["clean_surface"]
    mechanical_pass = (
        max_force is not None
        and float(max_force) <= float(spec["relaxation"]["force_gate_ev_per_angstrom"])
        and delta <= float(spec["independent_scf_reproduction_gate_ev"])
    )
    bulk_e0 = float(surface["inherited_stage_a_settings"]["bulk_e0_ev_per_atom"])
    excess = (float(result["energy_ev"]) - int(t["layers"]) * bulk_e0) / 2.0
    layer_z = sorted(float(a["position_angstrom"][2]) for a in atoms)
    summary = {
        "schema": "co-cu111-pbe-clean-surface-case-v0.1",
        "status": "COMPLETE" if mechanical_pass else "NUMERICAL_HOLD",
        "case_id": t["case_id"],
        "role": t["role"],
        "layers": int(t["layers"]),
        "vacuum_angstrom": float(t["vacuum_angstrom"]),
        "kmesh": int(t["kmesh"]),
        "cell_angstrom": cell,
        "layer_z_angstrom": layer_z,
        "final_atoms": atoms,
        "relax_energy_ev": float(relax_energy),
        "fixed_geometry_scf_energy_ev": float(result["energy_ev"]),
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": max_force,
        "surface_excess_ev_per_surface_atom": excess,
        "mechanical_pass": mechanical_pass,
        "provenance": {
            "protocol_sha256": sha256(surface_path),
            "stage_a_result_sha256": sha256(Path(args.stage_a_result).resolve()),
            "bundle_sha256": sha256(bundle_path),
            "pw_sha256": sha256(pw),
            "mechanical_recovery_protocol_sha256": p["_sha256"],
            "source_timeout_run_id": p["source_run"]["run_id"],
            "source_artifact_id": t["source_artifact_id"],
            "continuation_mode": p["continuation_contract"]["continuation_mode"],
            "restart_claim": p["continuation_contract"]["restart_claim"],
            "kinetic_inputs_used": False,
            "stage_a_scientific_settings_modified": False,
            "scientific_settings_changed": False,
        },
        "raw_hashes": {
            "relax_input_sha256": seg["raw_hashes"]["relax_input_sha256"],
            "relax_output_sha256": seg["raw_hashes"]["relax_output_sha256"],
            "reproduce_input_sha256": sha256(inp),
            "reproduce_output_sha256": sha256(out),
            "final_recovery_segment_sha256": sha256(seg_path),
        },
    }
    write_json(root / "summary.json", summary)
    write_json(root / "REPRODUCTION_RESULT.json", {
        "schema": REPRO_SCHEMA,
        "status": "COMPLETE",
        "case_id": t["case_id"],
        "summary_sha256": sha256(root / "summary.json"),
        "scientific_settings_changed": False,
        "kinetic_inputs_used": False,
    })
    base.stage_manifest(root, [root / "summary.json", root / "REPRODUCTION_RESULT.json"])
    if tmp.exists():
        shutil.rmtree(tmp)
    print(json.dumps(summary, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="command", required=True)

    p = sp.add_parser("self-test")
    p.add_argument("--recovery-protocol", required=True)
    p.set_defaults(func=command_self_test)

    p = sp.add_parser("verify-source")
    p.add_argument("--recovery-protocol", required=True)
    p.add_argument("--target", required=True, choices=["reference", "audit"])
    p.add_argument("--source-root", required=True)
    p.set_defaults(func=command_verify_source)

    p = sp.add_parser("recover-relax")
    p.add_argument("--recovery-protocol", required=True)
    p.add_argument("--surface-protocol", required=True)
    p.add_argument("--stage-a-result", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--target", required=True, choices=["reference", "audit"])
    p.add_argument("--source-root", required=True)
    p.add_argument("--prior-root")
    p.add_argument("--segment", required=True, type=int)
    p.add_argument("--runtime-cap-s", type=int)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_recover_relax)

    p = sp.add_parser("reproduce")
    p.add_argument("--recovery-protocol", required=True)
    p.add_argument("--surface-protocol", required=True)
    p.add_argument("--stage-a-result", required=True)
    p.add_argument("--bundle", required=True)
    p.add_argument("--pseudo-dir", required=True)
    p.add_argument("--pw", required=True)
    p.add_argument("--target", required=True, choices=["reference", "audit"])
    p.add_argument("--relax-root", required=True)
    p.add_argument("--runtime-cap-s", type=int)
    p.add_argument("--out", required=True)
    p.set_defaults(func=command_reproduce)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
