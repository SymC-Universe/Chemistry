#!/usr/bin/env python3
"""Static contract checks for the post-HOLD bulk extension workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def fail(message: str) -> None:
    raise SystemExit(f"HOLD: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow")
    parser.add_argument("--protocol", required=True)
    args = parser.parse_args()
    workflow_path = Path(args.workflow)
    protocol_path = Path(args.protocol)
    data = yaml.safe_load(workflow_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    jobs = data.get("jobs") or {}
    if set(jobs) != {"prepare-engine", "extension-eos", "extension-gate"}:
        fail(f"unexpected job set: {sorted(jobs)}")
    if str(jobs["extension-gate"].get("if")) != "always()":
        fail("extension gate must execute even when a registered EOS case fails")
    needs = jobs["extension-gate"].get("needs") or []
    if set(needs) != {"prepare-engine", "extension-eos"}:
        fail("extension gate must depend on engine preparation and all EOS cases")
    include = (((jobs["extension-eos"].get("strategy") or {}).get("matrix") or {}).get("include") or [])
    actual = {(int(x["ecut"]), int(x["kmesh"]), str(x["role"])) for x in include}
    expected = {
        (int(e), int(k), "candidate")
        for e in protocol["extension_candidates"]["ecuts_ry"]
        for k in protocol["extension_candidates"]["kmeshes"]
    }
    expected.add((int(protocol["reference"]["ecutwfc_ry"]), int(protocol["reference"]["kmesh"]), "reference"))
    expected.add((int(protocol["independent_reference_audit"]["ecutwfc_ry"]), int(protocol["independent_reference_audit"]["kmesh"]), "audit"))
    if actual != expected or len(include) != 26:
        fail(f"EOS matrix mismatch: expected 26 exact cases, found {len(include)}")
    if len({x["tag"] for x in include}) != len(include):
        fail("EOS matrix tags are not unique")
    strategy = jobs["extension-eos"].get("strategy") or {}
    if strategy.get("fail-fast") is not False:
        fail("EOS matrix must retain all case failures")
    if int(strategy.get("max-parallel", 0)) < 1 or int(strategy.get("max-parallel", 0)) > 8:
        fail("EOS matrix max-parallel must be between 1 and 8")
    downloads = [s for s in jobs["extension-gate"].get("steps", []) if s.get("uses") == "actions/download-artifact@v4"]
    matching = [s for s in downloads if (s.get("with") or {}).get("pattern") == "na-cu001-bulk-extension-raw-*"]
    if len(matching) != 1:
        fail("extension gate lacks exact raw artifact collection")
    spec = matching[0]["with"]
    if spec.get("path") != "extension_raw" or spec.get("merge-multiple") is not True:
        fail("extension raw artifacts must merge into extension_raw")
    gate_text = json.dumps(jobs["extension-gate"], sort_keys=True)
    if "upstream_prepare_or_registered_eos_matrix_failed" not in gate_text or "UPSTREAM_RESULTS.json" not in gate_text:
        fail("extension gate lacks explicit upstream failure evidence")
    decision_uploads = [
        s for s in jobs["extension-gate"].get("steps", [])
        if s.get("uses") == "actions/upload-artifact@v4"
        and (s.get("with") or {}).get("name") == "na-cu001-bulk-extension-decision-v0.4"
    ]
    if len(decision_uploads) != 1 or str(decision_uploads[0].get("if")) != "always()":
        fail("decision evidence must upload on PASS or HOLD")
    concurrency = data.get("concurrency") or {}
    if concurrency.get("cancel-in-progress") is not False or "github.sha" not in str(concurrency.get("group")):
        fail("bulk extension must be commit-specific and non-cancelling")
    text = workflow_path.read_text()
    required = [
        "bulk_extension_protocol_v0.1.json",
        "bulk_extension_runner_v1.py",
        "test_bulk_extension_v1.py",
        "bulk_extension_workflow_linter_v1.py",
        "na-cu001-bulk-extension-v1.yml",
    ]
    for item in required:
        if item not in text:
            fail(f"workflow trigger or preflight omits {item}")
    forbidden = ["workflow_dispatches", "na-cu001-computational-route-v2.yml/dispatches"]
    if any(item in text for item in forbidden):
        fail("bulk extension workflow must not launch downstream computation")
    print("PASS: bulk extension workflow contract verified (26 EOS cases, audited reference)")


if __name__ == "__main__":
    main()
