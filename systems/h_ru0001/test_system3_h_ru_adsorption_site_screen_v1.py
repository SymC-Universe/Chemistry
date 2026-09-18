#!/usr/bin/env python3
import importlib.util, json, math, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("site",ROOT/"system3_h_ru_adsorption_site_screen_v1.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class TestHRuSiteScreen(unittest.TestCase):
    def test_protocol_is_prospective_and_complete(self):
        p=json.load(open(ROOT/"SYSTEM3_ADSORPTION_SITE_SCREEN_PROTOCOL_v0.1.json"))
        self.assertEqual(p["status"],"FROZEN_BEFORE_ADSORPTION_RESULTS")
        self.assertEqual(p["screen_model"]["candidate_sites"],["top","bridge","fcc_hollow","hcp_hollow"])
        self.assertEqual(p["screen_model"]["starting_heights_angstrom"],[1.0,1.5,2.0])
        self.assertEqual(p["screen_model"]["spin_treatment"]["nspin"],1)
        self.assertEqual(p["numerical_reproduction"]["ordering_resolution_ev"],0.002)
        self.assertEqual(p["execution"]["segment_seconds"],3300)
        self.assertEqual(p["execution"]["max_segments_per_relaxation_case"],5)
        self.assertTrue(all(v is False for v in p["evidence_firewall"].values()))

    def test_hcp_hollow_is_over_second_layer_b_site(self):
        a=2.7252915734660723
        a1,a2=m.primitive_vectors(a)
        origin=m.vadd(a1,a2)
        hcp=m.site_xy(a,"hcp_hollow")
        local=(hcp[0]-origin[0],hcp[1]-origin[1])
        expected=(0.5*a,a/(2.0*math.sqrt(3.0)))
        self.assertAlmostEqual(local[0],expected[0],places=10)
        self.assertAlmostEqual(local[1],expected[1],places=10)

    def test_fcc_and_hcp_are_distinct(self):
        a=2.7252915734660723
        f=m.site_xy(a,"fcc_hollow"); h=m.site_xy(a,"hcp_hollow")
        self.assertGreater(math.hypot(f[0]-h[0],f[1]-h[1]),0.5)

    def test_supercell_atom_count_and_mobility(self):
        a=2.7252915734660723
        coords=[]
        for i in range(17):
            coords.append(["Ru",0.0 if i%2==0 else a/2.0,0.0 if i%2==0 else a/(2*math.sqrt(3)),7.0+i*2.0])
        atoms=m.build_stage_a_atoms(coords,a,"top",1.5)
        self.assertEqual(len(atoms),70)
        self.assertEqual(sum(1 for x in atoms if x["label"]=="Ru"),68)
        self.assertEqual(sum(1 for x in atoms if x["label"]=="H"),2)
        self.assertEqual(sum(1 for x in atoms if x["label"]=="Ru" and x["flags"]==[0,0,1]),16)
        self.assertTrue(all(x["flags"]==[0,0,1] for x in atoms[-2:]))

if __name__=="__main__":
    unittest.main()
