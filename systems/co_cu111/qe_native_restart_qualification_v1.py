#!/usr/bin/env python3
"""Non-evidentiary two-job qualification for Quantum ESPRESSO native restart.

This does not generate CO/Cu(111) scientific evidence. It exercises the exact
Stage A pw.x binary with a small Cu(111) relax fixture, forces a clean QE stop
through CONTROL.max_seconds, persists and verifies the native restart state,
then compares a fresh-runner restart against an uninterrupted reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

RY_TO_EV = 13.605693122994
BOHR_TO_ANG = 0.529177210903
RY_BOHR_TO_EV_ANG = RY_TO_EV / BOHR_TO_ANG
ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([-+0-9.Ee]+)\s+Ry")
ATOM_FORCE_RE = re.compile(
    r"atom\s+(\d+)\s+type\s+\d+\s+force\s*=\s*"
    r"([-+0-9.Ee]+)\s+([-+0-9.Ee]+)\s+([-+0-9.Ee]+)"
)
A0 = 3.632355796707377
PW_SHA256 = "2b1ede22d276b1d4dab3e31212f306e88ae57e00f33ce6b532b849493a457855"
CU_PSEUDO = "Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf"
CU_PSEUDO_SHA256 = "b31028b2bae60cd9903260715a49b4c6d2b6dc654558c87023fa5206e427a16d"
PREFIX = "qe_restart_qual"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fixture_geometry() -> tuple[list[list[float]], list[tuple[float, float, float, int, int, int]]]:
    axy = A0 / math.sqrt(2.0)
    d111 = A0 / math.sqrt(3.0)
    layers = 5
    vacuum = 18.0
    cell_z = (layers - 1) * d111 + vacuum
    a1 = [axy, 0.0, 0.0]
    a2 = [0.5 * axy, math.sqrt(3.0) * 0.5 * axy, 0.0]
    cell = [a1, a2, [0.0, 0.0, cell_z]]
    midpoint = 2.0
    offsets = {0: 0.04, 1: 0.01, 3: -0.01, 4: -0.04}
    atoms = []
    for layer in range(layers):
        shift = (layer % 3) / 3.0
        x = shift * a1[0] + shift * a2[0]
        y = shift * a1[1] + shift * a2[1]
        z = (layer - midpoint) * d111 + offsets.get(layer, 0.0)
        movable = 1 if layer in (0, 1, 3, 4) else 0
        atoms.append((x, y, z, 0, 0, movable))
    return cell, atoms


def make_input(restart_mode: str, max_seconds: float | None) -> str:
    cell, atoms = fixture_geometry()
    forc_ry_bohr = 0.02 / RY_BOHR_TO_EV_ANG
    lines = [
        "&CONTROL",
        " calculation='relax',",
        f" restart_mode='{restart_mode}',",
        f" prefix='{PREFIX}',",
        " pseudo_dir='./engine/pseudos',",
        " outdir='./restart_state',",
        " disk_io='medium',",
        " tprnfor=.true.,",
        " tstress=.true.,",
        " verbosity='high',",
        f" forc_conv_thr={forc_ry_bohr:.12g},",
    ]
    if max_seconds is not None:
        lines.append(f" max_seconds={float(max_seconds):.6f},")
    lines += [
        "/",
        "&SYSTEM",
        " ibrav=0,",
        " nat=5,",
        " ntyp=1,",
        " ecutwfc=90,",
        " ecutrho=900,",
        " input_dft='PBE',",
        " occupations='smearing',",
        " smearing='mv',",
        " degauss=0.02,",
        " assume_isolated='esm',",
        " esm_bc='bc1',",
        "/",
        "&ELECTRONS",
        " conv_thr=1.0d-10,",
        " mixing_beta=0.3,",
        " electron_maxstep=200,",
        "/",
        "&IONS",
        " ion_dynamics='bfgs',",
        "/",
        "ATOMIC_SPECIES",
        f"Cu 63.546000 {CU_PSEUDO}",
        "CELL_PARAMETERS angstrom",
    ]
    lines += [" ".join(f"{x:.12f}" for x in row) for row in cell]
    lines.append("ATOMIC_POSITIONS angstrom")
    for x, y, z, fx, fy, fz in atoms:
        lines.append(f"Cu {x:.12f} {y:.12f} {z:.12f} {fx} {fy} {fz}")
    lines += ["K_POINTS automatic", "4 4 1 0 0 0"]
    return "\n".join(lines) + "\n"


def complete_force_blocks(text: str, nat: int = 5) -> list[list[tuple[float, float, float]]]:
    lines = text.splitlines()
    out: list[list[tuple[float, float, float]]] = []
    for i, line in enumerate(lines):
        if "Forces acting on atoms" not in line:
            continue
        rows: list[tuple[float, float, float]] = []
        expected = 1
        for row in lines[i + 1:]:
            if "The non-local contrib." in row or "Total force =" in row:
                break
            m = ATOM_FORCE_RE.search(row)
            if not m:
                continue
            if int(m.group(1)) != expected:
                rows = []
                break
            rows.append((float(m.group(2)), float(m.group(3)), float(m.group(4))))
            expected += 1
            if len(rows) == nat:
                break
        if len(rows) == nat:
            out.append(rows)
    return out


def recursive_manifest(root: Path) -> dict:
    files = []
    total = 0
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel = p.relative_to(root).as_posix()
        if rel in {"checkpoint_manifest.json", "checkpoint_manifest.sha256"}:
            continue
        size = p.stat().st_size
        total += size
        files.append({"path": rel, "sha256": sha256(p), "size_bytes": size})
    return {"schema": "qe-native-restart-recursive-manifest-v0.1", "file_count": len(files), "size_bytes": total, "files": files}


def cmd_write(args: argparse.Namespace) -> None:
    mode = args.mode
    if mode not in {"reference", "checkpoint", "resume"}:
        raise SystemExit("bad mode")
    restart = "restart" if mode == "resume" else "from_scratch"
    max_seconds = float(args.max_seconds) if mode == "checkpoint" else None
    Path(args.out).write_text(make_input(restart, max_seconds))


def cmd_verify_binary(args: argparse.Namespace) -> None:
    pw = Path(args.pw)
    pseudo = Path(args.pseudo)
    if sha256(pw) != PW_SHA256:
        raise SystemExit("QUALIFICATION_HOLD: pw.x hash mismatch")
    if sha256(pseudo) != CU_PSEUDO_SHA256:
        raise SystemExit("QUALIFICATION_HOLD: Cu pseudopotential hash mismatch")
    print("EXACT_STAGE_A_ENGINE_VERIFIED")


def cmd_check_stop(args: argparse.Namespace) -> None:
    text = Path(args.output).read_text(errors="replace")
    save = Path(args.restart_root) / f"{PREFIX}.save"
    if "Maximum CPU time exceeded" not in text:
        raise SystemExit("QUALIFICATION_HOLD: fixture did not exercise max_seconds clean stop")
    if not save.is_dir():
        raise SystemExit("QUALIFICATION_HOLD: QE save directory missing after clean stop")
    if not (save / "data-file-schema.xml").is_file():
        raise SystemExit("QUALIFICATION_HOLD: QE data-file-schema.xml missing after clean stop")
    print("QE_CLEAN_STOP_AND_SAVE_VERIFIED")


def cmd_manifest(args: argparse.Namespace) -> None:
    root = Path(args.root)
    m = recursive_manifest(root)
    out = Path(args.out)
    out.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")
    Path(str(out) + ".sha256").write_text(sha256(out) + "  " + out.name + "\n")
    print(json.dumps({"file_count": m["file_count"], "size_bytes": m["size_bytes"], "manifest_sha256": sha256(out)}, sort_keys=True))


def cmd_verify_manifest(args: argparse.Namespace) -> None:
    root = Path(args.root)
    expected = json.loads(Path(args.manifest).read_text())
    actual = recursive_manifest(root)
    if expected != actual:
        raise SystemExit("QUALIFICATION_HOLD: recursive restart manifest mismatch")
    print("RESTART_MANIFEST_VERIFIED")


def last_energy_ev(text: str) -> float:
    vals = ENERGY_RE.findall(text)
    if not vals:
        raise SystemExit("QUALIFICATION_HOLD: no total energy found")
    return float(vals[-1]) * RY_TO_EV


def cmd_compare(args: argparse.Namespace) -> None:
    ref_text = Path(args.reference).read_text(errors="replace")
    resumed_text = Path(args.resumed).read_text(errors="replace")
    if "JOB DONE." not in ref_text or "JOB DONE." not in resumed_text:
        raise SystemExit("QUALIFICATION_HOLD: reference or restarted fixture did not finish")
    ref_e = last_energy_ev(ref_text)
    res_e = last_energy_ev(resumed_text)
    ref_blocks = complete_force_blocks(ref_text)
    res_blocks = complete_force_blocks(resumed_text)
    if not ref_blocks or not res_blocks:
        raise SystemExit("QUALIFICATION_HOLD: missing final force block")
    force_delta = max(
        abs(a - b) * RY_BOHR_TO_EV_ANG
        for ra, rb in zip(ref_blocks[-1], res_blocks[-1])
        for a, b in zip(ra, rb)
    )
    energy_delta = abs(ref_e - res_e)
    passed = energy_delta <= 0.0001 and force_delta <= 0.0001
    result = {
        "schema": "co-cu111-qe-native-restart-qualification-result-v0.1",
        "status": "PASS" if passed else "MECHANICAL_CHECKPOINT_HOLD",
        "fixture_is_non_evidentiary": True,
        "reference_energy_ev": ref_e,
        "restarted_energy_ev": res_e,
        "energy_absolute_difference_ev": energy_delta,
        "energy_tolerance_ev": 0.0001,
        "force_component_absolute_difference_max_ev_per_angstrom": force_delta,
        "force_tolerance_ev_per_angstrom": 0.0001,
        "exact_stage_a_pw_x_sha256": PW_SHA256,
        "direct_one_rank": True,
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit("QUALIFICATION_HOLD: native restart parity failed")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("write-input")
    sp.add_argument("--mode", required=True)
    sp.add_argument("--max-seconds", type=float, default=15.0)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_write)
    sp = sub.add_parser("verify-binary")
    sp.add_argument("--pw", required=True)
    sp.add_argument("--pseudo", required=True)
    sp.set_defaults(func=cmd_verify_binary)
    sp = sub.add_parser("check-clean-stop")
    sp.add_argument("--output", required=True)
    sp.add_argument("--restart-root", required=True)
    sp.set_defaults(func=cmd_check_stop)
    sp = sub.add_parser("manifest")
    sp.add_argument("--root", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_manifest)
    sp = sub.add_parser("verify-manifest")
    sp.add_argument("--root", required=True)
    sp.add_argument("--manifest", required=True)
    sp.set_defaults(func=cmd_verify_manifest)
    sp = sub.add_parser("compare")
    sp.add_argument("--reference", required=True)
    sp.add_argument("--resumed", required=True)
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_compare)
    return ap


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
