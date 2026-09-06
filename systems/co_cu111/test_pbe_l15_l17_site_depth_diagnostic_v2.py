#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "pbe_l15_l17_site_depth_diagnostic_v2.py"
PROTOCOL_PATH = HERE / "SYSTEM2_PBE_L15_L17_SITE_DEPTH_DIAGNOSTIC_v0.2.json"
spec = importlib.util.spec_from_file_location("depth_v2", RUNNER_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def normalized_protocol():
    p = json.loads(PROTOCOL_PATH.read_text())
    m.verify_protocol_v2(p)
    q = json.loads(json.dumps(p))
    q["matched_site_screen"] = q["matched_site_depth_diagnostic"]
    return q


def synthetic_clean(layers: int, vacuum: float):
    a0 = 3.632355796707377
    d111 = a0 / math.sqrt(3.0)
    cell_z = (layers - 1) * d111 + vacuum
    midpoint = (layers - 1) / 2.0
    atoms = []
    for layer in range(layers):
        z = (layer - midpoint) * d111
        atoms.append({
            "symbol": "Cu",
            "position_angstrom": [0.0, 0.0, z],
            "flags": [0, 0, 0],
            "layer": layer,
        })
    return {
        "case_id": f"L{layers}-synthetic",
        "layers": layers,
        "vacuum_angstrom": vacuum,
        "cell_angstrom": [[a0 / math.sqrt(2.0), 0.0, 0.0], [0.5 * a0 / math.sqrt(2.0), 0.5 * math.sqrt(3.0) * a0 / math.sqrt(2.0), 0.0], [0.0, 0.0, cell_z]],
        "final_atoms": atoms,
    }


class TestL15L17SiteDepthDiagnosticV2(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(PROTOCOL_PATH.read_text())
        self.p = normalized_protocol()

    def test_frozen_v02_contract(self):
        m.verify_protocol_v2(self.raw)
        self.assertEqual(self.raw["matched_site_depth_diagnostic"]["supercell"], [2, 2])
        self.assertEqual(self.raw["matched_site_depth_diagnostic"]["kmesh"], 8)
        self.assertAlmostEqual(self.raw["matched_site_depth_diagnostic"]["nominal_coverage_ML"], 0.25)
        self.assertAlmostEqual(self.raw["matched_site_depth_diagnostic"]["slab_depth_sensitivity_max_ev_per_CO"], 0.005)
        self.assertFalse(self.raw["decision"]["low_coverage_4x4_sufficiency_claimed"])
        self.assertFalse(self.raw["decision"]["absolute_clean_surface_pass_claimed"])

    def test_resource_hold_is_preserved(self):
        parent = self.raw["parent_v0_1_resource_hold"]
        self.assertEqual(parent["workflow_run_id"], 34016668712)
        self.assertTrue(parent["all_eight_segment1_cases_failed_before_scientific_energy_result"])
        self.assertFalse(parent["scientific_result_consulted"])
        self.assertGreater(parent["requested_single_allocation_bytes"], 40_000_000_000)

    def test_rejects_return_to_4x4_under_v02_claim(self):
        q = json.loads(json.dumps(self.raw))
        q["matched_site_depth_diagnostic"]["supercell"] = [4, 4]
        with self.assertRaises(SystemExit):
            m.verify_protocol_v2(q)

    def test_rejects_threshold_retuning(self):
        q = json.loads(json.dumps(self.raw))
        q["matched_site_depth_diagnostic"]["slab_depth_sensitivity_max_ev_per_CO"] = 0.006
        with self.assertRaises(SystemExit):
            m.verify_protocol_v2(q)

    def test_rejects_l17_reclassification(self):
        q = json.loads(json.dumps(self.raw))
        q["source_l17"]["original_surface_excess_gate_pass"] = True
        with self.assertRaises(SystemExit):
            m.verify_protocol_v2(q)

    def test_matched_geometry_atom_counts_and_common_vacuum(self):
        l15 = synthetic_clean(15, 32.0)
        l17 = synthetic_clean(17, 36.0)
        c15, a15, e15 = m.matched_geometry_v2(l15, "L15", "top", self.p)
        c17, a17, e17 = m.matched_geometry_v2(l17, "L17", "top", self.p)
        self.assertEqual(len(a15), 15 * 4 + 2)
        self.assertEqual(len(a17), 17 * 4 + 2)
        self.assertAlmostEqual(e15["cell_z_adjustment_angstrom"], 4.0)
        self.assertAlmostEqual(e17["cell_z_adjustment_angstrom"], 0.0)
        self.assertEqual(e15["kmesh"], 8)
        self.assertFalse(e15["low_coverage_4x4_sufficiency_claimed"])
        self.assertGreater(c17[2][2], c15[2][2])

    def test_sufficiency_classifier_pass_and_fail(self):
        good = m.classify_sufficiency(
            {
                "L15": {"top": -100.0, "bridge": -99.950, "fcc_hollow": -99.940, "hcp_hollow": -99.930},
                "L17": {"top": -120.0, "bridge": -119.951, "fcc_hollow": -119.941, "hcp_hollow": -119.931},
            },
            0.005,
        )
        self.assertTrue(good["sufficiency_pass"])
        bad = m.classify_sufficiency(
            {
                "L15": {"top": -100.0, "bridge": -99.995, "fcc_hollow": -99.990, "hcp_hollow": -99.980},
                "L17": {"top": -120.0, "bridge": -120.002, "fcc_hollow": -119.990, "hcp_hollow": -119.980},
            },
            0.005,
        )
        self.assertFalse(bad["sufficiency_pass"])

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

    def test_exact_restart_control_fields(self):
        raw = "&CONTROL\n calculation='scf',\n/\n&SYSTEM\n/\n"
        out = m.add_control_fields(raw, "restart", 16200)
        self.assertIn("restart_mode='restart'", out)
        self.assertIn("max_seconds=16200", out)
        self.assertEqual(out.count("restart_mode"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
