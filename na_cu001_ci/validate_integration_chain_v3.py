#!/usr/bin/env python3
"""Validate the v0.4-aware Na/Cu(001) artifact DAG without self-reference.

The complete validation algorithm remains the audited V2 implementation. This
adapter accepts the versioned v0.3 plan, invokes the same validation logic on a
temporary schema-normalized copy, then restores the original plan hash and emits
the v0.3 terminal schema. No PASS condition is relaxed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import validate_integration_chain_v2 as v2

PLAN_SCHEMA = "na-cu001-integration-closure-v0.3"
OUTPUT_SCHEMA = "na-cu001-integration-readiness-v0.3"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate(plan_path: Path, artifacts: Path, raw_root: Path) -> dict:
    original = json.loads(plan_path.read_text())
    if original.get("schema") != PLAN_SCHEMA:
        raise SystemExit("HOLD: v0.3 artifact plan schema required")
    adapted = json.loads(json.dumps(original))
    adapted["schema"] = "na-cu001-integration-closure-v0.2"
    with tempfile.TemporaryDirectory() as tmp:
        compatible = Path(tmp) / "plan_v02_compat.json"
        compatible.write_text(json.dumps(adapted, indent=2) + "\n")
        result = v2.validate(compatible, artifacts, raw_root)
    result["schema"] = OUTPUT_SCHEMA
    result["plan_sha256"] = sha256(plan_path)
    result["plan_schema"] = PLAN_SCHEMA
    result["validator_logic"] = "validate_integration_chain_v2.validate with schema-only v0.3 adapter; all stage, hash, raw-manifest, dependency-link, and nonresult checks unchanged"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = validate(Path(args.plan).resolve(), Path(args.artifacts).resolve(), Path(args.raw_root).resolve())
    out = Path(args.out).resolve()
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
