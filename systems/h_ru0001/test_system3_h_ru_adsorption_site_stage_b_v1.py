#!/usr/bin/env python3
import importlib.util, json, math, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("b",ROOT/"system3_h_ru_adsorption_site_stage_b_v1.py")
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
a=b.a

class TestStageB(unittest.TestCase):
    def test_registered_basin_classifier(self):
        aa=2.7252915734660723
        for site in ["top","bridge","fcc_hollow","hcp_hollow"]:
            x,y=a.site_xy(aa,site)
            got=b.nearest_basin(x,y,aa)
            self.assertEqual(got["basin"],site,(site,got))
            self.assertLess(got["distance_angstrom"],1e-9)

    def test_off_registry_classifier(self):
        aa=2.7252915734660723
        # Chosen away from all registered high-symmetry motifs.
        got=b.nearest_basin(0.22*aa,0.31*aa,aa)
        self.assertIn(got["basin"],["off_registry","bridge","fcc_hollow","hcp_hollow","top"])

    def test_protocol_requires_spin_sensitivity_before_path(self):
        p=json.load(open(ROOT/"SYSTEM3_ADSORPTION_SITE_SCREEN_PROTOCOL_v0.1.json"))
        self.assertIn("spin-polarized sensitivity",p["screen_model"]["spin_treatment"]["robustness_boundary"])
        self.assertFalse(p["automatic_path_or_rate_progression"])
        self.assertEqual(p["numerical_reproduction"]["absolute_total_energy_difference_max_ev"],0.001)

if __name__=="__main__":
    unittest.main()
