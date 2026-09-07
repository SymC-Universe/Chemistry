#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, os, re, subprocess, time
from pathlib import Path
import numpy as np
RY_TO_EV=13.605693122994
E_RE=re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")

def sha256(p: Path)->str:
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load(p): return json.loads(Path(p).read_text())
def write(p,obj): Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

def qe_input(a,c,ecutwfc,ecutrho,kx,ky,kz,pseudo,outdir,prefix):
    return f"""&CONTROL
 calculation='scf',
 prefix='{prefix}',
 pseudo_dir='{pseudo}',
 outdir='{outdir}',
 tprnfor=.true.,
 tstress=.true.,
 verbosity='high',
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=1,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 occupations='smearing',
 smearing='mv',
 degauss=0.02,
/
&ELECTRONS
 conv_thr=1.0d-10,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
Ru 101.07 Ru.nc.pbe.z_16.oncvpsp4.sg15.v0.upf
CELL_PARAMETERS angstrom
{a:.12f} 0.0 0.0
{-0.5*a:.12f} {math.sqrt(3)*0.5*a:.12f} 0.0
0.0 0.0 {c:.12f}
ATOMIC_POSITIONS crystal
Ru 0.0 0.0 0.0
Ru 0.666666666666667 0.333333333333333 0.5
K_POINTS automatic
{kx} {ky} {kz} 0 0 0
"""

def run_case(root,pw,pseudo,a,c,ecutwfc,ecutrho,kmesh,timeout_s,tag):
    d=root/tag; d.mkdir(parents=True,exist_ok=True); outdir=d/'tmp'; outdir.mkdir(exist_ok=True)
    inp=d/'pw.in'; out=d/'pw.out'; inp.write_text(qe_input(a,c,ecutwfc,ecutrho,*kmesh,pseudo,outdir,tag))
    env=dict(os.environ); env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    start=time.time(); timed=False
    with inp.open('rb') as fi, out.open('wb') as fo:
        p=subprocess.Popen([str(pw)],stdin=fi,stdout=fo,stderr=subprocess.STDOUT,env=env)
        try: rc=p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed=True; p.terminate()
            try: rc=p.wait(timeout=30)
            except subprocess.TimeoutExpired: p.kill(); rc=p.wait(timeout=10)
    text=out.read_text(errors='replace'); vals=[float(x)*RY_TO_EV for x in E_RE.findall(text)]
    if timed or rc!=0 or 'JOB DONE.' not in text or not vals:
        raise RuntimeError(f'MECHANICAL_HOLD {tag}: timeout={timed} rc={rc} job_done={"JOB DONE." in text} energies={len(vals)}')
    return {'tag':tag,'a_angstrom':a,'c_angstrom':c,'ecutwfc_ry':ecutwfc,'ecutrho_ry':ecutrho,'kmesh':list(kmesh),'energy_ev':vals[-1],'energy_ev_per_atom':vals[-1]/2,'elapsed_s':time.time()-start,'input_sha256':sha256(inp),'output_sha256':sha256(out)}

def select_lowest(rows,tol):
    ref=rows[-1]['energy_ev_per_atom']
    for i,r in enumerate(rows):
        if abs(r['energy_ev_per_atom']-ref)<=tol: return i,abs(r['energy_ev_per_atom']-ref)
    return len(rows)-1,0.0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',required=True); ap.add_argument('--pw',required=True); ap.add_argument('--pseudo-dir',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    pr=load(args.protocol); outroot=Path(args.out); outroot.mkdir(parents=True,exist_ok=True); pw=Path(args.pw).resolve(); pseudo=Path(args.pseudo_dir).resolve()
    if pr['status']!='FROZEN_BEFORE_SYSTEM3_PBE_BULK_RESULTS': raise SystemExit('SCIENTIFIC_HOLD: protocol not frozen')
    if sha256(pw)!=pr['provenance']['pw_x_sha256']: raise SystemExit('MECHANICAL_HOLD: pw hash mismatch')
    for el in ('Ru','H'):
        p=pseudo/pr['pseudopotentials'][el]['filename']
        if not p.is_file() or sha256(p)!=pr['pseudopotentials'][el]['sha256']: raise SystemExit(f'MECHANICAL_HOLD: {el} pseudo mismatch')
    ref=pr['bulk_reference']; a0=float(ref['a_angstrom']); c0=float(ref['c_angstrom']); tol=float(pr['numerical_gates']['energy_convergence_ev_per_atom']); timeout=int(pr['execution']['per_scf_timeout_seconds'])
    calcroot=outroot/'raw'; calcroot.mkdir(exist_ok=True)
    cutoff_rows=[]; fixedk=tuple(pr['cutoff_grid']['fixed_kmesh'])
    for e in pr['cutoff_grid']['pairs_ry']:
        cutoff_rows.append(run_case(calcroot,pw,pseudo,a0,c0,int(e[0]),int(e[1]),fixedk,timeout,f"cut_{e[0]}_{e[1]}"))
    ci,cd=select_lowest(cutoff_rows,tol); ecw=cutoff_rows[ci]['ecutwfc_ry']; ecr=cutoff_rows[ci]['ecutrho_ry']
    k_rows=[]
    for k in pr['kmesh_grid']:
        kt=tuple(k); k_rows.append(run_case(calcroot,pw,pseudo,a0,c0,ecw,ecr,kt,timeout,f"k_{k[0]}_{k[1]}_{k[2]}"))
    ki,kd=select_lowest(k_rows,tol); km=tuple(k_rows[ki]['kmesh'])
    struct=[]
    for ia,fa in enumerate(pr['structure_grid']['scale_factors']):
        for ic,fc in enumerate(pr['structure_grid']['scale_factors']):
            a=a0*float(fa); c=c0*float(fc)
            struct.append(run_case(calcroot,pw,pseudo,a,c,ecw,ecr,km,timeout,f"struct_a{ia}_c{ic}"))
    X=np.array([[1,r['a_angstrom'],r['c_angstrom'],r['a_angstrom']**2,r['a_angstrom']*r['c_angstrom'],r['c_angstrom']**2] for r in struct],float)
    y=np.array([r['energy_ev_per_atom'] for r in struct],float)
    coef=np.linalg.lstsq(X,y,rcond=None)[0]
    b,cc,d,e,f=coef[1],coef[2],coef[3],coef[4],coef[5]
    H=np.array([[2*d,e],[e,2*f]],float); rhs=-np.array([b,cc],float)
    fit_ok=True
    try: stat=np.linalg.solve(H,rhs)
    except np.linalg.LinAlgError: fit_ok=False; stat=np.array([math.nan,math.nan])
    eig=np.linalg.eigvalsh(H) if fit_ok else np.array([-1,-1])
    amin=a0*min(pr['structure_grid']['scale_factors']); amax=a0*max(pr['structure_grid']['scale_factors']); cmin=c0*min(pr['structure_grid']['scale_factors']); cmax=c0*max(pr['structure_grid']['scale_factors'])
    fit_ok=fit_ok and bool((eig>0).all()) and amin<=stat[0]<=amax and cmin<=stat[1]<=cmax
    aerr=abs(stat[0]-a0)/a0 if fit_ok else math.inf; cerr=abs(stat[1]-c0)/c0 if fit_ok else math.inf
    structural_pass=fit_ok and aerr<=pr['structural_gate']['relative_error_max'] and cerr<=pr['structural_gate']['relative_error_max']
    numerical_pass=cd<=tol and kd<=tol
    passed=numerical_pass and structural_pass
    result={'schema':'h-ru0001-pbe-bulk-candidate-result-v0.1','status':'PBE_CANDIDATE_BULK_PASS' if passed else 'PBE_CANDIDATE_BULK_HOLD','system':'H/Ru(0001)','scope':'NON_KINETIC_METHOD_CANDIDATE_AUDIT','selected_numerical_settings':{'ecutwfc_ry':ecw,'ecutrho_ry':ecr,'kmesh':list(km)},'cutoff_delta_to_highest_ev_per_atom':cd,'kmesh_delta_to_highest_ev_per_atom':kd,'fit':{'a_angstrom':float(stat[0]) if fit_ok else None,'c_angstrom':float(stat[1]) if fit_ok else None,'a_relative_error':aerr if fit_ok else None,'c_relative_error':cerr if fit_ok else None,'positive_definite_hessian':bool((eig>0).all()) if fit_ok else False,'stationary_point_inside_grid':bool(fit_ok)},'gates':{'numerical_pass':numerical_pass,'structural_pass':structural_pass,'energy_convergence_ev_per_atom':tol,'structural_relative_error_max':pr['structural_gate']['relative_error_max']},'next_gate':pr['decision']['pass_next_gate'] if passed else pr['decision']['hold_next_gate'],'provenance':{'protocol_sha256':sha256(Path(args.protocol)),'pw_x_sha256':sha256(pw),'ru_pseudo_sha256':sha256(pseudo/pr['pseudopotentials']['Ru']['filename']),'h_pseudo_sha256':sha256(pseudo/pr['pseudopotentials']['H']['filename']),'scientific_settings_changed':False,'kinetic_inputs_used':False,'published_barrier_rate_or_site_energy_used_for_selection':False},'compute':{'total_scf_count':len(cutoff_rows)+len(k_rows)+len(struct),'measured_qe_wall_seconds':sum(r['elapsed_s'] for r in cutoff_rows+k_rows+struct)},'raw':{'cutoff':cutoff_rows,'kmesh':k_rows,'structure':struct}}
    write(outroot/'SYSTEM3_PBE_BULK_CANDIDATE_RESULT.json',result); print(json.dumps(result,indent=2,sort_keys=True))
    if not passed: raise SystemExit('SCIENTIFIC_HOLD: PBE bulk candidate failed frozen non-kinetic gate')
if __name__=='__main__': main()
