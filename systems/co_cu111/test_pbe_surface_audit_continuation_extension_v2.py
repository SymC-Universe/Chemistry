#!/usr/bin/env python3
import importlib.util,json,os,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
MOD=HERE/'pbe_surface_audit_continuation_extension_v2.py'
spec=importlib.util.spec_from_file_location('ext2',MOD); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)
class TestExtensionV2(unittest.TestCase):
    def test_protocol_frozen(self):
        p=m.protocol(HERE/'SYSTEM2_PBE_SURFACE_AUDIT_CONTINUATION_EXTENSION_v0.2.json')
        self.assertEqual(p['execution']['maximum_new_continuation_segments'],6)
        self.assertEqual(p['execution']['logical_segment_numbers'],list(range(25,31)))
        self.assertEqual(p['selection']['required_selected_mpi_ranks'],1)
        self.assertEqual(p['selection']['required_execution_mode'],'DIRECT_ONE_RANK')
        self.assertEqual(p['unchanged_science']['force_gate_ev_per_angstrom'],0.02)
        self.assertEqual(p['unchanged_science']['independent_scf_reproduction_gate_ev'],0.001)
        self.assertFalse(p['provenance']['scientific_settings_changed'])
        self.assertFalse(p['provenance']['kinetic_inputs_used'])
    def test_parent_fixture_when_supplied(self):
        root=os.environ.get('CO_CU111_SEG24_FIXTURE')
        if not root: self.skipTest('fixture not supplied')
        p=m.protocol(HERE/'SYSTEM2_PBE_SURFACE_AUDIT_CONTINUATION_EXTENSION_v0.2.json')
        d,q=m.verify_parent_segment24(Path(root),p)
        self.assertEqual(d['status'],'CONTINUE'); self.assertEqual(d['logical_segment'],24)
        self.assertEqual(d['execution_mode'],'DIRECT_ONE_RANK'); self.assertEqual(d['mpi_ranks'],1)
        self.assertAlmostEqual(d['latest_authoritative_max_movable_force_ev_per_angstrom'],0.02317772558394175,places=12)
        self.assertTrue(d['next_trial_atoms'])
if __name__=='__main__': unittest.main()
