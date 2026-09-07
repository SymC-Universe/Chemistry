#!/usr/bin/env python3
"""Generic prospectively frozen odd-layer CO/Cu(111) clean-surface extension.

This runner is first instantiated for L19/V40/K36. It reuses the previously
qualified L17 QE clean-stop restart mechanics while keeping rung selection,
initialization, thresholds, and continuation logic in a frozen protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any

SCHEMA = "co-cu111-pbe-surface-convergence-extension-v0.1"
STATUS = "FROZEN_BEFORE_TARGET_RESULTS"
STATE_SCHEMA = "co-cu111-pbe-surface-depth-qe-restart-state-v0.1"
RESULT_SCHEMA = "co-cu111-pbe-surface-depth-convergence-result-v0.1"
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
        raise SystemExit(f"MECHANICAL_HOLD: JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(float(a) - float(b)) <= tol


def import_runtime():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_convergence_l17_v1 as legacy  # type: ignore
    base, old = legacy.import_runtime()
    return legacy, base, old


def protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != SCHEMA or p.get("status") != STATUS:
        raise SystemExit("SCIENTIFIC_HOLD: wrong or unfrozen surface-depth extension protocol")
    if p.get("scientific_scope") != "PROSPECTIVE_ODD_LAYER_DEPTH_EXTENSION_UNDER_FROZEN_STACKING_POLICY":
        raise SystemExit("SCIENTIFIC_HOLD: surface-depth extension scope drift")

    src = p["source_reference"]
    dst = p["extension_audit"]
    if int(dst["layers"]) != int(src["layers"]) + 2:
        raise SystemExit("SCIENTIFIC_HOLD: layer rung rule drift")
    if not close(dst["vacuum_angstrom"], float(src["vacuum_angstrom"]) + 4.0):
        raise SystemExit("SCIENTIFIC_HOLD: vacuum rung rule drift")
    if int(dst["kmesh"]) != int(src["kmesh"]) + 4:
        raise SystemExit("SCIENTIFIC_HOLD: kmesh rung rule drift")
    if src.get("prior_failure_preserved") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: source HOLD provenance removed")
    if src.get("force_pass") is not True or src.get("energy_reproduction_pass") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: source rung is not mechanically/reproducibly admissible")
    if src.get("surface_excess_pass") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: source rung failure was reclassified")

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

    init = p["initialization"]
    source_layers = [int(x) for x in init["source_layers"]]
    target_layers = [int(x) for x in init["target_layers"]]
    nsrc = int(src["layers"])
    ndst = int(dst["layers"])
    if source_layers != [0, 1, nsrc - 2, nsrc - 1]:
        raise SystemExit("SCIENTIFIC_HOLD: source surface-offset layer map drift")
    if target_layers != [0, 1, ndst - 2, ndst - 1]:
        raise SystemExit("SCIENTIFIC_HOLD: target surface-offset layer map drift")
    if init.get("energy_or_surface_excess_used_to_seed") is not False or init.get("initialization_only") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: outcome-dependent target initialization enabled")
    if init.get("symmetry_required") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: symmetry requirement disabled")

    ex = p["execution"]
    if ex.get("checkpoint_mode") != "QE_CLEAN_MAX_SECONDS_EXACT_RESTART":
        raise SystemExit("SCIENTIFIC_HOLD: exact QE restart disabled")
    if int(ex.get("qe_max_seconds_per_segment", -1)) != 16200:
        raise SystemExit("SCIENTIFIC_HOLD: QE checkpoint cadence drift")
    if int(ex.get("github_job_timeout_minutes", -1)) != 360:
        raise SystemExit("SCIENTIFIC_HOLD: job timeout drift")
    if int(ex.get("shutdown_and_artifact_reserve_seconds", -1)) != 5400:
        raise SystemExit("SCIENTIFIC_HOLD: checkpoint upload reserve drift")
    if int(ex.get("maximum_relax_segments", -1)) != 6 or int(ex.get("maximum_scf_segments", -1)) != 4:
        raise SystemExit("SCIENTIFIC_HOLD: finite restart runway drift")
    if ex.get("full_qe_outdir_preserved") is not True or ex.get("exact_restart_required_after_first_segment") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: full exact-restart state preservation disabled")
    if int(ex.get("mpi_ranks", -1)) != 1 or ex.get("execution_mode") != "DIRECT_ONE_RANK":
        raise SystemExit("SCIENTIFIC_HOLD: execution-rank drift")

    dec = p["decision"]
    if dec.get("no_threshold_retuning_after_results") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: threshold-retuning firewall disabled")
    if dec.get("automatic_site_ordering_dispatch") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: downstream auto-dispatch enabled")
    if dec.get("next_rung_authorized_only_if_force_and_reproduction_pass") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: continuation firewall weakened")

    prov = p["provenance"]
    if prov.get("original_l17_failure_preserved_as_failure") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: L17 failure preservation removed")
    for key in ("scientific_settings_changed", "thresholds_changed", "kinetic_inputs_used", "execution_checkpointing_changes_science"):
        if prov.get(key) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: provenance drift: {key}")

    repo = Path(__file__).resolve().parent.parent.parent
    pol = p["stacking_policy"]
    policy_path = repo / pol["path"]
    if not policy_path.is_file() or sha256(policy_path) != pol["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: frozen stacking policy hash mismatch")
    policy = load_json(policy_path)
    if policy.get("status") != "FROZEN_BEFORE_L19_RESULTS":
        raise SystemExit("SCIENTIFIC_HOLD: stacking policy is not prospectively frozen")
    rung = policy["rung_rule"]
    if int(rung.get("layers_increment", -1)) != 2 or not close(rung.get("vacuum_angstrom_increment", -1), 4.0) or int(rung.get("in_plane_kmesh_increment", -1)) != 4:
        raise SystemExit("SCIENTIFIC_HOLD: frozen stacking rung increments drift")
    if policy["continuation_logic"].get("next_rung_requires_new_hash_binding_before_compute") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: next-rung hash-binding firewall disabled")
    if policy["continuation_logic"].get("no_outcome_dependent_threshold_retuning") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: stacking anti-retuning firewall disabled")
    gates = policy["unchanged_scientific_gates"]
    if not close(gates["max_movable_force_ev_per_angstrom"], method["force_gate_ev_per_angstrom"]):
        raise SystemExit("SCIENTIFIC_HOLD: stacking force gate mismatch")
    if not close(gates["independent_scf_reproduction_delta_ev"], method["independent_scf_reproduction_gate_ev"]):
        raise SystemExit("SCIENTIFIC_HOLD: stacking reproduction gate mismatch")
    if not close(gates["adjacent_rung_surface_excess_delta_ev_per_surface_atom"], method["surface_excess_convergence_max_ev_per_surface_atom"]):
        raise SystemExit("SCIENTIFIC_HOLD: stacking surface gate mismatch")
    p["_protocol_sha256"] = sha256(path)
    return p


def verify_runtime(args: argparse.Namespace, p: dict[str, Any]):
    legacy, base, old = import_runtime()
    repo = Path(__file__).resolve().parent.parent.parent
    for key in ("surface_protocol", "pseudopotential_bundle"):
        row = p["frozen_sources"][key]
        target = repo / row["path"]
        if not target.is_file() or sha256(target) != row["sha256"]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source mismatch: {row['path']}")
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
    return legacy, base, old, surface, bundle


def find_exact(root: Path, filename: str) -> Path:
    hits = [x for x in root.rglob(filename) if x.is_file()]
    if len(hits) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {filename}, found {len(hits)}")
    return hits[0]


def verify_source_state(root: Path, p: dict[str, Any]) -> dict[str, Any]:
    src = p["source_reference"]
    path = find_exact(root, src["relax_state_filename"])
    if sha256(path) != src["relax_state_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: source relax-state hash mismatch")
    row = load_json(path)
    checks = {
        "schema": src["relax_state_schema"],
        "stage": "relax",
        "status": "COMPLETE",
        "case_id": src["case_id"],
        "layers": src["layers"],
        "vacuum_angstrom": src["vacuum_angstrom"],
        "kmesh": src["kmesh"],
        "bfgs_finished": True,
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
    }
    for key, value in checks.items():
        if row.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: source relax-state mismatch: {key}")
    atoms = row.get("final_atoms")
    if not isinstance(atoms, list) or len(atoms) != int(src["layers"]):
        raise SystemExit("MECHANICAL_HOLD: source final geometry missing or wrong length")
    if not close(row["max_movable_force_ev_per_angstrom"], src["max_movable_force_ev_per_angstrom"], 1e-12):
        raise SystemExit("MECHANICAL_HOLD: source force numeric drift")
    return row


def verify_source_result(root: Path, p: dict[str, Any]) -> dict[str, Any]:
    src = p["source_reference"]
    path = find_exact(root, src["result_filename"])
    if sha256(path) != src["result_json_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: source result hash mismatch")
    row = load_json(path)
    if row.get("status") != src["required_result_status"] or row.get("case_id") != src["case_id"]:
        raise SystemExit("MECHANICAL_HOLD: source result identity/status drift")
    if row.get("force_pass") is not True or row.get("energy_reproduction_pass") is not True or row.get("surface_excess_pass") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: source gate history reclassified")
    if not close(row["surface_excess_ev_per_surface_atom"], src["surface_excess_ev_per_surface_atom"], 1e-12):
        raise SystemExit("MECHANICAL_HOLD: source surface-excess numeric drift")
    return row


def seed_target(source: dict[str, Any], p: dict[str, Any], base) -> tuple[list[list[float]], list[dict[str, Any]], dict[str, Any]]:
    src = p["source_reference"]
    dst = p["extension_audit"]
    a0 = float(p["frozen_method"]["bulk_lattice_constant_angstrom"])
    _, ideal_src = base.clean_geometry(a0, int(src["layers"]), float(src["vacuum_angstrom"]))
    cell, ideal_dst = base.clean_geometry(a0, int(dst["layers"]), float(dst["vacuum_angstrom"]))
    src_layers = [int(x) for x in p["initialization"]["source_layers"]]
    dst_layers = [int(x) for x in p["initialization"]["target_layers"]]
    offsets = [
        float(source["final_atoms"][i]["position_angstrom"][2]) - float(ideal_src[i]["position_angstrom"][2])
        for i in src_layers
    ]
    if not close(offsets[0], -offsets[3], 1e-10) or not close(offsets[1], -offsets[2], 1e-10):
        raise SystemExit("SCIENTIFIC_HOLD: source relaxation offsets are not symmetric")
    seed = json.loads(json.dumps(ideal_dst))
    for dst_i, delta in zip(dst_layers, offsets):
        seed[dst_i]["position_angstrom"][2] = float(seed[dst_i]["position_angstrom"][2]) + delta
    evidence = {
        "source": "IMMEDIATELY_PRECEDING_RUNG_RELAXED_SURFACE_OFFSETS_ONLY",
        "source_case_id": src["case_id"],
        "source_relax_state_sha256": src["relax_state_sha256"],
        "source_layers": src_layers,
        "target_layers": dst_layers,
        "z_offsets_angstrom": offsets,
        "energy_or_surface_excess_used_to_seed": False,
        "initialization_only": True,
    }
    return cell, seed, evidence


def checkpoint_files(root: Path) -> list[Path]:
    checkpoint = root / "qe_checkpoint"
    if not checkpoint.is_dir():
        raise SystemExit("MECHANICAL_HOLD: missing QE checkpoint directory")
    files = sorted(x for x in checkpoint.rglob("*") if x.is_file())
    if not files:
        raise SystemExit("MECHANICAL_HOLD: empty QE checkpoint directory")
    return files


def write_checkpoint_manifest(root: Path) -> str:
    checkpoint = root / "qe_checkpoint"
    lines = [f"{sha256(path)}  {path.relative_to(checkpoint).as_posix()}" for path in checkpoint_files(root)]
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    manifest.write_text("\n".join(lines) + "\n")
    return sha256(manifest)


def verify_checkpoint_manifest(root: Path, expected_sha: str | None = None) -> str:
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    if not manifest.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing QE checkpoint manifest")
    actual = sha256(manifest)
    if expected_sha is not None and actual != expected_sha:
        raise SystemExit("MECHANICAL_HOLD: QE checkpoint manifest hash drift")
    checkpoint = root / "qe_checkpoint"
    for raw in manifest.read_text().splitlines():
        if not raw.strip():
            continue
        expected, rel = raw.split("  ", 1)
        target = checkpoint / rel
        if not target.is_file() or sha256(target) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: QE checkpoint file drift: {rel}")
    return actual


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
    return text.replace(marker, marker + f" restart_mode='{restart_mode}',\n max_seconds={int(max_seconds)},\n", 1)


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
    if wrapper_timeout:
        raise SystemExit("MECHANICAL_HOLD: external timeout before guaranteed QE checkpoint")
    if rc != 0 or "error in routine" in lower or "mpi_abort" in lower:
        raise SystemExit(f"MECHANICAL_HOLD: pw.x failed before admissible checkpoint, rc={rc}")
    clean_stop = "maximum cpu time exceeded" in lower
    job_done = "job done" in lower
    bfgs_finished = "end of bfgs geometry optimization" in lower or "bfgs converged" in lower
    scf_converged = "convergence has been achieved" in lower or "end of self-consistent calculation" in lower
    complete = (job_done and bfgs_finished) if calculation == "relax" else (job_done and scf_converged and bool(ENERGY_RE.findall(text)))
    if complete:
        status = "COMPLETE"
    elif clean_stop and job_done:
        status = "CHECKPOINT"
    else:
        raise SystemExit("MECHANICAL_HOLD: output is neither complete nor clean max_seconds checkpoint")
    return {
        "status": status,
        "job_done": job_done,
        "clean_max_seconds_stop": clean_stop,
        "bfgs_finished": bfgs_finished,
        "scf_converged": scf_converged,
    }


def state_output_path(root: Path) -> Path:
    return root / "SURFACE_DEPTH_RESTART_STATE.json"


def state_path(root: Path) -> Path:
    path = state_output_path(root)
    if not path.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing target surface-depth restart state")
    return path


def load_prior(root: Path, stage: str, segment: int, p: dict[str, Any]) -> dict[str, Any]:
    row = load_json(state_path(root))
    if row.get("schema") != STATE_SCHEMA or row.get("stage") != stage or int(row.get("segment", -1)) != segment:
        raise SystemExit("MECHANICAL_HOLD: prior target restart sequence mismatch")
    dst = p["extension_audit"]
    if row.get("case_id") != dst["case_id"] or int(row.get("layers", -1)) != int(dst["layers"]):
        raise SystemExit("SCIENTIFIC_HOLD: prior target case drift")
    if row.get("scientific_settings_changed") is not False or row.get("thresholds_changed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: prior target state contaminated")
    if row.get("protocol_sha256") != p.get("_protocol_sha256"):
        raise SystemExit("MECHANICAL_HOLD: prior target state protocol hash mismatch")
    if row.get("status") == "CHECKPOINT":
        verify_checkpoint_manifest(root, row.get("checkpoint_manifest_sha256"))
    elif row.get("status") != "COMPLETE":
        raise SystemExit("MECHANICAL_HOLD: prior target state invalid")
    return row


def runtime_paths(root: Path, stage: str) -> tuple[Path, Path, Path]:
    checkpoint = root / "qe_checkpoint"
    checkpoint.mkdir(parents=True, exist_ok=True)
    return checkpoint, root / f"{stage}.in", root / f"{stage}.out"


def command_preflight(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    source = verify_source_state(Path(args.source_relax_root).resolve(), p)
    result = verify_source_result(Path(args.source_result_root).resolve(), p)
    verify_runtime(args, p)
    out = {
        "schema": "co-cu111-pbe-surface-depth-extension-preflight-v0.1",
        "status": "PASS",
        "source_case_id": source["case_id"],
        "source_result_status": result["status"],
        "target_case_id": p["extension_audit"]["case_id"],
        "target_layers": p["extension_audit"]["layers"],
        "target_vacuum_angstrom": p["extension_audit"]["vacuum_angstrom"],
        "target_kmesh": p["extension_audit"]["kmesh"],
        "source_failure_preserved": True,
        "thresholds_changed": False,
        "exact_restart_required": True,
        "runner_label": p["execution"]["runner_label"],
    }
    write_json(Path(args.out).resolve(), out)
    print(json.dumps(out, indent=2, sort_keys=True))


def command_relax_segment(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    seg = int(args.segment)
    if seg < 1 or seg > int(p["execution"]["maximum_relax_segments"]):
        raise SystemExit("MECHANICAL_HOLD: relaxation segment outside frozen bound")
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    _legacy, base, old, surface, bundle = verify_runtime(args, p)
    source = verify_source_state(Path(args.source_relax_root).resolve(), p)
    cell, seed, seed_evidence = seed_target(source, p, base)
    dst = p["extension_audit"]

    if seg > 1:
        prior_root = Path(args.prior_root).resolve()
        prior = load_prior(prior_root, "relax", seg - 1, p)
        if prior["status"] == "COMPLETE":
            carried = dict(prior)
            carried.update({"segment": seg, "carried_forward_without_recomputation": True, "source_state_sha256": sha256(state_path(prior_root))})
            write_json(state_output_path(out_root), carried)
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        copy_checkpoint(prior_root, out_root)
        restart_mode = "restart"
    else:
        restart_mode = "from_scratch"

    checkpoint, inp, out = runtime_paths(out_root, "relax")
    text = base.qe_input(
        calculation="relax",
        prefix=f"co_cu111_clean_l{int(dst['layers'])}_extension",
        cell=cell,
        atoms=seed,
        kmesh=int(dst["kmesh"]),
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
    final_energy = None
    force = None
    if outcome["status"] == "COMPLETE":
        layers = int(dst["layers"])
        final_atoms = base.parse_positions(raw, layers, seed)
        blocks = old.authoritative_force_blocks(raw, layers)
        if final_atoms is None or not blocks:
            raise SystemExit("MECHANICAL_HOLD: completed target relaxation lacks final geometry/forces")
        _, template = base.clean_geometry(float(p["frozen_method"]["bulk_lattice_constant_angstrom"]), layers, float(dst["vacuum_angstrom"]))
        final_atoms = old.apply_template(final_atoms, template)
        force = old.max_movable_force_ev_a(blocks[-1], final_atoms)
        energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(raw)]
        if not energies:
            raise SystemExit("MECHANICAL_HOLD: completed target relaxation lacks final energy")
        final_energy = energies[-1]
    manifest_sha = write_checkpoint_manifest(out_root)
    state = {
        "schema": STATE_SCHEMA,
        "stage": "relax",
        "status": outcome["status"],
        "segment": seg,
        "case_id": dst["case_id"],
        "layers": int(dst["layers"]),
        "vacuum_angstrom": float(dst["vacuum_angstrom"]),
        "kmesh": int(dst["kmesh"]),
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
        "relax_energy_ev": final_energy,
        "max_movable_force_ev_per_angstrom": force,
        "raw_input_sha256": sha256(inp),
        "raw_output_sha256": sha256(out),
        "protocol_sha256": sha256(pp),
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "source_failure_preserved": True,
        "carried_forward_without_recomputation": False,
    }
    write_json(state_output_path(out_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))


def command_scf_segment(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    seg = int(args.segment)
    if seg < 1 or seg > int(p["execution"]["maximum_scf_segments"]):
        raise SystemExit("MECHANICAL_HOLD: SCF segment outside frozen bound")
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    _legacy, base, _old, surface, bundle = verify_runtime(args, p)
    dst = p["extension_audit"]

    if seg > 1:
        prior_root = Path(args.prior_root).resolve()
        prior = load_prior(prior_root, "scf", seg - 1, p)
        if prior["status"] == "COMPLETE":
            carried = dict(prior)
            carried.update({"segment": seg, "carried_forward_without_recomputation": True, "source_state_sha256": sha256(state_path(prior_root))})
            write_json(state_output_path(out_root), carried)
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
            raise SystemExit("SCIENTIFIC_HOLD: target relaxation did not complete inside frozen restart runway")
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
        prefix=f"co_cu111_clean_l{int(dst['layers'])}_extension_repro",
        cell=cell,
        atoms=atoms,
        kmesh=int(dst["kmesh"]),
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
        "case_id": dst["case_id"],
        "layers": int(dst["layers"]),
        "vacuum_angstrom": float(dst["vacuum_angstrom"]),
        "kmesh": int(dst["kmesh"]),
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
        "protocol_sha256": sha256(pp),
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "source_failure_preserved": True,
        "carried_forward_without_recomputation": False,
    }
    write_json(state_output_path(out_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))


def command_adjudicate(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = protocol(pp)
    source_result = verify_source_result(Path(args.source_result_root).resolve(), p)
    relax = load_prior(Path(args.relax_root).resolve(), "relax", int(p["execution"]["maximum_relax_segments"]), p)
    scf = load_prior(Path(args.scf_root).resolve(), "scf", int(p["execution"]["maximum_scf_segments"]), p)
    if relax["status"] != "COMPLETE":
        raise SystemExit("SCIENTIFIC_HOLD: target relaxation incomplete inside frozen runway")
    if scf["status"] != "COMPLETE" or scf.get("fixed_geometry_scf_energy_ev") is None:
        raise SystemExit("SCIENTIFIC_HOLD: target independent SCF incomplete inside frozen runway")

    dst = p["extension_audit"]
    force = float(relax["max_movable_force_ev_per_angstrom"])
    relax_energy = float(relax["relax_energy_ev"])
    repro_energy = float(scf["fixed_geometry_scf_energy_ev"])
    repro_delta = abs(relax_energy - repro_energy)
    excess = (repro_energy - float(dst["layers"]) * float(p["frozen_method"]["bulk_e0_ev_per_atom"])) / 2.0
    source_excess = float(source_result["surface_excess_ev_per_surface_atom"])
    surface_delta = abs(excess - source_excess)
    force_pass = force <= float(p["frozen_method"]["force_gate_ev_per_angstrom"])
    repro_pass = repro_delta <= float(p["frozen_method"]["independent_scf_reproduction_gate_ev"])
    surface_pass = surface_delta <= float(p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"])
    passed = force_pass and repro_pass and surface_pass
    continue_rung = (not passed) and force_pass and repro_pass and (not surface_pass)
    result = {
        "schema": RESULT_SCHEMA,
        "status": p["decision"]["pass_status"] if passed else p["decision"]["fail_status"],
        "next_gate": p["decision"]["pass_next_gate"] if passed else (p["decision"]["fail_next_gate"] if continue_rung else "SCIENTIFIC_REVIEW_REQUIRED_BEFORE_MORE_DEPTH"),
        "case_id": dst["case_id"],
        "layers": int(dst["layers"]),
        "vacuum_angstrom": float(dst["vacuum_angstrom"]),
        "kmesh": int(dst["kmesh"]),
        "relax_energy_ev": relax_energy,
        "fixed_geometry_scf_energy_ev": repro_energy,
        "energy_reproduction_delta_ev": repro_delta,
        "energy_reproduction_gate_ev": p["frozen_method"]["independent_scf_reproduction_gate_ev"],
        "energy_reproduction_pass": repro_pass,
        "max_movable_force_ev_per_angstrom": force,
        "force_gate_ev_per_angstrom": p["frozen_method"]["force_gate_ev_per_angstrom"],
        "force_pass": force_pass,
        "surface_excess_ev_per_surface_atom": excess,
        "source_surface_excess_ev_per_surface_atom": source_excess,
        "adjacent_rung_delta_ev_per_surface_atom": surface_delta,
        "surface_excess_gate_ev_per_surface_atom": p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"],
        "surface_excess_pass": surface_pass,
        "additional_scientific_rung_authorized": continue_rung,
        "checkpoint_semantics": "QE_CLEAN_MAX_SECONDS_EXACT_RESTART",
        "approximate_restart_used": False,
        "automatic_site_ordering_dispatch": False,
        "source_failure_preserved": True,
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "source_result_sha256": p["source_reference"]["result_json_sha256"],
        "source_relax_state_sha256": p["source_reference"]["relax_state_sha256"],
        "protocol_sha256": sha256(pp),
        "final_relax_state_sha256": sha256(state_path(Path(args.relax_root).resolve())),
        "final_scf_state_sha256": sha256(state_path(Path(args.scf_root).resolve())),
    }
    write_json(Path(args.out).resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        if continue_rung:
            raise SystemExit("SCIENTIFIC_HOLD: adjacent surface-excess gate still open; next frozen odd-depth rung authorized")
        raise SystemExit("SCIENTIFIC_HOLD: force/reproduction/incomplete gate prevents automatic deeper-rung continuation")


def command_self_test(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    ex = p["execution"]
    if int(ex["qe_max_seconds_per_segment"]) + int(ex["shutdown_and_artifact_reserve_seconds"]) != int(ex["github_job_timeout_minutes"]) * 60:
        raise SystemExit("SELF_TEST_FAIL: checkpoint plus reserve does not equal job limit")
    src = p["source_reference"]
    dst = p["extension_audit"]
    print("SURFACE_DEPTH_EXTENSION_SELF_TEST_PASS")
    print(f"SOURCE=L{src['layers']}-V{int(src['vacuum_angstrom'])}-K{src['kmesh']}")
    print(f"TARGET=L{dst['layers']}-V{int(dst['vacuum_angstrom'])}-K{dst['kmesh']}")
    print("QE_MAX_SECONDS=16200")
    print("APPROXIMATE_RESTART_ALLOWED=false")
    print("THRESHOLDS_CHANGED=false")
    print("SOURCE_FAILURE_PRESERVED=true")


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

    sp = sub.add_parser("preflight")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--source-relax-root", required=True)
    sp.add_argument("--source-result-root", required=True)
    sp.add_argument("--out", required=True)
    add_runtime_args(sp)
    sp.set_defaults(func=command_preflight)

    sp = sub.add_parser("relax-segment")
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--source-relax-root", required=True)
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
    sp.add_argument("--source-result-root", required=True)
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
