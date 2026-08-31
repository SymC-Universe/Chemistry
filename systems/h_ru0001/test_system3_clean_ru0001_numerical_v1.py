#!/usr/bin/env python3
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("surf", HERE / "system3_clean_ru0001_numerical_v1.py")
surf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(surf)


class SurfaceNumericalTests(unittest.TestCase):
    def test_geometry_is_centered_and_same_termination(self):
        cell_z, rows = surf.slab_geometry(2.725, 4.295, 7, 20.0)
        self.assertGreater(cell_z, 20.0)
        zs = [r[2] for r in rows]
        self.assertAlmostEqual(sum(zs) / len(zs), 0.5, places=14)
        self.assertEqual(rows[0][:2], rows[-1][:2])
        for i in range(len(rows)):
            self.assertAlmostEqual(zs[i] + zs[-1-i], 1.0, places=14)

    def test_total_vacuum_definition(self):
        c = 4.2946867285
        layers = 13
        vacuum = 25.0
        cell_z, _ = surf.slab_geometry(2.725, c, layers, vacuum)
        self.assertAlmostEqual(cell_z - (layers - 1) * c / 2.0, vacuum, places=12)

    def test_suffix_selection_rejects_endpoint_only(self):
        rows = [
            {"surface_excess_ev_per_surface_atom": 0.0},
            {"surface_excess_ev_per_surface_atom": 0.004},
            {"surface_excess_ev_per_surface_atom": 0.006},
        ]
        idx, _ = surf.suffix_selection(rows, 0.001)
        self.assertIsNone(idx)

    def test_suffix_selection_requires_all_finer_points(self):
        rows = [
            {"surface_excess_ev_per_surface_atom": 0.5004},
            {"surface_excess_ev_per_surface_atom": 0.5030},
            {"surface_excess_ev_per_surface_atom": 0.5000},
        ]
        idx, _ = surf.suffix_selection(rows, 0.001)
        self.assertIsNone(idx)

    def test_suffix_selection_can_choose_lowest_stable_nonterminal(self):
        rows = [
            {"surface_excess_ev_per_surface_atom": 0.5030},
            {"surface_excess_ev_per_surface_atom": 0.5008},
            {"surface_excess_ev_per_surface_atom": 0.5000},
        ]
        idx, deltas = surf.suffix_selection(rows, 0.001)
        self.assertEqual(idx, 1)
        self.assertAlmostEqual(deltas[1], 0.0008)

    def test_protocol_firewall_and_minimum_layer(self):
        p = json.loads((HERE / "SYSTEM3_CLEAN_RU0001_SURFACE_PROTOCOL_v0.1.json").read_text())
        self.assertEqual(p["status"], "FROZEN_BEFORE_SYSTEM3_CLEAN_SURFACE_RESULTS")
        self.assertTrue(all(v is False for v in p["evidence_firewall"].values()))
        self.assertEqual(p["numerical_gate"]["layer_stage"]["minimum_eligible_layers"], 7)
        self.assertEqual(p["numerical_gate"]["layer_stage"]["terminal_reference_layers"], 13)
        self.assertEqual(p["fresh_bulk_reference"]["kmesh"], [24, 24, 16])

    def test_relaxation_requires_native_checkpoint_wiring(self):
        p = json.loads((HERE / "SYSTEM3_CLEAN_RU0001_RELAXATION_PROTOCOL_v0.1.json").read_text())
        c = p["native_qe_checkpoint_restart"]
        self.assertTrue(c["required"])
        self.assertEqual(c["qualification_run_id"], 33343734581)
        self.assertTrue(c["qualification_is_not_production_activation"])
        self.assertEqual(c["clean_stop_mechanism"], "CONTROL.max_seconds")
        self.assertEqual(c["resume_restart_mode"], "restart")


if __name__ == "__main__":
    unittest.main()
