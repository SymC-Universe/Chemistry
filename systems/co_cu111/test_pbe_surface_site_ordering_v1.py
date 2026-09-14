#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "pbe_surface_site_ordering_v1.py"
PROTOCOL_PATH = HERE / "SYSTEM2_PBE_SURFACE_SITE_ORDERING_PROTOCOL_v0.1.json"
spec = importlib.util.spec_from_file_location("surface_gate", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class SurfaceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads(PROTOCOL_PATH.read_text())

    def test_clean_geometry_centered_and_abc(self) -> None:
        a0 = self.protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]
        cell, atoms = mod.clean_geometry(a0, 7, 16.0)
        self.assertEqual(len(atoms), 7)
        self.assertAlmostEqual(sum(a["position_angstrom"][2] for a in atoms), 0.0, places=10)
        self.assertEqual(sum(a["flags"][2] for a in atoms), 4)
        self.assertGreater(cell[2][2], 16.0)

    def test_hollow_labels_follow_subsurface_stacking(self) -> None:
        for layers in (7, 9, 11, 13):
            sites = mod.site_offsets(layers)
            self.assertNotEqual(sites["fcc_hollow"], sites["hcp_hollow"])
            self.assertEqual(set(sites), {"top", "bridge", "fcc_hollow", "hcp_hollow"})

    def test_adsorption_supercell_atom_count(self) -> None:
        a0 = self.protocol["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]
        cell, atoms = mod.clean_geometry(a0, 7, 16.0)
        clean = {"layers": 7, "vacuum_angstrom": 16.0, "layer_z_angstrom": sorted(a["position_angstrom"][2] for a in atoms), "cell_angstrom": cell, "case_id": "synthetic"}
        ads_cell, ads = mod.adsorption_geometry(clean, "fcc_hollow", self.protocol)
        self.assertEqual(len(ads), 114)
        self.assertAlmostEqual(ads_cell[2][2], cell[2][2] + 4.0, places=10)
        self.assertEqual([ads[-2]["symbol"], ads[-1]["symbol"]], ["C", "O"])
        self.assertEqual(ads[-2]["flags"], [0, 0, 1])

    def test_good_top_ordering_passes(self) -> None:
        r = mod.classify_site_gate(
            {"top": -10.0, "bridge": -9.95, "fcc_hollow": -9.94, "hcp_hollow": -9.93},
            {"top": -10.02, "bridge": -9.969, "fcc_hollow": -9.959, "hcp_hollow": -9.949},
            0.005,
        )
        self.assertTrue(r["numerical_sensitivity_pass"])
        self.assertTrue(r["top_site_ordering_pass"])

    def test_hollow_below_top_rejects(self) -> None:
        r = mod.classify_site_gate(
            {"top": -10.0, "bridge": -9.99, "fcc_hollow": -10.02, "hcp_hollow": -9.98},
            {"top": -10.01, "bridge": -10.00, "fcc_hollow": -10.03, "hcp_hollow": -9.99},
            0.005,
        )
        self.assertTrue(r["numerical_sensitivity_pass"])
        self.assertFalse(r["top_site_ordering_pass"])

    def test_numerical_sensitivity_hold(self) -> None:
        r = mod.classify_site_gate(
            {"top": -10.0, "bridge": -9.95, "fcc_hollow": -9.94, "hcp_hollow": -9.93},
            {"top": -10.0, "bridge": -9.93, "fcc_hollow": -9.92, "hcp_hollow": -9.91},
            0.005,
        )
        self.assertFalse(r["numerical_sensitivity_pass"])
        self.assertFalse(r["top_site_ordering_pass"])


if __name__ == "__main__":
    unittest.main()
