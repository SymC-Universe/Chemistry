#!/usr/bin/env python3
"""
PowerCell local replication/continuation for shared-H qualification recovery v0.2.

Mechanical execution only:
- one QE process at a time;
- clean QE CONTROL.max_seconds chunks;
- v0.1 HOLD is never overwritten;
- v0.2 scientific thresholds and electronic settings are read from the frozen protocol;
- incomplete wall-clock budget => INCOMPLETE_SAFE_CHECKPOINT, never PASS/HOLD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG
QE_SHA256 = "2b1ede22d276b1d4dab3e31212f306e88ae57e00f33ce6b532b849493a457855"
PSEUDO_MD5 = "39a7d154f04d65093d603a437119a874"


def digest(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def total_energy_ev(txt: str):
    vals = re.findall(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry", txt)
    return float(vals[-1]) * RY_TO_EV if vals else None


def final_positions(txt: str, nat: int):
    idx = txt.rfind("Begin final coordinates")
    chunk = txt[idx:] if idx >= 0 else txt
    matches = list(re.finditer(r"ATOMIC_POSITIONS\s*\(angstrom\)\s*\n", chunk))
    if not matches:
        return None
    pts = []
    for line in chunk[matches[-1].end():].splitlines():
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


def max_force_ev_ang(txt: str, nat: int):
    vals = re.findall(
        r"force\s*=\s*([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)",
        txt,
    )
    if len(vals) < nat:
        return None
    block = vals[-nat:]
    return max(
        math.sqrt(sum(float(x) ** 2 for x in v)) * RY_BOHR_TO_EV_ANG
        for v in block
    )


def bond_length(pts):
    return math.sqrt(sum((pts[0][i] - pts[1][i]) ** 2 for i in range(3)))


def atom_input(pseudo_name, ew, er, cell, prefix, settings, max_seconds):
    c = cell / 2.0
    return f"""&CONTROL
 calculation='scf',
 restart_mode='restart',
 prefix='{prefix}',
 pseudo_dir='.',
 outdir='./qe_tmp',
 tstress=.true.,
 tprnfor=.true.,
 disk_io='medium',
 max_seconds={max_seconds},
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


def h2_input(pseudo_name, ew, er, cell, pts, prefix, settings, h2, max_seconds, restart):
    p1, p2 = pts
    return f"""&CONTROL
 calculation='relax',
 restart_mode='{restart}',
 prefix='{prefix}',
 pseudo_dir='.',
 outdir='./qe_tmp',
 tstress=.true.,
 tprnfor=.true.,
 disk_io='medium',
 max_seconds={max_seconds},
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


def qe_checkpoint_ok(case_dir: Path, prefix: str) -> bool:
    save = case_dir / "qe_tmp" / f"{prefix}.save"
    xml = save / "data-file-schema.xml"
    return save.is_dir() and xml.is_file() and xml.stat().st_size > 0


def checkpoint_manifest(case_dir: Path, prefix: str, out_path: Path):
    save = case_dir / "qe_tmp" / f"{prefix}.save"
    rows = []
    if save.is_dir():
        for p in sorted(x for x in save.rglob("*") if x.is_file()):
            rows.append({"path": str(p.relative_to(case_dir)), "sha256": digest(p), "bytes": p.stat().st_size})
    write_json(out_path, {"prefix": prefix, "files": rows})


def run_qe(pw: Path, case_dir: Path, name: str, inp_text: str, safety_timeout: int):
    inp = case_dir / f"{name}.in"
    out = case_dir / f"{name}.out"
    inp.write_text(inp_text, encoding="utf-8")
    started = time.time()
    with inp.open("rb") as fin, out.open("wb") as fout:
        try:
            proc = subprocess.run(
                [str(pw)],
                stdin=fin,
                stdout=fout,
                stderr=subprocess.STDOUT,
                cwd=case_dir,
                timeout=safety_timeout,
            )
            rc = proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            rc = 124
            timed_out = True
    elapsed = time.time() - started
    txt = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
    return rc, timed_out, elapsed, txt, inp, out


def initialize_atom_checkpoint(source_root: Path, work: Path, tag: str, pseudo: Path):
    case = work / f"atom_{tag}"
    case.mkdir(parents=True, exist_ok=True)
    prefix = f"H_atom_{tag}"
    local_save = case / "qe_tmp" / f"{prefix}.save"
    if not local_save.exists():
        src = source_root / f"atom_{tag}" / "qe_tmp" / f"{prefix}.save"
        if not src.is_dir():
            raise RuntimeError(f"Missing parent atom checkpoint: {src}")
        (case / "qe_tmp").mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, local_save)
    shutil.copy2(pseudo, case / pseudo.name)
    return case, prefix


def parent_h2_geometry(source_root: Path, tag: str, cell: float):
    src_out = source_root / f"h2_{tag}" / f"H2_{tag}.out"
    if src_out.is_file():
        pts = final_positions(src_out.read_text(encoding="utf-8", errors="replace"), 2)
        if pts:
            return pts, str(src_out)
    # v0.1 result documented an unchanged 0.750 A bond. This fallback is the exact
    # frozen starting geometry, used only when the raw source output is not yet local.
    c = cell / 2.0
    bond = 0.75
    return [[c, c, c - bond / 2], [c, c, c + bond / 2]], "frozen_v0.1_0.750A_geometry_fallback"


def load_case_state(path: Path, kind: str, tag: str):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "schema": "symc-powercell-shared-h-v02-case-state-v0.1",
        "kind": kind,
        "basis_tag": tag,
        "status": "NOT_STARTED",
        "chunks": [],
        "terminal": False,
    }


def choose_chunk_seconds(deadline: float):
    remaining = deadline - time.time()
    # Keep five minutes outside QE for manifest/result writes and clean exit.
    usable = int(remaining - 300)
    if usable < 600:
        return None
    return min(3600, usable)


def run_atom_case(protocol, pw, pseudo, source_root, work, tag, deadline):
    case_protocol = protocol["basis_cases"][tag]
    settings = protocol["shared_electronic_settings"]
    max_chunks = int(protocol["atom_recovery"]["max_additional_segments"])
    case, prefix = initialize_atom_checkpoint(source_root, work, tag, pseudo)
    state_path = case / "POWER_CELL_CASE_STATE.json"
    state = load_case_state(state_path, "atom", tag)
    state["source_parent_run_id"] = protocol["parent_run_id"]
    state["parent_hold_preserved"] = True
    if state.get("terminal"):
        return state

    while len(state["chunks"]) < max_chunks:
        sec = choose_chunk_seconds(deadline)
        if sec is None:
            state["status"] = "INCOMPLETE_SAFE_CHECKPOINT"
            break
        idx = len(state["chunks"]) + 1
        name = f"H_atom_{tag}_powercell_chunk{idx}"
        rc, timed_out, elapsed, txt, inp, out = run_qe(
            pw,
            case,
            name,
            atom_input(
                pseudo.name,
                case_protocol["ecutwfc_ry"],
                case_protocol["ecutrho_ry"],
                18.0,
                prefix,
                settings,
                sec,
            ),
            safety_timeout=sec + 1200,
        )
        checkpoint = qe_checkpoint_ok(case, prefix)
        conv = "convergence has been achieved" in txt.lower()
        not_conv = "convergence not achieved" in txt.lower()
        done = "JOB DONE." in txt
        energy = total_energy_ev(txt)
        chunk = {
            "chunk": idx,
            "qe_max_seconds": sec,
            "elapsed_s": elapsed,
            "returncode": rc,
            "safety_timeout": timed_out,
            "job_done": done,
            "converged": conv,
            "convergence_not_achieved": not_conv,
            "checkpoint_valid": checkpoint,
            "energy_ev": energy,
            "input_sha256": digest(inp),
            "output_sha256": digest(out) if out.exists() else None,
        }
        state["chunks"].append(chunk)
        checkpoint_manifest(case, prefix, case / f"CHECKPOINT_MANIFEST_chunk{idx}.json")

        if timed_out or rc != 0:
            state["status"] = "MECHANICAL_HOLD"
            state["terminal"] = True
            state["reason"] = "QE exceeded safety timeout or returned nonzero"
            break
        if conv and done and energy is not None:
            state["status"] = "ATOM_RECOVERY_CONVERGED"
            state["terminal"] = True
            state["energy_ev"] = energy
            break
        if not checkpoint:
            state["status"] = "MECHANICAL_HOLD"
            state["terminal"] = True
            state["reason"] = "No valid exact-restart checkpoint after chunk"
            break
        state["status"] = "CHECKPOINT_READY"
        write_json(state_path, state)

    if not state["terminal"] and len(state["chunks"]) >= max_chunks:
        state["status"] = "ATOM_RECOVERY_HOLD"
        state["terminal"] = True
        state["reason"] = "Frozen v0.2 additional-segment limit exhausted without electronic convergence"
    write_json(state_path, state)
    return state


def run_h2_case(protocol, pw, pseudo, source_root, work, tag, deadline):
    case_protocol = protocol["basis_cases"][tag]
    settings = protocol["shared_electronic_settings"]
    h2p = protocol["h2_recovery"]
    max_chunks = int(h2p["max_segments"])
    case = work / f"h2_{tag}"
    case.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pseudo, case / pseudo.name)
    prefix = f"H2_powercell_{tag}"
    state_path = case / "POWER_CELL_CASE_STATE.json"
    state = load_case_state(state_path, "h2", tag)
    state["source_parent_run_id"] = protocol["parent_run_id"]
    state["parent_hold_preserved"] = True
    if state.get("terminal"):
        return state

    cell = 18.0
    if state["chunks"]:
        last_out = case / state["chunks"][-1]["output"]
        pts = final_positions(last_out.read_text(encoding="utf-8", errors="replace"), 2) if last_out.exists() else None
        if not pts:
            pts, geom_source = parent_h2_geometry(source_root, tag, cell)
        else:
            geom_source = str(last_out)
        restart = "restart" if qe_checkpoint_ok(case, prefix) else "from_scratch"
    else:
        pts, geom_source = parent_h2_geometry(source_root, tag, cell)
        restart = "from_scratch"
        state["initial_geometry_source"] = geom_source

    while len(state["chunks"]) < max_chunks:
        sec = choose_chunk_seconds(deadline)
        if sec is None:
            state["status"] = "INCOMPLETE_SAFE_CHECKPOINT"
            break
        idx = len(state["chunks"]) + 1
        name = f"H2_{tag}_powercell_chunk{idx}"
        rc, timed_out, elapsed, txt, inp, out = run_qe(
            pw,
            case,
            name,
            h2_input(
                pseudo.name,
                case_protocol["ecutwfc_ry"],
                case_protocol["ecutrho_ry"],
                cell,
                pts,
                prefix,
                settings,
                h2p,
                sec,
                restart,
            ),
            safety_timeout=sec + 1200,
        )
        checkpoint = qe_checkpoint_ok(case, prefix)
        conv = "convergence has been achieved" in txt.lower()
        bfgs = "bfgs converged" in txt.lower()
        done = "JOB DONE." in txt
        energy = total_energy_ev(txt)
        new_pts = final_positions(txt, 2)
        if new_pts:
            pts = new_pts
        force = max_force_ev_ang(txt, 2)
        bond = bond_length(pts) if pts else None
        local_pass = (
            rc == 0
            and not timed_out
            and done
            and conv
            and bfgs
            and energy is not None
            and force is not None
            and force <= protocol["acceptance"]["max_h2_final_force_ev_per_angstrom"]
        )
        chunk = {
            "chunk": idx,
            "qe_max_seconds": sec,
            "elapsed_s": elapsed,
            "returncode": rc,
            "safety_timeout": timed_out,
            "job_done": done,
            "electronic_converged": conv,
            "bfgs_converged": bfgs,
            "checkpoint_valid": checkpoint,
            "energy_ev": energy,
            "bond_angstrom": bond,
            "max_force_ev_per_angstrom": force,
            "input_sha256": digest(inp),
            "output_sha256": digest(out) if out.exists() else None,
            "output": out.name,
        }
        state["chunks"].append(chunk)
        if checkpoint:
            checkpoint_manifest(case, prefix, case / f"CHECKPOINT_MANIFEST_chunk{idx}.json")

        if timed_out or rc != 0:
            state["status"] = "MECHANICAL_HOLD"
            state["terminal"] = True
            state["reason"] = "QE exceeded safety timeout or returned nonzero"
            break
        if local_pass:
            state["status"] = "H2_RECOVERY_LOCAL_PASS"
            state["terminal"] = True
            state["energy_ev"] = energy
            state["bond_angstrom"] = bond
            state["max_force_ev_per_angstrom"] = force
            break
        if not checkpoint and not done:
            state["status"] = "MECHANICAL_HOLD"
            state["terminal"] = True
            state["reason"] = "No valid restart checkpoint after incomplete H2 chunk"
            break
        state["status"] = "CHECKPOINT_READY"
        restart = "restart" if checkpoint else "from_scratch"
        write_json(state_path, state)

    if not state["terminal"] and len(state["chunks"]) >= max_chunks:
        state["status"] = "H2_RECOVERY_HOLD"
        state["terminal"] = True
        state["reason"] = "Frozen v0.2 H2 segment limit exhausted without satisfying unchanged force/convergence gate"
    write_json(state_path, state)
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--pw", required=True)
    ap.add_argument("--pseudo", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--hours", type=float, default=5.75)
    ap.add_argument(
        "--order",
        default="h2-70,h2-80,atom-70,atom-80",
        help="Comma-separated local single-QE queue",
    )
    args = ap.parse_args()

    protocol = json.load(open(args.protocol, encoding="utf-8"))
    if protocol["status"] != "FROZEN_AFTER_V0_1_HOLD_BEFORE_V0_2_RECOVERY_RESULTS":
        raise SystemExit("Protocol is not the frozen v0.2 recovery contract")
    if not protocol["non_retroactivity"]["v0_1_hold_remains_valid"]:
        raise SystemExit("v0.1 HOLD preservation firewall is not active")

    pw = Path(args.pw).resolve()
    pseudo = Path(args.pseudo).resolve()
    source_root = Path(args.source_root).resolve()
    work = Path(args.work_root).resolve()
    work.mkdir(parents=True, exist_ok=True)

    if digest(pw) != QE_SHA256:
        raise SystemExit("PowerCell pw.x SHA-256 mismatch")
    if digest(pseudo, "md5") != PSEUDO_MD5:
        raise SystemExit("H pseudopotential MD5 mismatch")

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"

    start = time.time()
    deadline = start + args.hours * 3600.0
    summary = {
        "schema": "symc-powercell-shared-h-v02-session-v0.1",
        "started_epoch": start,
        "budget_hours": args.hours,
        "pw_sha256": digest(pw),
        "pseudo_md5": digest(pseudo, "md5"),
        "protocol": str(Path(args.protocol).resolve()),
        "source_root": str(source_root),
        "parent_v0_1_hold_preserved": True,
        "queue": args.order.split(","),
        "cases": {},
    }
    write_json(work / "POWER_CELL_SESSION.json", summary)

    for item in summary["queue"]:
        if choose_chunk_seconds(deadline) is None:
            break
        kind, tag = item.strip().split("-", 1)
        print(f"\n=== POWERCELL START {kind.upper()} {tag} ===", flush=True)
        if kind == "atom":
            state = run_atom_case(protocol, pw, pseudo, source_root, work, tag, deadline)
        elif kind == "h2":
            state = run_h2_case(protocol, pw, pseudo, source_root, work, tag, deadline)
        else:
            raise SystemExit(f"Unknown queue item: {item}")
        summary["cases"][item] = state
        summary["elapsed_s"] = time.time() - start
        summary["remaining_s"] = max(0.0, deadline - time.time())
        write_json(work / "POWER_CELL_SESSION.json", summary)
        print(f"=== POWERCELL END {item}: {state['status']} ===", flush=True)

    summary["finished_epoch"] = time.time()
    summary["elapsed_s"] = summary["finished_epoch"] - start
    summary["remaining_s"] = max(0.0, deadline - summary["finished_epoch"])
    summary["session_status"] = (
        "BUDGET_EXIT_WITH_SAFE_STATE"
        if any(not c.get("terminal", False) for c in summary["cases"].values())
        or len(summary["cases"]) < len(summary["queue"])
        else "QUEUE_TERMINAL"
    )
    write_json(work / "POWER_CELL_SESSION.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
