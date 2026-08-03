#!/usr/bin/env python3
"""Validate the corrected Na/Cu(001) artifact DAG without self-reference."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any

PASS_STATES={"PASS","bulk_convergence_passed_slab_not_yet_run"}
def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def state(d:dict[str,Any]):
    for k in ('status','gate','scientific_status'):
        if isinstance(d.get(k),str):return d[k]
    return None
def check_links(d,root):
    errors=[]
    for i,x in enumerate(d.get('input_artifacts') or []):
        if not isinstance(x,dict) or not isinstance(x.get('path'),str) or not isinstance(x.get('sha256'),str):errors.append(f'bad input_artifacts[{i}]');continue
        p=root/x['path']
        if not p.is_file():errors.append(f'missing linked artifact {x["path"]}')
        elif sha256(p)!=x['sha256']:errors.append(f'hash mismatch {x["path"]}')
    return errors
def check_raw(path,root):
    errors=[]
    if not path.is_file():return {'status':'HOLD','errors':['raw manifest absent']}
    d=json.loads(path.read_text())
    if d.get('schema')!='na-cu001-computational-manifest-v0.2' or d.get('status')!='PASS':errors.append('raw manifest schema/state mismatch')
    rows=d.get('files') or []
    if not root.is_dir():errors.append('raw root absent')
    else:
        for x in rows:
            p=root/x['path']
            if not p.is_file():errors.append(f'raw file absent {x["path"]}')
            elif sha256(p)!=x['sha256']:errors.append(f'raw hash mismatch {x["path"]}')
            elif p.stat().st_size!=x['size_bytes']:errors.append(f'raw size mismatch {x["path"]}')
    return {'status':'PASS' if not errors else 'HOLD','errors':errors,'file_count':len(rows),'manifest_sha256':sha256(path)}
def check_nonresult_files(plan:dict[str,Any],root:Path)->dict[str,Any]:
    rows=[];errors=[]
    for item in plan.get('required_nonresult_files') or []:
        if isinstance(item,str):
            spec={'path':item}
        elif isinstance(item,dict):
            spec=item
        else:
            errors.append('invalid required_nonresult_files entry');continue
        rel=spec.get('path');row={'path':rel}
        if not isinstance(rel,str):
            row['errors']=['path absent'];errors.append('nonresult path absent');rows.append(row);continue
        p=root/rel;row_errors=[]
        if not p.is_file():
            row_errors.append('file absent')
        else:
            row['sha256']=sha256(p);row['size_bytes']=p.stat().st_size
            expected_sha=spec.get('sha256')
            if isinstance(expected_sha,str) and row['sha256']!=expected_sha:row_errors.append('hash mismatch')
            expected_schema=spec.get('schema');states=set(spec.get('states') or [])
            if expected_schema or states:
                try:d=json.loads(p.read_text())
                except Exception as e:d={};row_errors.append(f'invalid JSON: {e}')
                if expected_schema and d.get('schema')!=expected_schema:row_errors.append(f'schema mismatch {d.get("schema")}')
                if states and state(d) not in states:row_errors.append(f'state mismatch {state(d)}')
        row['status']='PASS' if not row_errors else 'HOLD';row['errors']=row_errors
        errors.extend(f'{rel}: {e}' for e in row_errors);rows.append(row)
    return {'status':'PASS' if not errors else 'HOLD','files':rows,'errors':errors}

def validate(plan_path,root,raw_root):
    plan=json.loads(plan_path.read_text())
    if plan.get('schema')!='na-cu001-integration-closure-v0.2':raise SystemExit('HOLD: plan schema')
    stages=plan.get('stages') or [];by_id={int(x['id']):x for x in stages};seen={};results=[];raw=check_raw(root/'RAW_ARTIFACT_INDEX.json',raw_root);nonresults=check_nonresult_files(plan,root)
    for s in stages:
        sid=int(s['id']);deps=[int(x) for x in s.get('dependencies',[])];up=all(seen.get(x,False) for x in deps);errors=[]
        rec={'id':sid,'name':s['name'],'artifact':s['artifact'],'expected_schema':s['schema'],'dependencies':deps}
        if s.get('generated_by_validator'):
            if not up:errors.append('upstream dependency not PASS')
            if raw['status']!='PASS':errors.append('raw artifacts not verified')
            if nonresults['status']!='PASS':errors.append('required non-result files not verified')
            rec.update({'declared_state':'PASS' if not errors else 'HOLD','validation_state':'PASS' if not errors else 'HOLD','generated_by_this_validation_run':True,'errors':errors})
        else:
            p=root/s['artifact']
            if not p.is_file():errors.append('artifact absent')
            else:
                try:d=json.loads(p.read_text())
                except Exception as e:d={};errors.append(f'invalid JSON: {e}')
                if d.get('schema')!=s['schema']:errors.append(f'schema mismatch {d.get("schema")}')
                if state(d) not in PASS_STATES:errors.append(f'non-PASS state {state(d)}')
                if not up and deps:errors.append('upstream dependency not PASS')
                errors.extend(check_links(d,root))
                linked={x.get('path') for x in (d.get('input_artifacts') or []) if isinstance(x,dict)}
                for dep in deps:
                    expected=by_id[dep]['artifact']
                    if expected not in linked:errors.append(f'dependency artifact not hash-linked {expected}')
                rec['actual_sha256']=sha256(p);rec['declared_state']=state(d)
            rec.update({'validation_state':'PASS' if not errors else 'HOLD','errors':errors})
        seen[sid]=not errors;results.append(rec)
    overall='PASS' if all(seen.values()) else 'HOLD'
    return {'schema':'na-cu001-integration-readiness-v0.2','status':overall,'plan_sha256':sha256(plan_path),'raw_artifact_validation':raw,'required_nonresult_validation':nonresults,'stages':results,
            'rule':'No missing, malformed, non-PASS, unhashed, or self-referential stage may be promoted.','experimental_only_gaps':plan.get('experimental_only_gaps',[])}
def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--artifacts',required=True);p.add_argument('--raw-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    r=validate(Path(a.plan).resolve(),Path(a.artifacts).resolve(),Path(a.raw_root).resolve());Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
    if r['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
