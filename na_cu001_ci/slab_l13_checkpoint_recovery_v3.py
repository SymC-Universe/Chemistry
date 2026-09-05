#!/usr/bin/env python3
"""Fail-closed checkpoint recovery for registered Na/Cu(001) L13 timeout cases.

The frozen scientific source and physical inputs are not modified. This wrapper
adds only Quantum ESPRESSO execution controls and auditable restart handling.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterator

FROZEN_SOURCE_COMMIT = "055b2f5d782c2a590e65ad429cefd0981f0dd37b"
REGISTERED_CASES = {
    (13, 16.0, 22),
    (13, 24.0, 20),
    (13, 24.0, 22),
}
RECOVERY_SCHEMA = "na-cu001-l13-checkpoint-recovery-v0.3"
BOOTSTRAP_SCHEMA = "na-cu001-l13-checkpoint-bootstrap-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n")


def registered_case(layers: int, vacuum: float, kmesh: int) -> tuple[int, float, int]:
    case = (int(layers), float(vacuum), int(kmesh))
    if case not in REGISTERED_CASES:
        raise SystemExit(f"HOLD: checkpoint recovery is not registered for {case}")
    return case


def inject_execution_controls(
    text: str, *, restart_mode: str, max_seconds: float
) -> str:
    if restart_mode not in {"from_scratch", "restart"}:
        raise ValueError(f"unsupported restart mode: {restart_mode}")
    lines = text.splitlines()
    try:
        control_index = lines.index("&CONTROL")
    except ValueError as exc:
        raise ValueError("QE input has no &CONTROL namelist") from exc
    forbidden = ("restart_mode", "max_seconds")
    if any(any(token in line.lower() for token in forbidden) for line in lines):
        raise ValueError("QE input already contains execution-control fields")
    additions = [
        f"  restart_mode = '{restart_mode}',",
        f"  max_seconds = {float(max_seconds):.1f},",
    ]
    lines[control_index + 1 : control_index + 1] = additions
    return "\n".join(lines) + "\n"


def manifest_entries(root: Path, target: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for path in sorted(target.rglob("*")):
        if path.is_file():
            entries.append((sha256(path), path.relative_to(root).as_posix()))
    return entries


def write_manifest(root: Path, target: Path, manifest: Path) -> dict[str, Any]:
    entries = manifest_entries(root, target)
    if not entries:
        raise SystemExit(f"HOLD: no restart files found under {target}")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("".join(f"{digest}  {name}\n" for digest, name in entries))
    return {
        "file_count": len(entries),
        "total_bytes": sum((root / name).stat().st_size for _, name in entries),
        "manifest_sha256": sha256(manifest),
    }


def verify_manifest(root: Path, manifest: Path) -> dict[str, Any]:
    checked = 0
    total_bytes = 0
    for number, line in enumerate(manifest.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or len(fields[0]) != 64:
            raise SystemExit(f"HOLD: malformed restart manifest line {number}")
        expected, relative = fields
        path = root / relative.strip()
        if not path.is_file() or sha256(path) != expected:
            raise SystemExit(f"HOLD: restart-state mismatch for {relative.strip()}")
        checked += 1
        total_bytes += path.stat().st_size
    if checked == 0:
        raise SystemExit("HOLD: restart manifest is empty")
    return {
        "file_count": checked,
        "total_bytes": total_bytes,
        "manifest_sha256": sha256(manifest),
    }


def load_frozen_modules(source_dir: Path) -> tuple[Any, Any, Any]:
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"HOLD: frozen source directory missing: {source_dir}")
    sys.path.insert(0, str(source_dir))
    v2 = importlib.import_module("slab_runner_v2")
    v3 = importlib.import_module("slab_runner_v3")
    v5 = importlib.import_module("slab_runner_v5")
    return v2, v3, v5


@contextmanager
def extended_layer_registry(v2: Any) -> Iterator[None]:
    original_layers = list(v2.LAYERS)
    try:
        v2.LAYERS = sorted(set(original_layers + [13]))
        yield
    finally:
        v2.LAYERS = original_layers


def case_paths(
    v5: Any, out: Path, layers: int, vacuum: float, kmesh: int
) -> tuple[str, Path, Path, Path]:
    tag = v5.case_tag(layers, vacuum, kmesh)
    job = out.resolve() / tag
    record = job / "run_record.json"
    restart_root = job / "tmp"
    return tag, job, record, restart_root


def completed_record(row: dict[str, Any]) -> bool:
    return bool(
        row.get("returncode") == 0
        and row.get("job_done")
        and row.get("scf_converged")
        and row.get("final_energy_ev") is not None
    )


def output_has_internal_error(output_path: Path) -> bool:
    text = output_path.read_text(errors="replace") if output_path.is_file() else ""
    return "Error in routine" in text or "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" in text


def verify_case_identity(
    row: dict[str, Any], *, tag: str, layers: int, vacuum: float, kmesh: int
) -> None:
    identity = {
        "tag": row.get("tag") == tag,
        "layers": int(row.get("layers", -1)) == int(layers),
        "vacuum": abs(float(row.get("vacuum_angstrom", -1.0)) - float(vacuum)) <= 1e-12,
        "kmesh": int(row.get("kmesh_inplane", -1)) == int(kmesh),
    }
    if not all(identity.values()):
        raise SystemExit(f"HOLD: recovery record identity mismatch: {identity}")


def verify_compact_hashes(job: Path, row: dict[str, Any], pseudo: Path | None = None) -> None:
    tag = str(row.get("tag") or "")
    inp = job / f"{tag}.in"
    out = job / f"{tag}.out"
    if not inp.is_file() or sha256(inp) != row.get("input_sha256"):
        raise SystemExit("HOLD: recovery input hash mismatch")
    if not out.is_file() or sha256(out) != row.get("output_sha256"):
        raise SystemExit("HOLD: recovery output hash mismatch")
    if pseudo is not None:
        if not pseudo.is_file() or sha256(pseudo) != row.get("pseudo_sha256"):
            raise SystemExit("HOLD: recovery pseudopotential hash mismatch")


def run_segment(args: argparse.Namespace) -> None:
    layers, vacuum, kmesh = registered_case(args.layers, args.vacuum, args.kmesh)
    if int(args.np) != 2:
        raise SystemExit("HOLD: restart requires the original two-process parallelization")
    if args.segment < 1:
        raise SystemExit("HOLD: segment number must be positive")

    source_dir = Path(args.source_dir)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    v2, v3, v5 = load_frozen_modules(source_dir)
    tag, job, record_path, restart_root = case_paths(v5, out, layers, vacuum, kmesh)
    restart_manifest = job / "RESTART_STATE.sha256"

    prior_restart: dict[str, Any] | None = None
    if args.restart_mode == "restart":
        if not restart_manifest.is_file():
            raise SystemExit("HOLD: restart requested without a restart-state manifest")
        prior_restart = verify_manifest(out, restart_manifest)

    base_qe_input: Callable[..., str] = v5.qe_input_esm_centered

    def segmented_qe_input(**kwargs: Any) -> str:
        return inject_execution_controls(
            base_qe_input(**kwargs),
            restart_mode=args.restart_mode,
            max_seconds=float(args.max_seconds),
        )

    hold_message: str | None = None
    with extended_layer_registry(v2):
        v2.load_bulk = v3.load_bulk_v04
        v2.fcc001_geometry = v5.fcc001_geometry_esm_centered
        v2.qe_input = segmented_qe_input
        namespace = SimpleNamespace(
            layers=layers,
            vacuum=vacuum,
            kmesh=kmesh,
            handoff=args.handoff,
            bulk_result=args.bulk_result,
            pw=args.pw,
            pseudo_dir=args.pseudo_dir,
            out=str(out),
            np=int(args.np),
        )
        try:
            v2.run_case(namespace)
        except SystemExit as exc:
            hold_message = str(exc)

        if not record_path.is_file():
            raise SystemExit(f"HOLD: segment produced no run record for {tag}")
        row = json.loads(record_path.read_text())
        verify_case_identity(row, tag=tag, layers=layers, vacuum=vacuum, kmesh=kmesh)
        verify_compact_hashes(job, row)
        complete = completed_record(row)

        restart_state: dict[str, Any] | None = None
        if not complete:
            output_path = job / f"{tag}.out"
            if output_has_internal_error(output_path):
                raise SystemExit("HOLD: QE reported an internal error before checkpointing")
            if not restart_root.is_dir():
                raise SystemExit("HOLD: incomplete segment has no QE restart directory")
            # Persist and hash the restart state before optional metadata attachment.
            restart_state = write_manifest(out, restart_root, restart_manifest)

        # Layer 13 must remain registered while the frozen geometry helper runs.
        v5.attach_geometry_to_case_record(out, layers, vacuum, kmesh)
        row = json.loads(record_path.read_text())

    recovery = {
        "schema": RECOVERY_SCHEMA,
        "frozen_source_commit": FROZEN_SOURCE_COMMIT,
        "case": {
            "layers": layers,
            "vacuum_angstrom": vacuum,
            "kmesh_inplane": kmesh,
        },
        "segment": int(args.segment),
        "restart_mode": args.restart_mode,
        "max_seconds": float(args.max_seconds),
        "mpi_processes": int(args.np),
        "same_parallelization_required_for_restart": True,
        "prior_restart_state": prior_restart,
        "new_restart_state": restart_state,
        "complete": complete,
        "runner_hold_message": hold_message,
    }
    row["checkpoint_recovery"] = recovery
    record_path.write_text(json.dumps(row, indent=2, sort_keys=False) + "\n")

    status = {
        **recovery,
        "record_path": record_path.relative_to(out).as_posix(),
        "record_sha256": sha256(record_path),
        "final_energy_ev": row.get("final_energy_ev"),
        "job_done": bool(row.get("job_done")),
        "scf_converged": bool(row.get("scf_converged")),
        "returncode": row.get("returncode"),
    }
    write_json(Path(args.status_out), status)
    print(json.dumps(status, indent=2))


def bootstrap_restart(args: argparse.Namespace) -> None:
    layers, vacuum, kmesh = registered_case(args.layers, args.vacuum, args.kmesh)
    source_dir = Path(args.source_dir)
    out = Path(args.out).resolve()
    pseudo = Path(args.pseudo).resolve()
    v2, _v3, v5 = load_frozen_modules(source_dir)
    tag, job, record_path, restart_root = case_paths(v5, out, layers, vacuum, kmesh)
    restart_manifest = job / "RESTART_STATE.sha256"
    if not record_path.is_file():
        raise SystemExit(f"HOLD: imported checkpoint has no run record for {tag}")

    with extended_layer_registry(v2):
        row = json.loads(record_path.read_text())
        verify_case_identity(row, tag=tag, layers=layers, vacuum=vacuum, kmesh=kmesh)
        verify_compact_hashes(job, row, pseudo)
        if completed_record(row):
            raise SystemExit("HOLD: bootstrap was requested for an already complete case")
        if output_has_internal_error(job / f"{tag}.out"):
            raise SystemExit("HOLD: imported checkpoint contains a QE internal error")
        if not restart_root.is_dir():
            raise SystemExit("HOLD: imported checkpoint has no QE restart directory")
        restart_state = (
            verify_manifest(out, restart_manifest)
            if restart_manifest.is_file()
            else write_manifest(out, restart_root, restart_manifest)
        )
        v5.attach_geometry_to_case_record(out, layers, vacuum, kmesh)
        row = json.loads(record_path.read_text())
        try:
            v5.audit_input_file(record_path, row)
        except SystemExit as exc:
            raise SystemExit(f"HOLD: imported QE input audit failed: {exc}") from exc

    bootstrap = {
        "schema": BOOTSTRAP_SCHEMA,
        "frozen_source_commit": FROZEN_SOURCE_COMMIT,
        "case": {
            "layers": layers,
            "vacuum_angstrom": vacuum,
            "kmesh_inplane": kmesh,
        },
        "source_workflow_run_id": int(args.source_run_id),
        "source_artifact_id": int(args.source_artifact_id),
        "source_artifact_name": args.source_artifact_name,
        "source_artifact_digest": args.source_artifact_digest,
        "restart_state": restart_state,
    }
    row["checkpoint_bootstrap"] = bootstrap
    record_path.write_text(json.dumps(row, indent=2, sort_keys=False) + "\n")
    status = {
        **bootstrap,
        "complete": False,
        "record_path": record_path.relative_to(out).as_posix(),
        "record_sha256": sha256(record_path),
    }
    write_json(Path(args.status_out), status)
    print(json.dumps(status, indent=2))


def add_case_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--layers", required=True, type=int)
    parser.add_argument("--vacuum", required=True, type=float)
    parser.add_argument("--kmesh", required=True, type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--status-out", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    segment = sub.add_parser("segment")
    add_case_arguments(segment)
    segment.add_argument("--segment", required=True, type=int)
    segment.add_argument("--restart-mode", required=True, choices=["from_scratch", "restart"])
    segment.add_argument("--max-seconds", required=True, type=float)
    segment.add_argument("--handoff", required=True)
    segment.add_argument("--bulk-result", required=True)
    segment.add_argument("--pw", required=True)
    segment.add_argument("--pseudo-dir", required=True)
    segment.add_argument("--np", required=True, type=int)
    segment.set_defaults(func=run_segment)

    bootstrap = sub.add_parser("bootstrap")
    add_case_arguments(bootstrap)
    bootstrap.add_argument("--pseudo", required=True)
    bootstrap.add_argument("--source-run-id", required=True, type=int)
    bootstrap.add_argument("--source-artifact-id", required=True, type=int)
    bootstrap.add_argument("--source-artifact-name", required=True)
    bootstrap.add_argument("--source-artifact-digest", required=True)
    bootstrap.set_defaults(func=bootstrap_restart)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
