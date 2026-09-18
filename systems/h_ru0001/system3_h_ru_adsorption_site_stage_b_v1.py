#!/usr/bin/env python3
import argparse, json, math, pathlib, re, subprocess, hashlib, importlib.util

ROOT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("stagea",ROOT/"system3_h_ru_adsorption_site_screen_v1.py")
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

RY_TO_EV=a.RY_TO_EV
RY_BOHR_TO_EV_ANG=a.RY_BOHR_TO_EV_ANG

def sha256(path): return a.sha256(path)

def cell_vectors(aa,cc):
    a1,a2=a.primitive_vectors(aa)
    return (2*a1[0],2*a1[1],0.0),(2*a2[0],2*a2[1],0.0),(0.0,0.0,8.0*cc+15.0)

def relax_input(atoms,aa,cc,ru_pseudo,h_pseudo,restart_mode,prefix,segment_seconds,force_thr):
    A1,A2,A3=cell_vectors(aa,cc)
    frc=force_thr/RY_BOHR_TO_EV_ANG
    lines=[
      "&CONTROL"," calculation='relax',",f" restart_mode='{restart_mode}',",f" prefix='{prefix}',",
      " pseudo_dir='./pseudos',"," outdir='./qe_tmp_relax',"," tstress=.true.,"," tprnfor=.true.,",
      " disk_io='medium',",f" max_seconds={float(segment_seconds):.1f},"," etot_conv_thr=1.0d-4,",
      f" forc_conv_thr={frc:.12e},","/","&SYSTEM"," ibrav=0,",f" nat={len(atoms)},"," ntyp=2,",
      " ecutwfc=70.0,"," ecutrho=280.0,"," input_dft='PBE',"," occupations='smearing',",
      " smearing='mv',"," degauss=0.02,"," nspin=1,","/","&ELECTRONS"," conv_thr=1.0d-10,",
      " mixing_beta=0.3,"," electron_maxstep=200,","/","&IONS"," ion_dynamics='bfgs',","/",
      "ATOMIC_SPECIES",f"Ru 101.07000 {ru_pseudo}",f"H 1.00794 {h_pseudo}","CELL_PARAMETERS angstrom",
      f"{A1[0]:.12f} {A1[1]:.12f} 0.0",f"{A2[0]:.12f} {A2[1]:.12f} 0.0",f"0.0 0.0 {A3[2]:.12f}",
      "ATOMIC_POSITIONS angstrom"
    ]
    for at in atoms:
        fl=at.get("flags",[0,0,0])
        lines.append(f"{at['label']} {at['x']:.12f} {at['y']:.12f} {at['z']:.12f} {fl[0]} {fl[1]} {fl[2]}")
    lines += ["K_POINTS automatic","8 8 1 0 0 0",""]
    return "\n".join(lines)

def scf_input(atoms,aa,cc,ru_pseudo,h_pseudo,restart_mode,prefix,segment_seconds):
    A1,A2,A3=cell_vectors(aa,cc)
    lines=[
      "&CONTROL"," calculation='scf',",f" restart_mode='{restart_mode}',",f" prefix='{prefix}',",
      " pseudo_dir='./pseudos',"," outdir='./qe_tmp_scf',"," tstress=.true.,"," tprnfor=.true.,",
      " disk_io='medium',",f" max_seconds={float(segment_seconds):.1f},","/","&SYSTEM"," ibrav=0,",
      f" nat={len(atoms)},"," ntyp=2,"," ecutwfc=70.0,"," ecutrho=280.0,"," input_dft='PBE',",
      " occupations='smearing',"," smearing='mv',"," degauss=0.02,"," nspin=1,","/","&ELECTRONS",
      " conv_thr=1.0d-10,"," mixing_beta=0.3,"," electron_maxstep=200,","/",
      "ATOMIC_SPECIES",f"Ru 101.07000 {ru_pseudo}",f"H 1.00794 {h_pseudo}","CELL_PARAMETERS angstrom",
      f"{A1[0]:.12f} {A1[1]:.12f} 0.0",f"{A2[0]:.12f} {A2[1]:.12f} 0.0",f"0.0 0.0 {A3[2]:.12f}",
      "ATOMIC_POSITIONS angstrom"
    ]
    for at in atoms:
        lines.append(f"{at['label']} {at['x']:.12f} {at['y']:.12f} {at['z']:.12f}")
    lines += ["K_POINTS automatic","8 8 1 0 0 0",""]
    return "\n".join(lines)

def run_segment(pw,work,name,text,timeout_s):
    inp=work/f"{name}.in"; out=work/f"{name}.out"; inp.write_text(text,encoding="utf-8")
    with inp.open("rb") as fi,out.open("wb") as fo:
        try:
            p=subprocess.run([str(pw)],stdin=fi,stdout=fo,stderr=subprocess.STDOUT,cwd=work,timeout=timeout_s)
            rc=p.returncode
        except subprocess.TimeoutExpired:
            rc=124
    txt=out.read_text(encoding="utf-8",errors="replace") if out.exists() else ""
    return rc,txt,inp,out

def segmented_relax(pw,work,atoms,aa,cc,ru_name,h_name,prefix,sec,nseg,force_thr):
    rec=[]; final=""
    for i in range(1,nseg+1):
        mode="from_scratch" if i==1 else "restart"
        text=relax_input(atoms,aa,cc,ru_name,h_name,mode,prefix,sec,force_thr)
        rc,txt,_,out=run_segment(pw,work,f"relax_segment_{i:02d}",text,sec+900)
        low=txt.lower(); stop="maximum cpu time exceeded" in low
        conv="bfgs converged" in low and "job done." in low and not stop
        rec.append({"segment":i,"restart_mode":mode,"returncode":rc,"clean_max_seconds_stop":stop,
                    "bfgs_converged":conv,"energy_ev":a.last_energy_ev(txt),"output":out.name})
        final=txt
        if conv: return "COMPLETE",rec,final
        if stop and rc==0:
            if not (work/"qe_tmp_relax"/f"{prefix}.save").exists():
                return "MECHANICAL_HOLD",rec,final
            continue
        return "NUMERICAL_HOLD",rec,final
    return "CHECKPOINT_LIMIT_HOLD",rec,final

def segmented_scf(pw,work,atoms,aa,cc,ru_name,h_name,prefix,sec,nseg):
    rec=[]; final=""
    for i in range(1,nseg+1):
        mode="from_scratch" if i==1 else "restart"
        text=scf_input(atoms,aa,cc,ru_name,h_name,mode,prefix,sec)
        rc,txt,_,out=run_segment(pw,work,f"scf_segment_{i:02d}",text,sec+900)
        low=txt.lower(); stop="maximum cpu time exceeded" in low
        conv=("job done." in low and "convergence has been achieved" in low and not stop)
        rec.append({"segment":i,"restart_mode":mode,"returncode":rc,"clean_max_seconds_stop":stop,
                    "scf_converged":conv,"energy_ev":a.last_energy_ev(txt),"output":out.name})
        final=txt
        if conv: return "COMPLETE",rec,final
        if stop and rc==0:
            if not (work/"qe_tmp_scf"/f"{prefix}.save").exists():
                return "MECHANICAL_HOLD",rec,final
            continue
        return "NUMERICAL_HOLD",rec,final
    return "CHECKPOINT_LIMIT_HOLD",rec,final

def nearest_basin(x,y,aa):
    a1,a2=a.primitive_vectors(aa)
    motifs={
      "top":[(0.0,0.0)],
      "bridge":[(0.5,0.0),(0.0,0.5),(0.5,0.5)],
      "fcc_hollow":[(1/3,2/3)],
      "hcp_hollow":[(2/3,1/3)]
    }
    best=(1e9,None)
    for name,fracs in motifs.items():
        for u0,v0 in fracs:
            for i in range(-2,5):
                for j in range(-2,5):
                    u=u0+i; v=v0+j
                    px=u*a1[0]+v*a2[0]; py=u*a1[1]+v*a2[1]
                    d=math.hypot(x-px,y-py)
                    if d<best[0]: best=(d,name)
    return {"basin":best[1] if best[0]<=0.35 else "off_registry","distance_angstrom":best[0]}

def run_stage_b(args):
    protocol=json.load(open(args.protocol)); sel=json.load(open(args.selection)); bulk=json.load(open(args.bulk_adjudication))
    if sel["status"]!="STAGE_A_SELECTION_PASS": raise SystemExit("Stage-A selection is not PASS")
    if args.site not in sel["selected"]: raise SystemExit("Site missing from Stage-A selection")
    aa=float(bulk["structural_fit"]["a_angstrom"]); cc=float(bulk["structural_fit"]["c_angstrom"])
    atoms=[dict(x) for x in sel["selected"][args.site]["final_atoms"]]
    for at in atoms:
        if at["label"]=="H": at["flags"]=[1,1,1]
    work=pathlib.Path(args.out).resolve(); work.mkdir(parents=True,exist_ok=True); (work/"pseudos").mkdir(exist_ok=True)
    ru=pathlib.Path(args.ru_pseudo).resolve(); hp=pathlib.Path(args.h_pseudo).resolve(); pw=pathlib.Path(args.pw).resolve()
    (work/"pseudos"/ru.name).write_bytes(ru.read_bytes()); (work/"pseudos"/hp.name).write_bytes(hp.read_bytes())
    sec=int(protocol["execution"]["segment_seconds"]); nseg=int(protocol["execution"]["max_segments_per_relaxation_case"])
    force_thr=float(protocol["screen_model"]["stage_B_stability_release"]["force_threshold_ev_per_angstrom"])
    rstate,rrec,rtxt=segmented_relax(pw,work,atoms,aa,cc,ru.name,hp.name,f"hru_B_{args.site}",sec,nseg,force_thr)
    if rstate!="COMPLETE":
        result={"schema":"symc-system3-h-ru0001-stage-b-site-result-v0.1","status":"STAGE_B_"+rstate,
                "start_site":args.site,"relax_segments":rrec,"scientific_settings_changed":False,"thresholds_changed":False}
        (work/"STAGE_B_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2)); return
    pts=a.final_positions(rtxt,len(atoms)); maxf=a.last_max_force(rtxt,len(atoms)); re=a.last_energy_ev(rtxt)
    if pts is None or maxf is None:
        raise SystemExit("Completed Stage-B relaxation lacks final geometry/forces")
    final=[]
    for t,p in zip(atoms,pts):
        z=dict(t); z.update({"label":p[0],"x":p[1],"y":p[2],"z":p[3]}); final.append(z)
    sstate,srec,stxt=segmented_scf(pw,work,final,aa,cc,ru.name,hp.name,f"hru_B_scf_{args.site}",sec,nseg)
    se=a.last_energy_ev(stxt) if sstate=="COMPLETE" else None
    repro_delta=abs(re-se) if se is not None else None
    repro_lim=float(protocol["numerical_reproduction"]["absolute_total_energy_difference_max_ev"])
    hs=[x for x in final if x["label"]=="H"]; top=max(hs,key=lambda x:x["z"]); bot=min(hs,key=lambda x:x["z"])
    bt=nearest_basin(top["x"],top["y"],aa); bb=nearest_basin(bot["x"],bot["y"],aa)
    status="STAGE_B_PASS" if (maxf<=force_thr and sstate=="COMPLETE" and repro_delta<=repro_lim) else (
      "ADSORPTION_SITE_REPRODUCTION_HOLD" if sstate=="COMPLETE" else "STAGE_B_"+sstate)
    result={
      "schema":"symc-system3-h-ru0001-stage-b-site-result-v0.1","status":status,"start_site":args.site,
      "relax_energy_ev":re,"fresh_scf_energy_ev":se,"reproduction_delta_ev":repro_delta,
      "reproduction_limit_ev":repro_lim,"max_force_ev_per_angstrom":maxf,"force_threshold_ev_per_angstrom":force_thr,
      "final_basin_top":bt,"final_basin_bottom":bb,"final_atoms":final,
      "relax_segments":rrec,"scf_segments":srec,"pseudo_sha256":{"Ru":sha256(ru),"H":sha256(hp)},"pw_sha256":sha256(pw),
      "scientific_settings_changed":False,"thresholds_changed":False
    }
    (work/"STAGE_B_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

def adjudicate(args):
    protocol=json.load(open(args.protocol)); rows=[]
    for p in pathlib.Path(args.cases_root).rglob("STAGE_B_RESULT.json"):
        try: rows.append(json.load(open(p)))
        except Exception: pass
    sites=["top","bridge","fcc_hollow","hcp_hollow"]
    by={r.get("start_site"):r for r in rows}
    missing=[s for s in sites if s not in by]
    if missing:
        out={"schema":"symc-system3-h-ru0001-site-screen-adjudication-v0.1","status":"ADSORPTION_SITE_NUMERICAL_HOLD",
             "reason":"missing_stage_b_cases","missing":missing}; pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2)); raise SystemExit(2)
    bad={s:by[s]["status"] for s in sites if by[s].get("status")!="STAGE_B_PASS"}
    if bad:
        out={"schema":"symc-system3-h-ru0001-site-screen-adjudication-v0.1","status":"ADSORPTION_SITE_NUMERICAL_HOLD",
             "reason":"nonpassing_stage_b_cases","cases":bad}; pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n"); print(json.dumps(out,indent=2)); raise SystemExit(2)
    minima={}
    migrations={}
    for s,r in by.items():
        top=r["final_basin_top"]["basin"]; bot=r["final_basin_bottom"]["basin"]
        basin=top if top==bot else f"asymmetric:{top}|{bot}"
        migrations[s]={"final_basin":basin,"migrated":basin!=s}
        key=basin if basin!="off_registry" else f"off_registry_from_{s}"
        if key not in minima or r["fresh_scf_energy_ev"]<minima[key]["energy_ev"]:
            minima[key]={"energy_ev":r["fresh_scf_energy_ev"],"source_start_site":s,
                         "reproduction_delta_ev":r["reproduction_delta_ev"],"final_atoms":r["final_atoms"]}
    ranked=sorted([{"basin":k,**v} for k,v in minima.items()],key=lambda x:x["energy_ev"])
    resolution=float(protocol["numerical_reproduction"]["ordering_resolution_ev"])
    gap=(ranked[1]["energy_ev"]-ranked[0]["energy_ev"]) if len(ranked)>1 else None
    unresolved=(gap is not None and gap<=resolution)
    status="ADSORPTION_SITE_ORDERING_UNRESOLVED" if unresolved else "ADSORPTION_SITE_SCREEN_PASS"
    out={"schema":"symc-system3-h-ru0001-site-screen-adjudication-v0.1","status":status,
         "ranked_retained_minima":ranked,"migrations":migrations,"lowest_gap_ev":gap,
         "ordering_resolution_ev":resolution,"next_gate":protocol["pass_next_gate"] if not unresolved else None,
         "automatic_path_or_rate_progression":False}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    if unresolved: raise SystemExit(3)

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    r=sp.add_parser("stage-b")
    for flag in ["protocol","selection","bulk-adjudication","pw","ru-pseudo","h-pseudo","site","out"]:
        r.add_argument("--"+flag,required=True)
    r.set_defaults(func=run_stage_b)
    d=sp.add_parser("adjudicate")
    d.add_argument("--protocol",required=True); d.add_argument("--cases-root",required=True); d.add_argument("--out",required=True); d.set_defaults(func=adjudicate)
    args=ap.parse_args(); args.func(args)

if __name__=="__main__":
    main()
