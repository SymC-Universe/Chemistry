#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "pbe_l15_l17_observable_sufficiency_v1.py"
PROTOCOL_PATH = HERE / "SYSTEM2_PBE_L15_L17_OBSERVABLE_SUFFICIENCY_v0.1.json"
spec = importlib.util.spec_from_file_location("l15l17", RUNNER_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestL15L17ObservableSufficiency(unittest.TestCase):
    def setUp(self):
        self.p = json.loads(PROTOCOL_PATH.read_text())

    def test_frozen_protocol(self):
        m.verify_protocol(self.p)
        self.assertFalse(self.p["decision"]["absolute_clean_surface_pass_claimed"])
        self.assertTrue(self.p["decision"]["l17_original_failure_preserved"])
        self.assertEqual(self.p["source_l17"]["required_result_status"], "NUMERICAL_HOLD_L17_TERMINAL_UNDER_CURRENT_CONTRACT")
        self.assertAlmostEqual(self.p["matched_site_screen"]["slab_depth_sensitivity_max_ev_per_CO"], 0.005)
        self.assertEqual(self.p["execution"]["checkpoint_mode"], "QE_CLEAN_MAX_SECONDS_EXACT_RESTART")

    def test_protocol_rejects_retuning(self):
        q = json.loads(json.dumps(self.p))
        q["matched_site_screen"]["slab_depth_sensitivity_max_ev_per_CO"] = 0.006
        with self.assertRaises(SystemExit):
            m.verify_protocol(q)

    def test_protocol_rejects_l17_reclassification(self):
        q = json.loads(json.dumps(self.p))
        q["source_l17"]["original_surface_excess_gate_pass"] = True
        with self.assertRaises(SystemExit):
            m.verify_protocol(q)

    def test_site_offsets_are_distinct(self):
        for layers in (15, 17):
            sites = m.site_offsets(layers)
            self.assertNotEqual(sites["fcc_hollow"], sites["hcp_hollow"])
            self.assertIn("top", sites)
            self.assertIn("bridge", sites)

    def test_sufficiency_pass(self):
        result = m.classify_sufficiency(
            {
                "L15": {"top": -100.0, "bridge": -99.950, "fcc_hollow": -99.940, "hcp_hollow": -99.930},
                "L17": {"top": -120.0, "bridge": -119.951, "fcc_hollow": -119.941, "hcp_hollow": -119.931},
            },
            0.005,
        )
        self.assertTrue(result["sufficiency_pass"])
        self.assertTrue(result["same_global_minimum"])
        self.assertLessEqual(result["slab_depth_sensitivity_ev_per_CO"], 0.005)

    def test_sufficiency_fails_on_minimum_flip(self):
        result = m.classify_sufficiency(
            {
                "L15": {"top": -100.0, "bridge": -99.995, "fcc_hollow": -99.990, "hcp_hollow": -99.980},
                "L17": {"top": -120.0, "bridge": -120.002, "fcc_hollow": -119.990, "hcp_hollow": -119.980},
            },
            0.005,
        )
        self.assertFalse(result["sufficiency_pass"])
        self.assertFalse(result["same_global_minimum"])

    def test_checkpoint_manifest_detects_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = root / "qe_checkpoint"
            c.mkdir()
            f = c / "state.bin"
            f.write_bytes(b"abc")
            digest = m.write_checkpoint_manifest(root)
            self.assertEqual(m.verify_checkpoint_manifest(root, digest), digest)
            f.write_bytes(b"abd")
            with self.assertRaises(SystemExit):
                m.verify_checkpoint_manifest(root, digest)

    def test_control_only_restart_fields(self):
        raw = "&CONTROL\n calculation='scf',\n/\n&SYSTEM\n/\n"
        out = m.add_control_fields(raw, "restart", 16200)
        self.assertIn("restart_mode='restart'", out)
        self.assertIn("max_seconds=16200", out)
        self.assertEqual(out.count("restart_mode"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
