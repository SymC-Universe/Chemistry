#!/usr/bin/env python3
"""Mechanical continuation helper for the frozen CO/Cu(111) L15 reproduction SCF.

This helper changes no scientific setting or acceptance threshold. It provisions
bounded 5.5 h SCF cells and, when a cell ends before JOB DONE, carries the last
QE SCF density state into the next cell as a warm-start state. For the frozen
PAW calculation that state necessarily includes ``paw.txt`` as well as the
charge density and XML schema. Exact QE restart is not claimed. A completed
result is carried through later provisioned cells without recomputation.
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

CELL_RUNTIME_S = 19800
MIN_CELLS = 5
PREFIX = "co_cu111_clean_l15_extension_repro"
STATE_SCHEMA = "co-cu111-l15-scf-continuation-state-v0.2"
LEGACY_STATE_SCHEMA = "co-cu111-l15-scf-continuation-state-v0.1"
FINAL_ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
ITERATION_ENERGY_RE = re.compile(r"^\s*total energy\s+=\s+([-+0-9.Ee]+)\s+Ry", re.MULTILINE)
REQUIRED_DENSITY_STATE_FILES = ("data-file-schema.xml", "paw.txt")


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


def import_extension():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_convergence_extension_v1 as ext  # type: ignore
    return ext


def policy(path: Path) -> dict[str, Any]:
    row = load_json(path)
    if row.get("schema") != "symc-compute-continuation-policy-v0.1":
        raise SystemExit("MECHANICAL_HOLD: wrong continuation policy schema")
    if row.get("status") != "ACTIVE_MECHANICAL_EXECUTION_POLICY":
        raise SystemExit("MECHANICAL_HOLD: continuation policy is not active")
    if int(row.get("minimum_continuation_cells", -1)) < MIN_CELLS:
        raise SystemExit("MECHANICAL_HOLD: continuation policy provides fewer than five cells")
    if int(row.get("cell_compute_runtime_seconds", -1)) < CELL_RUNTIME_S:
        raise SystemExit("MECHANICAL_HOLD: continuation cell runtime is below 5.5 hours")
    if row.get("scientific_effect", {}).get("scientific_settings_changed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: continuation policy permits scientific drift")
    if row.get("scientific_effect", {}).get("thresholds_changed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: continuation policy permits threshold drift")
    return row


def state_path(root: Path) -> Path:
    path = root / "SCF_CONTINUATION_STATE.json"
    if not path.is_file():
        raise SystemExit(f"MECHANICAL_HOLD: missing continuation state: {path}")
    return path


def preserved_relaxation_seed(root: Path, protocol_path: Path, p: dict[str, Any]) -> dict[str, Any]:
    """Recover only frozen L15 geometry/energy/force metadata from a pinned prior state."""
    path = state_path(root)
    state = load_json(path)
    if state.get("schema") not in {LEGACY_STATE_SCHEMA, STATE_SCHEMA}:
        raise SystemExit("MECHANICAL_HOLD: wrong preserved L15 seed-state schema")
    if state.get("status") != "CONTINUE" or int(state.get("cell", -1)) != 1:
        raise SystemExit("MECHANICAL_HOLD: preserved L15 seed is not the fresh-start cell-1 checkpoint")
    if int(state.get("total_cells_provisioned", 0)) < MIN_CELLS:
        raise SystemExit("MECHANICAL_HOLD: preserved L15 seed was not provisioned with five cells")
    audit = p["extension_audit"]
    expected_case = (
        audit["case_id"],
        int(audit["layers"]),
        float(audit["vacuum_angstrom"]),
        int(audit["kmesh"]),
    )
    actual_case = (
        state.get("case_id"),
        int(state.get("layers", -1)),
        float(state.get("vacuum_angstrom", -1)),
        int(state.get("kmesh", -1)),
    )
    if actual_case != expected_case:
        raise SystemExit("SCIENTIFIC_HOLD: preserved L15 seed case drift")
    for flag in ("scientific_settings_changed", "thresholds_changed", "geometry_changed", "method_changed", "rank_changed", "kinetic_inputs_used"):
        if state.get(flag) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: preserved L15 seed flag drift: {flag}")
    warm_started = state.get(
        "warm_started_from_prior_density_state",
        state.get("warm_started_from_prior_charge_density"),
    )
    if warm_started is not False or state.get("continuation_semantics") != "FROZEN_GEOMETRY_FRESH_START":
        raise SystemExit("SCIENTIFIC_HOLD: preserved L15 seed did not originate from a fresh reproduction start")
    if state.get("surface_convergence_extension_protocol_sha256") != sha256(protocol_path):
        raise SystemExit("SCIENTIFIC_HOLD: preserved L15 seed protocol hash drift")
    if state.get("pw_returncode") != 0 or state.get("wrapper_timeout") is not False:
        raise SystemExit("MECHANICAL_HOLD: preserved L15 seed did not end at a clean QE stop")
    atoms = state.get("final_atoms")
    if not isinstance(atoms, list) or len(atoms) != 15:
        raise SystemExit("MECHANICAL_HOLD: preserved L15 seed lacks the 15-atom relaxed geometry")
    for key in ("relax_energy_ev", "max_movable_force_ev_per_angstrom"):
        try:
            value = float(state[key])
        except (KeyError, TypeError, ValueError):
            raise SystemExit(f"MECHANICAL_HOLD: preserved L15 seed lacks numeric {key}") from None
        if not math.isfinite(value):
            raise SystemExit(f"MECHANICAL_HOLD: preserved L15 seed has non-finite {key}")
    if int(state.get("completion_segment", 0)) < 1:
        raise SystemExit("MECHANICAL_HOLD: preserved L15 seed lacks a valid relaxation completion segment")
    return state


def density_state_files(save_dir: Path) -> list[Path]:
    """Return the minimal complete PAW density warm-start state, fail closed."""
    if not save_dir.is_dir():
        raise SystemExit("MECHANICAL_HOLD: missing QE density-state directory")
    files: list[Path] = []
    for name in REQUIRED_DENSITY_STATE_FILES:
        path = save_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"MECHANICAL_HOLD: QE density state lacks required {name}")
        files.append(path)
    charge = sorted(p for p in save_dir.glob("charge-density*") if p.is_file() and p.stat().st_size > 0)
    if not charge:
        raise SystemExit("MECHANICAL_HOLD: QE density state lacks charge density")
    files.extend(charge)
    return files


def copy_density_state(source_root: Path, target_tmp: Path) -> list[str]:
    src_save = source_root / "density_state" / f"{PREFIX}.save"
    if not src_save.is_dir():
        raise SystemExit("MECHANICAL_HOLD: previous continuation state lacks QE density-state directory")
    targets = density_state_files(src_save)
    dst_save = target_tmp / f"{PREFIX}.save"
    dst_save.mkdir(parents=True, exist_ok=True)
    for src in targets:
        shutil.copy2(src, dst_save / src.name)
    return [src.name for src in targets]


def preserve_density_state(tmp: Path, root: Path) -> list[str]:
    src_save = tmp / f"{PREFIX}.save"
    if not src_save.is_dir():
        raise SystemExit("MECHANICAL_HOLD: QE continuation cell produced no save directory")
    targets = density_state_files(src_save)
    dst_save = root / "density_state" / f"{PREFIX}.save"
    dst_save.mkdir(parents=True, exist_ok=True)
    for src in targets:
        shutil.copy2(src, dst_save / src.name)
    return [src.name for src in targets]


def interpret_pw_output(output: str, returncode: int, wrapper_timeout: bool) -> dict[str, Any]:
    """Classify only a converged result or a clean max_seconds checkpoint as valid."""
    final_energies = [float(value) for value in FINAL_ENERGY_RE.findall(output)]
    iteration_energies = [float(value) for value in ITERATION_ENERGY_RE.findall(output)]
    job_done = "JOB DONE." in output
    scf_converged = (
        "convergence has been achieved" in output.lower()
        or "end of self-consistent calculation" in output.lower()
    )
    clean_max_seconds_stop = "maximum cpu time exceeded" in output.lower()
    fatal_marker = "error in routine" in output.lower() or "mpi_abort" in output.lower()

    if wrapper_timeout:
        raise SystemExit("MECHANICAL_HOLD: external wrapper timeout is not a valid QE checkpoint")
    if returncode != 0 or fatal_marker:
        raise SystemExit(f"MECHANICAL_HOLD: QE continuation cell failed with return code {returncode}")
    if job_done and scf_converged and final_energies:
        status = "COMPLETE"
    elif job_done and clean_max_seconds_stop and not scf_converged:
        status = "CONTINUE"
    else:
        raise SystemExit("MECHANICAL_HOLD: QE output is neither converged nor a clean max_seconds stop")

    return {
        "status": status,
        "job_done": job_done,
        "scf_converged": scf_converged,
        "clean_max_seconds_stop": clean_max_seconds_stop,
        "final_energy_ry": final_energies[-1] if final_energies else None,
        "last_iteration_energy_ry": iteration_energies[-1] if iteration_energies else None,
    }


def run_pw(pw: Path, inp: Path, out: Path) -> tuple[int, bool, float]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    start = time.time()
    wrapper_timeout = False
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        try:
            rc = proc.wait(timeout=CELL_RUNTIME_S + 300)
        except subprocess.TimeoutExpired:
            wrapper_timeout = True
            proc.terminate()
            try:
                rc = proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait(timeout=30)
    return int(rc), wrapper_timeout, time.time() - start


def command_cell(args: argparse.Namespace) -> None:
    policy(Path(args.policy).resolve())
    cell = int(args.cell)
    if cell < 1 or cell < 1 or cell > int(args.total_cells):
        raise SystemExit("MECHANICAL_HOLD: continuation cell outside declared range")
    if int(args.total_cells) < MIN_CELLS:
        raise SystemExit("MECHANICAL_HOLD: fewer than five continuation cells were provisioned")

    ext = import_extension()
    pp = Path(args.protocol).resolve()
    p = ext.protocol(pp)
    p["_protocol_path"] = str(pp)
    max_seg = int(p["execution"]["maximum_continuation_segments"])

    base, old, _relay, surface, bundle, _sel = ext.runtime_context(args, p)
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=True)

    prior_state: dict[str, Any] | None = None
    relaxation_source_mode = "NATIVE_RELAXATION_ARTIFACT"
    relaxation_seed_state_sha256: str | None = None
    carried_files: list[str] = []
    if args.state_in:
        if args.prior_root or args.seed_state_root:
            raise SystemExit("MECHANICAL_HOLD: continued cells may specify only --state-in")
        source = Path(args.state_in).resolve()
        prior_state = load_json(state_path(source))
        if prior_state.get("schema") != STATE_SCHEMA:
            raise SystemExit("MECHANICAL_HOLD: wrong continuation state schema")
        if int(prior_state.get("cell", -1)) != cell - 1:
            raise SystemExit("MECHANICAL_HOLD: continuation state cell sequence is broken")
        if prior_state.get("scientific_settings_changed") is not False or prior_state.get("thresholds_changed") is not False:
            raise SystemExit("SCIENTIFIC_HOLD: continuation state is scientifically contaminated")
        if prior_state.get("status") == "COMPLETE":
            carried = dict(prior_state)
            carried.update({
                "cell": cell,
                "carried_forward_without_recomputation": True,
                "source_state_sha256": sha256(state_path(source)),
            })
            write_json(root / "SCF_CONTINUATION_STATE.json", carried)
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        if prior_state.get("status") != "CONTINUE":
            raise SystemExit("MECHANICAL_HOLD: prior continuation state is neither CONTINUE nor COMPLETE")
        atoms = prior_state["final_atoms"]
        cell_matrix = prior_state["cell_angstrom"]
        relax_energy = float(prior_state["relax_energy_ev"])
        force = float(prior_state["max_movable_force_ev_per_angstrom"])
        completion_segment = int(prior_state["completion_segment"])
        relaxation_source_mode = str(prior_state.get("relaxation_source_mode", "UNKNOWN_PRIOR_STATE_SOURCE"))
        relaxation_seed_state_sha256 = prior_state.get("relaxation_seed_state_sha256")
    else:
        if bool(args.prior_root) == bool(args.seed_state_root):
            raise SystemExit("MECHANICAL_HOLD: initial cell requires exactly one L15 relaxation source")
        if args.seed_state_root:
            seed_root = Path(args.seed_state_root).resolve()
            seg = preserved_relaxation_seed(seed_root, pp, p)
            atoms = json.loads(json.dumps(seg["final_atoms"]))
            relax_energy = float(seg["relax_energy_ev"])
            force = float(seg["max_movable_force_ev_per_angstrom"])
            completion_segment = int(seg["completion_segment"])
            relaxation_source_mode = "PINNED_DERIVED_STATE_METADATA_ONLY"
            relaxation_seed_state_sha256 = sha256(state_path(seed_root))
        else:
            prior_root = Path(args.prior_root).resolve()
            seg, _seg_path = ext.verify_prior_segment(prior_root, p, max_seg)
            if seg.get("status") != "RELAX_COMPLETE" or not seg.get("final_atoms"):
                raise SystemExit("MECHANICAL_HOLD: source L15 relaxation is not complete")
            atoms = json.loads(json.dumps(seg["final_atoms"]))
            relax_energy = float(seg["energy_ev"])
            force = float(seg["latest_authoritative_max_movable_force_ev_per_angstrom"])
            completion_segment = int(seg["completion_segment"])
        cell_matrix, _template = base.clean_geometry(
            float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 15, 32.0
        )

    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]

    work = root / "work"
    tmp = work / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    warm_started = prior_state is not None
    if warm_started:
        carried_files = copy_density_state(Path(args.state_in).resolve(), tmp)

    inp = work / f"cell_{cell:02d}.in"
    out = work / f"cell_{cell:02d}.out"
    text = base.qe_input(
        calculation="scf",
        prefix=PREFIX,
        cell=cell_matrix,
        atoms=fixed,
        kmesh=28,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=tmp,
    )
    text = text.replace(" verbosity='high',\n", f" verbosity='high',\n max_seconds={CELL_RUNTIME_S},\n")
    if warm_started:
        text = text.replace("&ELECTRONS\n", "&ELECTRONS\n startingpot='file',\n startingwfc='atomic+random',\n")
    inp.write_text(text)

    rc, wrapper_timeout, elapsed = run_pw(Path(args.pw).resolve(), inp, out)
    output = out.read_text(errors="replace") if out.is_file() else ""
    outcome = interpret_pw_output(output, rc, wrapper_timeout)
    final_energy_ev = (
        float(outcome["final_energy_ry"]) * base.RY_TO_EV
        if outcome["final_energy_ry"] is not None
        else None
    )
    last_iteration_energy_ev = (
        float(outcome["last_iteration_energy_ry"]) * base.RY_TO_EV
        if outcome["last_iteration_energy_ry"] is not None
        else None
    )

    density_state_files_preserved: list[str] = []
    if outcome["status"] == "CONTINUE":
        density_state_files_preserved = preserve_density_state(tmp, root)

    state = {
        "schema": STATE_SCHEMA,
        "status": outcome["status"],
        "cell": cell,
        "total_cells_provisioned": int(args.total_cells),
        "cell_runtime_budget_seconds": CELL_RUNTIME_S,
        "minimum_total_runway_seconds": int(args.total_cells) * CELL_RUNTIME_S,
        "case_id": p["extension_audit"]["case_id"],
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "cell_angstrom": cell_matrix,
        "final_atoms": atoms,
        "relax_energy_ev": relax_energy,
        "max_movable_force_ev_per_angstrom": force,
        "completion_segment": completion_segment,
        "relaxation_source_mode": relaxation_source_mode,
        "relaxation_seed_state_sha256": relaxation_seed_state_sha256,
        "fixed_geometry_scf_energy_ev": final_energy_ev,
        "last_reported_energy_ev": final_energy_ev if final_energy_ev is not None else last_iteration_energy_ev,
        "pw_returncode": rc,
        "wrapper_timeout": wrapper_timeout,
        "job_done": outcome["job_done"],
        "scf_converged": outcome["scf_converged"],
        "clean_max_seconds_stop": outcome["clean_max_seconds_stop"],
        "elapsed_s": elapsed,
        "warm_started_from_prior_density_state": warm_started,
        "continuation_semantics": "SCF_DENSITY_AND_PAW_STATE_CARRY_FORWARD" if warm_started else "FROZEN_GEOMETRY_FRESH_START",
        "exact_qe_restart_claimed": False,
        "carried_density_state_files": carried_files,
        "preserved_density_state_files": density_state_files_preserved,
        "raw_input_sha256": sha256(inp),
        "raw_output_sha256": sha256(out),
        "surface_convergence_extension_protocol_sha256": sha256(pp),
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "geometry_changed": False,
        "method_changed": False,
        "rank_changed": False,
        "kinetic_inputs_used": False,
        "carried_forward_without_recomputation": False,
    }
    write_json(root / "SCF_CONTINUATION_STATE.json", state)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(state, indent=2, sort_keys=True))


def command_finalize(args: argparse.Namespace) -> None:
    policy(Path(args.policy).resolve())
    ext = import_extension()
    pp = Path(args.protocol).resolve()
    p = ext.protocol(pp)
    p["_protocol_path"] = str(pp)
    state_root = Path(args.state_root).resolve()
    state = load_json(state_path(state_root))
    if state.get("schema") != STATE_SCHEMA:
        raise SystemExit("MECHANICAL_HOLD: wrong final continuation state schema")
    if int(state.get("total_cells_provisioned", 0)) < MIN_CELLS:
        raise SystemExit("MECHANICAL_HOLD: final state was not provisioned with five cells")
    if state.get("status") != "COMPLETE" or state.get("fixed_geometry_scf_energy_ev") is None:
        raise SystemExit("MECHANICAL_HOLD: independent L15 SCF did not complete within the five-cell 5.5 h continuation runway")
    if state.get("scientific_settings_changed") is not False or state.get("thresholds_changed") is not False:
        raise SystemExit("SCIENTIFIC_HOLD: final continuation state is scientifically contaminated")

    force = float(state["max_movable_force_ev_per_angstrom"])
    relax_energy = float(state["relax_energy_ev"])
    repro_energy = float(state["fixed_geometry_scf_energy_ev"])
    delta = abs(relax_energy - repro_energy)
    fg = float(p["frozen_method"]["force_gate_ev_per_angstrom"])
    rg = float(p["frozen_method"]["independent_scf_reproduction_gate_ev"])
    passed = force <= fg and delta <= rg
    excess = (repro_energy - 15.0 * float(p["frozen_method"]["bulk_e0_ev_per_atom"])) / 2.0

    summary = {
        "schema": ext.CLEAN_SCHEMA,
        "status": "COMPLETE" if passed else "NUMERICAL_HOLD",
        "case_id": p["extension_audit"]["case_id"],
        "role": "extension_audit",
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "cell_angstrom": state["cell_angstrom"],
        "final_atoms": state["final_atoms"],
        "layer_z_angstrom": [float(a["position_angstrom"][2]) for a in state["final_atoms"]],
        "relax_energy_ev": relax_energy,
        "fixed_geometry_scf_energy_ev": repro_energy,
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": force,
        "mechanical_pass": passed,
        "surface_excess_ev_per_surface_atom": excess,
        "completion_segment": state["completion_segment"],
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
            "continuation_policy": "5x5.5h minimum",
            "continuation_semantics": state["continuation_semantics"],
            "exact_qe_restart_claimed": False,
        },
        "raw_hashes": {
            "final_continuation_state_sha256": sha256(state_path(state_root)),
            "final_cell_input_sha256": state["raw_input_sha256"],
            "final_cell_output_sha256": state["raw_output_sha256"],
        },
    }
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    summary_path = out_root / "summary.json"
    write_json(summary_path, summary)
    base, _old, _relay = ext.import_runtime()
    base.stage_manifest(out_root, [summary_path])
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("SCIENTIFIC_HOLD: L15 force or independent reproduction gate failed")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("cell")
    sp.add_argument("--policy", required=True)
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--prior-root")
    sp.add_argument("--seed-state-root")
    sp.add_argument("--state-in")
    sp.add_argument("--surface-protocol", required=True)
    sp.add_argument("--stage-a-result", required=True)
    sp.add_argument("--bundle", required=True)
    sp.add_argument("--pseudo-dir", required=True)
    sp.add_argument("--pw", required=True)
    sp.add_argument("--selection", required=True)
    sp.add_argument("--cell", type=int, required=True)
    sp.add_argument("--total-cells", type=int, required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=command_cell)

    sp = sub.add_parser("finalize")
    sp.add_argument("--policy", required=True)
    sp.add_argument("--protocol", required=True)
    sp.add_argument("--state-root", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=command_finalize)
    return ap


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
