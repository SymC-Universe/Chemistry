#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

import pbe_surface_audit_proposal_relay_v1 as relay

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "SYSTEM2_PBE_SURFACE_AUDIT_PROPOSAL_RELAY_v0.1.json"


class ProposalRelayTests(unittest.TestCase):
    def test_protocol_is_frozen_mechanical_only(self) -> None:
        p = relay.protocol(PROTOCOL)
        self.assertEqual(p["relay_contract"]["target"], "audit")
        self.assertEqual(p["relay_contract"]["case_id"], "L13-V28-K24-audit")
        self.assertEqual(p["relay_contract"]["logical_segment_numbers"], [5, 6, 7, 8])
        self.assertEqual(p["relay_contract"]["segment_runtime_cap_seconds"], 16200)
        self.assertFalse(p["provenance"]["scientific_settings_changed"])
        self.assertFalse(p["provenance"]["kinetic_inputs_used"])
        self.assertFalse(p["provenance"]["surface_energies_or_kinetic_results_used_to_choose_relay"])

    def test_last_proposed_trial_requires_evaluated_parent(self) -> None:
        template = [
            {"symbol": "Cu", "position_angstrom": [0.0, 0.0, 0.0], "flags": [0, 0, 1], "layer": 0},
            {"symbol": "Cu", "position_angstrom": [0.0, 0.0, 1.0], "flags": [0, 0, 1], "layer": 1},
        ]
        good = """
!    total energy              =   -10.00000000 Ry
     Total force =     0.001000     Total SCF correction =     0.000000
     BFGS Geometry Optimization
ATOMIC_POSITIONS (angstrom)
Cu 0.0 0.0 0.01 0 0 1
Cu 0.0 0.0 0.99 0 0 1
"""
        got = relay.last_bfgs_proposed_trial(good, 2, template)
        self.assertIsNotNone(got)
        rows, evidence = got
        self.assertEqual(evidence["trial_semantics"], "PROPOSED_NOT_YET_EVALUATED")
        self.assertAlmostEqual(rows[0]["position_angstrom"][2], 0.01)

        no_force = """
!    total energy              =   -10.00000000 Ry
     BFGS Geometry Optimization
ATOMIC_POSITIONS (angstrom)
Cu 0.0 0.0 0.01 0 0 1
Cu 0.0 0.0 0.99 0 0 1
"""
        self.assertIsNone(relay.last_bfgs_proposed_trial(no_force, 2, template))

    def test_last_of_multiple_trials_is_selected_only_after_parent_evaluation(self) -> None:
        template = [
            {"symbol": "Cu", "position_angstrom": [0.0, 0.0, 0.0], "flags": [0, 0, 1], "layer": 0},
            {"symbol": "Cu", "position_angstrom": [0.0, 0.0, 1.0], "flags": [0, 0, 1], "layer": 1},
        ]
        text = """
!    total energy              =   -10.00000000 Ry
     Total force =     0.001000     Total SCF correction =     0.000000
     BFGS Geometry Optimization
ATOMIC_POSITIONS (angstrom)
Cu 0.0 0.0 0.01 0 0 1
Cu 0.0 0.0 0.99 0 0 1
!    total energy              =   -10.10000000 Ry
     Total force =     0.000900     Total SCF correction =     0.000000
     BFGS Geometry Optimization
ATOMIC_POSITIONS (angstrom)
Cu 0.0 0.0 0.02 0 0 1
Cu 0.0 0.0 0.98 0 0 1
"""
        got = relay.last_bfgs_proposed_trial(text, 2, template)
        self.assertIsNotNone(got)
        rows, _ = got
        self.assertAlmostEqual(rows[0]["position_angstrom"][2], 0.02)
        self.assertAlmostEqual(rows[1]["position_angstrom"][2], 0.98)

    def test_same_geometry_fails_progress_diagnostic(self) -> None:
        rows = [{"position_angstrom": [0.0, 0.0, 0.0]}]
        self.assertTrue(relay.same_geometry(rows, rows))
        shifted = [{"position_angstrom": [0.0, 0.0, 1e-4]}]
        self.assertFalse(relay.same_geometry(rows, shifted))
        self.assertGreater(relay.max_displacement_angstrom(rows, shifted), 0.0)

    def test_real_parent_seed_when_provided(self) -> None:
        root = os.environ.get("CO_CU111_AUDIT_SEG4")
        if not root:
            self.skipTest("real audit segment-4 artifact not provided")
        p = relay.protocol(PROTOCOL)
        p["_sha256"] = relay.sha256(PROTOCOL)
        relay.verify_frozen_sources(p)
        _, surface, target = relay.original_context(p)
        _, template = relay.v1.cell_and_template(surface, target)
        trial, evidence = relay.load_parent_v1_seed(Path(root), p, target, template)
        self.assertEqual(len(trial), 13)
        self.assertEqual(evidence["trial_semantics"], "PROPOSED_NOT_YET_EVALUATED")
        self.assertGreater(evidence["input_to_trial_max_displacement_angstrom"], 1e-10)


if __name__ == "__main__":
    unittest.main()
