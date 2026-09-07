#!/usr/bin/env python3
"""Static contract checks for the corrected Na/Cu(001) Actions workflow."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def fail(message: str) -> None:
    raise SystemExit(f"HOLD: {message}")


def steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    value = job.get("steps") or []
    return [x for x in value if isinstance(x, dict)]


def find_download(job: dict[str, Any], pattern: str) -> dict[str, Any]:
    for step in steps(job):
        if step.get("uses") == "actions/download-artifact@v4":
            spec = step.get("with") or {}
            if spec.get("pattern") == pattern:
                return spec
    fail(f"download pattern absent in job: {pattern}")


def matrix_size(job: dict[str, Any]) -> int:
    matrix = ((job.get("strategy") or {}).get("matrix") or {})
    if "include" in matrix:
        return len(matrix["include"])
    size = 1
    found = False
    for key, values in matrix.items():
        if key in {"include", "exclude"}:
            continue
        if isinstance(values, list):
            found = True
            size *= len(values)
    return size if found else 1


def check_dag(jobs: dict[str, Any]) -> None:
    graph: dict[str, list[str]] = {}
    for name, job in jobs.items():
        needs = job.get("needs") or []
        if isinstance(needs, str):
            needs = [needs]
        for dep in needs:
            if dep not in jobs:
                fail(f"job {name} depends on missing job {dep}")
        graph[name] = list(needs)
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visiting:
            fail(f"workflow dependency cycle at {node}")
        if node in visited:
            return
        visiting.add(node)
        for dep in graph[node]:
            visit(dep)
        visiting.remove(node); visited.add(node)
    for node in graph:
        visit(node)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow")
    args = parser.parse_args()
    path = Path(args.workflow)
    data = yaml.safe_load(path.read_text())
    jobs = data.get("jobs") or {}
    if len(jobs) != 20:
        fail(f"expected 20 jobs, found {len(jobs)}")
    check_dag(jobs)

    expected_sizes = {
        "slab-cases": 16,
        "adsorption-cases": 18,
        "endpoints": 2,
        "neb-cases": 6,
        "neb-gates": 2,
        "ci-neb": 2,
        "hessian-centers": 2,
        "hessian-cases": 108,
        "sensitivity-cases": 5,
    }
    for name, expected in expected_sizes.items():
        actual = matrix_size(jobs[name])
        if actual != expected:
            fail(f"matrix size mismatch for {name}: expected {expected}, found {actual}")

    destinations = {
        ("slab-gate", "na-cu001-v2-raw-slab-*"): "slab_outputs",
        ("adsorption-gate", "na-cu001-v2-raw-ads-*"): "ads_records",
        ("neb-gates", "na-cu001-v2-raw-neb-${{ matrix.mobility }}-*"): "neb_records",
        ("hessian-gate", "na-cu001-v2-hessian-center-*"): "hessian_centers",
        ("hessian-gate", "na-cu001-v2-raw-hessian-*"): "hessian_records",
        ("sensitivity-gate", "na-cu001-v2-raw-sensitivity-*"): "sensitivity_records",
    }
    for (job, pattern), destination in destinations.items():
        spec = find_download(jobs[job], pattern)
        if spec.get("path") != destination or spec.get("merge-multiple") is not True:
            fail(f"artifact collection contract mismatch for {job}: {pattern}")

    raw_spec = find_download(jobs["finalize"], "na-cu001-v2-raw-*")
    if raw_spec.get("path") != "raw" or raw_spec.get("merge-multiple") is not False:
        fail("final raw artifacts must remain separated by artifact name")

    concurrency = data.get("concurrency") or {}
    if concurrency.get("cancel-in-progress") is not False:
        fail("corrected long-running route must not be cancelled by an incidental later push")
    if "github.sha" not in str(concurrency.get("group")):
        fail("concurrency group must be commit-specific")

    text = path.read_text()
    required_trigger_paths = [
        "test_negative_gates_v2.py", "validate_integration_chain_v2.py",
        "workflow_contract_linter_v2.py", "artifact_contract_linter_v2.py", "validation_selection_protocol_v0.1.json",
        "tier_linter_v2.py", "downstream_protocol_v0.2.json", "slab_protocol_v0.3.json",
    ]
    for name in required_trigger_paths:
        if name not in text:
            fail(f"push trigger does not cover {name}")

    print(f"PASS: workflow contract verified ({len(jobs)} jobs)")


if __name__ == "__main__":
    main()
