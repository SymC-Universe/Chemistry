#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("l17", HERE / "pbe_surface_convergence_l17_v1.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


class TestL17ExactRestart(unittest.TestCase):
    def setUp(self):
        self.protocol_path = HERE / "SYSTEM2_PBE_SURFACE_CONVERGENCE_L17_v0.1.json"
        self.p = mod.protocol(self.protocol_path)

    def test_frozen_rung_and_thresholds(self):
        self.assertEqual(self.p["extension_audit"]["layers"], 17)
        self.assertEqual(self.p["extension_audit"]["vacuum_angstrom"], 36.0)
        self.assertEqual(self.p["extension_audit"]["kmesh"], 32)
        self.assertEqual(self.p["frozen_method"]["surface_excess_convergence_max_ev_per_surface_atom"], 0.001)
        self.assertTrue(self.p["decision"]["no_additional_scientific_rung_authorized"])

    def test_checkpoint_contract_has_90_minute_safety_margin(self):
        ex = self.p["execution"]
        self.assertEqual(ex["qe_max_seconds_per_segment"], 16200)
        self.assertEqual(ex["github_job_timeout_minutes"] * 60, 21600)
        self.assertEqual(ex["shutdown_and_artifact_reserve_seconds"], 5400)
        self.assertEqual(ex["qe_max_seconds_per_segment"] + ex["shutdown_and_artifact_reserve_seconds"], 21600)
        self.assertEqual(ex["checkpoint_mode"], "QE_CLEAN_MAX_SECONDS_EXACT_RESTART")
        self.assertTrue(ex["full_qe_outdir_preserved"])

    def test_restart_input_changes_only_control_restart_fields(self):
        base = "&CONTROL\n calculation='relax',\n/\n&SYSTEM\n/\n"
        first = mod.add_control_fields(base, "from_scratch", 16200)
        rest = mod.add_control_fields(base, "restart", 16200)
        self.assertIn("restart_mode='from_scratch'", first)
        self.assertIn("restart_mode='restart'", rest)
        self.assertIn("max_seconds=16200", first)
        self.assertIn("max_seconds=16200", rest)
        self.assertEqual(first.replace("from_scratch", "restart"), rest)

    def test_checkpoint_manifest_detects_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            q = root / "qe_checkpoint" / "prefix.save"
            q.mkdir(parents=True)
            f = q / "data-file-schema.xml"
            f.write_text("state-a")
            manifest_sha = mod.write_checkpoint_manifest(root)
            self.assertEqual(mod.verify_checkpoint_manifest(root, manifest_sha), manifest_sha)
            f.write_text("state-b")
            with self.assertRaises(SystemExit):
                mod.verify_checkpoint_manifest(root, manifest_sha)

    def test_prior_failure_preserved(self):
        src = self.p["source_l15_reference"]
        self.assertFalse(src["prior_gate_pass"])
        self.assertGreater(src["observed_l13_l15_delta_ev_per_surface_atom"], src["frozen_threshold_ev_per_surface_atom"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
