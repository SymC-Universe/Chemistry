#!/usr/bin/env python3
"""Prospective CO/Cu(111) L17 clean-surface convergence extension.

The scientific contract is frozen in SYSTEM2_PBE_SURFACE_CONVERGENCE_L17_v0.1.json.
Unlike the older geometry-relay recovery path, production continuation here uses
Quantum ESPRESSO's supported clean-stop restart mechanism: max_seconds -> complete
outdir preservation -> restart_mode='restart'. The full QE restart state is hashed
at every segment boundary. No approximate geometry-only or density-only restart is
accepted as production evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any

SCHEMA = "co-cu111-pbe-surface-convergence-l17-v0.1"
STATUS = "FROZEN_BEFORE_L17_RESULTS"
STATE_SCHEMA = "co-cu111-pbe-l17-qe-restart-state-v0.1"
RESULT_SCHEMA = "co-cu111-pbe-l17-convergence-result-v0.1"
RY_TO_EV = 13.605693122994
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
ITER_ENERGY_RE = re.compile(r"^\s*total energy\s+=\s+([-+0-9.Ee]+)\s+Ry", re.MULTILINE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"MECHANICAL_HOLD: JSON root must be an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def find_one(root: Path, name: str) -> Path:
    rows = [p for p in root.rglob(name) if p.is_file()]
    if len(rows) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name} under {root}, found {len(rows)}")
    return rows[0]


def protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != SCHEMA or p.get("status") != STATUS:
        raise SystemExit("SCIENTIFIC_HOLD: wrong or unfrozen L17 protocol")
    if p.get("scientific_scope") != "PROSPECTIVE_SINGLE_RUNG_EXTENSION_AFTER_L15_NUMERICAL_HOLD":
        raise SystemExit("SCIENTIFIC_HOLD: L17 scope drift")
    src = p["source_l15_reference"]
    if src.get("case_id") != "L15-V32-K28-extension-audit" or int(src.get("layers", -1)) != 15:
        raise SystemExit("SCIENTIFIC_HOLD: L15 reference changed")
    if float(src.get("observed_l13_l15_delta_ev_per_surface_atom", 0.0)) <= 0.001 or src.get("prior_gate_pass") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: prior L13-L15 failure not preserved")
    aud = p["extension_audit"]
    if (aud.get("case_id"), int(aud.get("layers", -1)), float(aud.get("vacuum_angstrom", -1)), int(aud.get("kmesh", -1))) != (
        "L17-V36-K32-extension-audit", 17, 36.0, 32
    ):
        raise SystemExit("SCIENTIFIC_HOLD: L17 audit rung changed")
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
    if ex.get("checkpoint_mode") != "QE_CLEAN_MAX_SECONDS_EXACT_RESTART":
        raise SystemExit("SCIENTIFIC_HOLD: exact QE restart contract disabled")
    if ex.get("full_qe_outdir_preserved") is not True or ex.get("exact_restart_required_after_first_segment") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: full checkpoint preservation disabled")
    if int(ex.get("qe_max_seconds_per_segment", -1)) != 16200:
        raise SystemExit("SCIENTIFIC_HOLD: QE checkpoint cadence changed")
    if int(ex.get("github_job_timeout_minutes", -1)) != 360 or int(ex.get("shutdown_and_artifact_reserve_seconds", -1)) != 5400:
        raise SystemExit("SCIENTIFIC_HOLD: runner safety margin changed")
    if int(ex.get("mpi_ranks", -1)) != 1 or ex.get("execution_mode") != "DIRECT_ONE_RANK":
        raise SystemExit("SCIENTIFIC_HOLD: execution rank changed")
    dec = p["decision"]
    if dec.get("no_threshold_retuning_after_results") is not True or dec.get("no_additional_scientific_rung_authorized") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: anti-retuning/finite-stop firewall disabled")
    if dec.get("automatic_site_ordering_dispatch") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: downstream auto-dispatch enabled")
    prov = p["provenance"]
    for key in ("scientific_settings_changed", "thresholds_changed", "kinetic_inputs_used", "execution_checkpointing_changes_science"):
        if prov.get(key) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: provenance drift: {key}")
    return p


def import_runtime():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_site_ordering_v1 as base  # type: ignore
    import pbe_surface_audit_rank_fallback_recovery_v1 as old  # type: ignore
    return base, old


def verify_repo_sources(p: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    for key in ("surface_protocol", "pseudopotential_bundle"):
        row = p["frozen_sources"][key]
        target = repo / row["path"]
        if not target.is_file() or sha256(target) != row["sha256"]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source mismatch: {row['path']}")


def verify_runtime(args: argparse.Namespace, p: dict[str, Any]):
    base, old = import_runtime()
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
    if sha256(bundle_path) != p["frozen_sources"]["pseudopotential_bundle"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pseudopotential bundle hash mismatch")
    bundle = base.verify_bundle(surface, bundle_path, Path(args.pseudo_dir).resolve(), Path(args.pw).resolve())
    if sha256(Path(args.pw).resolve()) != p["frozen_sources"]["pw_x_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pw.x hash mismatch")
    selection = Path(args.selection).resolve()
    if sha256(selection) != p["frozen_sources"]["rank_selection_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: rank-selection hash mismatch")
    sel = load_json(selection)
    if sel.get("selected_execution_mode") != "DIRECT_ONE_RANK" or int(sel.get("selected_mpi_ranks", -1)) != 1:
        raise SystemExit("SCIENTIFIC_HOLD: one-rank execution selection drift")
    return base, old, surface, bundle


def verify_l15(root: Path, p: dict[str, Any]) -> dict[str, Any]:
    summary = find_one(root, "summary.json")
    src = p["source_l15_reference"]
    if sha256(summary) != src["summary_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pinned L15 summary hash mismatch")
    row = load_json(summary)
    checks = {
        "case_id": src["case_id"],
        "layers": src["layers"],
        "vacuum_angstrom": src["vacuum_angstrom"],
        "kmesh": src["kmesh"],
        "mechanical_pass": True,
        "status": "COMPLETE",
    }
    for key, value in checks.items():
        if row.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: L15 reference mismatch: {key}")
    for key in ("fixed_geometry_scf_energy_ev", "max_movable_force_ev_per_angstrom", "energy_reproduction_delta_ev", "surface_excess_ev_per_surface_atom"):
        if not close(row[key], src[key], 1e-12):
            raise SystemExit(f"MECHANICAL_HOLD: L15 reference numeric drift: {key}")
    if len(row.get("final_atoms", [])) != 15:
        raise SystemExit("MECHANICAL_HOLD: L15 reference geometry length mismatch")
    return row


def seed_l17(l15: dict[str, Any], p: dict[str, Any], base) -> tuple[list[list[float]], list[dict[str, Any]], dict[str, Any]]:
    a0 = float(p["frozen_method"]["bulk_lattice_constant_angstrom"])
    _, ideal15 = base.clean_geometry(a0, 15, 32.0)
    cell17, ideal17 = base.clean_geometry(a0, 17, 36.0)
    src_layers = p["initialization"]["source_layers"]
    dst_layers = p["initialization"]["target_layers"]
    offsets = [float(l15["final_atoms"][i]["position_angstrom"][2]) - float(ideal15[i]["position_angstrom"][2]) for i in src_layers]
    if not close(offsets[0], -offsets[3], 1e-10) or not close(offsets[1], -offsets[2], 1e-10):
        raise SystemExit("SCIENTIFIC_HOLD: L15 seed offsets are not symmetric")
    seed = json.loads(json.dumps(ideal17))
    for src, dst, delta in zip(src_layers, dst_layers, offsets):
        _ = src
        seed[dst]["position_angstrom"][2] = float(seed[dst]["position_angstrom"][2]) + delta
    evidence = {
        "source": "PINNED_L15_RELAXED_SURFACE_OFFSETS_ONLY",
        "source_summary_sha256": p["source_l15_reference"]["summary_sha256"],
        "source_layers": src_layers,
        "target_layers": dst_layers,
        "z_offsets_angstrom": offsets,
        "energy_or_surface_excess_used_to_seed": False,
        "initialization_only": True,
    }
    return cell17, seed, evidence


def checkpoint_files(root: Path) -> list[Path]:
    checkpoint = root / "qe_checkpoint"
    if not checkpoint.is_dir():
        raise SystemExit("MECHANICAL_HOLD: missing QE checkpoint directory")
    files = sorted(p for p in checkpoint.rglob("*") if p.is_file())
    if not files:
        raise SystemExit("MECHANICAL_HOLD: empty QE checkpoint directory")
    return files


def write_checkpoint_manifest(root: Path) -> str:
    checkpoint = root / "qe_checkpoint"
    lines = []
    for path in sorted(p for p in checkpoint.rglob("*") if p.is_file()):
        rel = path.relative_to(checkpoint).as_posix()
        lines.append(f"{sha256(path)}  {rel}")
    if not lines:
        raise SystemExit("MECHANICAL_HOLD: cannot manifest empty QE checkpoint")
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    manifest.write_text("\n".join(lines) + "\n")
    return sha256(manifest)


def verify_checkpoint_manifest(root: Path, expected_sha: str | None = None) -> str:
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    if not manifest.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing QE checkpoint manifest")
    if expected_sha is not None and sha256(manifest) != expected_sha:
        raise SystemExit("MECHANICAL_HOLD: QE checkpoint manifest hash drift")
    checkpoint = root / "qe_checkpoint"
    for raw in manifest.read_text().splitlines():
        if not raw.strip():
            continue
        expected, rel = raw.split("  ", 1)
        target = checkpoint / rel
        if not target.is_file() or sha256(target) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: QE checkpoint file drift: {rel}")
    return sha256(manifest)


def copy_checkpoint(source: Path, target: Path) -> None:
    verify_checkpoint_manifest(source)
    src = source / "qe_checkpoint"
    dst = target / "qe_checkpoint"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def add_control_fields(text: str, restart_mode: str, max_seconds: int) -> str:
    marker = "&CONTROL\n"
    if marker not in text:
        raise SystemExit("MECHANICAL_HOLD: QE input lacks CONTROL namelist")
    insert = f" restart_mode='{restart_mode}',\n max_seconds={int(max_seconds)},\n"
    return text.replace(marker, marker + insert, 1)


def run_pw(pw: Path, inp: Path, out: Path, external_timeout_s: int) -> tuple[int, bool, float]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    start = time.time()
    wrapper_timeout = False
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        try:
            rc = proc.wait(timeout=external_timeout_s)
        except subprocess.TimeoutExpired:
            wrapper_timeout = True
            proc.terminate()
            try:
                rc = proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait(timeout=30)
    return int(rc), wrapper_timeout, time.time() - start


def classify_output(text: str, calculation: str, rc: int, wrapper_timeout: bool) -> dict[str, Any]:
    lower = text.lower()
    fatal = "error in routine" in lower or "mpi_abort" in lower
    if wrapper_timeout:
        raise SystemExit("MECHANICAL_HOLD: external timeout occurred before a guaranteed QE checkpoint")
    if rc != 0 or fatal:
        raise SystemExit(f"MECHANICAL_HOLD: pw.x failed before admissible checkpoint, rc={rc}")
    clean_max_stop = "maximum cpu time exceeded" in lower
    job_done = "job done" in lower
    bfgs_finished = "end of bfgs geometry optimization" in lower or "bfgs converged" in lower
    scf_converged = "convergence has been achieved" in lower or "end of self-consistent calculation" in lower
    if calculation == "relax":
        complete = job_done and bfgs_finished
    else:
        complete = job_done and scf_converged and bool(ENERGY_RE.findall(text))
    if complete:
        status = "COMPLETE"
    elif clean_max_stop and job_done:
        status = "CHECKPOINT"
    else:
        raise SystemExit("MECHANICAL_HOLD: output is neither complete nor a clean max_seconds checkpoint")
    return {
        "status": status,
        "job_done": job_done,
        "clean_max_seconds_stop": clean_max_stop,
        "bfgs_finished": bfgs_finished,
        "scf_converged": scf_converged,
    }


def state_path(root: Path) -> Path:
    path = root / "L17_RESTART_STATE.json"
    if not path.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing L17 restart state")
    return path


def load_prior(root: Path, stage: str, segment: int, p: dict[str, Any]) -> dict[str, Any]:
    row = load_json(state_path(root))
    if row.get("schema") != STATE_SCHEMA or row.get("stage") != stage or int(row.get("segment", -1)) != segment:
        raise SystemExit("MECHANICAL_HOLD: prior L17 restart state sequence mismatch")
    if row.get("scientific_settings_changed") is not False or row.get("thresholds_changed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: prior restart state contaminated")
    if row.get("status") == "CHECKPOINT":
        if row.get("restart_mode") not in {"from_scratch", "restart"}:
            raise SystemExit("MECHANICAL_HOLD: prior restart-mode provenance missing")
        verify_checkpoint_manifest(root, row.get("checkpoint_manifest_sha256"))
    elif row.get("status") != "COMPLETE":
        raise SystemExit("MECHANICAL_HOLD: prior L17 state is neither CHECKPOINT nor COMPLETE")
    if row.get("case_id") != p["extension_audit"]["case_id"]:
        raise SystemExit("SCIENTIFIC_HOLD: prior L17 case drift")
    return row


def runtime_paths(root: Path, stage: str) -> tuple[Path, Path, Path]:
    checkpoint = root / "qe_checkpoint"
    checkpoint.mkdir(parents=True, exist_ok=True)
    inp = root / f"{stage}.in"
    out = root / f"{stage}.out"
    return checkpoint, inp, out


def command_relax_segment(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    seg = int(args.segment)
    max_seg = int(p["execution"]["maximum_relax_segments"])
    if seg < 1 or seg > max_seg:
        raise SystemExit("MECHANICAL_HOLD: relaxation segment outside frozen bound")
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    base, old, surface, bundle = verify_runtime(args, p)
    cell, seed, seed_evidence = seed_l17(verify_l15(Path(args.l15_root).resolve(), p), p, base)

    if seg > 1:
        prior_root = Path(args.prior_root).resolve()
        prior = load_prior(prior_root, "relax", seg - 1, p)
        if prior["status"] == "COMPLETE":
            carried = dict(prior)
            carried.update({"segment": seg, "carried_forward_without_recomputation": True, "source_state_sha256": sha256(state_path(prior_root))})
            write_json(state_path(out_root), carried)
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        copy_checkpoint(prior_root, out_root)
        restart_mode = "restart"
    else:
        restart_mode = "from_scratch"

    checkpoint, inp, out = runtime_paths(out_root, "relax")
    text = base.qe_input(
        calculation="relax",
        prefix="co_cu111_clean_l17_extension",
        cell=cell,
        atoms=seed,
        kmesh=32,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=checkpoint,
    )
    text = add_control_fields(text, restart_mode, int(p["execution"]["qe_max_seconds_per_segment"]))
    inp.write_text(text)
    rc, wrapper_timeout, elapsed = run_pw(Path(args.pw).resolve(), inp, out, int(p["execution"]["qe_max_seconds_per_segment"]) + 3600)
    raw = out.read_text(errors="replace")
    outcome = classify_output(raw, "relax", rc, wrapper_timeout)

    final_atoms = None
    final_energy_ev = None
    force = None
    if outcome["status"] == "COMPLETE":
        final_atoms = base.parse_positions(raw, 17, seed)
        blocks = old.authoritative_force_blocks(raw, 17)
        if final_atoms is None or not blocks:
            raise SystemExit("MECHANICAL_HOLD: completed L17 relaxation lacks final geometry/forces")
        _, template = base.clean_geometry(float(p["frozen_method"]["bulk_lattice_constant_angstrom"]), 17, 36.0)
        final_atoms = old.apply_template(final_atoms, template)
        force = old.max_movable_force_ev_a(blocks[-1], final_atoms)
        energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(raw)]
        if not energies:
            raise SystemExit("MECHANICAL_HOLD: completed L17 relaxation lacks final energy")
        final_energy_ev = energies[-1]
    manifest_sha = write_checkpoint_manifest(out_root)
    state = {
        "schema": STATE_SCHEMA,
        "stage": "relax",
        "status": outcome["status"],
        "segment": seg,
        "case_id": p["extension_audit"]["case_id"],
        "layers": 17,
        "vacuum_angstrom": 36.0,
        "kmesh": 32,
        "restart_mode": restart_mode,
        "checkpoint_semantics": "QE_CLEAN_MAX_SECONDS_EXACT_RESTART",
        "checkpoint_manifest_sha256": manifest_sha,
        "full_qe_outdir_preserved": True,
        "wrapper_timeout": wrapper_timeout,
        "pw_returncode": rc,
        "elapsed_s": elapsed,
        "job_done": outcome["job_done"],
        "clean_max_seconds_stop": outcome["clean_max_seconds_stop"],
        "bfgs_finished": outcome["bfgs_finished"],
        "cell_angstrom": cell,
        "seed_evidence": seed_evidence,
        "final_atoms": final_atoms,
        "relax_energy_ev": final_energy_ev,
        "max_movable_force_ev_per_angstrom": force,
        "raw_input_sha256": sha256(inp),
        "raw_output_sha256": sha256(out),
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "carried_forward_without_recomputation": False,
    }
    write_json(state_path(out_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))


def command_scf_segment(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    seg = int(args.segment)
    max_seg = int(p["execution"]["maximum_scf_segments"])
    if seg < 1 or seg > max_seg:
        raise SystemExit("MECHANICAL_HOLD: SCF segment outside frozen bound")
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    base, _old, surface, bundle = verify_runtime(args, p)

    if seg > 1:
        prior_root = Path(args.prior_root).resolve()
        prior = load_prior(prior_root, "scf", seg - 1, p)
        if prior["status"] == "COMPLETE":
            carried = dict(prior)
            carried.update({"segment": seg, "carried_forward_without_recomputation": True, "source_state_sha256": sha256(state_path(prior_root))})
            write_json(state_path(out_root), carried)
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        copy_checkpoint(prior_root, out_root)
        restart_mode = "restart"
        atoms = prior["fixed_atoms"]
        cell = prior["cell_angstrom"]
        relax_energy = float(prior["relax_energy_ev"])
        force = float(prior["max_movable_force_ev_per_angstrom"])
    else:
        relax_root = Path(args.relax_root).resolve()
        relax = load_prior(relax_root, "relax", int(p["execution"]["maximum_relax_segments"]), p)
        if relax["status"] != "COMPLETE" or relax.get("final_atoms") is None or relax.get("relax_energy_ev") is None or relax.get("max_movable_force_ev_per_angstrom") is None:
            raise SystemExit("SCIENTIFIC_HOLD: L17 relaxation did not complete inside the frozen exact-restart runway")
        atoms = json.loads(json.dumps(relax["final_atoms"]))
        for atom in atoms:
            atom["flags"] = [0, 0, 0]
        cell = relax["cell_angstrom"]
        relax_energy = float(relax["relax_energy_ev"])
        force = float(relax["max_movable_force_ev_per_angstrom"])
        restart_mode = "from_scratch"

    checkpoint, inp, out = runtime_paths(out_root, "scf")
    text = base.qe_input(
        calculation="scf",
        prefix="co_cu111_clean_l17_extension_repro",
        cell=cell,
        atoms=atoms,
        kmesh=32,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=checkpoint,
    )
    text = add_control_fields(text, restart_mode, int(p["execution"]["qe_max_seconds_per_segment"]))
    inp.write_text(text)
    rc, wrapper_timeout, elapsed = run_pw(Path(args.pw).resolve(), inp, out, int(p["execution"]["qe_max_seconds_per_segment"]) + 3600)
    raw = out.read_text(errors="replace")
    outcome = classify_output(raw, "scf", rc, wrapper_timeout)
    energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(raw)]
    final_energy = energies[-1] if outcome["status"] == "COMPLETE" and energies else None
    last_iter = [float(x) * RY_TO_EV for x in ITER_ENERGY_RE.findall(raw)]
    manifest_sha = write_checkpoint_manifest(out_root)
    state = {
        "schema": STATE_SCHEMA,
        "stage": "scf",
        "status": outcome["status"],
        "segment": seg,
        "case_id": p["extension_audit"]["case_id"],
        "layers": 17,
        "vacuum_angstrom": 36.0,
        "kmesh": 32,
        "restart_mode": restart_mode,
        "checkpoint_semantics": "QE_CLEAN_MAX_SECONDS_EXACT_RESTART",
        "checkpoint_manifest_sha256": manifest_sha,
        "full_qe_outdir_preserved": True,
        "wrapper_timeout": wrapper_timeout,
        "pw_returncode": rc,
        "elapsed_s": elapsed,
        "job_done": outcome["job_done"],
        "clean_max_seconds_stop": outcome["clean_max_seconds_stop"],
        "scf_converged": outcome["scf_converged"],
        "cell_angstrom": cell,
        "fixed_atoms": atoms,
        "relax_energy_ev": relax_energy,
        "max_movable_force_ev_per_angstrom": force,
        "fixed_geometry_scf_energy_ev": final_energy,
        "last_reported_energy_ev": final_energy if final_energy is not None else (last_iter[-1] if last_iter else None),
        "raw_input_sha256": sha256(inp),
        "raw_output_sha256": sha256(out),
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "carried_forward_without_recomputation": False,
    }
    write_json(state_path(out_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))


def command_adjudicate(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    l15 = verify_l15(Path(args.l15_root).resolve(), p)
    relax = load_prior(Path(args.relax_root).resolve(), "relax", int(p["execution"]["maximum_relax_segments"]), p)
    scf = load_prior(Path(args.scf_root).resolve(), "scf", int(p["execution"]["maximum_scf_segments"]), p)
    if relax["status"] != "COMPLETE":
        raise SystemExit("SCIENTIFIC_HOLD: L17 relaxation did not complete within frozen exact-restart runway")
    if scf["status"] != "COMPLETE" or scf.get("fixed_geometry_scf_energy_ev") is None:
        raise SystemExit("SCIENTIFIC_HOLD: L17 independent SCF did not complete within frozen exact-restart runway")
    force = float(relax["max_movable_force_ev_per_angstrom"])
    relax_energy = float(relax["relax_energy_ev"])
    repro_energy = float(scf["fixed_geometry_scf_energy_ev"])
    repro_delta = abs(relax_energy - repro_energy)
    excess = (repro_energy - 17.0 * float(p["frozen_method"]["bulk_e0_ev_per_atom"])) / 2.0
    surface_delta = abs(excess - float(l15["surface_excess_ev_per_surface_atom"]))
    force_pass = force <= float(p["frozen_method"]["force_gate_ev_per_angstrom"])
    repro_pass = repro_delta <= float(p["frozen_method"]["independent_scf_reproduction_gate_ev"])
    surface_pass = surface_delta <= float(p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"])
    passed = force_pass and repro_pass and surface_pass
    result = {
        "schema": RESULT_SCHEMA,
        "status": "PASS" if passed else p["decision"]["fail_status"],
        "next_gate": p["decision"]["pass_next_gate"] if passed else "STOP_CURRENT_CONTRACT",
        "case_id": p["extension_audit"]["case_id"],
        "layers": 17,
        "vacuum_angstrom": 36.0,
        "kmesh": 32,
        "relax_energy_ev": relax_energy,
        "fixed_geometry_scf_energy_ev": repro_energy,
        "energy_reproduction_delta_ev": repro_delta,
        "energy_reproduction_gate_ev": p["frozen_method"]["independent_scf_reproduction_gate_ev"],
        "energy_reproduction_pass": repro_pass,
        "max_movable_force_ev_per_angstrom": force,
        "force_gate_ev_per_angstrom": p["frozen_method"]["force_gate_ev_per_angstrom"],
        "force_pass": force_pass,
        "surface_excess_ev_per_surface_atom": excess,
        "l15_surface_excess_ev_per_surface_atom": l15["surface_excess_ev_per_surface_atom"],
        "l15_l17_delta_ev_per_surface_atom": surface_delta,
        "surface_excess_gate_ev_per_surface_atom": p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"],
        "surface_excess_pass": surface_pass,
        "checkpoint_semantics": "QE_CLEAN_MAX_SECONDS_EXACT_RESTART",
        "full_qe_outdir_preserved_each_active_segment": True,
        "approximate_restart_used": False,
        "automatic_site_ordering_dispatch": False,
        "additional_scientific_rung_authorized": False,
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "source_l15_summary_sha256": p["source_l15_reference"]["summary_sha256"],
        "protocol_sha256": sha256(pp),
        "final_relax_state_sha256": sha256(state_path(Path(args.relax_root).resolve())),
        "final_scf_state_sha256": sha256(state_path(Path(args.scf_root).resolve())),
    }
    out = Path(args.out).resolve()
    write_json(out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("SCIENTIFIC_HOLD: L17 failed one or more unchanged frozen numerical gates")


def command_self_test(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    ex = p["execution"]
    if int(ex["qe_max_seconds_per_segment"]) + int(ex["shutdown_and_artifact_reserve_seconds"]) != int(ex["github_job_timeout_minutes"]) * 60:
        raise SystemExit("SELF_TEST_FAIL: checkpoint plus reserve does not equal GitHub job limit")
    print("L17_EXACT_RESTART_PROTOCOL_SELF_TEST_PASS")
    print("L17_V36_K32_FROZEN=true")
    print("QE_MAX_SECONDS=16200")
    print("GITHUB_JOB_TIMEOUT_SECONDS=21600")
    print("CLEAN_STOP_AND_UPLOAD_RESERVE_SECONDS=5400")
    print("APPROXIMATE_RESTART_ALLOWED=false")
    print("THRESHOLDS_CHANGED=false")


def add_runtime_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--surface-protocol", required=True)
    sp.add_argument("--stage-a-result", required=True)
    sp.add_argument("--bundle", required=True)
    sp.add_argument("--pseudo-dir", required=True)
    sp.add_argument("--pw", required=True)
    sp.add_argument("--selection", required=True)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("self-test")
    sp.add_argument("--protocol", required=True)
    sp.set_defaults(func=command_self_test)
    sp = sub.add_parser("relax-segment")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--l15-root", required=True)
    sp.add_argument("--prior-root")
    sp.add_argument("--segment", type=int, required=True)
    sp.add_argument("--out", required=True)
    add_runtime_args(sp)
    sp.set_defaults(func=command_relax_segment)
    sp = sub.add_parser("scf-segment")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--relax-root")
    sp.add_argument("--prior-root")
    sp.add_argument("--segment", type=int, required=True)
    sp.add_argument("--out", required=True)
    add_runtime_args(sp)
    sp.set_defaults(func=command_scf_segment)
    sp = sub.add_parser("adjudicate")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--l15-root", required=True)
    sp.add_argument("--relax-root", required=True)
    sp.add_argument("--scf-root", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=command_adjudicate)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
