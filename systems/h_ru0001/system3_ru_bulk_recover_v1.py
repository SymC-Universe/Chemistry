#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path
import numpy as np
RY_TO_EV=13.605693122994
E_RE=re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text())
def write(p,x): Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def row(root,tag,a,c,ew,er,k):
    d=Path(root)/tag; inp=d/'pw.in'; out=d/'pw.out'
    if not inp.is_file() or not out.is_file(): raise SystemExit(f'MECHANICAL_HOLD: missing preserved case {tag}')
    text=out.read_text(errors='replace'); vals=[float(x)*RY_TO_EV for x in E_RE.findall(text)]
    if 'JOB DONE.' not in text or not vals: raise SystemExit(f'MECHANICAL_HOLD: preserved case incomplete {tag}')
    return {'tag':tag,'a_angstrom':float(a),'c_angstrom':float(c),'ecutwfc_ry':int(ew),'ecutrho_ry':int(er),'kmesh':list(k),'energy_ev':float(vals[-1]),'energy_ev_per_atom':float(vals[-1]/2),'input_sha256':sha(inp),'output_sha256':sha(out)}
def select(rows,tol):
    ref=rows[-1]['energy_ev_per_atom']
    for i,r in enumerate(rows):
        d=abs(r['energy_ev_per_atom']-ref)
        if d<=tol:return i,float(d)
    return len(rows)-1,0.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',required=True); ap.add_argument('--preserved-root',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    p=load(a.protocol); root=Path(a.preserved_root); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if p['status']!='FROZEN_BEFORE_SYSTEM3_PBE_BULK_RESULTS': raise SystemExit('SCIENTIFIC_HOLD: protocol drift')
    if sha(root/'engine_provenance'/'Ru.nc.pbe.z_16.oncvpsp4.sg15.v0.upf')!=p['pseudopotentials']['Ru']['sha256']: raise SystemExit('MECHANICAL_HOLD: Ru pseudo drift in preserved artifact')
    if sha(root/'engine_provenance'/'H.us.pbe.z_1.uspp.gbrv.v1.4.upf')!=p['pseudopotentials']['H']['sha256']: raise SystemExit('MECHANICAL_HOLD: H pseudo drift in preserved artifact')
    a0=float(p['bulk_reference']['a_angstrom']); c0=float(p['bulk_reference']['c_angstrom']); tol=float(p['numerical_gates']['energy_convergence_ev_per_atom']); raw=root/'raw'; fk=tuple(p['cutoff_grid']['fixed_kmesh'])
    cut=[row(raw,f"cut_{e[0]}_{e[1]}",a0,c0,e[0],e[1],fk) for e in p['cutoff_grid']['pairs_ry']]
    ci,cd=select(cut,tol); ew=cut[ci]['ecutwfc_ry']; er=cut[ci]['ecutrho_ry']
    ks=[row(raw,f"k_{k[0]}_{k[1]}_{k[2]}",a0,c0,ew,er,tuple(k)) for k in p['kmesh_grid']]
    ki,kd=select(ks,tol); km=tuple(ks[ki]['kmesh'])
    struct=[]
    for ia,fa in enumerate(p['structure_grid']['scale_factors']):
        for ic,fc in enumerate(p['structure_grid']['scale_factors']):
            struct.append(row(raw,f"struct_a{ia}_c{ic}",a0*float(fa),c0*float(fc),ew,er,km))
    X=np.array([[1,r['a_angstrom'],r['c_angstrom'],r['a_angstrom']**2,r['a_angstrom']*r['c_angstrom'],r['c_angstrom']**2] for r in struct],float); y=np.array([r['energy_ev_per_atom'] for r in struct],float)
    coef=np.linalg.lstsq(X,y,rcond=None)[0]; b,cc,d,e,f=coef[1],coef[2],coef[3],coef[4],coef[5]; H=np.array([[2*d,e],[e,2*f]],float)
    try: stat=np.linalg.solve(H,-np.array([b,cc],float)); eig=np.linalg.eigvalsh(H); solved=True
    except np.linalg.LinAlgError: stat=np.array([math.nan,math.nan]); eig=np.array([-1.,-1.]); solved=False
    sf=p['structure_grid']['scale_factors']; inside=bool(solved and a0*min(sf)<=stat[0]<=a0*max(sf) and c0*min(sf)<=stat[1]<=c0*max(sf)); positive=bool(solved and (eig>0).all()); fit_ok=bool(inside and positive)
    aerr=float(abs(stat[0]-a0)/a0) if fit_ok else None; cerr=float(abs(stat[1]-c0)/c0) if fit_ok else None; lim=float(p['structural_gate']['relative_error_max'])
    structural=bool(fit_ok and aerr<=lim and cerr<=lim); numerical=bool(cd<=tol and kd<=tol); passed=bool(structural and numerical)
    result={'schema':'h-ru0001-pbe-bulk-candidate-result-v0.1','status':'PBE_CANDIDATE_BULK_PASS' if passed else 'PBE_CANDIDATE_BULK_HOLD','system':'H/Ru(0001)','scope':'NON_KINETIC_METHOD_CANDIDATE_AUDIT','selected_numerical_settings':{'ecutwfc_ry':ew,'ecutrho_ry':er,'kmesh':list(km)},'cutoff_delta_to_highest_ev_per_atom':float(cd),'kmesh_delta_to_highest_ev_per_atom':float(kd),'fit':{'a_angstrom':float(stat[0]) if fit_ok else None,'c_angstrom':float(stat[1]) if fit_ok else None,'a_relative_error':aerr,'c_relative_error':cerr,'positive_definite_hessian':positive,'stationary_point_inside_grid':inside},'gates':{'numerical_pass':numerical,'structural_pass':structural,'energy_convergence_ev_per_atom':tol,'structural_relative_error_max':lim},'next_gate':p['decision']['pass_next_gate'] if passed else p['decision']['hold_next_gate'],'provenance':{'protocol_sha256':sha(a.protocol),'source_run_id':33345475633,'source_artifact_id':9742623887,'source_artifact_digest':'sha256:1e06abd3f5563aa24d316f5dac311039154c0f0a8dc67d2bf3b35d589e0a0cf5','recomputed_qe_cases':0,'preserved_completed_scf_count':34,'recovery_reason':'original postprocessor failed only on numpy.bool_ JSON serialization after all SCFs completed','scientific_settings_changed':False,'thresholds_changed':False,'kinetic_inputs_used':False},'raw_summary':{'cutoff':cut,'kmesh':ks,'structure':struct}}
    write(out/'SYSTEM3_PBE_BULK_CANDIDATE_RESULT.json',result); print(json.dumps(result,indent=2,sort_keys=True))
    if not passed: raise SystemExit('SCIENTIFIC_HOLD: PBE bulk candidate failed frozen non-kinetic gate')
if __name__=='__main__': main()
