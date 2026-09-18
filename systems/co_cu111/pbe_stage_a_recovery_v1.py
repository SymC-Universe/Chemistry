#!/usr/bin/env python3
"""Mechanical-only recovery wrapper for frozen CO/Cu(111) PBE Stage A.

This file does not redefine the scientific model. It imports the frozen
pbe_stage_a_runner_v1.py and uses its input generator, QE executor, hash
function, JSON writer, protocol parser, and bond grid unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
from typing import Any


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_frozen_runner(path: Path):
    spec = importlib.util.spec_from_file_location("co_cu111_frozen_stage_a", path)
    if spec is None or spec.loader is None:
        raise SystemExit("HOLD: cannot load frozen Stage A runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"HOLD: JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def verify_recovery_contract(contract_path: Path, protocol_path: Path, bundle_path: Path, runner_path: Path) -> dict[str, Any]:
    c = load_json(contract_path)
    if c.get("schema") != "co-cu111-stage-a-mechanical-recovery-v0.1":
        raise SystemExit("HOLD: wrong recovery-controller schema")
    if c.get("status") != "FROZEN_BEFORE_RECOVERY_RESULTS":
        raise SystemExit("HOLD: recovery controller is not frozen")
    frozen = c["frozen_inputs"]
    checks = [
        (protocol_path, frozen["protocol_git_blob_sha"]),
        (bundle_path, frozen["bundle_git_blob_sha"]),
        (runner_path, frozen["runner_git_blob_sha"]),
    ]
    for path, expected_blob in checks:
        payload = path.read_bytes()
        blob = hashlib.sha1((f"blob {len(payload)}\0").encode() + payload).hexdigest()
        if blob != expected_blob:
            raise SystemExit(f"HOLD: frozen Git blob mismatch for {path}")
    return c


def target_allowed(contract: dict[str, Any], cutoff_id: str, box: float) -> bool:
    return any(
        row["cutoff_id"] == cutoff_id and abs(float(row["box_angstrom"]) - float(box)) < 1e-9
        for row in contract["recovery_targets"]
    )


def chunk_allowed(contract: dict[str, Any], start_index: int, end_index: int) -> bool:
    return any(
        int(row["start_index"]) == start_index and int(row["end_index"]) == end_index
        for row in contract["bond_point_chunks"]
    )


def find_seed_member(seed_root: Path | None, cutoff_id: str, box: float) -> Path | None:
    if seed_root is None or not seed_root.exists():
        return None
    tag = f"co_{cutoff_id}_L{int(box) if float(box).is_integer() else box}"
    hits = [p for p in seed_root.rglob(tag) if p.is_dir()]
    return hits[0] if len(hits) == 1 else None


def valid_seed_point(seed_member: Path | None, tag: str, expected_input: str) -> tuple[bool, dict[str, Any] | None, Path | None]:
    if seed_member is None:
        return False, None, None
    d = seed_member / tag
    record_path = d / "run_record.json"
    inp = d / f"{tag}.in"
    out = d / f"{tag}.out"
    if not (record_path.is_file() and inp.is_file() and out.is_file()):
        return False, None, None
    try:
        rec = load_json(record_path)
    except Exception:
        return False, None, None
    if rec.get("returncode") != 0 or rec.get("job_done") is not True or rec.get("energy_ev_total") is None:
        return False, None, None
    try:
        if not math.isfinite(float(rec["energy_ev_total"])):
            return False, None, None
    except Exception:
        return False, None, None
    if rec.get("input_sha256") != file_sha256(inp) or rec.get("output_sha256") != file_sha256(out):
        return False, None, None
    if inp.read_text() != expected_input:
        return False, None, None
    return True, rec, d


def command_co_chunk(args: argparse.Namespace) -> None:
    runner_path = Path(args.runner).resolve()
    protocol_path = Path(args.protocol).resolve()
    bundle_path = Path(args.bundle).resolve()
    contract_path = Path(args.contract).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve()
    pw = Path(args.pw).resolve()
    root = Path(args.out).resolve()
    seed_root = Path(args.seed_root).resolve() if args.seed_root else None

    contract = verify_recovery_contract(contract_path, protocol_path, bundle_path, runner_path)
    if not target_allowed(contract, args.cutoff_id, args.box):
        raise SystemExit("HOLD: cutoff/box is not a preregistered recovery target")
    if not chunk_allowed(contract, args.start_index, args.end_index):
        raise SystemExit("HOLD: chunk is not preregistered")

    frozen = load_frozen_runner(runner_path)
    protocol, bundle = frozen.verify_inputs(protocol_path, bundle_path, pseudo_dir, pw)
    cutoff = frozen.protocol_cutoff(protocol, args.cutoff_id)
    grid = frozen.bond_grid(protocol["isolated_CO"]["bond_scan_angstrom"])
    if len(grid) != 23 or not (0 <= args.start_index <= args.end_index < len(grid)):
        raise SystemExit("HOLD: frozen bond grid/chunk mismatch")

    env = dict(os.environ)
    env["OMP_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    c_name = bundle["pseudopotentials"]["C"]["filename"]
    o_name = bundle["pseudopotentials"]["O"]["filename"]
    seed_member = find_seed_member(seed_root, args.cutoff_id, args.box)
    root.mkdir(parents=True, exist_ok=True)
    records = []

    for idx in range(args.start_index, args.end_index + 1):
        r = grid[idx]
        tag = f"r{r:.2f}"
        d = root / tag
        tmp = d / "tmp"
        d.mkdir(exist_ok=True)
        tmp.mkdir(exist_ok=True)
        inp = d / f"{tag}.in"
        out = d / f"{tag}.out"
        expected_input = frozen.co_input(
            r,
            float(args.box),
            int(cutoff["ecutwfc"]),
            int(cutoff["ecutrho"]),
            pseudo_dir,
            tmp,
            c_name,
            o_name,
        )

        reusable, seed_rec, seed_dir = valid_seed_point(seed_member, tag, expected_input)
        if reusable and seed_rec is not None and seed_dir is not None:
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(seed_dir, d)
            rec = load_json(d / "run_record.json")
            rec["mechanical_recovery_source"] = "reused_source_run_31371043888"
            frozen.write_json(d / "run_record.json", rec)
            records.append(rec)
            continue

        inp.write_text(expected_input)
        rc, elapsed, energy, done = frozen.run_pw(pw, inp, out, env)
        rec = {
            "bond_angstrom": r,
            "returncode": rc,
            "job_done": done,
            "energy_ev_total": energy,
            "elapsed_s": elapsed,
            "input_sha256": frozen.sha256(inp),
            "output_sha256": frozen.sha256(out),
            "mechanical_recovery_source": "recomputed_unchanged_frozen_input",
        }
        frozen.write_json(d / "run_record.json", rec)
        records.append(rec)
        if rc != 0 or not done or energy is None:
            raise SystemExit(f"MECHANICAL_INCOMPLETE: frozen CO point failed {args.cutoff_id} L{args.box} {tag}")
        for p in list(tmp.iterdir()):
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    chunk = {
        "schema": "co-cu111-stage-a-mechanical-recovery-chunk-v0.1",
        "status": "COMPLETE",
        "cutoff_id": args.cutoff_id,
        "box_angstrom": float(args.box),
        "start_index": args.start_index,
        "end_index": args.end_index,
        "records": records,
        "provenance": {
            "source_stage_a_run_id": int(contract["source_stage_a"]["run_id"]),
            "protocol_sha256": file_sha256(protocol_path),
            "bundle_sha256": file_sha256(bundle_path),
            "frozen_runner_sha256": file_sha256(runner_path),
            "recovery_contract_sha256": file_sha256(contract_path),
            "pw_sha256": file_sha256(pw),
            "scientific_settings_changed": False,
        },
    }
    frozen.write_json(root / f"CHUNK_{args.start_index:02d}_{args.end_index:02d}.json", chunk)


def validate_and_assemble_member(frozen, contract: dict[str, Any], protocol: dict[str, Any], bundle: dict[str, Any], member: Path, cutoff_id: str, box: float) -> dict[str, Any]:
    grid = frozen.bond_grid(protocol["isolated_CO"]["bond_scan_angstrom"])
    cutoff = frozen.protocol_cutoff(protocol, cutoff_id)
    records = []
    missing = []
    invalid = []
    for r in grid:
        tag = f"r{r:.2f}"
        d = member / tag
        rp = d / "run_record.json"
        inp = d / f"{tag}.in"
        out = d / f"{tag}.out"
        if not (rp.is_file() and inp.is_file() and out.is_file()):
            missing.append(tag)
            continue
        rec = load_json(rp)
        good = (
            rec.get("returncode") == 0
            and rec.get("job_done") is True
            and rec.get("energy_ev_total") is not None
            and rec.get("input_sha256") == file_sha256(inp)
            and rec.get("output_sha256") == file_sha256(out)
            and abs(float(rec.get("bond_angstrom")) - float(r)) < 1e-9
        )
        if not good:
            invalid.append(tag)
            continue
        records.append(rec)
    if missing or invalid or len(records) != 23:
        return {"complete": False, "missing": missing, "invalid": invalid, "record_count": len(records)}

    records.sort(key=lambda x: float(x["bond_angstrom"]))
    summary = {
        "schema": "co-cu111-pbe-stage-a-co-scan-v0.1",
        "status": "COMPLETE",
        "cutoff_id": cutoff_id,
        "ecutwfc_ry": cutoff["ecutwfc"],
        "ecutrho_ry": cutoff["ecutrho"],
        "box_angstrom": float(box),
        "records": records,
        "provenance": {
            "protocol_sha256": file_sha256(Path(contract["frozen_inputs"]["protocol"])),
            "bundle_sha256": file_sha256(Path(contract["frozen_inputs"]["bundle"])),
            "pw_sha256": bundle["solver_bundle"]["pw_x_sha256"],
            "c_pseudo_sha256": bundle["pseudopotentials"]["C"]["sha256"],
            "o_pseudo_sha256": bundle["pseudopotentials"]["O"]["sha256"],
            "scientific_settings_changed": False,
        },
    }
    frozen.write_json(member / "summary.json", summary)
    manifest_files = sorted(member.rglob("*.in")) + sorted(member.rglob("*.out")) + [member / "summary.json"]
    (member / "STAGE_TIME_MANIFEST.sha256").write_text(
        "\n".join(f"{frozen.sha256(p)}  {p.relative_to(member)}" for p in manifest_files) + "\n"
    )
    return {"complete": True, "missing": [], "invalid": [], "record_count": 23, "summary_sha256": file_sha256(member / "summary.json")}


def command_assemble_all(args: argparse.Namespace) -> None:
    runner_path = Path(args.runner).resolve()
    protocol_path = Path(args.protocol).resolve()
    bundle_path = Path(args.bundle).resolve()
    contract_path = Path(args.contract).resolve()
    root = Path(args.root).resolve()
    state_path = Path(args.state_out).resolve()

    contract = verify_recovery_contract(contract_path, protocol_path, bundle_path, runner_path)
    frozen = load_frozen_runner(runner_path)
    protocol = frozen.load_json(protocol_path)
    bundle = frozen.load_json(bundle_path)
    members = []
    all_complete = True
    for row in contract["recovery_targets"]:
        cutoff_id = row["cutoff_id"]
        box = float(row["box_angstrom"])
        box_tag = int(box) if box.is_integer() else box
        member = root / "stageA" / f"co_{cutoff_id}_L{box_tag}"
        result = validate_and_assemble_member(frozen, contract, protocol, bundle, member, cutoff_id, box)
        result.update({"cutoff_id": cutoff_id, "box_angstrom": box})
        members.append(result)
        all_complete = all_complete and result["complete"]

    state = {
        "schema": "co-cu111-stage-a-mechanical-recovery-state-v0.1",
        "status": "COMPLETE" if all_complete else "MECHANICAL_INCOMPLETE",
        "scientific_result_available": False,
        "members": members,
        "provenance": {
            "source_stage_a_run_id": contract["source_stage_a"]["run_id"],
            "recovery_contract_sha256": file_sha256(contract_path),
            "scientific_settings_changed": False,
        },
    }
    write_json(state_path, state)
    if not all_complete:
        raise SystemExit(3)


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)

    c = sp.add_parser("co-chunk")
    for name in ("runner", "protocol", "bundle", "contract", "pseudo_dir", "pw", "cutoff_id", "out"):
        c.add_argument("--" + name.replace("_", "-"), required=True)
    c.add_argument("--box", type=float, required=True)
    c.add_argument("--start-index", type=int, required=True)
    c.add_argument("--end-index", type=int, required=True)
    c.add_argument("--seed-root")
    c.set_defaults(func=command_co_chunk)

    a = sp.add_parser("assemble-all")
    for name in ("runner", "protocol", "bundle", "contract", "root", "state_out"):
        a.add_argument("--" + name.replace("_", "-"), required=True)
    a.set_defaults(func=command_assemble_all)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
