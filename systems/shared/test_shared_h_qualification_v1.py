#!/usr/bin/env python3
import json, math, pathlib, tempfile, unittest, importlib.util

ROOT=pathlib.Path(__file__).resolve().parent
MOD=ROOT/"shared_h_qualification_v1.py"
spec=importlib.util.spec_from_file_location("hqual", MOD)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class TestSharedHQualification(unittest.TestCase):
    def test_protocol_frozen_and_non_target(self):
        p=json.load(open(ROOT/"H_PSEUDOPOTENTIAL_QUALIFICATION_v0.1.json"))
        self.assertEqual(p["status"],"FROZEN_BEFORE_QUALIFICATION_RESULTS")
        self.assertEqual(p["candidate"]["family"],"SG15 ONCV")
        self.assertEqual(p["independent_convergence_evidence"]["wavefunction_cutoff_ry"],70.0)
        self.assertEqual(p["independent_convergence_evidence"]["charge_density_cutoff_ry"],140.0)
        self.assertEqual(p["production_basis_compatibility"]["h_ru0001_basis"],{"ecutwfc_ry":70.0,"ecutrho_ry":280.0})
        self.assertTrue(all(v is False for v in p["firewall"].values()))

    def test_energy_parser(self):
        txt="!    total energy              =   -1.25000000 Ry\nJOB DONE.\n"
        self.assertAlmostEqual(m.last_energy_ev(txt), -1.25*m.RY_TO_EV, places=10)

    def test_final_positions_and_bond(self):
        txt="""Begin final coordinates
ATOMIC_POSITIONS (angstrom)
H 1.0 2.0 3.0
H 1.0 2.0 3.75
End final coordinates
"""
        pts=m.final_positions(txt,2)
        self.assertAlmostEqual(m.bond_length(pts),0.75,places=12)

    def test_force_parser(self):
        txt="""Forces acting on atoms (cartesian axes, Ry/au):
atom    1 type  1   force = 0.000100 0.000000 0.000000
atom    2 type  1   force = 0.000000 0.000200 0.000000
"""
        self.assertAlmostEqual(m.last_max_force_ev_ang(txt,2),0.0002*m.RY_BOHR_TO_EV_ANG,places=12)

if __name__=="__main__":
    unittest.main()
