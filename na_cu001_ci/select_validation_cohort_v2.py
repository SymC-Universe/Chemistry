#!/usr/bin/env python3
"""Deterministically draw an independently selected validation cohort."""
from __future__ import annotations
import argparse,hashlib,json,random
from pathlib import Path

def sha256(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidates',required=True);p.add_argument('--protocol',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--n',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args()
    protocol=json.load(open(a.protocol));candidates=json.load(open(a.candidates))
    if protocol.get('schema')!='barrier-atlas-validation-selection-v0.1' or protocol.get('status')!='FROZEN_BEFORE_SYSTEM_2_SELECTION':raise SystemExit('HOLD: selection protocol not frozen')
    if not isinstance(candidates,list) or len(candidates)<a.n:raise SystemExit('HOLD: candidate list insufficient')
    ids=[str(x['candidate_id']) for x in candidates]
    if len(set(ids))!=len(ids):raise SystemExit('HOLD: duplicate candidate_id')
    rng=random.Random(a.seed);selected=rng.sample(candidates,a.n)
    out={'schema':'barrier-atlas-validation-cohort-v0.1','status':'PASS','candidate_list_sha256':sha256(a.candidates),'selection_protocol_sha256':sha256(a.protocol),'seed':a.seed,'n':a.n,'selected':selected,'failure_retention_required':True}
    Path(a.out).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
