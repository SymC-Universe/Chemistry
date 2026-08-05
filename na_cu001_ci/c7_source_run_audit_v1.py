#!/usr/bin/env python3
"""Audit the immutable 64-job Na/Cu(001) C7 source run across all attempts."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

LAYERS = (5, 7, 9, 11)
VACUUMS = (12, 16, 20, 24)
KMESHES = (16, 18, 20, 22)
SLAB_RE = re.compile(r"^slab-cases \((5|7|9|11), (12|16|20|24), (16|18|20|22)\)$")


def read(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text())
    except Exception as exc:
        raise SystemExit(f"HOLD: unreadable JSON {path}: {exc}") from exc


def pages(payload: Any, key: str) -> list[dict[str, Any]]:
    page_list = payload if isinstance(payload, list) else [payload]
    rows: list[dict[str, Any]] = []
    for page in page_list:
        if not isinstance(page, dict) or not isinstance(page.get(key), list):
            raise SystemExit(f"HOLD: malformed paginated {key} payload")
        rows.extend(row for row in page[key] if isinstance(row, dict))
    return rows


def order_key(job: dict[str, Any]) -> tuple[int, int]:
    return int(job.get("run_attempt") or 0), int(job.get("id") or 0)


def latest_named(jobs: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [job for job in jobs if job.get("name") == name]
    if not matches:
        raise SystemExit(f"HOLD: source job missing: {name}")
    return max(matches, key=order_key)


def compact_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(job.get("id") or 0),
        "name": job.get("name"),
        "run_attempt": int(job.get("run_attempt") or 0),
        "status": job.get("status"),
        "conclusion": job.get("conclusion"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
    }


def audit(args: argparse.Namespace) -> dict[str, Any]:
    run = read(args.run)
    jobs = pages(read(args.job_pages), "jobs")
    artifacts = pages(read(args.artifact_pages), "artifacts")

    if int(run.get("id") or -1) != args.source_run_id or run.get("head_sha") != args.source_commit:
        raise SystemExit("HOLD: source run identity or commit changed")
    if run.get("status") != "completed":
        raise SystemExit("HOLD: source run is not completed")

    expected = {(layer, vacuum, kmesh) for layer in LAYERS for vacuum in VACUUMS for kmesh in KMESHES}
    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = {key: [] for key in expected}
    unexpected: list[str] = []
    for job in jobs:
        name = str(job.get("name") or "")
        match = SLAB_RE.match(name)
        if match:
            grouped[tuple(map(int, match.groups()))].append(job)
        elif name.startswith("slab-cases"):
            unexpected.append(name)
    if unexpected:
        raise SystemExit(f"HOLD: unexpected slab job identities: {sorted(set(unexpected))}")

    latest_slab_jobs: list[dict[str, Any]] = []
    superseded_failures: list[dict[str, Any]] = []
    for key in sorted(expected):
        attempts = grouped.get(key) or []
        if not attempts:
            raise SystemExit(f"HOLD: source slab job missing for {key}")
        latest = max(attempts, key=order_key)
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise SystemExit(
                f"HOLD: latest source slab attempt is not successful for {key}: "
                f"status={latest.get('status')} conclusion={latest.get('conclusion')}"
            )
        latest_slab_jobs.append(compact_job(latest))
        for prior in attempts:
            if prior is latest:
                continue
            if prior.get("status") == "completed" and prior.get("conclusion") != "success":
                superseded_failures.append(compact_job(prior))

    prepare = latest_named(jobs, "prepare")
    if prepare.get("status") != "completed" or prepare.get("conclusion") != "success":
        raise SystemExit("HOLD: latest source prepare job is not successful")
    gate = latest_named(jobs, "slab-gate")
    if gate.get("status") != "completed" or gate.get("conclusion") != "failure":
        raise SystemExit("HOLD: latest source slab gate is not the registered scientific HOLD")

    by_name: dict[str, list[dict[str, Any]]] = {}
    for artifact in artifacts:
        by_name.setdefault(str(artifact.get("name") or ""), []).append(artifact)
    raw_expected = {
        f"na-cu001-c7-raw-slab-l{layer}_v{vacuum}_k{kmesh}"
        for layer, vacuum, kmesh in expected
    }
    raw_actual = {name for name in by_name if name.startswith("na-cu001-c7-raw-slab-")}
    if raw_actual != raw_expected:
        raise SystemExit(
            f"HOLD: source raw artifact set differs from frozen 64 cases: "
            f"expected={len(raw_expected)} actual={len(raw_actual)}"
        )
    raw_records: list[dict[str, Any]] = []
    for name in sorted(raw_expected):
        matches = by_name[name]
        if len(matches) != 1:
            raise SystemExit(f"HOLD: expected one source artifact named {name}, found {len(matches)}")
        row = matches[0]
        if row.get("expired") or not row.get("digest") or int(row.get("size_in_bytes") or 0) <= 0:
            raise SystemExit(f"HOLD: invalid or expired source artifact {name}")
        raw_records.append(
            {
                "id": int(row.get("id") or 0),
                "name": name,
                "digest": row.get("digest"),
                "size_in_bytes": int(row.get("size_in_bytes") or 0),
                "created_at": row.get("created_at"),
                "expires_at": row.get("expires_at"),
            }
        )

    fixed = {
        "na-cu001-c7-base": (args.source_base_digest, args.source_base_size),
        "na-cu001-c7-qe": (args.source_qe_digest, args.source_qe_size),
    }
    fixed_records: dict[str, dict[str, Any]] = {}
    for name, (digest, size) in fixed.items():
        matches = by_name.get(name) or []
        if len(matches) != 1:
            raise SystemExit(f"HOLD: expected one pinned source artifact named {name}, found {len(matches)}")
        row = matches[0]
        if (
            row.get("expired")
            or row.get("digest") != digest
            or int(row.get("size_in_bytes") or -1) != size
        ):
            raise SystemExit(f"HOLD: pinned source artifact identity changed for {name}")
        fixed_records[name] = {
            key: row.get(key)
            for key in ("id", "name", "digest", "size_in_bytes", "created_at", "expires_at")
        }

    return {
        "schema": "na-cu001-c7-source-run-audit-v0.2",
        "status": "PASS",
        "source_run_id": args.source_run_id,
        "source_commit": args.source_commit,
        "source_run_conclusion": run.get("conclusion"),
        "source_job_payload_count": len(jobs),
        "source_prepare_job": compact_job(prepare),
        "source_gate_job": compact_job(gate),
        "source_gate_scientific_hold_observed": True,
        "source_slab_job_count": 64,
        "source_slab_latest_attempts_all_success": True,
        "latest_slab_jobs": latest_slab_jobs,
        "superseded_failed_attempts": sorted(
            superseded_failures,
            key=lambda row: (str(row.get("name")), int(row.get("run_attempt") or 0), int(row.get("id") or 0)),
        ),
        "source_raw_artifact_count": 64,
        "source_raw_artifacts": raw_records,
        "source_base_artifact": fixed_records["na-cu001-c7-base"],
        "source_qe_artifact": fixed_records["na-cu001-c7-qe"],
        "frozen_source_grid": {
            "layers": list(LAYERS),
            "vacuum_angstrom": [float(value) for value in VACUUMS],
            "kmesh_inplane": list(KMESHES),
            "calculation_count": 64,
        },
        "extension_grid": {
            "layers": [13],
            "vacuum_angstrom": [float(value) for value in VACUUMS],
            "kmesh_inplane": list(KMESHES),
            "calculation_count": 16,
            "eligible_for_selection": False,
        },
        "energy_tolerance_mev_per_surface_atom": 1.0,
        "downstream_layer_floor": 7,
        "electrostatic_convention": {
            "assume_isolated": "esm",
            "esm_bc": "bc1",
            "coordinate_origin": "cartesian_z_zero",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--job-pages", required=True)
    parser.add_argument("--artifact-pages", required=True)
    parser.add_argument("--source-run-id", type=int, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-base-digest", required=True)
    parser.add_argument("--source-base-size", type=int, required=True)
    parser.add_argument("--source-qe-digest", required=True)
    parser.add_argument("--source-qe-size", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = audit(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
