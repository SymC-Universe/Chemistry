#!/usr/bin/env python3
"""Validate the Na/Cu(001) closure chain without promoting missing stages.

Stages 1-11 must exist as hashed PASS artifacts. Stage 12 is the validator's own
output and is generated only when the upstream chain and the separately retained
raw-output manifest both verify. This avoids impossible self-hash validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PASS_STATES = {"PASS", "bulk_convergence_passed_slab_not_yet_run"}
SCHEMA_BY_STAGE = {
    1: "na-cu001-bulk-to-slab-handoff-v0.1",
    2: "na-cu001-clean-slab-to-relaxation-handoff-v0.2",
    3: "na-cu001-relaxed-clean-surface-handoff-v0.1",
    4: "na-cu001-na-pseudopotential-handoff-v0.1",
    5: "na-cu001-adsorption-site-handoff-v0.1",
    6: "na-cu001-endpoints-handoff-v0.1",
    7: "na-cu001-path-convergence-handoff-v0.1",
    8: "na-cu001-ci-neb-handoff-v0.1",
    9: "na-cu001-saddle-handoff-v0.1",
    10: "na-cu001-barrier-coordinate-v0.1",
    11: "na-cu001-atlas-admission-v0.1",
    12: "na-cu001-integration-readiness-v0.1",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def declared_state(data: dict[str, Any]) -> str | None:
    for key in ("gate", "scientific_status", "status"):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return None


def check_hash_links(data: dict[str, Any], artifact_root: Path) -> list[str]:
    errors: list[str] = []
    links = data.get("input_artifacts", [])
    if links is None:
        links = []
    if not isinstance(links, list):
        return ["input_artifacts must be a list"]
    for index, item in enumerate(links):
        if not isinstance(item, dict):
            errors.append(f"input_artifacts[{index}] is not an object")
            continue
        rel = item.get("path")
        expected = item.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            errors.append(f"input_artifacts[{index}] lacks path/sha256")
            continue
        target = artifact_root / rel
        if not target.is_file():
            errors.append(f"linked artifact missing: {rel}")
            continue
        if sha256(target) != expected:
            errors.append(f"linked artifact hash mismatch: {rel}")
    return errors


def validate_raw_manifest(manifest_path: Path, raw_root: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    if not manifest_path.is_file():
        return {"validation_state": "HOLD", "errors": ["RAW_ARTIFACT_INDEX.json absent"]}
    try:
        data = json.loads(manifest_path.read_text())
    except Exception as exc:
        return {"validation_state": "HOLD", "errors": [f"invalid raw manifest JSON: {exc}"]}
    if data.get("schema") != "na-cu001-computational-manifest-v0.1":
        errors.append("raw manifest schema mismatch")
    if data.get("status") != "PASS":
        errors.append("raw manifest state is not PASS")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        errors.append("raw manifest contains no files")
        files = []
    if raw_root is None or not raw_root.is_dir():
        errors.append("raw artifact root is absent")
    else:
        for index, item in enumerate(files):
            if not isinstance(item, dict):
                errors.append(f"raw files[{index}] is not an object")
                continue
            rel = item.get("path")
            expected = item.get("sha256")
            expected_size = item.get("size_bytes")
            if not isinstance(rel, str) or not isinstance(expected, str):
                errors.append(f"raw files[{index}] lacks path/sha256")
                continue
            target = raw_root / rel
            if not target.is_file():
                errors.append(f"raw file missing: {rel}")
                continue
            if sha256(target) != expected:
                errors.append(f"raw file hash mismatch: {rel}")
            if isinstance(expected_size, int) and target.stat().st_size != expected_size:
                errors.append(f"raw file size mismatch: {rel}")
    return {
        "validation_state": "PASS" if not errors else "HOLD",
        "errors": errors,
        "manifest_sha256": sha256(manifest_path),
        "file_count": len(files),
    }


def dependencies_for(stage_id: int) -> list[int]:
    if stage_id == 1:
        return []
    if stage_id == 4:
        return []
    if stage_id == 5:
        return [3, 4]
    return [stage_id - 1]


def validate(plan_path: Path, artifact_root: Path, raw_root: Path | None) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text())
    if plan.get("schema") != "na-cu001-integration-closure-v0.1":
        raise SystemExit("HOLD: unsupported integration plan schema")
    stages = plan.get("stages")
    if not isinstance(stages, list) or len(stages) != 12:
        raise SystemExit("HOLD: integration plan must contain exactly 12 stages")

    raw_check = validate_raw_manifest(artifact_root / "RAW_ARTIFACT_INDEX.json", raw_root)
    results: list[dict[str, Any]] = []
    prior_pass: dict[int, bool] = {}

    for stage in stages:
        stage_id = int(stage["id"])
        filename = str(stage["pass_artifact"])
        dependencies = dependencies_for(stage_id)
        upstream_ready = all(prior_pass.get(dep, False) for dep in dependencies)
        record: dict[str, Any] = {
            "id": stage_id,
            "name": stage["name"],
            "artifact": filename,
            "expected_schema": SCHEMA_BY_STAGE[stage_id],
            "dependencies": dependencies,
        }

        if stage_id == 12:
            errors = []
            if not upstream_ready:
                errors.append("upstream stage 11 is not PASS")
            if raw_check["validation_state"] != "PASS":
                errors.append("raw artifact manifest or retained raw files failed validation")
            record.update({
                "declared_state": "PASS" if not errors else "HOLD",
                "validation_state": "PASS" if not errors else "HOLD",
                "generated_by_this_validation_run": True,
                "errors": errors,
            })
            prior_pass[stage_id] = not errors
            results.append(record)
            continue

        path = artifact_root / filename
        if not path.is_file():
            record["validation_state"] = "BLOCKED" if not upstream_ready else "READY_NO_ARTIFACT"
            record["errors"] = ["stage artifact absent"]
            prior_pass[stage_id] = False
            results.append(record)
            continue
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            record["validation_state"] = "HOLD"
            record["errors"] = [f"invalid JSON: {exc}"]
            prior_pass[stage_id] = False
            results.append(record)
            continue

        errors: list[str] = []
        if data.get("schema") != SCHEMA_BY_STAGE[stage_id]:
            errors.append(f"schema mismatch: {data.get('schema')!r}")
        state = declared_state(data)
        if state not in PASS_STATES:
            errors.append(f"artifact state is not an accepted PASS state: {state!r}")
        if not upstream_ready and dependencies:
            errors.append("upstream dependency not PASS")
        errors.extend(check_hash_links(data, artifact_root))
        record.update({
            "actual_sha256": sha256(path),
            "declared_state": state,
            "validation_state": "PASS" if not errors else "HOLD",
            "errors": errors,
        })
        prior_pass[stage_id] = not errors
        results.append(record)

    all_computational_pass = all(r["validation_state"] == "PASS" for r in results if r["id"] <= 10)
    atlas_pass = next(r for r in results if r["id"] == 11)["validation_state"] == "PASS"
    integration_pass = next(r for r in results if r["id"] == 12)["validation_state"] == "PASS"
    overall = "PASS" if all_computational_pass and atlas_pass and integration_pass else "HOLD"
    return {
        "schema": "na-cu001-integration-readiness-v0.1",
        "status": overall,
        "plan_sha256": sha256(plan_path),
        "artifact_root": str(artifact_root),
        "raw_artifact_root": str(raw_root) if raw_root else None,
        "raw_artifact_validation": raw_check,
        "stages": results,
        "all_computational_stages_pass": all_computational_pass,
        "atlas_admission_pass": atlas_pass,
        "integration_gate_pass": integration_pass,
        "experimental_only_gaps": plan.get("experimental_only_gaps", []),
        "rule": "Missing, malformed, unhashed, schema-mismatched, non-PASS, or raw-unverifiable artifacts cannot be promoted.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    plan = Path(args.plan).resolve()
    artifacts = Path(args.artifacts).resolve()
    raw_root = Path(args.raw_root).resolve()
    output = Path(args.out).resolve()
    result = validate(plan, artifacts, raw_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
