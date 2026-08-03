#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

def main():
    p=Path(sys.argv[1]); data=json.loads(p.read_text()); jobs=data.get('jobs',{})
    assert set(jobs)=={'prepare','slab-cases','slab-gate'}
    assert jobs['slab-cases']['needs']=='prepare'
    assert jobs['slab-gate']['needs']==['prepare','slab-cases']
    inc=jobs['slab-cases']['strategy']['matrix']['include']
    assert len(inc)==16
    assert {(x['layers'],x['vacuum']) for x in inc}=={(l,v) for l in (5,7,9,11) for v in (12,16,20,24)}
    text=p.read_text()
    assert 'run_computational_stage_v4.sh prepare' in text
    assert 'run_computational_stage_v4.sh slab-case' in text
    assert 'run_computational_stage_v4.sh slab-analyze' in text
    assert data['permissions']=={'contents':'read','actions':'read'}
    print('PASS C6-C7 workflow contract: 3 jobs, 16 matrix jobs, 64 slab SCFs')
if __name__=='__main__': main()
