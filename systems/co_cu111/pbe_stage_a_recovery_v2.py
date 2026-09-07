#!/usr/bin/env python3
"""Mechanical-only v0.2 wrapper for frozen CO/Cu(111) Stage A recovery.

This wrapper changes no scientific input or execution logic. It reuses the
v0.1 recovery implementation and only admits the separately preregistered
v0.2 recovery-controller schema used to split unresolved C2/L22 work into
single frozen bond-point jobs after the v0.1 180-minute wall-time limit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).with_name("pbe_stage_a_recovery_v1.py")
_spec = importlib.util.spec_from_file_location("co_cu111_recovery_v1", BASE)
if _spec is None or _spec.loader is None:
    raise SystemExit("HOLD: cannot load v0.1 mechanical recovery implementation")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


def verify_recovery_contract_v02(contract_path: Path, protocol_path: Path, bundle_path: Path, runner_path: Path):
    c = json.loads(contract_path.read_text())
    if not isinstance(c, dict):
        raise SystemExit("HOLD: v0.2 recovery controller root must be object")
    if c.get("schema") != "co-cu111-stage-a-mechanical-recovery-v0.2":
        raise SystemExit("HOLD: wrong v0.2 recovery-controller schema")
    if c.get("status") != "FROZEN_BEFORE_RECOVERY_RESULTS":
        raise SystemExit("HOLD: v0.2 recovery controller is not frozen")
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
    if frozen.get("mpi_ranks") != 1:
        raise SystemExit("HOLD: frozen MPI rank mismatch")
    if frozen.get("thread_environment") != {"OMP_NUM_THREADS": 1, "OPENBLAS_NUM_THREADS": 1}:
        raise SystemExit("HOLD: frozen thread environment mismatch")
    return c


# Replace only contract-schema verification. All target checks, chunk checks,
# input generation, QE execution, hash validation, reuse rules, and assembly
# remain the unchanged v0.1 implementation.
base.verify_recovery_contract = verify_recovery_contract_v02

if __name__ == "__main__":
    base.main()
