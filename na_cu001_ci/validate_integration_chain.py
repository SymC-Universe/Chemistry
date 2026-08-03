#!/usr/bin/env python3
"""Validate the Na/Cu(001) closure chain without promoting missing or HOLD stages.

The validator is intentionally conservative. It records PASS only when a stage
artifact exists, has the registered filename/schema, declares an accepted PASS
state, and every declared upstream artifact hash resolves. Missing downstream
artifacts remain BLOCKED rather than being narratively inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PASS_STATES = {
    "PASS",
    "bulk_convergence_passed_slab_not_yet_run",
}

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
        actual = sha256(target)
        if actual != expected:
            errors.append(f"linked artifact hash mismatch: {rel}")
    return errors


def validate(plan_path: Path, artifact_root: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text())
    if plan.get("schema") != "na-cu001-integration-closure-v0.1":
        raise SystemExit("HOLD: unsupported integration plan schema")
    stages = plan.get("stages")
    if not isinstance(stages, list) or len(stages) != 12:
        raise SystemExit("HOLD: integration plan must contain exactly 12 stages")

    results: list[dict[str, Any]] = []
    prior_pass: dict[int, bool] = {}
    for stage in stages:
        stage_id = int(stage["id"])
        filename = str(stage["pass_artifact"])
        path = artifact_root / filename
        dependencies = [i for i in range(1, stage_id) if i not in (4,)]
        if stage_id == 4:
            dependencies = []
        elif stage_id == 5:
            dependencies = [3, 4]
        elif stage_id > 5:
            dependencies = [stage_id - 1]
        upstream_ready = all(prior_pass.get(dep, False) for dep in dependencies)

        record: dict[str, Any] = {
            "id": stage_id,
            "name": stage["name"],
            "artifact": filename,
            "expected_schema": SCHEMA_BY_STAGE[stage_id],
            "dependencies": dependencies,
        }
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

    computational = [r for r in results if r["id"] <= 10]
    atlas = next(r for r in results if r["id"] == 11)
    all_computational_pass = all(r["validation_state"] == "PASS" for r in computational)
    overall = "PASS" if all_computational_pass and atlas["validation_state"] == "PASS" else "HOLD"
    return {
        "schema": "na-cu001-integration-readiness-v0.1",
        "status": overall,
        "plan_sha256": sha256(plan_path),
        "artifact_root": str(artifact_root),
        "stages": results,
        "all_computational_stages_pass": all_computational_pass,
        "atlas_admission_pass": atlas["validation_state"] == "PASS",
        "experimental_only_gaps": plan.get("experimental_only_gaps", []),
        "rule": "Missing, malformed, unhashed, schema-mismatched, or non-PASS artifacts cannot be promoted.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    plan = Path(args.plan).resolve()
    artifacts = Path(args.artifacts).resolve()
    output = Path(args.out).resolve()
    result = validate(plan, artifacts)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
