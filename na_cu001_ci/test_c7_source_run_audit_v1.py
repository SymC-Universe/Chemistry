#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from c7_source_run_audit_v1 import KMESHES, LAYERS, VACUUMS, audit

BASE_DIGEST = "sha256:" + "1" * 64
QE_DIGEST = "sha256:" + "2" * 64
SOURCE_COMMIT = "8ca3f708537886050ef18210315e79a43595d3f3"
TARGET = "slab-cases (9, 20, 18)"


def write(path: Path, payload):
    path.write_text(json.dumps(payload))


def job(job_id, name, conclusion=None, attempt=1, status="completed"):
    return {
        "id": job_id,
        "name": name,
        "run_attempt": attempt,
        "status": status,
        "conclusion": conclusion,
    }


def payload(latest_completed_bad=False):
    jobs = [
        job(1, "prepare", "success", 1),
        job(2, "slab-gate", "failure", 2),
        job(9001, "prepare", None, 3, "queued"),
        job(9002, "slab-gate", None, 3, "queued"),
    ]
    next_id = 10
    for layer in LAYERS:
        for vacuum in VACUUMS:
            for kmesh in KMESHES:
                name = f"slab-cases ({layer}, {vacuum}, {kmesh})"
                jobs.append(job(next_id, name, "success", 2))
                next_id += 1
    jobs.append(job(5, TARGET, "failure", 1))
    jobs.append(job(999, TARGET, None, 3, "queued"))
    if latest_completed_bad:
        jobs.append(job(1000, TARGET, "failure", 4))

    artifacts = []
    artifact_id = 1000
    for layer in LAYERS:
        for vacuum in VACUUMS:
            for kmesh in KMESHES:
                artifacts.append(
                    {
                        "id": artifact_id,
                        "name": f"na-cu001-c7-raw-slab-l{layer}_v{vacuum}_k{kmesh}",
                        "digest": "sha256:" + f"{artifact_id:064x}"[-64:],
                        "size_in_bytes": 123,
                        "expired": False,
                    }
                )
                artifact_id += 1
    artifacts.extend(
        [
            {
                "id": 2000,
                "name": "na-cu001-c7-base",
                "digest": BASE_DIGEST,
                "size_in_bytes": 102658,
                "expired": False,
            },
            {
                "id": 2001,
                "name": "na-cu001-c7-qe",
                "digest": QE_DIGEST,
                "size_in_bytes": 101484780,
                "expired": False,
            },
        ]
    )
    return jobs, artifacts


def args(root: Path):
    return argparse.Namespace(
        run=str(root / "run.json"),
        job_pages=str(root / "job_pages.json"),
        artifact_pages=str(root / "artifact_pages.json"),
        source_run_id=30949901790,
        source_commit=SOURCE_COMMIT,
        source_base_digest=BASE_DIGEST,
        source_base_size=102658,
        source_qe_digest=QE_DIGEST,
        source_qe_size=101484780,
        out=str(root / "out.json"),
    )


def prepare(root: Path, latest_completed_bad=False):
    jobs, artifacts = payload(latest_completed_bad=latest_completed_bad)
    write(
        root / "run.json",
        {
            "id": 30949901790,
            "head_sha": SOURCE_COMMIT,
            "status": "completed",
            "conclusion": "failure",
        },
    )
    write(root / "job_pages.json", [{"jobs": jobs[:70]}, {"jobs": jobs[70:]}])
    write(root / "artifact_pages.json", [{"artifacts": artifacts[:40]}, {"artifacts": artifacts[40:]}])


def test_queued_record_does_not_displace_completed_success():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        prepare(root)
        result = audit(args(root))
        assert result["status"] == "PASS"
        assert result["source_slab_job_count"] == 64

        superseded = result["superseded_failed_attempts"]
        target_failures = [row for row in superseded if row["name"] == TARGET]
        assert len(target_failures) == 1
        assert target_failures[0]["conclusion"] == "failure"
        assert target_failures[0]["run_attempt"] == 1

        latest = [row for row in result["latest_slab_jobs"] if row["name"] == TARGET]
        assert len(latest) == 1
        assert latest[0]["conclusion"] == "success"
        assert latest[0]["run_attempt"] == 2

        nonexecuted = result["nonexecuted_job_records"]
        queued_target = [row for row in nonexecuted if row["name"] == TARGET]
        assert len(queued_target) == 1
        assert queued_target[0]["status"] == "queued"
        assert queued_target[0]["run_attempt"] == 3
        assert any(row["name"] == "prepare" and row["status"] == "queued" for row in nonexecuted)
        assert any(row["name"] == "slab-gate" and row["status"] == "queued" for row in nonexecuted)
        assert result["source_prepare_job"]["conclusion"] == "success"
        assert result["source_gate_job"]["conclusion"] == "failure"


def test_latest_completed_failure_is_fatal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        prepare(root, latest_completed_bad=True)
        try:
            audit(args(root))
        except SystemExit as exc:
            assert "latest completed source slab attempt is not successful" in str(exc)
        else:
            raise AssertionError("latest completed failed attempt should fail closed")


def main():
    test_queued_record_does_not_displace_completed_success()
    test_latest_completed_failure_is_fatal()
    print("c7_source_run_audit_v1 tests: PASS")


if __name__ == "__main__":
    main()
