#!/usr/bin/env python3
import json,tempfile,unittest
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent

def mod(path,name):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
V=mod(HERE/'validate_family_independence_campaign.py','validator')
I=mod(HERE/'inventory_public_trails.py','inventory')

class Tests(unittest.TestCase):
    def test_frozen_contract(self):
        c=json.loads((HERE/'FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json').read_text())
        t=json.loads((HERE/'candidate_trails_v0.1.json').read_text())
        self.assertEqual(V.validate(c,t),[])
    def test_mutation_fails(self):
        c=json.loads((HERE/'FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json').read_text())
        t=json.loads((HERE/'candidate_trails_v0.1.json').read_text())
        c['parent_release']['immutable']=False
        self.assertTrue(any('immutable' in x for x in V.validate(c,t)))
    def test_auto_admission_fails(self):
        c=json.loads((HERE/'FAMILY_INDEPENDENCE_CAMPAIGN_v0.1.json').read_text())
        t=json.loads((HERE/'candidate_trails_v0.1.json').read_text())
        t['trails'][0]['automatic_admission']=True
        self.assertTrue(any('automatic admission' in x for x in V.validate(c,t)))
    def test_inventory_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td); (r/'RATE').mkdir(); (r/'README.md').write_text('x'); (r/'RATE'/'plumed.dat').write_text('y')
            o=I.trypsin(r)
            self.assertEqual(o['role'],'candidate_generation_only')
            self.assertEqual(o['admission_decision'],'NOT_EVALUATED')
            self.assertTrue(o['files'][0]['sha256'])

if __name__=='__main__': unittest.main()
