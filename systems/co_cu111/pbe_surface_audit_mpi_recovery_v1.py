#!/usr/bin/env python3
"""Fail-closed mechanical MPI recovery for the frozen CO/Cu(111) L13 audit.

No scientific setting is changed. The runner first proves four-rank numerical
parity against the immutable one-rank segment-8 input geometry. Only a passing
parity record authorizes up to two bounded four-rank BFGS continuation segments.
Total forces are parsed only from QE's authoritative 'Forces acting on atoms'
blocks, correcting the verbose-force-decomposition ambiguity in the original
surface runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
ATOM_FORCE_RE = re.compile(
    r"atom\s+(\d+)\s+type\s+\d+\s+force\s*=\s*"
    r"([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)"
)
PROTOCOL_SCHEMA = "co-cu111-pbe-surface-audit-mpi-recovery-v0.1"
SEGMENT_SCHEMA = "co-cu111-pbe-surface-audit-mpi-recovery-segment-v0.1"
PARITY_SCHEMA = "co-cu111-pbe-surface-audit-mpi-parity-v0.1"


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


def import_base():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_site_ordering_v1 as base  # type: ignore
    import pbe_surface_audit_proposal_relay_v1 as relay  # type: ignore
    return base, relay


def protocol(path: Path) -> dict[str, Any]:
    p = load_json(path)
    if p.get("schema") != PROTOCOL_SCHEMA:
        raise SystemExit("MECHANICAL_HOLD: wrong MPI recovery protocol schema")
    if p.get("status") != "FROZEN_MECHANICAL_MPI_RECOVERY_AFTER_RELAY_EXHAUSTION_BEFORE_RESULTS":
        raise SystemExit("MECHANICAL_HOLD: MPI recovery protocol is not frozen")
    if p.get("scientific_scope") != "NO_SCIENTIFIC_CONFIGURATION_CHANGE":
        raise SystemExit("MECHANICAL_HOLD: scientific scope changed")
    prov = p.get("provenance", {})
    if prov.get("scientific_settings_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: provenance is not clean")
    ex = p.get("execution_amendment", {})
    if int(ex.get("mpi_rank_count_proposed", -1)) != 4:
        raise SystemExit("MECHANICAL_HOLD: proposed MPI rank count is not frozen at four")
    if int(ex.get("maximum_new_continuation_segments", -1)) != 2:
        raise SystemExit("MECHANICAL_HOLD: continuation bound changed")
    return p


def verify_repo_sources(p: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    for key in ("surface_protocol", "surface_runner", "proposal_relay_protocol", "proposal_relay_runner"):
        row = p["frozen_sources"][key]
        q = repo / row["path"]
        if not q.is_file() or sha256(q) != row["sha256"]:
            raise SystemExit(f"MECHANICAL_HOLD: frozen source mismatch: {row['path']}")


def find_one(root: Path, name: str) -> Path:
    rows = [p for p in root.rglob(name) if p.is_file()]
    if len(rows) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name} under {root}, found {len(rows)}")
    return rows[0]


def authoritative_force_blocks(text: str, nat: int) -> list[list[tuple[float, float, float]]]:
    """Parse only total-force rows immediately after QE's total-force header."""
    lines = text.splitlines()
    blocks: list[list[tuple[float, float, float]]] = []
    for i, line in enumerate(lines):
        if "Forces acting on atoms" not in line:
            continue
        rows: list[tuple[float, float, float]] = []
        expected_atom = 1
        for line2 in lines[i + 1 :]:
            if "The non-local contrib." in line2 or "Total force =" in line2:
                break
            m = ATOM_FORCE_RE.search(line2)
            if not m:
                continue
            atom = int(m.group(1))
            if atom != expected_atom:
                rows = []
                break
            rows.append((float(m.group(2)), float(m.group(3)), float(m.group(4))))
            expected_atom += 1
            if len(rows) == nat:
                break
        if len(rows) == nat:
            blocks.append(rows)
    return blocks


def max_movable_force_ev_a(forces: list[tuple[float, float, float]], atoms: list[dict[str, Any]]) -> float:
    if len(forces) != len(atoms):
        raise SystemExit("MECHANICAL_HOLD: force/atom count mismatch")
    values: list[float] = []
    for force, atom in zip(forces, atoms):
        flags = atom.get("flags", [0, 0, 0])
        for component, flag in zip(force, flags):
            if int(flag) == 1:
                values.append(abs(float(component)) * RY_BOHR_TO_EV_ANG)
    if not values:
        raise SystemExit("MECHANICAL_HOLD: no movable force components found")
    return max(values)


def max_force_component_difference_ev_a(
    a: list[tuple[float, float, float]], b: list[tuple[float, float, float]]
) -> float:
    if len(a) != len(b):
        return math.inf
    return max(abs(float(x) - float(y)) * RY_BOHR_TO_EV_ANG for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def apply_template(rows: list[dict[str, Any]], template: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) != len(template):
        raise SystemExit("MECHANICAL_HOLD: geometry length mismatch")
    out: list[dict[str, Any]] = []
    for row, tmpl in zip(rows, template):
        if row.get("symbol") != tmpl.get("symbol"):
            raise SystemExit("MECHANICAL_HOLD: geometry symbol mismatch")
        item = dict(tmpl)
        item["position_angstrom"] = [float(x) for x in row["position_angstrom"]]
        out.append(item)
    return out


def verify_segment8(root: Path, p: dict[str, Any]) -> tuple[dict[str, Any], Path, str]:
    seed = p["segment8_seed"]
    row_path = find_one(root, "RELAY_SEGMENT.json")
    out_path = find_one(root, "clean_relax.out")
    in_path = find_one(root, "clean_relax.in")
    if sha256(row_path) != seed["relay_segment_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: segment-8 JSON hash mismatch")
    if sha256(out_path) != seed["relax_output_sha256"] or sha256(in_path) != seed["relax_input_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: segment-8 raw hash mismatch")
    row = load_json(row_path)
    if row.get("status") != seed["required_status"] or int(row.get("logical_segment", -1)) != int(seed["required_logical_segment"]):
        raise SystemExit("MECHANICAL_HOLD: wrong segment-8 state")
    if row.get("next_trial_semantics") != seed["next_trial_semantics"]:
        raise SystemExit("MECHANICAL_HOLD: segment-8 trial semantics mismatch")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: segment-8 provenance mismatch")
    return row, out_path, out_path.read_text(errors="replace")


def run_pw_mpi(pw: Path, inp: Path, out: Path, ranks: int, cap_s: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    start = time.time()
    timed_out = False
    cmd = ["mpirun", "-np", str(int(ranks)), str(pw)]
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen(cmd, stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
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
    text = out.read_text(errors="replace") if out.is_file() else ""
    energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(text)]
    return {
        "returncode": int(rc),
        "elapsed_s": time.time() - start,
        "timed_out_by_wrapper": timed_out,
        "job_done": "JOB DONE." in text,
        "bfgs_finished": "End of BFGS Geometry Optimization" in text,
        "energy_ev": energies[-1] if energies else None,
        "text": text,
        "command": cmd,
    }


def command_self_test(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    pc = p["parser_correction"]
    if float(pc["unchanged_force_gate_ev_per_angstrom"]) != 0.02:
        raise SystemExit("MECHANICAL_HOLD: force gate changed")
    pg = p["mpi_parity_gate"]
    if float(pg["energy_absolute_difference_max_ev"]) > 0.0001 or float(pg["force_component_absolute_difference_max_ev_per_angstrom"]) > 0.0001:
        raise SystemExit("MECHANICAL_HOLD: parity tolerance weakened")
    science = p["unchanged_science"]
    exact = {"layers": 13, "vacuum_angstrom": 28.0, "kmesh": 24, "ecutwfc_ry": 90, "ecutrho_ry": 900}
    for key, value in exact.items():
        if science.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: frozen value changed: {key}")
    print("MPI_RECOVERY_SELF_TEST_PASS")
    print("SCIENTIFIC_SETTINGS_CHANGED=false")
    print("KINETIC_INPUTS_USED=false")


def command_verify_seed(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    row, _, text = verify_segment8(Path(args.segment8_root).resolve(), p)
    blocks = authoritative_force_blocks(text, int(row["layers"]))
    if len(blocks) < 2:
        raise SystemExit("MECHANICAL_HOLD: segment 8 lacks two authoritative force blocks")
    f0 = max_movable_force_ev_a(blocks[0], row["input_atoms"])
    # The second evaluated geometry has the same frozen flag template.
    f1 = max_movable_force_ev_a(blocks[1], row["input_atoms"])
    pc = p["parser_correction"]
    if abs(f0 - float(pc["segment8_true_input_max_movable_force_ev_per_angstrom"])) > 1e-10:
        raise SystemExit("MECHANICAL_HOLD: segment-8 corrected input force drift")
    if abs(f1 - float(pc["segment8_true_second_evaluated_max_movable_force_ev_per_angstrom"])) > 1e-10:
        raise SystemExit("MECHANICAL_HOLD: segment-8 corrected second force drift")
    print(json.dumps({"status": "SEED_VERIFIED", "input_force_ev_per_angstrom": f0, "second_force_ev_per_angstrom": f1}, sort_keys=True))


def runtime_context(args: argparse.Namespace, p: dict[str, Any]):
    base, relay = import_base()
    verify_repo_sources(p)
    surface_path = Path(args.surface_protocol).resolve()
    surface = base.load_json(surface_path)
    base.verify_protocol(surface)
    if sha256(surface_path) != p["frozen_sources"]["surface_protocol"]["sha256"]:
        raise SystemExit("MECHANICAL_HOLD: surface protocol hash mismatch")
    base.verify_stage_a(surface, Path(args.stage_a_result).resolve())
    bundle = base.verify_bundle(surface, Path(args.bundle).resolve(), Path(args.pseudo_dir).resolve(), Path(args.pw).resolve())
    if sha256(Path(args.pw).resolve()) != p["frozen_sources"]["pw_x_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: pw.x hash mismatch")
    return base, relay, surface, bundle


def command_parity(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, _, surface, bundle = runtime_context(args, p)
    seg, _, text = verify_segment8(Path(args.segment8_root).resolve(), p)
    nat = int(seg["layers"])
    ref_blocks = authoritative_force_blocks(text, nat)
    if not ref_blocks:
        raise SystemExit("MECHANICAL_HOLD: no authoritative one-rank force block")
    ref_forces = ref_blocks[0]
    ref_energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(text)]
    if not ref_energies:
        raise SystemExit("MECHANICAL_HOLD: no raw one-rank input energy in segment 8")
    ref_energy = ref_energies[0]
    expected_input_energy = float(p["parser_correction"]["segment8_true_input_energy_ev"])
    if abs(ref_energy - expected_input_energy) > 1e-8:
        raise SystemExit("MECHANICAL_HOLD: segment-8 raw input-energy drift")
    atoms = apply_template(seg["input_atoms"], seg["input_atoms"])
    cell = seg["cell_angstrom"]
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "parity_scf"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "parity.in"; out = run_dir / "parity.out"
    inp.write_text(base.qe_input(calculation="scf", prefix="co_cu111_mpi_parity", cell=cell, atoms=atoms, kmesh=24, protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir).resolve(), outdir=tmp))
    result = run_pw_mpi(Path(args.pw).resolve(), inp, out, 4, int(args.runtime_cap_s))
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit("MECHANICAL_MPI_PARITY_HOLD: four-rank SCF did not complete")
    blocks = authoritative_force_blocks(result["text"], nat)
    if not blocks:
        raise SystemExit("MECHANICAL_MPI_PARITY_HOLD: four-rank total-force block missing")
    energy_delta = abs(float(result["energy_ev"]) - ref_energy)
    force_delta = max_force_component_difference_ev_a(blocks[-1], ref_forces)
    pg = p["mpi_parity_gate"]
    passed = energy_delta <= float(pg["energy_absolute_difference_max_ev"]) and force_delta <= float(pg["force_component_absolute_difference_max_ev_per_angstrom"])
    record = {
        "schema": PARITY_SCHEMA,
        "status": "PASS" if passed else "MECHANICAL_MPI_PARITY_HOLD",
        "reference_mpi_ranks": 1,
        "test_mpi_ranks": 4,
        "reference_energy_ev": ref_energy,
        "test_energy_ev": result["energy_ev"],
        "energy_absolute_difference_ev": energy_delta,
        "force_component_absolute_difference_max_ev_per_angstrom": force_delta,
        "energy_tolerance_ev": pg["energy_absolute_difference_max_ev"],
        "force_tolerance_ev_per_angstrom": pg["force_component_absolute_difference_max_ev_per_angstrom"],
        "reference_true_max_movable_force_ev_per_angstrom": max_movable_force_ev_a(ref_forces, atoms),
        "test_true_max_movable_force_ev_per_angstrom": max_movable_force_ev_a(blocks[-1], atoms),
        "scientific_settings_changed": False,
        "execution_resource_changed": True,
        "kinetic_inputs_used": False,
        "raw_hashes": {"input_sha256": sha256(inp), "output_sha256": sha256(out)},
    }
    write_json(root / "MPI_PARITY_RESULT.json", record)
    base.cleanup_tmp(tmp)
    print(json.dumps(record, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(2)


def load_prior_seed(prior_root: Path, p: dict[str, Any], relay, segment: int) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    if segment == 1:
        seg, _, _ = verify_segment8(prior_root, p)
        return seg["next_trial_atoms"], {"source": "proposal_relay_segment_8", "source_sha256": p["segment8_seed"]["relay_segment_sha256"]}, False
    q = find_one(prior_root, "MPI_RECOVERY_SEGMENT.json")
    row = load_json(q)
    if row.get("schema") != SEGMENT_SCHEMA or int(row.get("segment", -1)) != segment - 1:
        raise SystemExit("MECHANICAL_HOLD: prior MPI segment mismatch")
    if row.get("status") == "RELAX_COMPLETE":
        return row["final_atoms"], {"source": "prior_mpi_relax_complete", "source_sha256": sha256(q)}, True
    if row.get("status") != "CONTINUE":
        raise SystemExit("MECHANICAL_HOLD: prior MPI segment status invalid")
    return row["next_trial_atoms"], {"source": "prior_mpi_next_trial", "source_sha256": sha256(q)}, False


def command_continue(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, relay, surface, bundle = runtime_context(args, p)
    parity = load_json(Path(args.parity).resolve())
    if parity.get("schema") != PARITY_SCHEMA or parity.get("status") != "PASS" or int(parity.get("test_mpi_ranks", -1)) != 4:
        raise SystemExit("MECHANICAL_HOLD: four-rank continuation lacks passing parity authorization")
    segment = int(args.segment)
    if segment not in (1, 2):
        raise SystemExit("MECHANICAL_HOLD: MPI segment must be 1 or 2")
    prior_root = Path(args.prior_root).resolve()
    seed, source_evidence, already_complete = load_prior_seed(prior_root, p, relay, segment)
    # Reconstruct the exact frozen L13 cell/template only to preserve flags.
    cell, template = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 13, 28.0)
    seed = apply_template(seed, template)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    if already_complete:
        source_row = load_json(find_one(prior_root, "MPI_RECOVERY_SEGMENT.json"))
        carried = dict(source_row)
        carried.update({"segment": segment, "logical_segment": 8 + segment, "carried_forward_without_recomputation": True, "source_evidence": source_evidence})
        write_json(root / "MPI_RECOVERY_SEGMENT.json", carried)
        print(json.dumps(carried, indent=2, sort_keys=True))
        return
    run_dir = root / "relax"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_relax.in"; out = run_dir / "clean_relax.out"
    inp.write_text(base.qe_input(calculation="relax", prefix="co_cu111_clean", cell=cell, atoms=seed, kmesh=24, protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir).resolve(), outdir=tmp))
    result = run_pw_mpi(Path(args.pw).resolve(), inp, out, 4, int(args.runtime_cap_s))
    if result["returncode"] != 0 and not result["timed_out_by_wrapper"]:
        raise SystemExit(f"MECHANICAL_HOLD: four-rank pw.x failed, rc={result['returncode']}")
    nat = 13
    blocks = authoritative_force_blocks(result["text"], nat)
    latest_force = max_movable_force_ev_a(blocks[-1], seed) if blocks else None
    relax_complete = bool(result["job_done"] and result["bfgs_finished"] and result["energy_ev"] is not None)
    final_atoms = None
    next_trial = None
    if relax_complete:
        final_atoms = base.parse_positions(result["text"], nat, seed)
        if final_atoms is None or not blocks:
            raise SystemExit("MECHANICAL_HOLD: completed relaxation lacks final geometry/forces")
        final_force = max_movable_force_ev_a(blocks[-1], final_atoms)
        if final_force > float(p["unchanged_science"]["force_gate_ev_per_angstrom"]):
            raise SystemExit("MECHANICAL_HOLD: QE completed but corrected movable-force gate failed")
        latest_force = final_force
    else:
        proposal = relay.last_bfgs_proposed_trial(result["text"], nat, seed)
        if proposal is None:
            raise SystemExit("MECHANICAL_HOLD: timed-out four-rank segment emitted no admissible next BFGS trial")
        next_trial, proposal_evidence = proposal
        next_trial = apply_template(next_trial, template)
        delta = relay.max_displacement_angstrom(seed, next_trial)
        if delta <= 1e-10:
            raise SystemExit("MECHANICAL_HOLD: four-rank continuation would repeat the same geometry")
        source_evidence["next_trial_parent_evidence"] = proposal_evidence
        source_evidence["next_trial_displacement_angstrom"] = delta
    row = {
        "schema": SEGMENT_SCHEMA,
        "status": "RELAX_COMPLETE" if relax_complete else "CONTINUE",
        "segment": segment,
        "logical_segment": 8 + segment,
        "case_id": "L13-V28-K24-audit",
        "mpi_ranks": 4,
        "thread_caps": p["execution_amendment"]["thread_caps"],
        "timed_out_by_wrapper": result["timed_out_by_wrapper"],
        "pw_returncode": result["returncode"],
        "job_done": result["job_done"],
        "bfgs_finished": result["bfgs_finished"],
        "energy_ev": result["energy_ev"],
        "latest_authoritative_max_movable_force_ev_per_angstrom": latest_force,
        "input_atoms": seed,
        "final_atoms": final_atoms,
        "next_trial_atoms": next_trial,
        "source_evidence": source_evidence,
        "scientific_settings_changed": False,
        "execution_resource_changed": True,
        "kinetic_inputs_used": False,
        "raw_hashes": {"relax_input_sha256": sha256(inp), "relax_output_sha256": sha256(out)},
        "protocol_sha256": sha256(pp),
        "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
        "pw_sha256": sha256(Path(args.pw).resolve()),
        "elapsed_s": result["elapsed_s"],
    }
    base.cleanup_tmp(tmp)
    write_json(root / "MPI_RECOVERY_SEGMENT.json", row)
    base.stage_manifest(root, [root / "MPI_RECOVERY_SEGMENT.json"])
    print(json.dumps(row, indent=2, sort_keys=True))


def command_reproduce(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, _, surface, bundle = runtime_context(args, p)
    parity = load_json(Path(args.parity).resolve())
    if parity.get("status") != "PASS":
        raise SystemExit("MECHANICAL_HOLD: reproduction lacks passing MPI parity")
    seg_path = find_one(Path(args.prior_root).resolve(), "MPI_RECOVERY_SEGMENT.json")
    seg = load_json(seg_path)
    if seg.get("status") != "RELAX_COMPLETE" or not seg.get("final_atoms"):
        raise SystemExit("MECHANICAL_INCOMPLETE: L13 audit relaxation still incomplete after bounded MPI recovery")
    atoms = seg["final_atoms"]
    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]
    cell, _ = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 13, 28.0)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "reproduce"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_reproduce.in"; out = run_dir / "clean_reproduce.out"
    inp.write_text(base.qe_input(calculation="scf", prefix="co_cu111_clean_repro", cell=cell, atoms=fixed, kmesh=24, protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir).resolve(), outdir=tmp))
    result = run_pw_mpi(Path(args.pw).resolve(), inp, out, 4, int(args.runtime_cap_s))
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit("MECHANICAL_HOLD: independent four-rank audit SCF did not complete")
    delta = abs(float(seg["energy_ev"]) - float(result["energy_ev"]))
    gate = float(p["unchanged_science"]["independent_scf_reproduction_gate_ev"])
    force = float(seg["latest_authoritative_max_movable_force_ev_per_angstrom"])
    mechanical_pass = force <= float(p["unchanged_science"]["force_gate_ev_per_angstrom"]) and delta <= gate
    bulk_e0 = float(surface["inherited_stage_a_settings"]["bulk_e0_ev_per_atom"])
    surface_excess = (float(result["energy_ev"]) - 13.0 * bulk_e0) / 2.0
    layer_z = [float(a["position_angstrom"][2]) for a in atoms]
    summary = {
        "schema": "co-cu111-pbe-clean-surface-case-v0.1",
        "status": "COMPLETE" if mechanical_pass else "HOLD",
        "case_id": "L13-V28-K24-audit",
        "role": "audit",
        "layers": 13,
        "vacuum_angstrom": 28.0,
        "kmesh": 24,
        "cell_angstrom": cell,
        "final_atoms": atoms,
        "layer_z_angstrom": layer_z,
        "relax_energy_ev": seg["energy_ev"],
        "fixed_geometry_scf_energy_ev": result["energy_ev"],
        "energy_reproduction_delta_ev": delta,
        "max_movable_force_ev_per_angstrom": force,
        "mechanical_pass": mechanical_pass,
        "surface_excess_ev_per_surface_atom": surface_excess,
        "provenance": {
            "protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
            "stage_a_result_sha256": p["frozen_sources"]["stage_a_result_sha256"],
            "pw_sha256": p["frozen_sources"]["pw_x_sha256"],
            "bundle_sha256": sha256(Path(args.bundle).resolve()),
            "stage_a_scientific_settings_modified": False,
            "kinetic_inputs_used": False,
            "mpi_parity_sha256": sha256(Path(args.parity).resolve()),
            "mpi_recovery_protocol_sha256": sha256(pp),
            "execution_resource_changed": True,
            "scientific_settings_changed": False,
            "authoritative_total_force_parser": True
        },
        "raw_hashes": {
            "relax_segment_record_sha256": sha256(seg_path),
            "reproduce_input_sha256": sha256(inp),
            "reproduce_output_sha256": sha256(out),
            "mpi_parity_sha256": sha256(Path(args.parity).resolve())
        }
    }
    base.cleanup_tmp(tmp)
    write_json(root / "summary.json", summary)
    base.stage_manifest(root, [root / "summary.json"])
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not mechanical_pass:
        raise SystemExit(2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("self-test"); s.add_argument("--protocol", required=True); s.set_defaults(func=command_self_test)
    s = sub.add_parser("verify-seed"); s.add_argument("--protocol", required=True); s.add_argument("--segment8-root", required=True); s.set_defaults(func=command_verify_seed)
    for name, func in (("parity", command_parity), ("continue", command_continue), ("reproduce", command_reproduce)):
        s = sub.add_parser(name)
        s.add_argument("--protocol", required=True); s.add_argument("--surface-protocol", required=True)
        s.add_argument("--stage-a-result", required=True); s.add_argument("--bundle", required=True)
        s.add_argument("--pseudo-dir", required=True); s.add_argument("--pw", required=True); s.add_argument("--out", required=True)
        s.add_argument("--runtime-cap-s", type=int, required=True)
        if name == "parity": s.add_argument("--segment8-root", required=True)
        elif name == "continue":
            s.add_argument("--parity", required=True); s.add_argument("--prior-root", required=True); s.add_argument("--segment", type=int, required=True)
        else:
            s.add_argument("--parity", required=True); s.add_argument("--prior-root", required=True)
        s.set_defaults(func=func)
    args = ap.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
