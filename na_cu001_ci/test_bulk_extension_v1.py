#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import bulk_extension_runner_v1 as extension
import bulk_runner_v2 as legacy

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "bulk_extension_protocol_v0.1.json"


class BulkExtensionTests(unittest.TestCase):
    def write_summary(self, root: Path, ecut: int, kmesh: int, a0: float, e0: float) -> Path:
        records = []
        for a in legacy.LATTICES:
            energy = e0 + 2.0 * (a - a0) ** 2
            records.append({
                "a_angstrom": a,
                "returncode": 0,
                "job_done": True,
                "scf_converged": True,
                "final_energy_ev_per_atom": energy,
            })
        data = {
            "schema": "na-cu001-bulk-matrix-v0.3",
            "ecutwfc_ry": ecut,
            "ecutrho_ry": 3 * ecut,
            "kmesh": kmesh,
            "records": records,
        }
        path = root / f"summary_e{ecut}_k{kmesh}.json"
        path.write_text(json.dumps(data))
        return path

    def full_grid(self, root: Path, *, audit_e0: float = -100.0004, make_pass: bool = True) -> None:
        protocol = json.loads(PROTOCOL.read_text())
        hist = protocol["reused_historical_candidates"]
        ext = protocol["extension_candidates"]
        reference_key = (protocol["reference"]["ecutwfc_ry"], protocol["reference"]["kmesh"])
        audit_key = (protocol["independent_reference_audit"]["ecutwfc_ry"], protocol["independent_reference_audit"]["kmesh"])
        for ecut in hist["ecuts_ry"]:
            for kmesh in hist["kmeshes"]:
                self.write_summary(root, ecut, kmesh, 3.6302, -99.98)
        for ecut in ext["ecuts_ry"]:
            for kmesh in ext["kmeshes"]:
                a0, e0 = 3.6302, -99.98
                if make_pass and (ecut, kmesh) == (90, 20):
                    a0, e0 = 3.6304, -100.0007
                if make_pass and (ecut, kmesh) == (100, 16):
                    a0, e0 = 3.6303, -100.0006
                self.write_summary(root, ecut, kmesh, a0, e0)
        self.write_summary(root, *reference_key, 3.6300, -100.0000)
        self.write_summary(root, *audit_key, 3.6302, audit_e0)

    def run_analyze(self, root: Path) -> tuple[int, dict]:
        out = root / "result.json"
        args = argparse.Namespace(protocol=str(PROTOCOL), summaries=str(root), out=str(out))
        rc = 0
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                extension.analyze(args)
            except SystemExit as exc:
                rc = int(exc.code or 0)
        return rc, json.loads(out.read_text()) if out.exists() else {}

    def test_audited_reference_and_cost_selection_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.full_grid(root)
            rc, result = self.run_analyze(root)
            self.assertEqual(rc, 0)
            self.assertEqual(result["gate"], "PASS")
            self.assertTrue(result["reference_audit_gate"]["pass"])
            selected = result["recommended_smallest_cost_candidate"]
            self.assertEqual((selected["ecutwfc_ry"], selected["kmesh"]), (100, 16))
            by = {(r["ecutwfc_ry"], r["kmesh"]): r for r in result["candidates"]}
            self.assertTrue(by[(90, 20)]["joint_gate_against_audited_reference"]["pass"])
            self.assertGreater(by[(90, 20)]["estimated_cost_score"], by[(100, 16)]["estimated_cost_score"])

    def test_reference_audit_failure_forces_hold(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.full_grid(root, audit_e0=-100.0100)
            rc, result = self.run_analyze(root)
            self.assertEqual(rc, 2)
            self.assertEqual(result["gate"], "HOLD")
            self.assertFalse(result["reference_audit_gate"]["pass"])
            self.assertIsNone(result["recommended_smallest_cost_candidate"])
            self.assertIn("reference_140Ry_22cubed_failed_independent_150Ry_24cubed_audit", result["hold_reasons"])

    def test_no_candidate_pass_does_not_select_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.full_grid(root, make_pass=False)
            rc, result = self.run_analyze(root)
            self.assertEqual(rc, 2)
            self.assertEqual(result["gate"], "HOLD")
            self.assertIsNone(result["recommended_smallest_cost_candidate"])
            keys = {(r["ecutwfc_ry"], r["kmesh"]) for r in result["candidates"]}
            self.assertNotIn((140, 22), keys)
            self.assertNotIn((150, 24), keys)

    def test_missing_registered_case_fails_before_result(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.full_grid(root)
            (root / "summary_e120_k18.json").unlink()
            out = root / "result.json"
            args = argparse.Namespace(protocol=str(PROTOCOL), summaries=str(root), out=str(out))
            with self.assertRaises(SystemExit) as ctx:
                extension.analyze(args)
            self.assertIn("missing registered EOS summaries", str(ctx.exception))
            self.assertFalse(out.exists())

    def test_handoff_hash_links_protocol_result_and_all_eos(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.full_grid(root)
            rc, _ = self.run_analyze(root)
            self.assertEqual(rc, 0)
            result_path = root / "result.json"
            handoff_path = root / "handoff.json"
            with contextlib.redirect_stdout(io.StringIO()):
                extension.make_handoff(argparse.Namespace(protocol=str(PROTOCOL), result=str(result_path), out=str(handoff_path)))
            handoff = json.loads(handoff_path.read_text())
            self.assertEqual(handoff["schema"], extension.HANDOFF_SCHEMA)
            self.assertTrue(handoff["reference_settings"]["independent_audit"]["gate"]["pass"])
            self.assertEqual(len(handoff["input_artifacts"]), 48)
            self.assertEqual(handoff["joint_gate"]["pass"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
