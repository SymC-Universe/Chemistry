#!/usr/bin/env python3
"""Prospective L15-vs-L17 CO/Cu(111) observable-specific slab sufficiency test.

This runner does not reclassify the failed absolute clean-surface gate. It uses
fixed-geometry low-coverage CO site SCFs to test whether the L15-to-L17 slab
difference materially propagates into relative adsorption-site energies.
Incomplete SCFs use Quantum ESPRESSO clean max_seconds stops and exact restart.
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

PROTOCOL_SCHEMA = "co-cu111-pbe-l15-l17-observable-sufficiency-v0.1"
PROTOCOL_STATUS = "FROZEN_BEFORE_L15_L17_SITE_RESULTS"
STATE_SCHEMA = "co-cu111-l15-l17-site-scf-state-v0.1"
RESULT_SCHEMA = "co-cu111-l15-l17-observable-sufficiency-result-v0.1"
RY_TO_EV = 13.605693122994
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")


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


def find_one(root: Path, name: str) -> Path:
    hits = [p for p in root.rglob(name) if p.is_file()]
    if len(hits) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected one {name} below {root}, found {len(hits)}")
    return hits[0]


def verify_protocol(p: dict[str, Any]) -> None:
    if p.get("schema") != PROTOCOL_SCHEMA or p.get("status") != PROTOCOL_STATUS:
        raise SystemExit("SCIENTIFIC_HOLD: wrong or unfrozen L15-L17 sufficiency protocol")
    if p.get("scientific_scope") != "PROSPECTIVE_OBSERVABLE_SPECIFIC_SLAB_SUFFICIENCY_AFTER_ABSOLUTE_SURFACE_HOLD":
        raise SystemExit("SCIENTIFIC_HOLD: sufficiency scope drift")
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
    screen = p["matched_site_screen"]
    if screen.get("supercell") != [4, 4] or int(screen.get("kmesh", -1)) != 4:
        raise SystemExit("SCIENTIFIC_HOLD: matched screen cell/kmesh drift")
    if screen.get("sites") != ["top", "bridge", "fcc_hollow", "hcp_hollow"]:
        raise SystemExit("SCIENTIFIC_HOLD: matched screen site set drift")
    if not close(screen.get("common_vacuum_angstrom"), 36.0):
        raise SystemExit("SCIENTIFIC_HOLD: common vacuum drift")
    if not close(screen.get("slab_depth_sensitivity_max_ev_per_CO"), 0.005):
        raise SystemExit("SCIENTIFIC_HOLD: slab-depth sensitivity ceiling drift")
    if screen.get("same_global_minimum_required") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: same-minimum requirement disabled")
    ex = p["execution"]
    if ex.get("checkpoint_mode") != "QE_CLEAN_MAX_SECONDS_EXACT_RESTART":
        raise SystemExit("SCIENTIFIC_HOLD: exact-restart contract disabled")
    if int(ex.get("qe_max_seconds_per_segment", -1)) != 16200:
        raise SystemExit("SCIENTIFIC_HOLD: checkpoint cadence drift")
    if int(ex.get("maximum_scf_segments", -1)) != 6:
        raise SystemExit("SCIENTIFIC_HOLD: finite segment bound drift")
    decision = p["decision"]
    if decision.get("absolute_clean_surface_pass_claimed") is not False or decision.get("l17_original_failure_preserved") is not True:
        raise SystemExit("SCIENTIFIC_HOLD: original clean-surface adjudication not preserved")
    prov = p["provenance"]
    for key in ("original_1_mev_clean_surface_gate_changed", "original_l17_result_reclassified", "kinetic_inputs_used", "barrier_or_rate_inputs_used", "threshold_retuned_to_observed_l17_result"):
        if prov.get(key) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: provenance drift: {key}")


def load_protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    verify_protocol(p)
    return p


def import_base():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_site_ordering_v1 as base  # type: ignore
    return base


def verify_repo_sources(p: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    inherited = p["inherited_method"]
    for path_key, hash_key in (
        ("surface_protocol_path", "surface_protocol_sha256"),
        ("pseudopotential_bundle_path", "pseudopotential_bundle_sha256"),
    ):
        target = repo / inherited[path_key]
        if not target.is_file() or sha256(target) != inherited[hash_key]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen repository source mismatch: {target}")


def verify_runtime(args: argparse.Namespace, p: dict[str, Any]):
    base = import_base()
    verify_repo_sources(p)
    inherited = p["inherited_method"]
    surface_path = Path(args.surface_protocol).resolve()
    bundle_path = Path(args.bundle).resolve()
    stage_path = Path(args.stage_a_result).resolve()
    pw = Path(args.pw).resolve()
    if sha256(surface_path) != inherited["surface_protocol_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: surface protocol hash mismatch")
    if sha256(bundle_path) != inherited["pseudopotential_bundle_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pseudopotential bundle hash mismatch")
    if sha256(stage_path) != inherited["stage_a_result_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: Stage A result hash mismatch")
    if sha256(pw) != inherited["pw_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pw.x hash mismatch")
    surface = base.load_json(surface_path)
    base.verify_protocol(surface)
    base.verify_stage_a(surface, stage_path)
    bundle = base.verify_bundle(surface, bundle_path, Path(args.pseudo_dir).resolve(), pw)
    return base, surface, bundle


def load_l15(root: Path, p: dict[str, Any]) -> dict[str, Any]:
    path = find_one(root, "summary.json")
    src = p["source_l15"]
    if sha256(path) != src["summary_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pinned L15 summary hash mismatch")
    row = load_json(path)
    if row.get("case_id") != src["case_id"] or int(row.get("layers", -1)) != 15 or row.get("mechanical_pass") is not True:
        raise SystemExit("MECHANICAL_HOLD: L15 source content mismatch")
    if len(row.get("final_atoms", [])) != 15:
        raise SystemExit("MECHANICAL_HOLD: L15 final geometry length mismatch")
    return row


def load_l17(root: Path, p: dict[str, Any]) -> dict[str, Any]:
    path = find_one(root, "L17_RESTART_STATE.json")
    src = p["source_l17"]
    if sha256(path) != src["relax_state_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pinned L17 relax-state hash mismatch")
    row = load_json(path)
    if row.get("case_id") != src["case_id"] or int(row.get("layers", -1)) != 17 or row.get("status") != "COMPLETE":
        raise SystemExit("MECHANICAL_HOLD: L17 source content mismatch")
    if row.get("checkpoint_semantics") != "QE_CLEAN_MAX_SECONDS_EXACT_RESTART":
        raise SystemExit("MECHANICAL_HOLD: L17 source lacks exact-restart provenance")
    if len(row.get("final_atoms", [])) != 17:
        raise SystemExit("MECHANICAL_HOLD: L17 final geometry length mismatch")
    return row


def source_for_depth(depth: str, l15_root: Path, l17_root: Path, p: dict[str, Any]) -> dict[str, Any]:
    if depth == "L15":
        return load_l15(l15_root, p)
    if depth == "L17":
        return load_l17(l17_root, p)
    raise SystemExit("MECHANICAL_HOLD: depth must be L15 or L17")


def frac_to_cart(u: float, v: float, a1: list[float], a2: list[float]) -> tuple[float, float]:
    return u * a1[0] + v * a2[0], u * a1[1] + v * a2[1]


def layer_shift(layer: int) -> tuple[float, float]:
    x = (layer % 3) / 3.0
    return x, x


def periodic_uv_dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    du = min(abs(a[0] - b[0]), 1.0 - abs(a[0] - b[0]))
    dv = min(abs(a[1] - b[1]), 1.0 - abs(a[1] - b[1]))
    return du + dv


def site_offsets(layers: int) -> dict[str, tuple[float, float]]:
    top = layer_shift(layers - 1)
    second = layer_shift(layers - 2)
    third = layer_shift(layers - 3)
    h1 = ((top[0] + 1.0 / 3.0) % 1.0, (top[1] + 1.0 / 3.0) % 1.0)
    h2 = ((top[0] + 2.0 / 3.0) % 1.0, (top[1] + 2.0 / 3.0) % 1.0)
    hcp = h1 if periodic_uv_dist(h1, second) < periodic_uv_dist(h2, second) else h2
    fcc = h1 if periodic_uv_dist(h1, third) < periodic_uv_dist(h2, third) else h2
    if hcp == fcc:
        raise SystemExit("MECHANICAL_HOLD: failed to distinguish fcc and hcp sites")
    return {"top": top, "bridge": ((top[0] + 0.5) % 1.0, top[1]), "fcc_hollow": fcc, "hcp_hollow": hcp}


def matched_geometry(source: dict[str, Any], depth: str, site: str, p: dict[str, Any]) -> tuple[list[list[float]], list[dict[str, Any]], dict[str, Any]]:
    screen = p["matched_site_screen"]
    layers = int(source["layers"])
    if site not in screen["sites"]:
        raise SystemExit("SCIENTIFIC_HOLD: requested site is not frozen")
    a0 = 3.632355796707377
    axy = a0 / math.sqrt(2.0)
    n = int(screen["supercell"][0])
    if screen["supercell"] != [n, n] or n != 4:
        raise SystemExit("SCIENTIFIC_HOLD: only frozen 4x4 screen is admissible")
    a1 = [n * axy, 0.0, 0.0]
    a2 = [0.5 * n * axy, 0.5 * n * math.sqrt(3.0) * axy, 0.0]
    base_cell = json.loads(json.dumps(source["cell_angstrom"]))
    source_vacuum = float(source["vacuum_angstrom"])
    common_vacuum = float(screen["common_vacuum_angstrom"])
    cell_z = float(base_cell[2][2]) + (common_vacuum - source_vacuum)
    cell = [a1, a2, [0.0, 0.0, cell_z]]
    z_by_layer = [None] * layers
    for atom in source["final_atoms"]:
        idx = int(atom["layer"])
        z_by_layer[idx] = float(atom["position_angstrom"][2])
    if any(z is None for z in z_by_layer):
        raise SystemExit("MECHANICAL_HOLD: source clean geometry lacks layer z values")
    atoms: list[dict[str, Any]] = []
    for layer in range(layers):
        su, sv = layer_shift(layer)
        for i in range(n):
            for j in range(n):
                u = (i + su) / n
                v = (j + sv) / n
                x, y = frac_to_cart(u, v, a1, a2)
                atoms.append({"symbol": "Cu", "position_angstrom": [x, y, float(z_by_layer[layer])], "flags": [0, 0, 0], "layer": layer})
    off = site_offsets(layers)[site]
    u = (2.0 + off[0]) / n
    v = (2.0 + off[1]) / n
    x, y = frac_to_cart(u, v, a1, a2)
    top_z = max(float(z) for z in z_by_layer)
    c_z = top_z + float(screen["initial_carbon_height_above_top_Cu_plane_angstrom"])
    o_z = c_z + float(screen["initial_co_bond_angstrom"])
    if o_z >= cell_z / 2.0 - 2.0:
        raise SystemExit("SCIENTIFIC_HOLD: CO too close to ESM boundary")
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
        "site": site,
        "all_atomic_coordinates_fixed": True,
    }
    return cell, atoms, evidence


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


def classify_scf(text: str, rc: int, wrapper_timeout: bool) -> dict[str, Any]:
    lower = text.lower()
    if wrapper_timeout:
        raise SystemExit("MECHANICAL_HOLD: external timeout before guaranteed QE checkpoint")
    if rc != 0 or "error in routine" in lower or "mpi_abort" in lower:
        raise SystemExit(f"MECHANICAL_HOLD: pw.x failed before admissible checkpoint, rc={rc}")
    job_done = "job done" in lower
    clean_stop = "maximum cpu time exceeded" in lower
    scf_converged = "convergence has been achieved" in lower or "end of self-consistent calculation" in lower
    energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(text)]
    if job_done and scf_converged and energies:
        return {"status": "COMPLETE", "job_done": True, "clean_max_seconds_stop": clean_stop, "scf_converged": True, "energy_ev": energies[-1]}
    if job_done and clean_stop:
        return {"status": "CHECKPOINT", "job_done": True, "clean_max_seconds_stop": True, "scf_converged": False, "energy_ev": None}
    raise SystemExit("MECHANICAL_HOLD: SCF output is neither complete nor a clean max_seconds checkpoint")


def checkpoint_files(root: Path) -> list[Path]:
    c = root / "qe_checkpoint"
    files = sorted(p for p in c.rglob("*") if p.is_file()) if c.is_dir() else []
    if not files:
        raise SystemExit("MECHANICAL_HOLD: missing or empty QE checkpoint")
    return files


def write_checkpoint_manifest(root: Path) -> str:
    c = root / "qe_checkpoint"
    lines = []
    for path in checkpoint_files(root):
        lines.append(f"{sha256(path)}  {path.relative_to(c).as_posix()}")
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    manifest.write_text("\n".join(lines) + "\n")
    return sha256(manifest)


def verify_checkpoint_manifest(root: Path, expected_sha: str | None = None) -> str:
    manifest = root / "QE_CHECKPOINT_MANIFEST.sha256"
    if not manifest.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing checkpoint manifest")
    if expected_sha is not None and sha256(manifest) != expected_sha:
        raise SystemExit("MECHANICAL_HOLD: checkpoint manifest hash drift")
    c = root / "qe_checkpoint"
    for raw in manifest.read_text().splitlines():
        if not raw.strip():
            continue
        expected, rel = raw.split("  ", 1)
        path = c / rel
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"MECHANICAL_HOLD: checkpoint file drift: {rel}")
    return sha256(manifest)


def copy_checkpoint(source: Path, target: Path) -> None:
    verify_checkpoint_manifest(source)
    src = source / "qe_checkpoint"
    dst = target / "qe_checkpoint"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def state_path(root: Path) -> Path:
    return root / "L15_L17_SITE_SCF_STATE.json"


def load_prior(root: Path, depth: str, site: str, segment: int) -> dict[str, Any]:
    path = state_path(root)
    if not path.is_file():
        raise SystemExit("MECHANICAL_HOLD: missing prior site SCF state")
    row = load_json(path)
    if row.get("schema") != STATE_SCHEMA or row.get("depth") != depth or row.get("site") != site or int(row.get("segment", -1)) != segment:
        raise SystemExit("MECHANICAL_HOLD: prior site SCF sequence mismatch")
    if row.get("status") == "CHECKPOINT":
        verify_checkpoint_manifest(root, row.get("checkpoint_manifest_sha256"))
    elif row.get("status") != "COMPLETE":
        raise SystemExit("MECHANICAL_HOLD: prior site SCF state invalid")
    return row


def command_preflight(args: argparse.Namespace) -> None:
    p = load_protocol(Path(args.protocol).resolve())
    l15 = load_l15(Path(args.l15_root).resolve(), p)
    l17 = load_l17(Path(args.l17_root).resolve(), p)
    out = {
        "schema": "co-cu111-l15-l17-observable-sufficiency-preflight-v0.1",
        "status": "PASS",
        "l15_summary_sha256": p["source_l15"]["summary_sha256"],
        "l17_state_sha256": p["source_l17"]["relax_state_sha256"],
        "l15_layers": l15["layers"],
        "l17_layers": l17["layers"],
        "original_l17_surface_gate_pass": False,
        "absolute_clean_surface_pass_claimed": False,
    }
    if args.out:
        write_json(Path(args.out).resolve(), out)
    print(json.dumps(out, indent=2, sort_keys=True))


def command_scf_segment(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = load_protocol(pp)
    depth = args.depth
    site = args.site
    segment = int(args.segment)
    if depth not in {"L15", "L17"} or site not in p["matched_site_screen"]["sites"]:
        raise SystemExit("SCIENTIFIC_HOLD: depth/site outside frozen screen")
    if segment < 1 or segment > int(p["execution"]["maximum_scf_segments"]):
        raise SystemExit("MECHANICAL_HOLD: segment outside frozen bound")
    base, surface, bundle = verify_runtime(args, p)
    source = source_for_depth(depth, Path(args.l15_root).resolve(), Path(args.l17_root).resolve(), p)
    cell, atoms, geometry_evidence = matched_geometry(source, depth, site, p)
    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if segment > 1:
        prior_root = Path(args.prior_root).resolve()
        prior = load_prior(prior_root, depth, site, segment - 1)
        if prior["status"] == "COMPLETE":
            carried = dict(prior)
            carried.update({"segment": segment, "carried_forward_without_recomputation": True, "source_state_sha256": sha256(state_path(prior_root))})
            write_json(state_path(out_root), carried)
            print(json.dumps(carried, indent=2, sort_keys=True))
            return
        copy_checkpoint(prior_root, out_root)
        restart_mode = "restart"
    else:
        restart_mode = "from_scratch"

    checkpoint = out_root / "qe_checkpoint"
    checkpoint.mkdir(parents=True, exist_ok=True)
    inp = out_root / "site_scf.in"
    out = out_root / "site_scf.out"
    text = base.qe_input(
        calculation="scf",
        prefix=f"co_cu111_l15l17_{depth.lower()}_{site}",
        cell=cell,
        atoms=atoms,
        kmesh=int(p["matched_site_screen"]["kmesh"]),
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=checkpoint,
    )
    text = add_control_fields(text, restart_mode, int(p["execution"]["qe_max_seconds_per_segment"]))
    inp.write_text(text)
    rc, wrapper_timeout, elapsed = run_pw(Path(args.pw).resolve(), inp, out, int(p["execution"]["qe_max_seconds_per_segment"]) + 3600)
    raw = out.read_text(errors="replace")
    outcome = classify_scf(raw, rc, wrapper_timeout)
    manifest_sha = None
    if outcome["status"] == "CHECKPOINT":
        manifest_sha = write_checkpoint_manifest(out_root)
    else:
        if checkpoint.exists():
            shutil.rmtree(checkpoint)
    state = {
        "schema": STATE_SCHEMA,
        "status": outcome["status"],
        "depth": depth,
        "site": site,
        "segment": segment,
        "restart_mode": restart_mode,
        "checkpoint_semantics": "QE_CLEAN_MAX_SECONDS_EXACT_RESTART",
        "checkpoint_manifest_sha256": manifest_sha,
        "energy_ev": outcome["energy_ev"],
        "job_done": outcome["job_done"],
        "clean_max_seconds_stop": outcome["clean_max_seconds_stop"],
        "scf_converged": outcome["scf_converged"],
        "elapsed_s": elapsed,
        "pw_returncode": rc,
        "wrapper_timeout": wrapper_timeout,
        "geometry_evidence": geometry_evidence,
        "raw_input_sha256": sha256(inp),
        "raw_output_sha256": sha256(out),
        "protocol_sha256": sha256(pp),
        "scientific_settings_changed": False,
        "original_l17_hold_preserved": True,
        "absolute_clean_surface_pass_claimed": False,
        "carried_forward_without_recomputation": False,
    }
    write_json(state_path(out_root), state)
    print(json.dumps(state, indent=2, sort_keys=True))


def classify_sufficiency(energies: dict[str, dict[str, float]], threshold: float) -> dict[str, Any]:
    sites = ["top", "bridge", "fcc_hollow", "hcp_hollow"]
    rel: dict[str, dict[str, float]] = {}
    minima: dict[str, str] = {}
    for depth in ("L15", "L17"):
        e = energies[depth]
        if set(e) != set(sites):
            raise ValueError(f"missing sites for {depth}")
        rel[depth] = {s: float(e[s]) - float(e["top"]) for s in sites}
        minima[depth] = min(sites, key=lambda s: float(e[s]))
    competitors = sites[1:]
    deltas = {s: abs(rel["L17"][s] - rel["L15"][s]) for s in competitors}
    sensitivity = max(deltas.values())
    same_min = minima["L15"] == minima["L17"]
    return {
        "relative_site_energies_ev_per_CO": rel,
        "sitewise_l15_l17_sensitivity_ev_per_CO": deltas,
        "slab_depth_sensitivity_ev_per_CO": sensitivity,
        "slab_depth_sensitivity_max_ev_per_CO": threshold,
        "sensitivity_pass": sensitivity <= threshold,
        "global_minimum_L15": minima["L15"],
        "global_minimum_L17": minima["L17"],
        "same_global_minimum": same_min,
        "sufficiency_pass": sensitivity <= threshold and same_min,
    }


def command_adjudicate(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve()
    p = load_protocol(pp)
    root = Path(args.root).resolve()
    sites = p["matched_site_screen"]["sites"]
    max_segment = int(p["execution"]["maximum_scf_segments"])
    energies: dict[str, dict[str, float]] = {"L15": {}, "L17": {}}
    evidence: dict[str, str] = {}
    incomplete: list[str] = []
    for depth in ("L15", "L17"):
        for site in sites:
            matches = []
            for state in root.rglob("L15_L17_SITE_SCF_STATE.json"):
                try:
                    row = load_json(state)
                except Exception:
                    continue
                if row.get("schema") == STATE_SCHEMA and row.get("depth") == depth and row.get("site") == site and int(row.get("segment", -1)) == max_segment:
                    matches.append((state, row))
            if len(matches) != 1:
                incomplete.append(f"{depth}:{site}:missing_or_duplicate_final_state")
                continue
            state, row = matches[0]
            if row.get("status") != "COMPLETE" or row.get("energy_ev") is None:
                incomplete.append(f"{depth}:{site}:{row.get('status')}")
                continue
            if row.get("original_l17_hold_preserved") is not True or row.get("absolute_clean_surface_pass_claimed") is not False:
                raise SystemExit("SCIENTIFIC_HOLD: site-state provenance tried to reclassify L17")
            energies[depth][site] = float(row["energy_ev"])
            evidence[f"{depth}:{site}"] = sha256(state)
    if incomplete:
        result = {
            "schema": RESULT_SCHEMA,
            "status": p["decision"]["incomplete_status"],
            "incomplete_cases": incomplete,
            "next_gate": "REPAIR_OR_EXTEND_ONLY_WITHIN_FROZEN_SIX_SEGMENT_BOUND",
            "absolute_clean_surface_pass_claimed": False,
            "original_l17_hold_preserved": True,
            "protocol_sha256": sha256(pp),
        }
        write_json(Path(args.out).resolve(), result)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit("MECHANICAL_HOLD: L15-L17 site screen incomplete")
    gate = classify_sufficiency(energies, float(p["matched_site_screen"]["slab_depth_sensitivity_max_ev_per_CO"]))
    passed = bool(gate["sufficiency_pass"])
    result = {
        "schema": RESULT_SCHEMA,
        "status": p["decision"]["pass_status"] if passed else p["decision"]["fail_status"],
        "next_gate": p["decision"]["pass_next_gate"] if passed else p["decision"]["fail_next_gate"],
        "energies_ev": energies,
        "gate": gate,
        "source_state_sha256": evidence,
        "original_l15_l17_clean_surface_delta_ev_per_surface_atom": p["source_l17"]["observed_l15_l17_delta_ev_per_surface_atom"],
        "original_clean_surface_gate_ev_per_surface_atom": 0.001,
        "absolute_clean_surface_pass_claimed": False,
        "original_l17_hold_preserved": True,
        "automatic_l19_dispatch": False,
        "automatic_barrier_dispatch": False,
        "protocol_sha256": sha256(pp),
        "kinetic_inputs_used": False,
    }
    write_json(Path(args.out).resolve(), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("SCIENTIFIC_HOLD: L15-L17 observable-specific slab sufficiency gate failed")


def command_self_test(args: argparse.Namespace) -> None:
    p = load_protocol(Path(args.protocol).resolve())
    assert site_offsets(15)["fcc_hollow"] != site_offsets(15)["hcp_hollow"]
    assert site_offsets(17)["fcc_hollow"] != site_offsets(17)["hcp_hollow"]
    good = classify_sufficiency(
        {
            "L15": {"top": -10.0, "bridge": -9.95, "fcc_hollow": -9.94, "hcp_hollow": -9.93},
            "L17": {"top": -12.0, "bridge": -11.951, "fcc_hollow": -11.941, "hcp_hollow": -11.931},
        },
        0.005,
    )
    assert good["sufficiency_pass"] and good["same_global_minimum"]
    bad = classify_sufficiency(
        {
            "L15": {"top": -10.0, "bridge": -9.99, "fcc_hollow": -9.98, "hcp_hollow": -9.97},
            "L17": {"top": -12.0, "bridge": -12.01, "fcc_hollow": -11.98, "hcp_hollow": -11.97},
        },
        0.005,
    )
    assert not bad["sufficiency_pass"] and not bad["same_global_minimum"]
    assert p["decision"]["absolute_clean_surface_pass_claimed"] is False
    print("SELF_TEST_PASS")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("self-test")
    s.add_argument("--protocol", required=True)
    s.set_defaults(func=command_self_test)

    s = sub.add_parser("preflight")
    s.add_argument("--protocol", required=True)
    s.add_argument("--l15-root", required=True)
    s.add_argument("--l17-root", required=True)
    s.add_argument("--out")
    s.set_defaults(func=command_preflight)

    s = sub.add_parser("scf-segment")
    for name in ("protocol", "surface_protocol", "stage_a_result", "bundle", "pseudo_dir", "pw", "l15_root", "l17_root", "depth", "site", "out"):
        s.add_argument("--" + name.replace("_", "-"), required=True)
    s.add_argument("--segment", required=True, type=int)
    s.add_argument("--prior-root")
    s.set_defaults(func=command_scf_segment)

    s = sub.add_parser("adjudicate")
    s.add_argument("--protocol", required=True)
    s.add_argument("--root", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(func=command_adjudicate)
    return ap


def main() -> None:
    args = parser().parse_args()
    if args.cmd == "scf-segment" and args.segment > 1 and not args.prior_root:
        raise SystemExit("MECHANICAL_HOLD: --prior-root required after segment 1")
    args.func(args)


if __name__ == "__main__":
    main()
