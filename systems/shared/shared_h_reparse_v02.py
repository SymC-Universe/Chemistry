#!/usr/bin/env python3
import argparse
import json
import math
import pathlib
import re

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG

def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def find_one(root, name):
    hits = list(pathlib.Path(root).rglob(name))
    if len(hits) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name}, found {len(hits)}")
    return hits[0]

def last_energy_ev(txt):
    vals = re.findall(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry", txt)
    return None if not vals else float(vals[-1]) * RY_TO_EV

def final_positions(txt, nat):
    idx = txt.rfind("Begin final coordinates")
    chunk = txt[idx:] if idx >= 0 else txt
    matches = list(re.finditer(r"ATOMIC_POSITIONS\s*\(angstrom\)\s*\n", chunk))
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
    vals = re.findall(r"force\s*=\s*([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)", txt)
    if len(vals) < nat:
        return None
    block = vals[-nat:]
    mags = [math.sqrt(sum(float(x) ** 2 for x in v)) * RY_BOHR_TO_EV_ANG for v in block]
    return max(mags)

def bond_length(pts):
    a, b = pts
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

def write_result(path, result):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

def reparse_h2(args, protocol):
    tag = str(args.basis)
    root = pathlib.Path(args.source_root)
    old_path = find_one(root, f"H2_{tag}_RECOVERY_RESULT.json")
    old = load_json(old_path)
    acc = protocol["acceptance"]
    records = []
    passed = False
    selected = None
    for oldseg in old["segments"]:
        seg = int(oldseg["segment"])
        outp = find_one(root, pathlib.Path(oldseg["output"]).name)
        txt = outp.read_text(encoding="utf-8", errors="replace")
        energy = last_energy_ev(txt)
        pts = final_positions(txt, 2)
        force = last_max_force_ev_ang(txt, 2)
        bond = bond_length(pts) if pts is not None else oldseg.get("bond_angstrom")
        rec = {
            "segment": seg,
            "returncode": oldseg.get("returncode"),
            "job_done": "JOB DONE." in txt,
            "electronic_converged": "convergence has been achieved" in txt.lower(),
            "bfgs_converged": "bfgs converged" in txt.lower(),
            "energy_ev": energy,
            "bond_angstrom": bond,
            "max_force_ev_per_angstrom": force,
            "source_output": str(outp),
        }
        rec["local_pass"] = (
            rec["returncode"] == 0
            and rec["job_done"]
            and rec["electronic_converged"]
            and rec["bfgs_converged"]
            and energy is not None
            and force is not None
            and force <= acc["max_h2_final_force_ev_per_angstrom"]
        )
        records.append(rec)
        if rec["local_pass"] and not passed:
            passed = True
            selected = rec
    if selected is None and records:
        selected = records[-1]
    result = {
        "schema": "symc-shared-h-h2-recovery-result-v0.2",
        "basis_tag": tag,
        "status": "H2_RECOVERY_LOCAL_PASS" if passed else "H2_RECOVERY_HOLD",
        "ecutwfc_ry": protocol["basis_cases"][tag]["ecutwfc_ry"],
        "ecutrho_ry": protocol["basis_cases"][tag]["ecutrho_ry"],
        "energy_ev": None if selected is None else selected["energy_ev"],
        "bond_angstrom": None if selected is None else selected["bond_angstrom"],
        "max_force_ev_per_angstrom": None if selected is None else selected["max_force_ev_per_angstrom"],
        "segments": records,
        "source_parent_run_id": protocol["parent_run_id"],
        "source_parent_hold_preserved": True,
        "forc_conv_thr_ry_per_bohr": protocol["h2_recovery"]["forc_conv_thr_ry_per_bohr"],
        "frozen_force_gate_ev_per_angstrom": acc["max_h2_final_force_ev_per_angstrom"],
        "mechanical_reparse_only": True,
        "source_result_file": str(old_path),
    }
    write_result(pathlib.Path(args.out) / f"H2_{tag}_RECOVERY_RESULT.json", result)

def reparse_atom(args, protocol):
    tag = str(args.basis)
    root = pathlib.Path(args.source_root)
    old_path = find_one(root, f"ATOM_{tag}_RECOVERY_RESULT.json")
    old = load_json(old_path)
    records = []
    selected = None
    for oldseg in old["segments"]:
        outp = find_one(root, pathlib.Path(oldseg["output"]).name)
        txt = outp.read_text(encoding="utf-8", errors="replace")
        rec = {
            "segment": int(oldseg["segment"]),
            "returncode": oldseg.get("returncode"),
            "job_done": "JOB DONE." in txt,
            "converged": "convergence has been achieved" in txt.lower(),
            "convergence_not_achieved": "convergence not achieved" in txt.lower(),
            "energy_ev": last_energy_ev(txt),
            "source_output": str(outp),
        }
        records.append(rec)
        if selected is None and rec["returncode"] == 0 and rec["job_done"] and rec["converged"] and rec["energy_ev"] is not None:
            selected = rec
    result = {
        "schema": "symc-shared-h-atom-recovery-result-v0.2",
        "basis_tag": tag,
        "status": "ATOM_RECOVERY_CONVERGED" if selected is not None else "ATOM_RECOVERY_HOLD",
        "ecutwfc_ry": protocol["basis_cases"][tag]["ecutwfc_ry"],
        "ecutrho_ry": protocol["basis_cases"][tag]["ecutrho_ry"],
        "energy_ev": None if selected is None else selected["energy_ev"],
        "segments": records,
        "source_parent_run_id": protocol["parent_run_id"],
        "source_parent_hold_preserved": True,
        "electronic_settings": protocol["shared_electronic_settings"],
        "mechanical_reparse_only": True,
        "source_result_file": str(old_path),
    }
    write_result(pathlib.Path(args.out) / f"ATOM_{tag}_RECOVERY_RESULT.json", result)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--mode", choices=["atom", "h2"], required=True)
    ap.add_argument("--basis", choices=["70", "80"], required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    protocol = load_json(args.protocol)
    if protocol["status"] != "FROZEN_AFTER_V0_1_HOLD_BEFORE_V0_2_RECOVERY_RESULTS":
        raise SystemExit("SCIENTIFIC_HOLD: recovery protocol is not frozen v0.2")
    if not protocol["non_retroactivity"]["v0_1_hold_remains_valid"]:
        raise SystemExit("SCIENTIFIC_HOLD: v0.1 HOLD preservation firewall disabled")
    if args.mode == "h2":
        reparse_h2(args, protocol)
    else:
        reparse_atom(args, protocol)

if __name__ == "__main__":
    main()
