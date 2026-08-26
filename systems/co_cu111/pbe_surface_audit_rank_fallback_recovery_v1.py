#!/usr/bin/env python3
"""Fail-closed rank-fallback recovery for the frozen CO/Cu(111) L13 audit.

Four MPI ranks are already excluded by immutable parity evidence. This runner
prospectively tests three and then two ranks against the same immutable direct
one-rank reference using unchanged tolerances, chooses the highest passing rank,
and otherwise falls back to the original direct one-rank pw.x execution.
Scientific inputs, force/reproduction gates, and clean-surface rules are not
changed. Only execution parallelism and the bounded continuation budget change.
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
PROTOCOL_SCHEMA = "co-cu111-pbe-surface-audit-rank-fallback-recovery-v0.1"
PROTOCOL_STATUS = "FROZEN_MECHANICAL_RANK_FALLBACK_AFTER_FOUR_RANK_PARITY_HOLD"
SELECTION_SCHEMA = "co-cu111-pbe-surface-audit-rank-selection-v0.1"
SEGMENT_SCHEMA = "co-cu111-pbe-surface-audit-rank-fallback-segment-v0.1"
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
    if p.get("schema") != PROTOCOL_SCHEMA or p.get("status") != PROTOCOL_STATUS:
        raise SystemExit("MECHANICAL_HOLD: wrong or unfrozen rank-fallback protocol")
    if p.get("scientific_scope") != "NO_SCIENTIFIC_CONFIGURATION_CHANGE":
        raise SystemExit("MECHANICAL_HOLD: scientific scope changed")
    q = p.get("rank_qualification", {})
    if q.get("candidate_mpi_ranks_descending") != [3, 2] or int(q.get("fallback_mpi_ranks", -1)) != 1:
        raise SystemExit("MECHANICAL_HOLD: rank candidate order/fallback changed")
    if float(q.get("energy_absolute_difference_max_ev", math.inf)) != 0.0001:
        raise SystemExit("MECHANICAL_HOLD: energy parity threshold changed")
    if float(q.get("force_component_absolute_difference_max_ev_per_angstrom", math.inf)) != 0.0001:
        raise SystemExit("MECHANICAL_HOLD: force parity threshold changed")
    ex = p.get("execution", {})
    if int(ex.get("maximum_new_continuation_segments", -1)) != 4:
        raise SystemExit("MECHANICAL_HOLD: bounded continuation count changed")
    if ex.get("logical_segment_numbers") != [9, 10, 11, 12]:
        raise SystemExit("MECHANICAL_HOLD: logical continuation sequence changed")
    prov = p.get("provenance", {})
    if prov.get("scientific_settings_changed") is not False or prov.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: provenance is not clean")
    return p


def verify_repo_sources(p: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parent.parent.parent
    for key in (
        "surface_protocol",
        "surface_runner",
        "proposal_relay_protocol",
        "proposal_relay_runner",
        "four_rank_protocol",
        "four_rank_runner",
    ):
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


def verify_four_rank_hold(path: Path, p: dict[str, Any]) -> dict[str, Any]:
    expected = p["parent_four_rank_parity"]
    if sha256(path) != expected["result_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: four-rank parity result hash mismatch")
    row = load_json(path)
    checks = {
        "schema": PARITY_SCHEMA,
        "status": "MECHANICAL_MPI_PARITY_HOLD",
        "reference_mpi_ranks": 1,
        "test_mpi_ranks": 4,
    }
    for key, value in checks.items():
        if row.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: four-rank parity evidence mismatch: {key}")
    numeric = (
        ("energy_absolute_difference_ev", "energy_absolute_difference_ev"),
        ("force_component_absolute_difference_max_ev_per_angstrom", "force_component_absolute_difference_max_ev_per_angstrom"),
        ("energy_tolerance_ev", "energy_tolerance_ev"),
        ("force_tolerance_ev_per_angstrom", "force_tolerance_ev_per_angstrom"),
    )
    for row_key, expected_key in numeric:
        if abs(float(row[row_key]) - float(expected[expected_key])) > 1e-15:
            raise SystemExit(f"MECHANICAL_HOLD: four-rank numeric evidence drift: {row_key}")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: four-rank provenance mismatch")
    if row.get("raw_hashes", {}).get("input_sha256") != expected["raw_input_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: four-rank parity input hash drift")
    if row.get("raw_hashes", {}).get("output_sha256") != expected["raw_output_sha256"]:
        raise SystemExit("MECHANICAL_HOLD: four-rank parity output hash drift")
    return row


def command_for_rank(pw: Path, ranks: int) -> list[str]:
    if int(ranks) == 1:
        return [str(pw)]
    if int(ranks) < 2:
        raise SystemExit("MECHANICAL_HOLD: invalid rank count")
    return ["mpirun", "-np", str(int(ranks)), str(pw)]


def run_pw(pw: Path, inp: Path, out: Path, ranks: int, cap_s: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    cmd = command_for_rank(pw, ranks)
    start = time.time()
    timed_out = False
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


def reference_state(seg: dict[str, Any], text: str, p: dict[str, Any]) -> tuple[float, list[tuple[float, float, float]]]:
    nat = int(seg["layers"])
    blocks = authoritative_force_blocks(text, nat)
    if not blocks:
        raise SystemExit("MECHANICAL_HOLD: no authoritative one-rank force block")
    energies = [float(x) * RY_TO_EV for x in ENERGY_RE.findall(text)]
    if not energies:
        raise SystemExit("MECHANICAL_HOLD: no raw one-rank input energy")
    energy = energies[0]
    expected = float(p["parser_correction"]["segment8_true_input_energy_ev"])
    if abs(energy - expected) > 1e-8:
        raise SystemExit("MECHANICAL_HOLD: one-rank reference energy drift")
    return energy, blocks[0]


def candidate_parity(
    *, base, surface: dict[str, Any], bundle: dict[str, Any], p: dict[str, Any], seg: dict[str, Any],
    ref_energy: float, ref_forces: list[tuple[float, float, float]], pw: Path, pseudo_dir: Path,
    ranks: int, cap_s: int, root: Path
) -> dict[str, Any]:
    atoms = apply_template(seg["input_atoms"], seg["input_atoms"])
    cell = seg["cell_angstrom"]
    run_dir = root / f"parity_rank_{ranks}"
    run_dir.mkdir(parents=True, exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "parity.in"; out = run_dir / "parity.out"
    inp.write_text(base.qe_input(
        calculation="scf", prefix=f"co_cu111_rank{ranks}_parity", cell=cell, atoms=atoms, kmesh=24,
        protocol=surface, bundle=bundle, pseudo_dir=pseudo_dir, outdir=tmp
    ))
    result = run_pw(pw, inp, out, ranks, cap_s)
    record: dict[str, Any] = {
        "test_mpi_ranks": ranks,
        "reference_mpi_ranks": 1,
        "execution_mode": "MPI" if ranks > 1 else "DIRECT_ONE_RANK",
        "returncode": result["returncode"],
        "elapsed_s": result["elapsed_s"],
        "timed_out_by_wrapper": result["timed_out_by_wrapper"],
        "job_done": result["job_done"],
        "scientific_settings_changed": False,
        "kinetic_inputs_used": False,
        "raw_hashes": {"input_sha256": sha256(inp), "output_sha256": sha256(out)},
    }
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        record.update({"status": "MECHANICAL_CANDIDATE_EXECUTION_REJECTED", "reason": "SCF_INCOMPLETE"})
        base.cleanup_tmp(tmp)
        return record
    blocks = authoritative_force_blocks(result["text"], int(seg["layers"]))
    if not blocks:
        record.update({"status": "MECHANICAL_CANDIDATE_EXECUTION_REJECTED", "reason": "TOTAL_FORCE_BLOCK_MISSING"})
        base.cleanup_tmp(tmp)
        return record
    energy_delta = abs(float(result["energy_ev"]) - ref_energy)
    force_delta = max_force_component_difference_ev_a(blocks[-1], ref_forces)
    q = p["rank_qualification"]
    passed = energy_delta <= float(q["energy_absolute_difference_max_ev"]) and force_delta <= float(q["force_component_absolute_difference_max_ev_per_angstrom"])
    record.update({
        "status": "PASS" if passed else "NUMERICAL_PARITY_REJECTED",
        "reference_energy_ev": ref_energy,
        "test_energy_ev": result["energy_ev"],
        "energy_absolute_difference_ev": energy_delta,
        "force_component_absolute_difference_max_ev_per_angstrom": force_delta,
        "energy_tolerance_ev": q["energy_absolute_difference_max_ev"],
        "force_tolerance_ev_per_angstrom": q["force_component_absolute_difference_max_ev_per_angstrom"],
        "reference_true_max_movable_force_ev_per_angstrom": max_movable_force_ev_a(ref_forces, atoms),
        "test_true_max_movable_force_ev_per_angstrom": max_movable_force_ev_a(blocks[-1], atoms),
    })
    base.cleanup_tmp(tmp)
    return record


def select_highest_passing(records: list[dict[str, Any]], candidates: list[int], fallback: int) -> int:
    by_rank = {int(r["test_mpi_ranks"]): r for r in records}
    for rank in candidates:
        if by_rank.get(rank, {}).get("status") == "PASS":
            return rank
    return fallback


def command_self_test(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    science = p["unchanged_science"]
    exact = {
        "layers": 13,
        "vacuum_angstrom": 28.0,
        "kmesh": 24,
        "ecutwfc_ry": 90,
        "ecutrho_ry": 900,
        "force_gate_ev_per_angstrom": 0.02,
        "independent_scf_reproduction_gate_ev": 0.001,
    }
    for key, value in exact.items():
        if science.get(key) != value:
            raise SystemExit(f"MECHANICAL_HOLD: frozen value changed: {key}")
    print("RANK_FALLBACK_RECOVERY_SELF_TEST_PASS")
    print("SCIENTIFIC_SETTINGS_CHANGED=false")
    print("PARITY_THRESHOLDS_CHANGED=false")
    print("KINETIC_INPUTS_USED=false")


def command_verify_evidence(args: argparse.Namespace) -> None:
    p = protocol(Path(args.protocol).resolve())
    seg, _, text = verify_segment8(Path(args.segment8_root).resolve(), p)
    blocks = authoritative_force_blocks(text, int(seg["layers"]))
    if len(blocks) < 2:
        raise SystemExit("MECHANICAL_HOLD: segment 8 lacks two authoritative force blocks")
    f0 = max_movable_force_ev_a(blocks[0], seg["input_atoms"])
    f1 = max_movable_force_ev_a(blocks[1], seg["input_atoms"])
    pc = p["parser_correction"]
    if abs(f0 - float(pc["segment8_true_input_max_movable_force_ev_per_angstrom"])) > 1e-10:
        raise SystemExit("MECHANICAL_HOLD: segment-8 input force drift")
    if abs(f1 - float(pc["segment8_true_second_evaluated_max_movable_force_ev_per_angstrom"])) > 1e-10:
        raise SystemExit("MECHANICAL_HOLD: segment-8 second force drift")
    four = verify_four_rank_hold(Path(args.four_rank_result).resolve(), p)
    print(json.dumps({
        "status": "IMMUTABLE_EVIDENCE_VERIFIED",
        "segment8_input_force_ev_per_angstrom": f0,
        "segment8_second_force_ev_per_angstrom": f1,
        "four_rank_status": four["status"],
        "four_rank_force_delta_ev_per_angstrom": four["force_component_absolute_difference_max_ev_per_angstrom"],
    }, sort_keys=True))


def command_qualify(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, _, surface, bundle = runtime_context(args, p)
    four_path = Path(args.four_rank_result).resolve()
    verify_four_rank_hold(four_path, p)
    seg, _, text = verify_segment8(Path(args.segment8_root).resolve(), p)
    ref_energy, ref_forces = reference_state(seg, text, p)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    candidates = [int(x) for x in p["rank_qualification"]["candidate_mpi_ranks_descending"]]
    fallback = int(p["rank_qualification"]["fallback_mpi_ranks"])
    records: list[dict[str, Any]] = []
    for rank in candidates:
        record = candidate_parity(
            base=base, surface=surface, bundle=bundle, p=p, seg=seg, ref_energy=ref_energy,
            ref_forces=ref_forces, pw=Path(args.pw).resolve(), pseudo_dir=Path(args.pseudo_dir).resolve(),
            ranks=rank, cap_s=int(args.runtime_cap_s), root=root
        )
        records.append(record)
        write_json(root / f"RANK_{rank}_PARITY_RESULT.json", record)
        if record.get("status") == "PASS":
            break
    selected = select_highest_passing(records, candidates, fallback)
    runner_label = p["execution"]["one_rank_runner_label"] if selected == 1 else p["execution"]["parallel_runner_label"]
    selection = {
        "schema": SELECTION_SCHEMA,
        "status": "PASS",
        "selected_mpi_ranks": selected,
        "selected_execution_mode": "DIRECT_ONE_RANK" if selected == 1 else "MPI",
        "selected_runner_label": runner_label,
        "selection_rule": p["rank_qualification"]["selection_rule"],
        "candidate_records": records,
        "four_rank_excluded": True,
        "four_rank_result_sha256": sha256(four_path),
        "reference_mpi_ranks": 1,
        "energy_tolerance_ev": p["rank_qualification"]["energy_absolute_difference_max_ev"],
        "force_tolerance_ev_per_angstrom": p["rank_qualification"]["force_component_absolute_difference_max_ev_per_angstrom"],
        "scientific_settings_changed": False,
        "parity_thresholds_changed": False,
        "kinetic_inputs_used": False,
        "protocol_sha256": sha256(pp),
    }
    write_json(root / "RANK_SELECTION_RESULT.json", selection)
    print(json.dumps(selection, indent=2, sort_keys=True))


def load_selection(path: Path, p: dict[str, Any]) -> dict[str, Any]:
    row = load_json(path)
    if row.get("schema") != SELECTION_SCHEMA or row.get("status") != "PASS":
        raise SystemExit("MECHANICAL_HOLD: invalid rank-selection authorization")
    selected = int(row.get("selected_mpi_ranks", -1))
    candidates = [int(x) for x in p["rank_qualification"]["candidate_mpi_ranks_descending"]]
    if selected not in candidates + [1]:
        raise SystemExit("MECHANICAL_HOLD: selected rank outside frozen set")
    expected = select_highest_passing(row.get("candidate_records", []), candidates, 1)
    if selected != expected:
        raise SystemExit("MECHANICAL_HOLD: rank selection does not follow frozen rule")
    if float(row.get("energy_tolerance_ev", math.inf)) != 0.0001 or float(row.get("force_tolerance_ev_per_angstrom", math.inf)) != 0.0001:
        raise SystemExit("MECHANICAL_HOLD: selection record threshold drift")
    if row.get("scientific_settings_changed") is not False or row.get("kinetic_inputs_used") is not False:
        raise SystemExit("MECHANICAL_HOLD: selection provenance mismatch")
    return row


def load_prior_seed(prior_root: Path, p: dict[str, Any], segment: int) -> tuple[list[dict[str, Any]], dict[str, Any], bool]:
    if segment == 1:
        seg, _, _ = verify_segment8(prior_root, p)
        return seg["next_trial_atoms"], {
            "source": "proposal_relay_segment_8",
            "source_sha256": p["segment8_seed"]["relay_segment_sha256"],
        }, False
    q = find_one(prior_root, "RANK_FALLBACK_SEGMENT.json")
    row = load_json(q)
    if row.get("schema") != SEGMENT_SCHEMA or int(row.get("segment", -1)) != segment - 1:
        raise SystemExit("MECHANICAL_HOLD: prior rank-fallback segment mismatch")
    if row.get("status") == "RELAX_COMPLETE":
        return row["final_atoms"], {"source": "prior_relax_complete", "source_sha256": sha256(q)}, True
    if row.get("status") != "CONTINUE":
        raise SystemExit("MECHANICAL_HOLD: prior rank-fallback status invalid")
    return row["next_trial_atoms"], {"source": "prior_next_trial", "source_sha256": sha256(q)}, False


def command_continue(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, relay, surface, bundle = runtime_context(args, p)
    selection_path = Path(args.selection).resolve()
    selection = load_selection(selection_path, p)
    ranks = int(selection["selected_mpi_ranks"])
    segment = int(args.segment)
    max_segments = int(p["execution"]["maximum_new_continuation_segments"])
    if segment < 1 or segment > max_segments:
        raise SystemExit("MECHANICAL_HOLD: continuation segment outside frozen bound")
    seed, source_evidence, already_complete = load_prior_seed(Path(args.prior_root).resolve(), p, segment)
    cell, template = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 13, 28.0)
    seed = apply_template(seed, template)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    if already_complete:
        source_row = load_json(find_one(Path(args.prior_root).resolve(), "RANK_FALLBACK_SEGMENT.json"))
        carried = dict(source_row)
        carried.update({
            "segment": segment,
            "logical_segment": 8 + segment,
            "carried_forward_without_recomputation": True,
            "source_evidence": source_evidence,
        })
        write_json(root / "RANK_FALLBACK_SEGMENT.json", carried)
        base.stage_manifest(root, [root / "RANK_FALLBACK_SEGMENT.json"])
        print(json.dumps(carried, indent=2, sort_keys=True))
        return
    run_dir = root / "relax"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_relax.in"; out = run_dir / "clean_relax.out"
    inp.write_text(base.qe_input(
        calculation="relax", prefix="co_cu111_clean", cell=cell, atoms=seed, kmesh=24,
        protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir).resolve(), outdir=tmp
    ))
    result = run_pw(Path(args.pw).resolve(), inp, out, ranks, int(args.runtime_cap_s))
    if result["returncode"] != 0 and not result["timed_out_by_wrapper"]:
        raise SystemExit(f"MECHANICAL_HOLD: selected {ranks}-rank pw.x failed, rc={result['returncode']}")
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
            raise SystemExit("SCIENTIFIC_HOLD: QE completed but corrected movable-force gate failed")
        latest_force = final_force
    else:
        proposal = relay.last_bfgs_proposed_trial(result["text"], nat, seed)
        if proposal is None:
            raise SystemExit("MECHANICAL_HOLD: bounded segment emitted no admissible next BFGS trial")
        next_trial, proposal_evidence = proposal
        next_trial = apply_template(next_trial, template)
        delta = relay.max_displacement_angstrom(seed, next_trial)
        if delta <= 1e-10:
            raise SystemExit("MECHANICAL_HOLD: continuation would repeat the same geometry")
        source_evidence["next_trial_parent_evidence"] = proposal_evidence
        source_evidence["next_trial_displacement_angstrom"] = delta
    row = {
        "schema": SEGMENT_SCHEMA,
        "status": "RELAX_COMPLETE" if relax_complete else "CONTINUE",
        "segment": segment,
        "logical_segment": 8 + segment,
        "case_id": "L13-V28-K24-audit",
        "mpi_ranks": ranks,
        "execution_mode": selection["selected_execution_mode"],
        "runner_label": selection["selected_runner_label"],
        "thread_caps": p["execution"]["thread_caps"],
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
        "parallelization_changed": ranks != 1,
        "kinetic_inputs_used": False,
        "raw_hashes": {"relax_input_sha256": sha256(inp), "relax_output_sha256": sha256(out)},
        "protocol_sha256": sha256(pp),
        "rank_selection_sha256": sha256(selection_path),
        "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
        "pw_sha256": sha256(Path(args.pw).resolve()),
        "elapsed_s": result["elapsed_s"],
    }
    base.cleanup_tmp(tmp)
    write_json(root / "RANK_FALLBACK_SEGMENT.json", row)
    base.stage_manifest(root, [root / "RANK_FALLBACK_SEGMENT.json"])
    print(json.dumps(row, indent=2, sort_keys=True))


def command_reproduce(args: argparse.Namespace) -> None:
    pp = Path(args.protocol).resolve(); p = protocol(pp)
    base, _, surface, bundle = runtime_context(args, p)
    selection_path = Path(args.selection).resolve()
    selection = load_selection(selection_path, p)
    ranks = int(selection["selected_mpi_ranks"])
    seg_path = find_one(Path(args.prior_root).resolve(), "RANK_FALLBACK_SEGMENT.json")
    seg = load_json(seg_path)
    if seg.get("status") != "RELAX_COMPLETE" or not seg.get("final_atoms"):
        raise SystemExit("MECHANICAL_INCOMPLETE: L13 audit relaxation still incomplete after four bounded fallback segments")
    if int(seg.get("mpi_ranks", -1)) != ranks:
        raise SystemExit("MECHANICAL_HOLD: final segment rank does not match selection")
    atoms = seg["final_atoms"]
    fixed = json.loads(json.dumps(atoms))
    for atom in fixed:
        atom["flags"] = [0, 0, 0]
    cell, _ = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 13, 28.0)
    root = Path(args.out).resolve(); root.mkdir(parents=True, exist_ok=True)
    run_dir = root / "reproduce"; run_dir.mkdir(exist_ok=True)
    tmp = run_dir / "tmp"; tmp.mkdir(exist_ok=True)
    inp = run_dir / "clean_reproduce.in"; out = run_dir / "clean_reproduce.out"
    inp.write_text(base.qe_input(
        calculation="scf", prefix="co_cu111_clean_repro", cell=cell, atoms=fixed, kmesh=24,
        protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir).resolve(), outdir=tmp
    ))
    result = run_pw(Path(args.pw).resolve(), inp, out, ranks, int(args.runtime_cap_s))
    if result["returncode"] != 0 or not result["job_done"] or result["energy_ev"] is None:
        raise SystemExit(f"MECHANICAL_HOLD: independent {ranks}-rank audit SCF did not complete")
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
        "selected_mpi_ranks": ranks,
        "selected_execution_mode": selection["selected_execution_mode"],
        "provenance": {
            "protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
            "stage_a_result_sha256": p["frozen_sources"]["stage_a_result_sha256"],
            "pw_sha256": p["frozen_sources"]["pw_x_sha256"],
            "bundle_sha256": sha256(Path(args.bundle).resolve()),
            "stage_a_scientific_settings_modified": False,
            "kinetic_inputs_used": False,
            "rank_selection_sha256": sha256(selection_path),
            "rank_fallback_protocol_sha256": sha256(pp),
            "scientific_settings_changed": False,
            "authoritative_total_force_parser": True,
            "four_rank_permanently_excluded": True,
        },
        "raw_hashes": {
            "relax_segment_record_sha256": sha256(seg_path),
            "reproduce_input_sha256": sha256(inp),
            "reproduce_output_sha256": sha256(out),
            "rank_selection_sha256": sha256(selection_path),
        },
    }
    base.cleanup_tmp(tmp)
    write_json(root / "summary.json", summary)
    base.stage_manifest(root, [root / "summary.json"])
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not mechanical_pass:
        raise SystemExit(2)


def add_runtime_args(s: argparse.ArgumentParser) -> None:
    s.add_argument("--protocol", required=True)
    s.add_argument("--surface-protocol", required=True)
    s.add_argument("--stage-a-result", required=True)
    s.add_argument("--bundle", required=True)
    s.add_argument("--pseudo-dir", required=True)
    s.add_argument("--pw", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--runtime-cap-s", type=int, required=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("self-test")
    s.add_argument("--protocol", required=True)
    s.set_defaults(func=command_self_test)
    s = sub.add_parser("verify-evidence")
    s.add_argument("--protocol", required=True)
    s.add_argument("--segment8-root", required=True)
    s.add_argument("--four-rank-result", required=True)
    s.set_defaults(func=command_verify_evidence)
    s = sub.add_parser("qualify")
    add_runtime_args(s)
    s.add_argument("--segment8-root", required=True)
    s.add_argument("--four-rank-result", required=True)
    s.set_defaults(func=command_qualify)
    s = sub.add_parser("continue")
    add_runtime_args(s)
    s.add_argument("--selection", required=True)
    s.add_argument("--prior-root", required=True)
    s.add_argument("--segment", type=int, required=True)
    s.set_defaults(func=command_continue)
    s = sub.add_parser("reproduce")
    add_runtime_args(s)
    s.add_argument("--selection", required=True)
    s.add_argument("--prior-root", required=True)
    s.set_defaults(func=command_reproduce)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
