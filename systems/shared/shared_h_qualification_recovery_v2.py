#!/usr/bin/env python3
import argparse
import hashlib
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pw(pw, work, name, text, timeout):
    work.mkdir(parents=True, exist_ok=True)
    inp = work / f"{name}.in"
    out = work / f"{name}.out"
    inp.write_text(text, encoding="utf-8")
    with inp.open("rb") as fin, out.open("wb") as fout:
        p = subprocess.run(
            [str(pw)],
            stdin=fin,
            stdout=fout,
            stderr=subprocess.STDOUT,
            cwd=work,
            timeout=timeout,
        )
    txt = out.read_text(encoding="utf-8", errors="replace")
    return p.returncode, txt, inp, out


def last_energy_ev(txt):
    vals = re.findall(r"!\\s+total energy\\s+=\\s+([-+0-9.Ee]+)\\s+Ry", txt)
    if not vals:
        return None
    return float(vals[-1]) * RY_TO_EV


def final_positions(txt, nat):
    idx = txt.rfind("Begin final coordinates")
    chunk = txt[idx:] if idx >= 0 else txt
    matches = list(re.finditer(r"ATOMIC_POSITIONS\\s*\\(angstrom\\)\\s*\\n", chunk))
    if not matches:
        return None
    lines = chunk[matches[-1].end():].splitlines()
    pts = []
    for line in lines:
        s = line.split()
        if len(s) < 4 or s[0] != "H":
            if pts:
                break
            continue
        try:
            pts.append([float(s[1]), float(s[2]), float(s[3])])
        except ValueError:
            continue
        if len(pts) == nat:
            break
    return pts if len(pts) == nat else None


def last_max_force_ev_ang(txt, nat):
    vals = re.findall(
        r"force\\s*=\\s*([-+0-9.Ee]+)\\s+([-+0-9.Ee]+)\\s+([-+0-9.Ee]+)",
        txt,
    )
    if len(vals) < nat:
        return None
    block = vals[-nat:]
    mags = [
        math.sqrt(sum(float(x) ** 2 for x in v)) * RY_BOHR_TO_EV_ANG
        for v in block
    ]
    return max(mags)


def bond_length(pts):
    a, b = pts
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def atom_input(pseudo_name, ew, er, cell, outdir, prefix, settings):
    c = cell / 2.0
    return f"""&CONTROL
 calculation='scf',
 restart_mode='restart',
 prefix='{prefix}',
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
 ecutwfc={ew},
 ecutrho={er},
 input_dft='PBE',
 occupations='fixed',
 nspin=2,
 starting_magnetization(1)=1.0,
 tot_magnetization=1,
/
&ELECTRONS
 conv_thr={settings['conv_thr']:.12e},
 mixing_beta={settings['mixing_beta']},
 electron_maxstep={settings['electron_maxstep_per_segment']},
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


def h2_input(pseudo_name, ew, er, cell, pts, outdir, prefix, settings, h2):
    p1, p2 = pts
    return f"""&CONTROL
 calculation='relax',
 restart_mode='from_scratch',
 prefix='{prefix}',
 pseudo_dir='.',
 outdir='{outdir}',
 tstress=.true.,
 tprnfor=.true.,
 disk_io='low',
 nstep={h2['ionic_steps_per_segment']},
 forc_conv_thr={h2['forc_conv_thr_ry_per_bohr']},
/
&SYSTEM
 ibrav=0,
 nat=2,
 ntyp=1,
 ecutwfc={ew},
 ecutrho={er},
 input_dft='PBE',
 occupations='fixed',
/
&ELECTRONS
 conv_thr={settings['conv_thr']:.12e},
 mixing_beta={settings['mixing_beta']},
 electron_maxstep={settings['electron_maxstep_per_segment']},
/
&IONS
 ion_dynamics='bfgs',
 trust_radius_max={h2['trust_radius_max']},
/
ATOMIC_SPECIES
H 1.00794 {pseudo_name}
CELL_PARAMETERS angstrom
{cell:.10f} 0.0 0.0
0.0 {cell:.10f} 0.0
0.0 0.0 {cell:.10f}
ATOMIC_POSITIONS angstrom
H {p1[0]:.10f} {p1[1]:.10f} {p1[2]:.10f}
H {p2[0]:.10f} {p2[1]:.10f} {p2[2]:.10f}
K_POINTS gamma
"""


def load_protocol(path):
    p = json.load(open(path, encoding="utf-8"))
    if p["status"] != "FROZEN_AFTER_V0_1_HOLD_BEFORE_V0_2_RECOVERY_RESULTS":
        raise SystemExit("Recovery protocol is not in frozen pre-result state")
    if not p["non_retroactivity"]["v0_1_hold_remains_valid"]:
        raise SystemExit("Non-retroactivity firewall not active")
    return p


def verify_pseudo(pseudo, protocol):
    md5 = hashlib.md5(pseudo.read_bytes()).hexdigest()
    if md5 != protocol["candidate"]["expected_md5"]:
        raise SystemExit(f"H pseudo MD5 mismatch: {md5}")
    return md5


def run_atom(args, protocol):
    tag = str(args.basis)
    case = protocol["basis_cases"][tag]
    settings = protocol["shared_electronic_settings"]
    recovery = protocol["atom_recovery"]
    source = pathlib.Path(args.source_root).resolve() / f"atom_{tag}"
    source_out = source / f"H_atom_{tag}.out"
    source_qe = source / "qe_tmp"
    if not source_out.exists() or not source_qe.exists():
        raise SystemExit(f"Missing v0.1 atom source/checkpoint for {tag}")
    source_txt = source_out.read_text(encoding="utf-8", errors="replace")
    if "convergence NOT achieved after 200 iterations" not in source_txt:
        raise SystemExit(f"Unexpected v0.1 atom disposition for {tag}")

    out = pathlib.Path(args.out).resolve()
    work = out / f"atom_{tag}"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint = work / "qe_tmp"
    if checkpoint.exists():
        shutil.rmtree(checkpoint)
    shutil.copytree(source_qe, checkpoint)

    pseudo = pathlib.Path(args.pseudo).resolve()
    pseudo_local = work / pseudo.name
    pseudo_local.write_bytes(pseudo.read_bytes())
    md5 = verify_pseudo(pseudo_local, protocol)

    pw = pathlib.Path(args.pw).resolve()
    if sha256(pw) != protocol["runtime"]["pw_sha256"]:
        raise SystemExit("QE runtime SHA256 mismatch")

    seg_records = []
    converged = False
    energy_ev = None
    prefix = f"H_atom_{tag}"
    for seg in range(1, int(recovery["max_additional_segments"]) + 1):
        name = f"H_atom_{tag}_recovery_seg{seg}"
        rc, txt, inp, qo = run_pw(
            pw,
            work,
            name,
            atom_input(
                pseudo.name,
                case["ecutwfc_ry"],
                case["ecutrho_ry"],
                18.0,
                "./qe_tmp",
                prefix,
                settings,
            ),
            args.timeout_seconds,
        )
        done = "JOB DONE." in txt
        conv = "convergence has been achieved" in txt.lower()
        not_conv = "convergence not achieved" in txt.lower()
        energy = last_energy_ev(txt)
        seg_records.append(
            {
                "segment": seg,
                "returncode": rc,
                "job_done": done,
                "converged": conv,
                "convergence_not_achieved": not_conv,
                "energy_ev": energy,
                "output": qo.name,
            }
        )
        if rc != 0:
            break
        if done and conv and energy is not None:
            converged = True
            energy_ev = energy
            break

    result = {
        "schema": "symc-shared-h-atom-recovery-result-v0.2",
        "basis_tag": tag,
        "status": "ATOM_RECOVERY_CONVERGED" if converged else "ATOM_RECOVERY_HOLD",
        "ecutwfc_ry": case["ecutwfc_ry"],
        "ecutrho_ry": case["ecutrho_ry"],
        "energy_ev": energy_ev,
        "segments": seg_records,
        "source_parent_run_id": protocol["parent_run_id"],
        "source_parent_hold_preserved": True,
        "pseudo_md5": md5,
        "pw_sha256": sha256(pw),
        "electronic_settings": settings,
    }
    p = out / f"ATOM_{tag}_RECOVERY_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


def run_h2(args, protocol):
    tag = str(args.basis)
    case = protocol["basis_cases"][tag]
    settings = protocol["shared_electronic_settings"]
    recovery = protocol["h2_recovery"]
    source = pathlib.Path(args.source_root).resolve() / f"h2_{tag}"
    source_out = source / f"H2_{tag}.out"
    if not source_out.exists():
        raise SystemExit(f"Missing v0.1 H2 output for {tag}")
    source_txt = source_out.read_text(encoding="utf-8", errors="replace")
    pts = final_positions(source_txt, 2)
    geometry_source = "raw_qe_final_coordinates"
    if pts is None:
        parent_result_path = pathlib.Path(args.source_root).resolve() / "H_PSEUDOPOTENTIAL_QUALIFICATION_RESULT.json"
        if not parent_result_path.exists():
            raise SystemExit(f"Cannot recover final v0.1 H2 geometry for {tag}: parent result JSON missing")
        parent_result = json.load(open(parent_result_path, encoding="utf-8"))
        rec = parent_result.get("records", {}).get(tag, {}).get("h2", {})
        candidate = rec.get("final_positions_angstrom")
        if not (
            isinstance(candidate, list) and len(candidate) == 2
            and all(isinstance(row, list) and len(row) == 3 for row in candidate)
        ):
            raise SystemExit(f"Cannot recover final v0.1 H2 geometry for {tag}: structured parent coordinates absent")
        pts = [[float(x) for x in row] for row in candidate]
        parent_bond = rec.get("bond_angstrom")
        if parent_bond is not None and abs(bond_length(pts) - float(parent_bond)) > 1.0e-8:
            raise SystemExit(f"Parent H2 geometry/bond mismatch for {tag}")
        geometry_source = "structured_parent_qualification_result"

    out = pathlib.Path(args.out).resolve()
    work = out / f"h2_{tag}"
    work.mkdir(parents=True, exist_ok=True)

    pseudo = pathlib.Path(args.pseudo).resolve()
    pseudo_local = work / pseudo.name
    pseudo_local.write_bytes(pseudo.read_bytes())
    md5 = verify_pseudo(pseudo_local, protocol)

    pw = pathlib.Path(args.pw).resolve()
    if sha256(pw) != protocol["runtime"]["pw_sha256"]:
        raise SystemExit("QE runtime SHA256 mismatch")

    seg_records = []
    passed_local = False
    energy_ev = None
    bond = None
    max_force = None
    current_pts = pts
    for seg in range(1, int(recovery["max_segments"]) + 1):
        segdir = work / f"seg{seg}"
        segdir.mkdir(parents=True, exist_ok=True)
        seg_pseudo = segdir / pseudo.name
        seg_pseudo.write_bytes(pseudo.read_bytes())
        name = f"H2_{tag}_recovery_seg{seg}"
        rc, txt, inp, qo = run_pw(
            pw,
            segdir,
            name,
            h2_input(
                pseudo.name,
                case["ecutwfc_ry"],
                case["ecutrho_ry"],
                18.0,
                current_pts,
                "./qe_tmp",
                f"H2_recovery_{tag}_seg{seg}",
                settings,
                recovery,
            ),
            args.timeout_seconds,
        )
        done = "JOB DONE." in txt
        conv = "convergence has been achieved" in txt.lower()
        bfgs = "bfgs converged" in txt.lower()
        energy = last_energy_ev(txt)
        new_pts = final_positions(txt, 2)
        force = last_max_force_ev_ang(txt, 2)
        if new_pts is not None:
            current_pts = new_pts
        bond_now = bond_length(current_pts)
        local_pass = (
            rc == 0
            and done
            and conv
            and bfgs
            and energy is not None
            and force is not None
            and force <= protocol["acceptance"]["max_h2_final_force_ev_per_angstrom"]
        )
        seg_records.append(
            {
                "segment": seg,
                "returncode": rc,
                "job_done": done,
                "electronic_converged": conv,
                "bfgs_converged": bfgs,
                "energy_ev": energy,
                "bond_angstrom": bond_now,
                "max_force_ev_per_angstrom": force,
                "output": str(qo.relative_to(out)),
            }
        )
        if local_pass:
            passed_local = True
            energy_ev = energy
            bond = bond_now
            max_force = force
            break
        if rc != 0:
            break

    if not passed_local and seg_records:
        last = seg_records[-1]
        energy_ev = last["energy_ev"]
        bond = last["bond_angstrom"]
        max_force = last["max_force_ev_per_angstrom"]

    result = {
        "schema": "symc-shared-h-h2-recovery-result-v0.2",
        "basis_tag": tag,
        "status": "H2_RECOVERY_LOCAL_PASS" if passed_local else "H2_RECOVERY_HOLD",
        "ecutwfc_ry": case["ecutwfc_ry"],
        "ecutrho_ry": case["ecutrho_ry"],
        "energy_ev": energy_ev,
        "bond_angstrom": bond,
        "max_force_ev_per_angstrom": max_force,
        "segments": seg_records,
        "source_parent_run_id": protocol["parent_run_id"],
        "source_parent_hold_preserved": True,
        "initial_geometry_source": geometry_source,
        "pseudo_md5": md5,
        "pw_sha256": sha256(pw),
        "forc_conv_thr_ry_per_bohr": recovery["forc_conv_thr_ry_per_bohr"],
        "frozen_force_gate_ev_per_angstrom": protocol["acceptance"]["max_h2_final_force_ev_per_angstrom"],
    }
    p = out / f"H2_{tag}_RECOVERY_RESULT.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


def adjudicate(args, protocol):
    root = pathlib.Path(args.source_root).resolve()
    atom = {}
    h2 = {}
    for tag in ("70", "80"):
        atom[tag] = json.load(open(root / f"ATOM_{tag}_RECOVERY_RESULT.json", encoding="utf-8"))
        h2[tag] = json.load(open(root / f"H2_{tag}_RECOVERY_RESULT.json", encoding="utf-8"))

    all_complete = all(atom[t]["status"] == "ATOM_RECOVERY_CONVERGED" for t in ("70", "80"))
    all_complete = all_complete and all(h2[t]["status"] == "H2_RECOVERY_LOCAL_PASS" for t in ("70", "80"))

    bond_delta = None
    bind_delta = None
    binding = {}
    if all_complete:
        for tag in ("70", "80"):
            binding[tag] = 2.0 * atom[tag]["energy_ev"] - h2[tag]["energy_ev"]
        bond_delta = abs(h2["70"]["bond_angstrom"] - h2["80"]["bond_angstrom"])
        bind_delta = abs(binding["70"] - binding["80"])

    acc = protocol["acceptance"]
    force_pass = all(
        h2[t]["max_force_ev_per_angstrom"] is not None
        and h2[t]["max_force_ev_per_angstrom"] <= acc["max_h2_final_force_ev_per_angstrom"]
        for t in ("70", "80")
    )
    pass_all = (
        all_complete
        and force_pass
        and bond_delta is not None
        and bond_delta <= acc["max_abs_h2_bond_difference_70_vs_80_angstrom"]
        and bind_delta is not None
        and bind_delta <= acc["max_abs_h2_binding_energy_difference_70_vs_80_ev"]
    )
    result = {
        "schema": "symc-shared-h-pseudopotential-qualification-recovery-adjudication-v0.2",
        "status": acc["pass_status"] if pass_all else acc["hold_status"],
        "parent_v0_1_disposition_preserved": protocol["parent_disposition"],
        "atom_results": atom,
        "h2_results": h2,
        "binding_energy_ev": binding,
        "crosscheck": {
            "all_complete": all_complete,
            "force_pass": force_pass,
            "bond_delta_angstrom": bond_delta,
            "binding_energy_delta_ev": bind_delta,
            "bond_delta_limit_angstrom": acc["max_abs_h2_bond_difference_70_vs_80_angstrom"],
            "binding_energy_delta_limit_ev": acc["max_abs_h2_binding_energy_difference_70_vs_80_ev"],
            "force_limit_ev_per_angstrom": acc["max_h2_final_force_ev_per_angstrom"],
        },
        "next_gate": protocol["next_gate_after_pass"] if pass_all else protocol["next_gate_after_hold"],
        "firewall": protocol["firewall"],
    }
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    p = out / "H_PSEUDOPOTENTIAL_QUALIFICATION_RECOVERY_RESULT_v0.2.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if pass_all else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--mode", choices=["atom", "h2", "adjudicate"], required=True)
    ap.add_argument("--basis", choices=["70", "80"])
    ap.add_argument("--pw")
    ap.add_argument("--pseudo")
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-seconds", type=int, default=3600)
    args = ap.parse_args()

    protocol = load_protocol(args.protocol)
    if args.mode in ("atom", "h2"):
        if not (args.basis and args.pw and args.pseudo):
            raise SystemExit("--basis, --pw, and --pseudo are required for compute modes")
        if args.mode == "atom":
            run_atom(args, protocol)
        else:
            run_h2(args, protocol)
        return 0
    return adjudicate(args, protocol)


if __name__ == "__main__":
    sys.exit(main())
