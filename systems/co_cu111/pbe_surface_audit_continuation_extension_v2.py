#!/usr/bin/env python3
"""Second fail-closed continuation extension for the frozen CO/Cu(111) L13 audit."""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
from typing import Any

SCHEMA="co-cu111-pbe-surface-audit-continuation-extension-v0.2"
STATUS="FROZEN_MECHANICAL_CONTINUATION_EXTENSION_AFTER_SEGMENT24_EXHAUSTION"
SEG_SCHEMA="co-cu111-pbe-surface-audit-continuation-extension-segment-v0.2"
PARENT_SEG_SCHEMA="co-cu111-pbe-surface-audit-continuation-extension-segment-v0.1"

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load_json(path:Path)->dict[str,Any]:
    d=json.loads(path.read_text())
    if not isinstance(d,dict): raise SystemExit(f"MECHANICAL_HOLD: JSON root must be object: {path}")
    return d

def write_json(path:Path,d:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')

def find_one(root:Path,name:str)->Path:
    xs=[x for x in root.rglob(name) if x.is_file()]
    if len(xs)!=1: raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name} under {root}, found {len(xs)}")
    return xs[0]

def import_ext1():
    here=Path(__file__).resolve().parent
    if str(here) not in sys.path: sys.path.insert(0,str(here))
    import pbe_surface_audit_continuation_extension_v1 as ext1
    return ext1

def protocol(path:Path)->dict[str,Any]:
    p=load_json(path)
    if p.get('schema')!=SCHEMA or p.get('status')!=STATUS: raise SystemExit('MECHANICAL_HOLD: wrong or unfrozen extension-v2 protocol')
    if p.get('scientific_scope')!='NO_SCIENTIFIC_CONFIGURATION_CHANGE': raise SystemExit('MECHANICAL_HOLD: scientific scope changed')
    ex=p['execution']
    if int(ex.get('maximum_new_continuation_segments',-1))!=6: raise SystemExit('MECHANICAL_HOLD: extension-v2 bound changed')
    if ex.get('logical_segment_numbers')!=list(range(25,31)): raise SystemExit('MECHANICAL_HOLD: logical segment sequence changed')
    if int(p['selection'].get('required_selected_mpi_ranks',-1))!=1 or p['selection'].get('required_execution_mode')!='DIRECT_ONE_RANK': raise SystemExit('MECHANICAL_HOLD: frozen execution mode changed')
    s=p['unchanged_science']; frozen={'layers':13,'vacuum_angstrom':28.0,'kmesh':24,'ecutwfc_ry':90,'ecutrho_ry':900,'force_gate_ev_per_angstrom':0.02,'independent_scf_reproduction_gate_ev':0.001,'surface_excess_convergence_max_ev_per_surface_atom':0.001}
    for k,v in frozen.items():
        if s.get(k)!=v: raise SystemExit(f'MECHANICAL_HOLD: frozen science changed: {k}')
    if s.get('input_dft')!='PBE' or s.get('esm_bc')!='bc1': raise SystemExit('MECHANICAL_HOLD: frozen method changed')
    pr=p['provenance']
    if pr.get('scientific_settings_changed') is not False or pr.get('kinetic_inputs_used') is not False: raise SystemExit('MECHANICAL_HOLD: provenance is not clean')
    return p

def runtime_context(args,p):
    ext1=import_ext1()
    e1pp=Path(p['frozen_extension_v1']['protocol_path']).resolve(); e1rp=Path(p['frozen_extension_v1']['runner_path']).resolve()
    if sha256(e1pp)!=p['frozen_extension_v1']['protocol_sha256']: raise SystemExit('MECHANICAL_HOLD: extension-v1 protocol hash mismatch')
    if sha256(e1rp)!=p['frozen_extension_v1']['runner_sha256']: raise SystemExit('MECHANICAL_HOLD: extension-v1 runner hash mismatch')
    old,oldp,base,relay,surface,bundle,sel=ext1.parent_context(args,p)
    return ext1,old,oldp,base,relay,surface,bundle,sel

def verify_parent_segment24(root:Path,p:dict[str,Any]):
    q=find_one(root,'CONTINUATION_EXTENSION_SEGMENT.json')
    e=p['parent_run']
    if sha256(q)!=e['segment24_record_sha256']: raise SystemExit('MECHANICAL_HOLD: parent segment-24 record hash mismatch')
    d=load_json(q)
    checks={'schema':e['required_schema'],'status':e['required_status'],'segment':e['required_segment'],'logical_segment':e['required_logical_segment'],'execution_mode':e['required_execution_mode'],'mpi_ranks':e['required_mpi_ranks'],'pw_sha256':e['pw_sha256'],'extension_protocol_sha256':e['extension_v1_protocol_sha256'],'rank_selection_sha256':e['rank_selection_sha256']}
    for k,v in checks.items():
        if d.get(k)!=v: raise SystemExit(f'MECHANICAL_HOLD: parent segment-24 mismatch: {k}')
    if abs(float(d['latest_authoritative_max_movable_force_ev_per_angstrom'])-float(e['latest_authoritative_max_movable_force_ev_per_angstrom']))>1e-12: raise SystemExit('MECHANICAL_HOLD: segment-24 force drift')
    if abs(float(d['energy_ev'])-float(e['energy_ev']))>1e-10: raise SystemExit('MECHANICAL_HOLD: segment-24 energy drift')
    rh=d.get('raw_hashes',{})
    if rh.get('relax_input_sha256')!=e['raw_relax_input_sha256'] or rh.get('relax_output_sha256')!=e['raw_relax_output_sha256']: raise SystemExit('MECHANICAL_HOLD: segment-24 raw hash drift')
    if d.get('scientific_settings_changed') is not False or d.get('kinetic_inputs_used') is not False: raise SystemExit('MECHANICAL_HOLD: parent provenance mismatch')
    if not d.get('next_trial_atoms'): raise SystemExit('MECHANICAL_HOLD: segment-24 lacks next BFGS trial')
    disp=float(d.get('source_evidence',{}).get('next_trial_displacement_angstrom',math.nan))
    if not math.isfinite(disp) or abs(disp-float(e['next_trial_displacement_angstrom']))>1e-12: raise SystemExit('MECHANICAL_HOLD: segment-24 proposal displacement drift')
    return d,q

def load_prior(root:Path,p:dict[str,Any],segment:int):
    if segment==1:
        d,q=verify_parent_segment24(root,p)
        return d['next_trial_atoms'],{'source':'parent_extension_v1_logical_segment_24','source_record_sha256':sha256(q),'source_raw_output_sha256':d['raw_hashes']['relax_output_sha256']},False
    q=find_one(root,'CONTINUATION_EXTENSION_V2_SEGMENT.json'); d=load_json(q)
    if d.get('schema')!=SEG_SCHEMA or int(d.get('segment',-1))!=segment-1: raise SystemExit('MECHANICAL_HOLD: prior extension-v2 segment mismatch')
    if d.get('status')=='RELAX_COMPLETE': return d['final_atoms'],{'source':'prior_relax_complete','source_record_sha256':sha256(q)},True
    if d.get('status')!='CONTINUE' or not d.get('next_trial_atoms'): raise SystemExit('MECHANICAL_HOLD: invalid prior extension-v2 state')
    return d['next_trial_atoms'],{'source':'prior_next_trial','source_record_sha256':sha256(q)},False

def command_self_test(args):
    protocol(Path(args.protocol).resolve()); print('CONTINUATION_EXTENSION_V2_SELF_TEST_PASS'); print('DIRECT_ONE_RANK_FROZEN=true'); print('SCIENTIFIC_SETTINGS_CHANGED=false'); print('KINETIC_INPUTS_USED=false')

def command_verify_parent(args):
    p=protocol(Path(args.protocol).resolve()); d,q=verify_parent_segment24(Path(args.parent_root).resolve(),p)
    print(json.dumps({'status':'PARENT_SEGMENT24_VERIFIED','record_sha256':sha256(q),'latest_force_ev_per_angstrom':d['latest_authoritative_max_movable_force_ev_per_angstrom'],'next_trial_displacement_angstrom':d['source_evidence']['next_trial_displacement_angstrom']},sort_keys=True))

def command_continue(args):
    pp=Path(args.protocol).resolve(); p=protocol(pp); ext1,old,oldp,base,relay,surface,bundle,sel=runtime_context(args,p)
    segment=int(args.segment)
    if segment<1 or segment>6: raise SystemExit('MECHANICAL_HOLD: extension-v2 segment outside frozen bound')
    seed,evidence,already=load_prior(Path(args.prior_root).resolve(),p,segment)
    cell,template=base.clean_geometry(float(surface['inherited_stage_a_settings']['bulk_lattice_constant_angstrom']),13,28.0); seed=old.apply_template(seed,template)
    root=Path(args.out).resolve(); root.mkdir(parents=True,exist_ok=True)
    if already:
        src=load_json(find_one(Path(args.prior_root).resolve(),'CONTINUATION_EXTENSION_V2_SEGMENT.json')); carried=dict(src); carried.update({'segment':segment,'logical_segment':24+segment,'carried_forward_without_recomputation':True,'source_evidence':evidence})
        write_json(root/'CONTINUATION_EXTENSION_V2_SEGMENT.json',carried); base.stage_manifest(root,[root/'CONTINUATION_EXTENSION_V2_SEGMENT.json']); print(json.dumps(carried,indent=2,sort_keys=True)); return
    rd=root/'relax'; rd.mkdir(exist_ok=True); tmp=rd/'tmp'; tmp.mkdir(exist_ok=True); inp=rd/'clean_relax.in'; out=rd/'clean_relax.out'
    inp.write_text(base.qe_input(calculation='relax',prefix='co_cu111_clean',cell=cell,atoms=seed,kmesh=24,protocol=surface,bundle=bundle,pseudo_dir=Path(args.pseudo_dir).resolve(),outdir=tmp))
    result=old.run_pw(Path(args.pw).resolve(),inp,out,1,int(args.runtime_cap_s))
    if result['returncode']!=0 and not result['timed_out_by_wrapper']: raise SystemExit(f"MECHANICAL_HOLD: direct one-rank pw.x failed, rc={result['returncode']}")
    blocks=old.authoritative_force_blocks(result['text'],13); latest=old.max_movable_force_ev_a(blocks[-1],seed) if blocks else None
    complete=bool(result['job_done'] and result['bfgs_finished'] and result['energy_ev'] is not None); final_atoms=None; next_trial=None
    if complete:
        final_atoms=base.parse_positions(result['text'],13,seed)
        if final_atoms is None or not blocks: raise SystemExit('MECHANICAL_HOLD: completed relaxation lacks final geometry/forces')
        final_force=old.max_movable_force_ev_a(blocks[-1],final_atoms)
        if final_force>float(p['unchanged_science']['force_gate_ev_per_angstrom']): raise SystemExit('SCIENTIFIC_HOLD: QE completed but corrected movable-force gate failed')
        latest=final_force
    else:
        proposal=relay.last_bfgs_proposed_trial(result['text'],13,seed)
        if proposal is None: raise SystemExit('MECHANICAL_HOLD: bounded extension-v2 emitted no admissible next BFGS trial')
        next_trial,pe=proposal; next_trial=old.apply_template(next_trial,template); delta=relay.max_displacement_angstrom(seed,next_trial)
        if delta<=1e-10: raise SystemExit('MECHANICAL_HOLD: extension-v2 would repeat the same geometry')
        evidence['next_trial_parent_evidence']=pe; evidence['next_trial_displacement_angstrom']=delta
    row={'schema':SEG_SCHEMA,'status':'RELAX_COMPLETE' if complete else 'CONTINUE','segment':segment,'logical_segment':24+segment,'case_id':'L13-V28-K24-audit','mpi_ranks':1,'execution_mode':'DIRECT_ONE_RANK','runner_label':p['execution']['runner_label'],'thread_caps':p['execution']['thread_caps'],'timed_out_by_wrapper':result['timed_out_by_wrapper'],'pw_returncode':result['returncode'],'job_done':result['job_done'],'bfgs_finished':result['bfgs_finished'],'energy_ev':result['energy_ev'],'latest_authoritative_max_movable_force_ev_per_angstrom':latest,'input_atoms':seed,'final_atoms':final_atoms,'next_trial_atoms':next_trial,'source_evidence':evidence,'scientific_settings_changed':False,'parallelization_changed':False,'kinetic_inputs_used':False,'raw_hashes':{'relax_input_sha256':sha256(inp),'relax_output_sha256':sha256(out)},'extension_v2_protocol_sha256':sha256(pp),'parent_extension_v1_protocol_sha256':p['frozen_extension_v1']['protocol_sha256'],'rank_selection_sha256':sha256(Path(args.selection).resolve()),'surface_protocol_sha256':oldp['frozen_sources']['surface_protocol']['sha256'],'pw_sha256':sha256(Path(args.pw).resolve()),'elapsed_s':result['elapsed_s']}
    base.cleanup_tmp(tmp); write_json(root/'CONTINUATION_EXTENSION_V2_SEGMENT.json',row); base.stage_manifest(root,[root/'CONTINUATION_EXTENSION_V2_SEGMENT.json']); print(json.dumps(row,indent=2,sort_keys=True))

def command_reproduce(args):
    pp=Path(args.protocol).resolve(); p=protocol(pp); ext1,old,oldp,base,relay,surface,bundle,sel=runtime_context(args,p)
    seg_path=find_one(Path(args.prior_root).resolve(),'CONTINUATION_EXTENSION_V2_SEGMENT.json'); seg=load_json(seg_path)
    if seg.get('status')!='RELAX_COMPLETE' or not seg.get('final_atoms'): raise SystemExit('MECHANICAL_INCOMPLETE: L13 audit relaxation still incomplete after six extension-v2 segments')
    if int(seg.get('mpi_ranks',-1))!=1 or seg.get('execution_mode')!='DIRECT_ONE_RANK': raise SystemExit('MECHANICAL_HOLD: final extension-v2 execution mode drift')
    atoms=seg['final_atoms']; fixed=json.loads(json.dumps(atoms))
    for a in fixed: a['flags']=[0,0,0]
    cell,_=base.clean_geometry(float(surface['inherited_stage_a_settings']['bulk_lattice_constant_angstrom']),13,28.0)
    root=Path(args.out).resolve(); root.mkdir(parents=True,exist_ok=True); rd=root/'reproduce'; rd.mkdir(exist_ok=True); tmp=rd/'tmp'; tmp.mkdir(exist_ok=True); inp=rd/'clean_reproduce.in'; out=rd/'clean_reproduce.out'
    inp.write_text(base.qe_input(calculation='scf',prefix='co_cu111_clean_repro',cell=cell,atoms=fixed,kmesh=24,protocol=surface,bundle=bundle,pseudo_dir=Path(args.pseudo_dir).resolve(),outdir=tmp))
    result=old.run_pw(Path(args.pw).resolve(),inp,out,1,int(args.runtime_cap_s))
    if result['returncode']!=0 or not result['job_done'] or result['energy_ev'] is None: raise SystemExit('MECHANICAL_HOLD: independent direct-one-rank audit SCF did not complete')
    delta=abs(float(seg['energy_ev'])-float(result['energy_ev'])); force=float(seg['latest_authoritative_max_movable_force_ev_per_angstrom']); fg=float(p['unchanged_science']['force_gate_ev_per_angstrom']); rg=float(p['unchanged_science']['independent_scf_reproduction_gate_ev']); passed=force<=fg and delta<=rg
    bulk_e0=float(surface['inherited_stage_a_settings']['bulk_e0_ev_per_atom']); excess=(float(result['energy_ev'])-13.0*bulk_e0)/2.0
    summary={'schema':'co-cu111-pbe-clean-surface-case-v0.1','status':'COMPLETE' if passed else 'HOLD','case_id':'L13-V28-K24-audit','role':'audit','layers':13,'vacuum_angstrom':28.0,'kmesh':24,'cell_angstrom':cell,'final_atoms':atoms,'layer_z_angstrom':[float(a['position_angstrom'][2]) for a in atoms],'relax_energy_ev':seg['energy_ev'],'fixed_geometry_scf_energy_ev':result['energy_ev'],'energy_reproduction_delta_ev':delta,'max_movable_force_ev_per_angstrom':force,'mechanical_pass':passed,'surface_excess_ev_per_surface_atom':excess,'provenance':{'protocol_sha256':oldp['frozen_sources']['surface_protocol']['sha256'],'stage_a_result_sha256':oldp['frozen_sources']['stage_a_result_sha256'],'pw_sha256':oldp['frozen_sources']['pw_x_sha256'],'bundle_sha256':sha256(Path(args.bundle).resolve()),'stage_a_scientific_settings_modified':False,'kinetic_inputs_used':False,'rank_selection_sha256':sha256(Path(args.selection).resolve()),'continuation_extension_v2_protocol_sha256':sha256(pp),'execution_resource_changed':False,'scientific_settings_changed':False,'authoritative_total_force_parser':True},'raw_hashes':{'relax_segment_record_sha256':sha256(seg_path),'reproduce_input_sha256':sha256(inp),'reproduce_output_sha256':sha256(out)}}
    base.cleanup_tmp(tmp); write_json(root/'summary.json',summary); base.stage_manifest(root,[root/'summary.json']); print(json.dumps(summary,indent=2,sort_keys=True))
    if not passed: raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('self-test'); s.add_argument('--protocol',required=True); s.set_defaults(func=command_self_test)
    s=sub.add_parser('verify-parent'); s.add_argument('--protocol',required=True); s.add_argument('--parent-root',required=True); s.set_defaults(func=command_verify_parent)
    for name,func in (('continue',command_continue),('reproduce',command_reproduce)):
        s=sub.add_parser(name); s.add_argument('--protocol',required=True); s.add_argument('--surface-protocol',required=True); s.add_argument('--stage-a-result',required=True); s.add_argument('--bundle',required=True); s.add_argument('--pseudo-dir',required=True); s.add_argument('--pw',required=True); s.add_argument('--selection',required=True); s.add_argument('--prior-root',required=True); s.add_argument('--runtime-cap-s',type=int,required=True); s.add_argument('--out',required=True)
        if name=='continue': s.add_argument('--segment',type=int,required=True)
        s.set_defaults(func=func)
    args=ap.parse_args(); args.func(args)
if __name__=='__main__': main()
