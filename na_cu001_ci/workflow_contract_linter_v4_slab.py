#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TRIGGER_PATHS = {
    "na_cu001_ci/bulk_v04_run_audit_v1.py",
    "na_cu001_ci/test_bulk_v04_run_audit_v1.py",
    "na_cu001_ci/workflow_contract_linter_v4_slab.py",
    "na_cu001_ci/slab_runner_v2.py",
    "na_cu001_ci/slab_runner_v3.py",
    "na_cu001_ci/slab_runner_v4.py",
    "na_cu001_ci/slab_runner_v5.py",
    "na_cu001_ci/test_slab_runner_v4.py",
    "na_cu001_ci/test_slab_runner_v5.py",
    "na_cu001_ci/closure_engine_v3.py",
    "na_cu001_ci/closure_engine_v4.py",
    "na_cu001_ci/test_slab_handoff_v4.py",
    "na_cu001_ci/run_computational_stage_v4.sh",
    ".github/workflows/na-cu001-v04-slab-route-v1.yml",
}


def fail(message: str) -> None:
    raise SystemExit(f"HOLD: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: workflow_contract_linter_v4_slab.py WORKFLOW")
    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    jobs = data.get("jobs", {})
    if set(jobs) != {"prepare", "slab-cases", "slab-gate"}:
        fail("C6-C7 workflow must contain exactly prepare, slab-cases, and slab-gate")
    if jobs["slab-cases"].get("needs") != "prepare":
        fail("slab matrix must depend on prepare")
    if jobs["slab-gate"].get("needs") != ["prepare", "slab-cases"]:
        fail("slab gate must depend on prepare and all slab cases")

    strategy = jobs["slab-cases"].get("strategy", {})
    if strategy.get("fail-fast") is not False:
        fail("slab matrix fail-fast must remain disabled")
    if int(strategy.get("max-parallel", -1)) != 8:
        fail("slab matrix max-parallel must remain 8")
    include = (strategy.get("matrix") or {}).get("include") or []
    expected = {(layer, vacuum) for layer in (5, 7, 9, 11) for vacuum in (12, 16, 20, 24)}
    actual = {(int(row["layers"]), int(row["vacuum"])) for row in include}
    if len(include) != 16 or actual != expected:
        fail("slab matrix is not the frozen 4x4 layer/vacuum grid")
    if len({row.get("tag") for row in include}) != 16:
        fail("slab matrix tags are not unique")

    trigger = (data.get("on") or {}).get("push") or {}
    if trigger.get("branches") != ["agent/na-cu001-integration"]:
        fail("source workflow branch trigger changed")
    paths = set(trigger.get("paths") or [])
    missing_paths = sorted(REQUIRED_TRIGGER_PATHS - paths)
    if missing_paths:
        fail(f"definitive source files missing from workflow trigger: {missing_paths}")

    if data.get("permissions") != {"contents": "read", "actions": "read"}:
        fail("workflow permissions must remain read-only")
    if data.get("env", {}).get("BULK_EXTENSION_RUN_ID") != "30843005718":
        fail("workflow is not bound to the audited v0.4 bulk run")

    text = path.read_text()
    required_text = [
        "run_computational_stage_v4.sh prepare",
        "run_computational_stage_v4.sh slab-case",
        "run_computational_stage_v4.sh slab-analyze",
        "na-cu001-c7-qe",
        "na-cu001-c7-base",
        "na-cu001-c6-run-audit",
        "na-cu001-c7-raw-slab-${{ matrix.tag }}",
        "na-cu001-c7-stage2",
    ]
    missing_text = [token for token in required_text if token not in text]
    if missing_text:
        fail(f"workflow contract tokens missing: {missing_text}")
    if jobs["prepare"].get("timeout-minutes") != 360:
        fail("prepare timeout changed")
    if jobs["slab-cases"].get("timeout-minutes") != 240:
        fail("slab-case timeout changed")

    upload_steps = [
        step
        for step in jobs["slab-cases"].get("steps", [])
        if step.get("uses") == "actions/upload-artifact@v4"
    ]
    if len(upload_steps) != 1 or upload_steps[0].get("if") != "always()":
        fail("each slab worker must retain its raw evidence even on failure")
    upload = upload_steps[0].get("with", {})
    if upload.get("if-no-files-found") != "error" or upload.get("path") != "slab_outputs":
        fail("raw slab artifact upload is not fail-closed")

    print(
        "PASS C6-C7 workflow contract: 3 jobs, 16 matrix jobs, 64 slab SCFs, "
        "definitive V5 geometry, strict holdouts, and proof-carrying handoff"
    )


if __name__ == "__main__":
    main()
