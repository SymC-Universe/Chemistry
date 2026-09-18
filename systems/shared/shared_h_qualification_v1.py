#!/usr/bin/env python3
import argparse, json, math, pathlib, re, subprocess, os, hashlib

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG

def q(v):
    return str(v).lower() if isinstance(v, bool) else str(v)

def atom_input(pseudo_name, ecutwfc, ecutrho, cell, outdir):
    c = cell / 2.0
    return f"""&CONTROL
 calculation='scf',
 restart_mode='from_scratch',
 prefix='H_atom_{int(ecutwfc)}',
 pseudo_dir='.',
 outdir='{outdir}',
 tstress=.true.,
 tprnfor=.true.,
 disk_io='low',
/
&SYSTEM
 ibrav=0,
 nat=1,
 ntyp=1,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 occupations='fixed',
 nspin=2,
 starting_magnetization(1)=1.0,
 tot_magnetization=1,
/
&ELECTRONS
 conv_thr=1.0d-12,
 mixing_beta=0.3,
 electron_maxstep=200,
/
ATOMIC_SPECIES
H 1.00794 {pseudo_name}
CELL_PARAMETERS angstrom
{cell:.10f} 0.0 0.0
0.0 {cell:.10f} 0.0
0.0 0.0 {cell:.10f}
ATOMIC_POSITIONS angstrom
H {c:.10f} {c:.10f} {c:.10f}
K_POINTS gamma
"""

def h2_input(pseudo_name, ecutwfc, ecutrho, cell, bond, outdir):
    c = cell / 2.0
    z1, z2 = c - bond/2.0, c + bond/2.0
    return f"""&CONTROL
 calculation='relax',
 restart_mode='from_scratch',
 prefix='H2_{int(ecutwfc)}',
 pseudo_dir='.',
 outdir='{outdir}',
 tstress=.true.,
 tprnfor=.true.,
 disk_io='low',
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=1,
 ecutwfc={ecutwfc},
 ecutrho={ecutrho},
 input_dft='PBE',
 occupations='fixed',
/
&ELECTRONS
 conv_thr=1.0d-12,
 mixing_beta=0.3,
 electron_maxstep=200,
/
&IONS
 ion_dynamics='bfgs',
 trust_radius_max=0.5,
/
ATOMIC_SPECIES
H 1.00794 {pseudo_name}
CELL_PARAMETERS angstrom
{cell:.10f} 0.0 0.0
0.0 {cell:.10f} 0.0
0.0 0.0 {cell:.10f}
ATOMIC_POSITIONS angstrom
H {c:.10f} {c:.10f} {z1:.10f}
H {c:.10f} {c:.10f} {z2:.10f}
K_POINTS gamma
"""

def run_pw(pw, work, name, text, timeout):
    work.mkdir(parents=True, exist_ok=True)
    inp = work / f"{name}.in"
    out = work / f"{name}.out"
    inp.write_text(text, encoding="utf-8")
    with inp.open("rb") as fin, out.open("wb") as fout:
        p = subprocess.run([str(pw)], stdin=fin, stdout=fout, stderr=subprocess.STDOUT,
                           cwd=work, timeout=timeout)
    txt = out.read_text(encoding="utf-8", errors="replace")
    return p.returncode, txt, inp, out

def last_energy_ev(txt):
    vals = re.findall(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry", txt)
    if not vals:
        raise RuntimeError("No QE total energy found")
    return float(vals[-1]) * RY_TO_EV

def final_positions(txt, nat):
    idx = txt.rfind("Begin final coordinates")
    chunk = txt[idx:] if idx >= 0 else txt
    matches = list(re.finditer(r"ATOMIC_POSITIONS\s*\(angstrom\)\s*\n", chunk))
    if not matches:
        raise RuntimeError("No final ATOMIC_POSITIONS block found")
    lines = chunk[matches[-1].end():].splitlines()
    pts = []
    for line in lines:
        s=line.split()
        if len(s) < 4 or s[0] != "H":
            if pts:
                break
            continue
        pts.append([float(s[1]), float(s[2]), float(s[3])])
        if len(pts)==nat:
            break
    if len(pts)!=nat:
        raise RuntimeError(f"Expected {nat} final H positions, found {len(pts)}")
    return pts

def last_max_force_ev_ang(txt, nat):
    vals = re.findall(r"force\s*=\s*([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", txt)
    if len(vals) < nat:
        raise RuntimeError("No complete QE force block found")
    block = vals[-nat:]
    mags = [math.sqrt(sum(float(x)**2 for x in v))*RY_BOHR_TO_EV_ANG for v in block]
    return max(mags)

def bond_length(pts):
    a,b=pts
    return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--pw", required=True)
    ap.add_argument("--pseudo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    args=ap.parse_args()

    protocol=json.load(open(args.protocol))
    if protocol["status"]!="FROZEN_BEFORE_QUALIFICATION_RESULTS":
        raise SystemExit("Protocol is not frozen qualification input")
    pw=pathlib.Path(args.pw).resolve()
    pseudo=pathlib.Path(args.pseudo).resolve()
    out=pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    pseudo_local=out/pseudo.name
    pseudo_local.write_bytes(pseudo.read_bytes())
    md5=hashlib.md5(pseudo_local.read_bytes()).hexdigest()
    if md5 != protocol["candidate"]["expected_md5"]:
        raise SystemExit(f"H pseudo MD5 mismatch: {md5}")

    cell=float(protocol["local_compatibility_tests"]["cell_angstrom"])
    bond0=float(protocol["local_compatibility_tests"]["h2"]["initial_bond_angstrom"])
    bases=[(70.0,280.0),(80.0,320.0)]
    records={}

    for ew,er in bases:
        tag=str(int(ew))
        atom_dir=out/f"atom_{tag}"
        atom_dir.mkdir(parents=True, exist_ok=True)
        atom_pseudo=atom_dir/pseudo.name
        atom_pseudo.write_bytes(pseudo.read_bytes())
        rc,txt,inp,qo=run_pw(pw, atom_dir, f"H_atom_{tag}",
            atom_input(pseudo.name, ew, er, cell, "./qe_tmp"), args.timeout_seconds)
        atom_ok=(rc==0 and "JOB DONE." in txt and "convergence has been achieved" in txt.lower())
        atom_e=last_energy_ev(txt) if atom_ok else None

        h2_dir=out/f"h2_{tag}"
        h2_dir.mkdir(parents=True, exist_ok=True)
        h2_pseudo=h2_dir/pseudo.name
        h2_pseudo.write_bytes(pseudo.read_bytes())
        rc2,txt2,inp2,qo2=run_pw(pw, h2_dir, f"H2_{tag}",
            h2_input(pseudo.name, ew, er, cell, bond0, "./qe_tmp"), args.timeout_seconds)
        h2_ok=(rc2==0 and "JOB DONE." in txt2 and "convergence has been achieved" in txt2.lower()
               and "bfgs converged" in txt2.lower())
        h2_e=last_energy_ev(txt2) if h2_ok else None
        pts=final_positions(txt2,2) if h2_ok else None
        bond=bond_length(pts) if pts else None
        maxf=last_max_force_ev_ang(txt2,2) if h2_ok else None

        records[tag]={
          "ecutwfc_ry":ew,"ecutrho_ry":er,
          "atom":{"returncode":rc,"complete":atom_ok,"energy_ev":atom_e},
          "h2":{"returncode":rc2,"complete":h2_ok,"energy_ev":h2_e,
                "bond_angstrom":bond,"max_force_ev_per_angstrom":maxf,
                "final_positions_angstrom":pts}
        }
        if atom_e is not None and h2_e is not None:
            records[tag]["binding_energy_ev"]=2.0*atom_e-h2_e

    a=records["70"]; b=records["80"]; acc=protocol["acceptance"]
    all_complete=all(r["atom"]["complete"] and r["h2"]["complete"] for r in records.values())
    force_pass=all(r["h2"]["max_force_ev_per_angstrom"] is not None and
                   r["h2"]["max_force_ev_per_angstrom"] <= acc["max_h2_final_force_ev_per_angstrom"]
                   for r in records.values())
    bond_delta=abs(a["h2"]["bond_angstrom"]-b["h2"]["bond_angstrom"]) if all_complete else None
    bind_delta=abs(a["binding_energy_ev"]-b["binding_energy_ev"]) if all_complete else None
    pass_all=(all_complete and force_pass
              and bond_delta <= acc["max_abs_h2_bond_difference_70_vs_80_angstrom"]
              and bind_delta <= acc["max_abs_h2_binding_energy_difference_70_vs_80_ev"])

    result={
      "schema":"symc-shared-h-pseudopotential-qualification-result-v0.1",
      "status":acc["pass_status"] if pass_all else acc["hold_status"],
      "protocol":str(args.protocol),
      "pseudo":{"filename":pseudo.name,"md5":md5,"sha256":sha256(pseudo_local)},
      "pw_sha256":sha256(pw),
      "records":records,
      "crosscheck":{
        "all_complete":all_complete,
        "force_pass":force_pass,
        "bond_delta_angstrom":bond_delta,
        "binding_energy_delta_ev":bind_delta,
        "bond_delta_limit_angstrom":acc["max_abs_h2_bond_difference_70_vs_80_angstrom"],
        "binding_energy_delta_limit_ev":acc["max_abs_h2_binding_energy_difference_70_vs_80_ev"]
      },
      "firewall":protocol["firewall"],
      "scope_boundary":protocol["scope_boundary"]
    }
    p=out/"H_PSEUDOPOTENTIAL_QUALIFICATION_RESULT.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
