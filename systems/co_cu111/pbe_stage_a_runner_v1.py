#!/usr/bin/env python3
"""Prospective non-kinetic PBE Stage A screen for CO/Cu(111).

This runner evaluates only Cu bulk numerical/structural fidelity and isolated CO
bond/vibrational fidelity. It contains no CO/Cu(111) diffusion barrier, hopping
rate, kinetic prefactor, fitted friction, or ChemSA target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any

import numpy as np

RY_TO_EV = 13.605693122994
EV_A2_TO_N_M = 16.02176634
AMU_TO_KG = 1.66053906660e-27
C_CM_S = 2.99792458e10
MASS_C_AMU = 12.0
MASS_O_AMU = 15.99491461957
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit(f"HOLD: JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def protocol_cutoff(protocol: dict[str, Any], cid: str) -> dict[str, Any]:
    rows = [x for x in protocol["cutoff_pairs_ry"] if x["id"] == cid]
    if len(rows) != 1:
        raise SystemExit(f"HOLD: cutoff id not unique: {cid}")
    return rows[0]


def verify_inputs(protocol_path: Path, bundle_path: Path, pseudo_dir: Path, pw: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = load_json(protocol_path)
    bundle = load_json(bundle_path)
    if protocol.get("schema") != "co-cu111-pbe-stage-a-protocol-v0.1" or protocol.get("status") != "FROZEN_BEFORE_PBE_STAGE_A_RESULTS":
        raise SystemExit("HOLD: wrong/unfrozen Stage A protocol")
    if bundle.get("schema") != "co-cu111-pbe-pseudopotential-bundle-v0.1" or bundle.get("status") != "PINNED_FOR_NON_KINETIC_METHOD_SCREEN":
        raise SystemExit("HOLD: wrong/unpinned PBE bundle")
    if sha256(pw) != bundle["solver_bundle"]["pw_x_sha256"]:
        raise SystemExit("HOLD: pw.x hash mismatch")
    for symbol in ("Cu", "C", "O"):
        row = bundle["pseudopotentials"][symbol]
        p = pseudo_dir / row["filename"]
        if not p.is_file() or sha256(p) != row["sha256"]:
            raise SystemExit(f"HOLD: pseudopotential mismatch for {symbol}")
    return protocol, bundle


def run_pw(pw: Path, inp: Path, out: Path, env: dict[str, str]) -> tuple[int, float, float | None, bool]:
    start = time.time()
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.run([str(pw)], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
    text = out.read_text(errors="replace")
    energies = [float(x) for x in ENERGY_RE.findall(text)]
    e = energies[-1] * RY_TO_EV if energies else None
    return proc.returncode, time.time() - start, e, "JOB DONE." in text


def bulk_input(a: float, ecutwfc: int, ecutrho: int, k: int, pseudo_dir: Path, outdir: Path, cu_name: str) -> str:
    pos = [(0,0,0),(0,0.5,0.5),(0.5,0,0.5),(0.5,0.5,0)]
    lines = [
        "&CONTROL", " calculation='scf',", " prefix='co_cu111_stageA_bulk',", f" pseudo_dir='{pseudo_dir}',", f" outdir='{outdir}',", " tstress=.true.,", " verbosity='high',", "/",
        "&SYSTEM", " ibrav=0,", " nat=4,", " ntyp=1,", f" ecutwfc={ecutwfc},", f" ecutrho={ecutrho},", " input_dft='PBE',", " occupations='smearing',", " smearing='mv',", " degauss=0.02,", "/",
        "&ELECTRONS", " conv_thr=1.0d-10,", " mixing_beta=0.3,", " electron_maxstep=200,", "/",
        "ATOMIC_SPECIES", f"Cu 63.546 {cu_name}",
        "CELL_PARAMETERS angstrom", f"{a:.12f} 0 0", f"0 {a:.12f} 0", f"0 0 {a:.12f}",
        "ATOMIC_POSITIONS crystal",
    ]
    lines += [f"Cu {x:.12f} {y:.12f} {z:.12f}" for x,y,z in pos]
    lines += ["K_POINTS automatic", f"{k} {k} {k} 0 0 0"]
    return "\n".join(lines) + "\n"


def co_input(r: float, L: float, ecutwfc: int, ecutrho: int, pseudo_dir: Path, outdir: Path, c_name: str, o_name: str) -> str:
    zc = L/2.0 - r/2.0
    zo = L/2.0 + r/2.0
    x = y = L/2.0
    return f"""&CONTROL
 calculation='scf',
 prefix='co_cu111_stageA_CO',
 pseudo_dir='{pseudo_dir}',
 outdir='{outdir}',
 verbosity='high',
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=2,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 assume_isolated='martyna-tuckerman',
 nosym=.true.,
/
&ELECTRONS
 conv_thr=1.0d-10,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
C 12.000000 {c_name}
O 15.999000 {o_name}
CELL_PARAMETERS angstrom
{L:.12f} 0 0
0 {L:.12f} 0
0 0 {L:.12f}
ATOMIC_POSITIONS angstrom
C {x:.12f} {y:.12f} {zc:.12f}
O {x:.12f} {y:.12f} {zo:.12f}
K_POINTS gamma
"""


def command_bulk(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); bundle_path = Path(args.bundle).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve(); root = Path(args.out).resolve()
    protocol, bundle = verify_inputs(protocol_path, bundle_path, pseudo_dir, pw)
    cutoff = protocol_cutoff(protocol, args.cutoff_id)
    allowed_k = {int(x["k"]) for x in protocol["bulk_cu"]["kmeshes"]}
    if args.kmesh not in allowed_k:
        raise SystemExit("HOLD: kmesh not frozen")
    env = dict(os.environ); env["OMP_NUM_THREADS"]="1"; env["OPENBLAS_NUM_THREADS"]="1"
    records=[]; root.mkdir(parents=True, exist_ok=True)
    cu = bundle["pseudopotentials"]["Cu"]["filename"]
    for a in protocol["bulk_cu"]["lattice_grid_angstrom"]:
        tag=f"a{float(a):.3f}"; d=root/tag; d.mkdir(exist_ok=True); tmp=d/"tmp"; tmp.mkdir(exist_ok=True)
        inp=d/f"{tag}.in"; out=d/f"{tag}.out"
        inp.write_text(bulk_input(float(a), int(cutoff["ecutwfc"]), int(cutoff["ecutrho"]), args.kmesh, pseudo_dir, tmp, cu))
        rc, elapsed, energy, done = run_pw(pw, inp, out, env)
        rec={"a_angstrom":float(a),"returncode":rc,"job_done":done,"energy_ev_total":energy,"energy_ev_per_atom":None if energy is None else energy/4.0,"elapsed_s":elapsed,"input_sha256":sha256(inp),"output_sha256":sha256(out)}
        write_json(d/"run_record.json",rec); records.append(rec)
        if rc != 0 or not done or energy is None:
            raise SystemExit(f"HOLD: bulk QE failure {tag}")
        for p in tmp.iterdir():
            if p.is_dir():
                import shutil; shutil.rmtree(p)
            else: p.unlink()
    summary={"schema":"co-cu111-pbe-stage-a-bulk-matrix-v0.1","status":"COMPLETE","cutoff_id":args.cutoff_id,"ecutwfc_ry":cutoff["ecutwfc"],"ecutrho_ry":cutoff["ecutrho"],"kmesh":args.kmesh,"records":records,"provenance":{"protocol_sha256":sha256(protocol_path),"bundle_sha256":sha256(bundle_path),"pw_sha256":sha256(pw),"cu_pseudo_sha256":bundle["pseudopotentials"]["Cu"]["sha256"],"scientific_settings_changed":False}}
    write_json(root/"summary.json",summary)
    (root/"STAGE_TIME_MANIFEST.sha256").write_text("\n".join(f"{sha256(p)}  {p.relative_to(root)}" for p in sorted(root.rglob("*.in"))+sorted(root.rglob("*.out"))+[root/"summary.json"]) + "\n")


def bond_grid(spec: dict[str, Any]) -> list[float]:
    start=float(spec["start"]); stop=float(spec["stop"]); step=float(spec["step"])
    n=int(round((stop-start)/step))
    vals=[round(start+i*step,10) for i in range(n+1)]
    if abs(vals[-1]-stop)>1e-8: raise SystemExit("HOLD: malformed bond grid")
    return vals


def command_co(args: argparse.Namespace) -> None:
    protocol_path = Path(args.protocol).resolve(); bundle_path = Path(args.bundle).resolve()
    pseudo_dir = Path(args.pseudo_dir).resolve(); pw = Path(args.pw).resolve(); root = Path(args.out).resolve()
    protocol, bundle = verify_inputs(protocol_path, bundle_path, pseudo_dir, pw)
    cutoff = protocol_cutoff(protocol, args.cutoff_id)
    allowed_L={float(x["L"]) for x in protocol["isolated_CO"]["box_lengths_angstrom"]}
    if float(args.box) not in allowed_L: raise SystemExit("HOLD: box not frozen")
    env=dict(os.environ); env["OMP_NUM_THREADS"]="1"; env["OPENBLAS_NUM_THREADS"]="1"
    c=bundle["pseudopotentials"]["C"]["filename"]; o=bundle["pseudopotentials"]["O"]["filename"]
    records=[]; root.mkdir(parents=True, exist_ok=True)
    for r in bond_grid(protocol["isolated_CO"]["bond_scan_angstrom"]):
        tag=f"r{r:.2f}"; d=root/tag; d.mkdir(exist_ok=True); tmp=d/"tmp"; tmp.mkdir(exist_ok=True)
        inp=d/f"{tag}.in"; out=d/f"{tag}.out"
        inp.write_text(co_input(r,float(args.box),int(cutoff["ecutwfc"]),int(cutoff["ecutrho"]),pseudo_dir,tmp,c,o))
        rc,elapsed,energy,done=run_pw(pw,inp,out,env)
        rec={"bond_angstrom":r,"returncode":rc,"job_done":done,"energy_ev_total":energy,"elapsed_s":elapsed,"input_sha256":sha256(inp),"output_sha256":sha256(out)}
        write_json(d/"run_record.json",rec); records.append(rec)
        if rc != 0 or not done or energy is None: raise SystemExit(f"HOLD: CO QE failure {tag}")
        for p in tmp.iterdir():
            if p.is_dir():
                import shutil; shutil.rmtree(p)
            else: p.unlink()
    summary={"schema":"co-cu111-pbe-stage-a-co-scan-v0.1","status":"COMPLETE","cutoff_id":args.cutoff_id,"ecutwfc_ry":cutoff["ecutwfc"],"ecutrho_ry":cutoff["ecutrho"],"box_angstrom":float(args.box),"records":records,"provenance":{"protocol_sha256":sha256(protocol_path),"bundle_sha256":sha256(bundle_path),"pw_sha256":sha256(pw),"c_pseudo_sha256":bundle["pseudopotentials"]["C"]["sha256"],"o_pseudo_sha256":bundle["pseudopotentials"]["O"]["sha256"],"scientific_settings_changed":False}}
    write_json(root/"summary.json",summary)
    (root/"STAGE_TIME_MANIFEST.sha256").write_text("\n".join(f"{sha256(p)}  {p.relative_to(root)}" for p in sorted(root.rglob("*.in"))+sorted(root.rglob("*.out"))+[root/"summary.json"]) + "\n")


def quadratic_fit(points: list[tuple[float,float]]) -> dict[str,float]:
    x=np.array([p[0] for p in points]); y=np.array([p[1] for p in points])
    coeff=np.polyfit(x,y,2)
    if coeff[0] <= 0: raise ValueError("non-convex bulk fit")
    a0=float(-coeff[1]/(2*coeff[0])); e0=float(np.polyval(coeff,a0))
    rms=float(np.sqrt(np.mean((y-np.polyval(coeff,x))**2))*1000)
    if not (min(x) <= a0 <= max(x)): raise ValueError("bulk fit minimum outside grid")
    return {"a0_angstrom":a0,"e0_ev_per_atom":e0,"rms_mev_per_atom":rms}


def co_fit(records: list[dict[str,Any]], sparse: bool=False) -> dict[str,float]:
    rows=sorted((float(r["bond_angstrom"]),float(r["energy_ev_total"])) for r in records)
    if sparse: rows=rows[::2]
    imin=min(range(len(rows)),key=lambda i:rows[i][1])
    lo=max(0,min(imin-3,len(rows)-7)); local=rows[lo:lo+7]
    if len(local)<5: raise ValueError("insufficient local CO points")
    x=np.array([p[0] for p in local]); y=np.array([p[1] for p in local]); coeff=np.polyfit(x,y,4)
    roots=np.roots(np.polyder(coeff))
    candidates=[]
    for root in roots:
        if abs(root.imag)<1e-8:
            rr=float(root.real)
            if min(x)<=rr<=max(x):
                second=float(np.polyval(np.polyder(coeff,2),rr))
                if second>0: candidates.append((float(np.polyval(coeff,rr)),rr,second))
    if not candidates: raise ValueError("no valid quartic minimum")
    _, r0, curvature=min(candidates)
    mu_amu=MASS_C_AMU*MASS_O_AMU/(MASS_C_AMU+MASS_O_AMU)
    omega=math.sqrt(curvature*EV_A2_TO_N_M/(mu_amu*AMU_TO_KG))
    cm1=omega/(2*math.pi*C_CM_S)
    rms=float(np.sqrt(np.mean((y-np.polyval(coeff,x))**2))*1000)
    return {"bond_angstrom":r0,"harmonic_stretch_cm_minus_1":cm1,"curvature_ev_per_angstrom2":curvature,"fit_rms_mev":rms,"fit_min_angstrom":float(min(x)),"fit_max_angstrom":float(max(x))}


def command_analyze(args: argparse.Namespace) -> None:
    protocol_path=Path(args.protocol).resolve(); bundle_path=Path(args.bundle).resolve(); root=Path(args.root).resolve(); out=Path(args.out).resolve()
    protocol=load_json(protocol_path); bundle=load_json(bundle_path)
    if protocol.get("status")!="FROZEN_BEFORE_PBE_STAGE_A_RESULTS": raise SystemExit("HOLD: protocol not frozen")
    cutoff_order={x["id"]:i for i,x in enumerate(protocol["cutoff_pairs_ry"])}
    selectable_cutoff={x["id"]:bool(x["selectable"]) for x in protocol["cutoff_pairs_ry"]}
    bulk=[]
    for p in root.rglob("bulk_*/summary.json"):
        d=load_json(p); fit=quadratic_fit([(float(r["a_angstrom"]),float(r["energy_ev_per_atom"])) for r in d["records"]]); bulk.append({"cutoff_id":d["cutoff_id"],"kmesh":int(d["kmesh"]),"fit":fit,"source":str(p),"source_sha256":sha256(p)})
    if len(bulk)!=9: raise SystemExit(f"HOLD: expected 9 bulk summaries, found {len(bulk)}")
    bref=next((x for x in bulk if x["cutoff_id"]=="C2" and x["kmesh"]==16),None)
    if bref is None: raise SystemExit("HOLD: terminal bulk reference missing")
    bgate=protocol["bulk_cu"]["joint_numerical_gate"]; expa=float(protocol["bulk_cu"]["physical_guard"]["reference_lattice_constant_angstrom"]); maxrel=float(protocol["bulk_cu"]["physical_guard"]["max_relative_error_fraction"])
    terminal_bulk_physical=abs(bref["fit"]["a0_angstrom"]-expa)/expa<=maxrel
    selectable_k={int(x["k"]):bool(x["selectable"]) for x in protocol["bulk_cu"]["kmeshes"]}
    for x in bulk:
        x["delta_a0_angstrom"]=abs(x["fit"]["a0_angstrom"]-bref["fit"]["a0_angstrom"]); x["delta_e0_ev_per_atom"]=abs(x["fit"]["e0_ev_per_atom"]-bref["fit"]["e0_ev_per_atom"])
        x["numerical_pass"]=x["delta_a0_angstrom"]<=float(bgate["delta_a0_max_angstrom"]) and x["delta_e0_ev_per_atom"]<=float(bgate["delta_e0_max_ev_per_atom"])
        x["physical_pass"]=abs(x["fit"]["a0_angstrom"]-expa)/expa<=maxrel
        x["selectable"]=selectable_cutoff[x["cutoff_id"]] and selectable_k[x["kmesh"]]
    bulk_pool=[x for x in bulk if x["selectable"] and x["numerical_pass"] and x["physical_pass"]]
    bulk_sel=min(bulk_pool,key=lambda x:(cutoff_order[x["cutoff_id"]],x["kmesh"])) if bulk_pool else None

    cos=[]
    for p in root.rglob("co_*/summary.json"):
        d=load_json(p); fit=co_fit(d["records"],False); sparse=co_fit(d["records"],True)
        cos.append({"cutoff_id":d["cutoff_id"],"box_angstrom":float(d["box_angstrom"]),"fit":fit,"sparse_fit":sparse,"discretization_delta_cm_minus_1":abs(fit["harmonic_stretch_cm_minus_1"]-sparse["harmonic_stretch_cm_minus_1"]),"source":str(p),"source_sha256":sha256(p)})
    if len(cos)!=9: raise SystemExit(f"HOLD: expected 9 CO summaries, found {len(cos)}")
    cref=next((x for x in cos if x["cutoff_id"]=="C2" and abs(x["box_angstrom"]-26.0)<1e-9),None)
    if cref is None: raise SystemExit("HOLD: terminal CO reference missing")
    ng=protocol["isolated_CO"]["numerical_gate_relative_to_terminal_C2_L26"]; pg=protocol["isolated_CO"]["physical_guards"]
    rref=float(pg["equilibrium_bond_reference_angstrom"]); fref=float(pg["fundamental_vibration_reference_cm_minus_1"])
    terminal_co_bond=abs(cref["fit"]["bond_angstrom"]-rref)/rref<=float(pg["bond_max_relative_error_fraction"])
    terminal_co_freq=abs(cref["fit"]["harmonic_stretch_cm_minus_1"]-fref)/fref<=float(pg["vibration_max_relative_error_fraction"])
    selectable_box={float(x["L"]):bool(x["selectable"]) for x in protocol["isolated_CO"]["box_lengths_angstrom"]}
    for x in cos:
        x["delta_bond_angstrom"]=abs(x["fit"]["bond_angstrom"]-cref["fit"]["bond_angstrom"]); x["delta_stretch_cm_minus_1"]=abs(x["fit"]["harmonic_stretch_cm_minus_1"]-cref["fit"]["harmonic_stretch_cm_minus_1"])
        x["numerical_pass"]=x["delta_bond_angstrom"]<=float(ng["bond_length_max_difference_angstrom"]) and x["delta_stretch_cm_minus_1"]<=float(ng["stretch_max_difference_cm_minus_1"])
        x["discretization_pass"]=x["discretization_delta_cm_minus_1"]<=10.0
        x["bond_physical_pass"]=abs(x["fit"]["bond_angstrom"]-rref)/rref<=float(pg["bond_max_relative_error_fraction"])
        x["frequency_physical_pass"]=abs(x["fit"]["harmonic_stretch_cm_minus_1"]-fref)/fref<=float(pg["vibration_max_relative_error_fraction"])
        x["selectable"]=selectable_cutoff[x["cutoff_id"]] and selectable_box[x["box_angstrom"]]
    co_pool=[x for x in cos if x["selectable"] and x["numerical_pass"] and x["discretization_pass"] and x["bond_physical_pass"] and x["frequency_physical_pass"]]
    co_sel=min(co_pool,key=lambda x:(cutoff_order[x["cutoff_id"]],x["box_angstrom"])) if co_pool else None

    if not terminal_bulk_physical: status="PBE_REJECT_BULK_STRUCTURE"
    elif not terminal_co_bond: status="PBE_REJECT_CO_STRUCTURE"
    elif not terminal_co_freq: status="PBE_REJECT_CO_VIBRATION"
    elif cref["discretization_delta_cm_minus_1"]>10.0: status="FIT_HOLD"
    elif bulk_sel is None or co_sel is None: status="NUMERICAL_HOLD"
    else: status="PASS"
    combined=None
    if status=="PASS":
        combined_id=max((bulk_sel["cutoff_id"],co_sel["cutoff_id"]),key=lambda cid:cutoff_order[cid])
        bulk_comb=next((x for x in bulk if x["cutoff_id"]==combined_id and x["kmesh"]==bulk_sel["kmesh"]),None)
        co_comb=next((x for x in cos if x["cutoff_id"]==combined_id and x["box_angstrom"]==co_sel["box_angstrom"]),None)
        if bulk_comb is None or co_comb is None or not bulk_comb["numerical_pass"] or not co_comb["numerical_pass"] or not co_comb["discretization_pass"]:
            status="NUMERICAL_HOLD"
        else:
            combined={"cutoff_id":combined_id,"ecutwfc_ry":protocol_cutoff(protocol,combined_id)["ecutwfc"],"ecutrho_ry":protocol_cutoff(protocol,combined_id)["ecutrho"],"bulk_kmesh":bulk_sel["kmesh"],"gas_box_angstrom":co_sel["box_angstrom"]}
    result={"schema":"co-cu111-pbe-stage-a-result-v0.1","status":status,"bulk_terminal_reference":bref,"bulk_terminal_physical_pass":terminal_bulk_physical,"bulk_candidates":sorted(bulk,key=lambda x:(cutoff_order[x["cutoff_id"]],x["kmesh"])),"bulk_selected":bulk_sel,"co_terminal_reference":cref,"co_terminal_bond_physical_pass":terminal_co_bond,"co_terminal_frequency_physical_pass":terminal_co_freq,"co_candidates":sorted(cos,key=lambda x:(cutoff_order[x["cutoff_id"]],x["box_angstrom"])),"co_selected":co_sel,"combined_selected_settings":combined,"next_gate":"PBE_CU111_CLEAN_SURFACE_AND_SITE_ORDERING_SCREEN" if status=="PASS" else ("BLYP_PP_PROVENANCE_GATE" if status.startswith("PBE_REJECT") else "STAGE_A_HOLD_REVIEW"),"provenance":{"protocol_sha256":sha256(protocol_path),"bundle_sha256":sha256(bundle_path),"scientific_settings_changed":False}}
    write_json(out,result)
    print(json.dumps(result,indent=2))
    if status!="PASS": raise SystemExit(2)


def main() -> None:
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True)
    b=sp.add_parser("bulk-run"); b.add_argument("--protocol",required=True); b.add_argument("--bundle",required=True); b.add_argument("--pseudo-dir",required=True); b.add_argument("--pw",required=True); b.add_argument("--cutoff-id",required=True); b.add_argument("--kmesh",type=int,required=True); b.add_argument("--out",required=True); b.set_defaults(func=command_bulk)
    c=sp.add_parser("co-run"); c.add_argument("--protocol",required=True); c.add_argument("--bundle",required=True); c.add_argument("--pseudo-dir",required=True); c.add_argument("--pw",required=True); c.add_argument("--cutoff-id",required=True); c.add_argument("--box",type=float,required=True); c.add_argument("--out",required=True); c.set_defaults(func=command_co)
    a=sp.add_parser("analyze"); a.add_argument("--protocol",required=True); a.add_argument("--bundle",required=True); a.add_argument("--root",required=True); a.add_argument("--out",required=True); a.set_defaults(func=command_analyze)
    args=ap.parse_args(); args.func(args)

if __name__=="__main__": main()
