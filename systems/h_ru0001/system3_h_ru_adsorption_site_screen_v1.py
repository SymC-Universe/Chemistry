#!/usr/bin/env python3
import argparse, json, math, pathlib, re, subprocess, hashlib

RY_TO_EV=13.605693122994
BOHR_TO_ANG=0.529177210903
RY_BOHR_TO_EV_ANG=RY_TO_EV/BOHR_TO_ANG

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def vadd(a,b): return (a[0]+b[0],a[1]+b[1])
def vscale(s,a): return (s*a[0],s*a[1])

def primitive_vectors(a):
    return (a,0.0),(-0.5*a,math.sqrt(3.0)*0.5*a)

def site_xy(a,site):
    a1,a2=primitive_vectors(a)
    origin=vadd(a1,a2)
    offs={
      "top":(0.0,0.0),
      "bridge":vscale(0.5,a1),
      "fcc_hollow":vadd(vscale(1.0/3.0,a1),vscale(2.0/3.0,a2)),
      "hcp_hollow":vadd(vscale(2.0/3.0,a1),vscale(1.0/3.0,a2)),
    }
    return vadd(origin,offs[site])

def build_stage_a_atoms(clean_coords,a,site,height):
    a1,a2=primitive_vectors(a)
    translations=[(0.0,0.0),a1,a2,vadd(a1,a2)]
    atoms=[]
    for layer,row in enumerate(clean_coords):
        assert row[0]=="Ru"
        for t in translations:
            atoms.append({
              "label":"Ru","x":row[1]+t[0],"y":row[2]+t[1],"z":row[3],
              "flags":[0,0,1] if layer in (0,1,15,16) else [0,0,0],
              "layer_index":layer
            })
    x,y=site_xy(a,site)
    zmin=min(r[3] for r in clean_coords); zmax=max(r[3] for r in clean_coords)
    atoms.append({"label":"H","x":x,"y":y,"z":zmax+height,"flags":[0,0,1],"side":"top"})
    atoms.append({"label":"H","x":x,"y":y,"z":zmin-height,"flags":[0,0,1],"side":"bottom"})
    return atoms

def qe_input(atoms,a,c,site,height,ru_pseudo,h_pseudo,restart_mode,prefix,segment_seconds,force_thr_ev_a):
    a1,a2=primitive_vectors(a)
    A1=(2*a1[0],2*a1[1],0.0); A2=(2*a2[0],2*a2[1],0.0)
    cell_z=8.0*c+15.0
    frc=force_thr_ev_a/RY_BOHR_TO_EV_ANG
    lines=[
      "&CONTROL"," calculation='relax',",f" restart_mode='{restart_mode}',",
      f" prefix='{prefix}',"," pseudo_dir='./pseudos',"," outdir='./qe_tmp',",
      " tstress=.true.,"," tprnfor=.true.,"," disk_io='medium',",
      f" max_seconds={float(segment_seconds):.1f},"," etot_conv_thr=1.0d-4,",
      f" forc_conv_thr={frc:.12e},","/","&SYSTEM"," ibrav=0,",f" nat={len(atoms)},"," ntyp=2,",
      " ecutwfc=70.0,"," ecutrho=280.0,"," input_dft='PBE',"," occupations='smearing',",
      " smearing='mv',"," degauss=0.02,"," nspin=1,","/","&ELECTRONS"," conv_thr=1.0d-10,",
      " mixing_beta=0.3,"," electron_maxstep=200,","/","&IONS"," ion_dynamics='bfgs',","/",
      "ATOMIC_SPECIES",f"Ru 101.07000 {ru_pseudo}",f"H 1.00794 {h_pseudo}",
      "CELL_PARAMETERS angstrom",
      f"{A1[0]:.12f} {A1[1]:.12f} 0.0",
      f"{A2[0]:.12f} {A2[1]:.12f} 0.0",
      f"0.0 0.0 {cell_z:.12f}",
      "ATOMIC_POSITIONS angstrom"
    ]
    for at in atoms:
        lines.append(f"{at['label']} {at['x']:.12f} {at['y']:.12f} {at['z']:.12f} {at['flags'][0]} {at['flags'][1]} {at['flags'][2]}")
    lines += ["K_POINTS automatic","8 8 1 0 0 0",""]
    return "\n".join(lines)

def run_segment(pw,work,idx,text,timeout_s):
    inp=work/f"segment_{idx:02d}.in"; out=work/f"segment_{idx:02d}.out"
    inp.write_text(text,encoding="utf-8")
    with inp.open("rb") as fi,out.open("wb") as fo:
        try:
            p=subprocess.run([str(pw)],stdin=fi,stdout=fo,stderr=subprocess.STDOUT,cwd=work,timeout=timeout_s)
            rc=p.returncode
        except subprocess.TimeoutExpired:
            rc=124
    txt=out.read_text(encoding="utf-8",errors="replace") if out.exists() else ""
    return rc,txt,inp,out

def last_energy_ev(txt):
    vals=re.findall(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry",txt)
    return float(vals[-1])*RY_TO_EV if vals else None

def final_positions(txt,nat):
    idx=txt.rfind("Begin final coordinates")
    chunk=txt[idx:] if idx>=0 else txt
    ms=list(re.finditer(r"ATOMIC_POSITIONS\s*\(angstrom\)\s*\n",chunk))
    if not ms: return None
    pts=[]
    for line in chunk[ms[-1].end():].splitlines():
        s=line.split()
        if len(s)<4 or s[0] not in ("Ru","H"):
            if pts: break
            continue
        pts.append((s[0],float(s[1]),float(s[2]),float(s[3])))
        if len(pts)==nat: break
    return pts if len(pts)==nat else None

def last_max_force(txt,nat):
    vals=re.findall(r"force\s*=\s*([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)",txt)
    if len(vals)<nat: return None
    return max(math.sqrt(sum(float(x)**2 for x in v))*RY_BOHR_TO_EV_ANG for v in vals[-nat:])

def run_stage_a(args):
    p=json.load(open(args.protocol)); clean=json.load(open(args.clean_result)); bulk=json.load(open(args.bulk_adjudication))
    if p["status"]!="FROZEN_BEFORE_ADSORPTION_RESULTS": raise SystemExit("Site-screen protocol is not frozen")
    if clean["readiness_state"]!="SURFACE_READY": raise SystemExit("Clean surface is not SURFACE_READY")
    a=float(bulk["structural_fit"]["a_angstrom"]); c=float(bulk["structural_fit"]["c_angstrom"])
    atoms=build_stage_a_atoms(clean["relaxation"]["final_coordinates_angstrom"],a,args.site,args.height)
    work=pathlib.Path(args.out).resolve(); work.mkdir(parents=True,exist_ok=True)
    (work/"pseudos").mkdir(exist_ok=True)
    ru=pathlib.Path(args.ru_pseudo).resolve(); hp=pathlib.Path(args.h_pseudo).resolve()
    (work/"pseudos"/ru.name).write_bytes(ru.read_bytes()); (work/"pseudos"/hp.name).write_bytes(hp.read_bytes())
    pw=pathlib.Path(args.pw).resolve()
    segs=int(p["execution"]["max_segments_per_relaxation_case"]); sec=int(p["execution"]["segment_seconds"])
    force_thr=float(p["screen_model"]["stage_A_constrained_screen"]["force_threshold_ev_per_angstrom"])
    prefix=f"hru_{args.site}_{int(round(args.height*100))}"
    segment_records=[]; final_txt=""; disposition="ADSORPTION_SITE_CHECKPOINT_HOLD"
    for i in range(1,segs+1):
        mode="from_scratch" if i==1 else "restart"
        text=qe_input(atoms,a,c,args.site,args.height,ru.name,hp.name,mode,prefix,sec,force_thr)
        rc,txt,inp,out=run_segment(pw,work,i,text,sec+900)
        low=txt.lower()
        clean_stop=("maximum cpu time exceeded" in low)
        converged=("bfgs converged" in low and "job done." in low and not clean_stop)
        segment_records.append({"segment":i,"restart_mode":mode,"returncode":rc,"clean_max_seconds_stop":clean_stop,
                                "bfgs_converged":converged,"output":out.name,"energy_ev":last_energy_ev(txt)})
        final_txt=txt
        if converged:
            disposition="STAGE_A_COMPLETE"; break
        if clean_stop and rc==0:
            save=work/"qe_tmp"/f"{prefix}.save"
            if not save.exists(): raise SystemExit("QE claimed clean max_seconds stop but restart save is missing")
            continue
        disposition="ADSORPTION_SITE_NUMERICAL_HOLD"; break
    pts=final_positions(final_txt,len(atoms)) if disposition=="STAGE_A_COMPLETE" else None
    maxf=last_max_force(final_txt,len(atoms)) if disposition=="STAGE_A_COMPLETE" else None
    energy=last_energy_ev(final_txt) if disposition=="STAGE_A_COMPLETE" else None
    pass_force=(maxf is not None and maxf<=force_thr)
    status="STAGE_A_PASS" if disposition=="STAGE_A_COMPLETE" and pass_force else disposition
    final_atoms=None
    if pts:
        final_atoms=[]
        for template,pos in zip(atoms,pts):
            item=dict(template); item.update({"label":pos[0],"x":pos[1],"y":pos[2],"z":pos[3]}); final_atoms.append(item)
    result={
      "schema":"symc-system3-h-ru0001-stage-a-site-result-v0.1","status":status,"site":args.site,
      "starting_height_angstrom":args.height,"energy_ev":energy,"max_force_ev_per_angstrom":maxf,
      "force_threshold_ev_per_angstrom":force_thr,"segments":segment_records,"final_atoms":final_atoms,
      "pseudo_sha256":{"Ru":sha256(ru),"H":sha256(hp)},"pw_sha256":sha256(pw),
      "scientific_settings_changed":False,"thresholds_changed":False
    }
    rp=work/"STAGE_A_RESULT.json"; rp.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

def select_stage_a(args):
    root=pathlib.Path(args.cases_root)
    rows=[]
    for path in root.rglob("STAGE_A_RESULT.json"):
        try: rows.append(json.load(open(path)))
        except Exception: pass
    sites=["top","bridge","fcc_hollow","hcp_hollow"]; selected={}; holds={}
    for s in sites:
        sr=[r for r in rows if r.get("site")==s]
        expected=sorted(round(x,6) for x in [1.0,1.5,2.0])
        seen=sorted(round(float(r["starting_height_angstrom"]),6) for r in sr)
        if seen!=expected:
            holds[s]={"reason":"incomplete_registered_height_set","seen":seen}; continue
        good=[r for r in sr if r.get("status")=="STAGE_A_PASS" and r.get("energy_ev") is not None]
        if not good:
            holds[s]={"reason":"no_converged_stage_a_basin","statuses":[r.get("status") for r in sr]}; continue
        best=min(good,key=lambda r:r["energy_ev"])
        selected[s]={"starting_height_angstrom":best["starting_height_angstrom"],"energy_ev":best["energy_ev"],
                     "max_force_ev_per_angstrom":best["max_force_ev_per_angstrom"],"final_atoms":best["final_atoms"],
                     "pseudo_sha256":best["pseudo_sha256"],"pw_sha256":best["pw_sha256"]}
    status="STAGE_A_SELECTION_PASS" if len(selected)==4 else "STAGE_A_SELECTION_HOLD"
    out={"schema":"symc-system3-h-ru0001-stage-a-selection-v0.1","status":status,"selected":selected,"holds":holds,
         "registered_sites":sites,"input_case_count":len(rows)}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    if status!="STAGE_A_SELECTION_PASS": raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("stage-a")
    for flag in ["protocol","clean-result","bulk-adjudication","pw","ru-pseudo","h-pseudo","site","out"]:
        a.add_argument("--"+flag,required=True)
    a.add_argument("--height",type=float,required=True)
    a.set_defaults(func=run_stage_a)
    s=sp.add_parser("select-stage-a")
    s.add_argument("--cases-root",required=True); s.add_argument("--out",required=True); s.set_defaults(func=select_stage_a)
    args=ap.parse_args(); args.func(args)

if __name__=="__main__":
    main()
