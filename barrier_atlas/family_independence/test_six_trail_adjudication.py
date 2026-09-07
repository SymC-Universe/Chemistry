#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from validate_six_trail_adjudication import validate

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


class SixTrailAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adj = load("SIX_TRAIL_ADJUDICATION_v0.1.json")
        cls.campaign = load("FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json")
        cls.readout = (ROOT / "CONGLOMERATE_EVIDENCE_READOUT_v0.1.md").read_text()

    def test_frozen_record_passes(self):
        self.assertEqual(validate(self.adj, self.campaign, self.readout), [])

    def test_missing_trail_fails(self):
        x = copy.deepcopy(self.adj)
        x["trails"] = x["trails"][:-1]
        self.assertTrue(validate(x, self.campaign, self.readout))

    def test_ready_with_hold_gate_fails(self):
        x = copy.deepcopy(self.adj)
        rec = next(r for r in x["trails"] if r["trail_id"] == "FI-MC06-CYCLOPROPANE-PROPENE")
        rec["condition_gate"] = "HOLD"
        self.assertTrue(validate(x, self.campaign, self.readout))

    def test_parent_hash_drift_fails(self):
        x = copy.deepcopy(self.adj)
        x["parent_release"]["workbook_sha256"] = "0" * 64
        self.assertTrue(validate(x, self.campaign, self.readout))

    def test_cyclobutene_reassignment_fails(self):
        x = copy.deepcopy(self.adj)
        rec = next(r for r in x["trails"] if r["trail_id"] == "FI-MC02-CYCLOBUTENE-CLASSIFICATION-CHECK")
        rec["terminal_state"] = "READY_FOR_ADJUDICATION"
        rec["ready_for_adjudication"] = True
        self.assertTrue(validate(x, self.campaign, self.readout))

    def test_cyclopropane_single_barrier_flattening_fails(self):
        x = copy.deepcopy(self.adj)
        rec = next(r for r in x["trails"] if r["trail_id"] == "FI-MC06-CYCLOPROPANE-PROPENE")
        rec["representation_mode"] = "SINGLE_BARRIER"
        self.assertTrue(validate(x, self.campaign, self.readout))

    def test_grade_change_fails(self):
        x = copy.deepcopy(self.adj)
        x["grades_changed"] = 1
        self.assertTrue(validate(x, self.campaign, self.readout))


if __name__ == "__main__":
    unittest.main()
