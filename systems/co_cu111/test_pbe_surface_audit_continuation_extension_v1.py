#!/usr/bin/env python3
import importlib.util, json, os, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
MOD=HERE/'pbe_surface_audit_continuation_extension_v1.py'
spec=importlib.util.spec_from_file_location('ext',MOD); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m)
class TestExtension(unittest.TestCase):
    def test_protocol_frozen(self):
        p=m.protocol(HERE/'SYSTEM2_PBE_SURFACE_AUDIT_CONTINUATION_EXTENSION_v0.1.json')
        self.assertEqual(p['execution']['maximum_new_continuation_segments'],12)
        self.assertEqual(p['execution']['logical_segment_numbers'],list(range(13,25)))
        self.assertEqual(p['selection']['required_selected_mpi_ranks'],1)
        self.assertEqual(p['selection']['required_execution_mode'],'DIRECT_ONE_RANK')
        self.assertEqual(p['unchanged_science']['force_gate_ev_per_angstrom'],0.02)
        self.assertEqual(p['unchanged_science']['independent_scf_reproduction_gate_ev'],0.001)
        self.assertFalse(p['provenance']['scientific_settings_changed'])
        self.assertFalse(p['provenance']['kinetic_inputs_used'])
    def test_parent_fixture_when_supplied(self):
        root=os.environ.get('CO_CU111_SEG12_FIXTURE')
        if not root: self.skipTest('fixture not supplied')
        p=m.protocol(HERE/'SYSTEM2_PBE_SURFACE_AUDIT_CONTINUATION_EXTENSION_v0.1.json')
        old=m.import_parent(); d,q=m.verify_parent_segment12(Path(root),p,old)
        self.assertEqual(d['status'],'CONTINUE'); self.assertEqual(d['logical_segment'],12)
        self.assertEqual(d['execution_mode'],'DIRECT_ONE_RANK'); self.assertEqual(d['mpi_ranks'],1)
        self.assertAlmostEqual(d['latest_authoritative_max_movable_force_ev_per_angstrom'],0.0368480251121856,places=12)
if __name__=='__main__': unittest.main()
