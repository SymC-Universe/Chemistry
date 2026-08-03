#!/usr/bin/env python3
from __future__ import annotations
import copy
from bulk_v04_run_audit_v1 import audit, EOS_PAIRS, DECISION, SUMMARIES

def fixture():
    steps=[
      {'name':'Audit matrix completeness, reference validity, and source hashes','conclusion':'success'},
      {'name':'Audit reference, select candidate, and build compact decision','conclusion':'success'},
      {'name':'Upload compact decision and PASS-only handoff','conclusion':'success'},
      {'name':'Upload all EOS summaries used by the decision','conclusion':'success'},
      {'name':'Upload complete retained raw extension evidence','conclusion':'failure'},
    ]
    jobs=[{'name':'prepare-engine','status':'completed','conclusion':'success'}]
    jobs += [{'name':f'extension-eos ({e}, {k}, candidate, e{e}_k{k})','status':'completed','conclusion':'success'} for e,k in EOS_PAIRS]
    jobs += [{'name':'extension-gate','status':'completed','conclusion':'cancelled','steps':steps}]
    names={DECISION,SUMMARIES}|{f'na-cu001-bulk-extension-raw-e{e}_k{k}' for e,k in EOS_PAIRS}
    arts=[{'id':i+1,'name':n,'size_in_bytes':100,'digest':'sha256:'+'a'*64,'expired':False} for i,n in enumerate(sorted(names))]
    return {'jobs':jobs},{'artifacts':arts}

def rejects(fn):
    try: fn()
    except SystemExit: return
    raise AssertionError('expected HOLD')

def test_accept_isolated_aggregate_failure():
    j,a=fixture(); out=audit(j,a,30843005718); assert out['status']=='PASS'; assert out['aggregate_raw_artifact']['required_for_scientific_closure'] is False

def test_reject_failed_eos():
    j,a=fixture(); j=copy.deepcopy(j); j['jobs'][1]['conclusion']='failure'; rejects(lambda:audit(j,a,1))

def test_reject_failed_scientific_gate_step():
    j,a=fixture(); j=copy.deepcopy(j); j['jobs'][-1]['steps'][1]['conclusion']='failure'; rejects(lambda:audit(j,a,1))

def test_reject_missing_individual_raw():
    j,a=fixture(); a=copy.deepcopy(a); a['artifacts']=[x for x in a['artifacts'] if x['name']!='na-cu001-bulk-extension-raw-e80_k14']; rejects(lambda:audit(j,a,1))

def test_reject_unhashed_artifact():
    j,a=fixture(); a=copy.deepcopy(a); a['artifacts'][0]['digest']=None; rejects(lambda:audit(j,a,1))

if __name__=='__main__':
    tests=[test_accept_isolated_aggregate_failure,test_reject_failed_eos,test_reject_failed_scientific_gate_step,test_reject_missing_individual_raw,test_reject_unhashed_artifact]
    for t in tests: t(); print('PASS',t.__name__)
    print(f'PASS {len(tests)} bulk run audit tests')
