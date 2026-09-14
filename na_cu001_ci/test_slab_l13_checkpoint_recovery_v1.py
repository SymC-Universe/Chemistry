#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import slab_l13_checkpoint_recovery_v1 as recovery


def test_inject_execution_controls() -> None:
    source = "&CONTROL\n  calculation = 'scf',\n/\n&SYSTEM\n/\n"
    result = recovery.inject_execution_controls(
        source, restart_mode="restart", max_seconds=13500
    )
    assert "restart_mode = 'restart'" in result
    assert "max_seconds = 13500.0" in result
    assert result.count("restart_mode") == 1
    assert result.count("max_seconds") == 1
    assert "calculation = 'scf'" in result


def test_manifest_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "case" / "tmp"
        target.mkdir(parents=True)
        (target / "a.bin").write_bytes(b"abc")
        (target / "nested").mkdir()
        (target / "nested" / "b.bin").write_bytes(b"def")
        manifest = root / "case" / "RESTART_STATE.sha256"
        written = recovery.write_manifest(root, target, manifest)
        checked = recovery.verify_manifest(root, manifest)
        assert written == checked
        assert checked["file_count"] == 2
        assert checked["total_bytes"] == 6


def test_completed_record() -> None:
    good = {
        "returncode": 0,
        "job_done": True,
        "scf_converged": True,
        "final_energy_ev": -1.0,
    }
    assert recovery.completed_record(good)
    bad = json.loads(json.dumps(good))
    bad["job_done"] = False
    assert not recovery.completed_record(bad)


def main() -> None:
    test_inject_execution_controls()
    test_manifest_roundtrip()
    test_completed_record()
    print("checkpoint recovery tests: PASS")


if __name__ == "__main__":
    main()
