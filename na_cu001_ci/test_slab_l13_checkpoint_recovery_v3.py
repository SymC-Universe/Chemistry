#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import slab_l13_checkpoint_recovery_v3 as recovery


def test_registered_cases() -> None:
    assert recovery.registered_case(13, 16, 22) == (13, 16.0, 22)
    assert recovery.registered_case(13, 24, 20) == (13, 24.0, 20)
    assert recovery.registered_case(13, 24, 22) == (13, 24.0, 22)
    try:
        recovery.registered_case(13, 20, 22)
    except SystemExit as exc:
        assert "not registered" in str(exc)
    else:
        raise AssertionError("unregistered recovery case was accepted")


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


def test_layer_13_remains_registered_until_context_exit() -> None:
    fake_v2 = SimpleNamespace(LAYERS=[5, 7, 9, 11])
    with recovery.extended_layer_registry(fake_v2):
        assert fake_v2.LAYERS == [5, 7, 9, 11, 13]
    assert fake_v2.LAYERS == [5, 7, 9, 11]


def test_compact_hash_verification() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        job = Path(tmp)
        tag = "cu001_L13_V24_K20"
        inp = job / f"{tag}.in"
        out = job / f"{tag}.out"
        pseudo = job / "Cu.upf"
        inp.write_text("input\n")
        out.write_text("output\n")
        pseudo.write_text("pseudo\n")
        row = {
            "tag": tag,
            "input_sha256": recovery.sha256(inp),
            "output_sha256": recovery.sha256(out),
            "pseudo_sha256": recovery.sha256(pseudo),
        }
        recovery.verify_compact_hashes(job, row, pseudo)
        out.write_text("tampered\n")
        try:
            recovery.verify_compact_hashes(job, row, pseudo)
        except SystemExit as exc:
            assert "output hash mismatch" in str(exc)
        else:
            raise AssertionError("tampered output was accepted")


def main() -> None:
    test_registered_cases()
    test_inject_execution_controls()
    test_manifest_roundtrip()
    test_completed_record()
    test_layer_13_remains_registered_until_context_exit()
    test_compact_hash_verification()
    print("checkpoint recovery v3 tests: PASS")


if __name__ == "__main__":
    main()
