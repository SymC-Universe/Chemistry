#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from system3_clean_ru0001_numerical_v1 import execute_qe, load, slab_input, write


def find_one(root: str | Path, name: str) -> Path:
    hits = list(Path(root).rglob(name))
    if len(hits) != 1:
        raise SystemExit(f"MECHANICAL_HOLD: expected exactly one {name}, found {len(hits)}")
    return hits[0]


def load_contract(protocol_path, source_root, bulk_adjudication_path):
    p = load(protocol_path)
    if p["status"] != "FROZEN_BEFORE_EXTENSION_RESULTS":
        raise SystemExit("SCIENTIFIC_HOLD: extension protocol not frozen")
    if any(bool(v) for v in p["evidence_firewall"].values()):
        raise SystemExit("SCIENTIFIC_HOLD: evidence firewall is open")
    src = load(find_one(source_root, "SYSTEM3_CLEAN_SURFACE_NUMERICAL_RESULT.json"))
    se = p["source_evidence"]
    if src.get("status") != se["required_source_status"] or src.get("failed_gate") != se["required_failed_gate"]:
        raise SystemExit("SCIENTIFIC_HOLD: source result identity/status mismatch")
    adj = load(bulk_adjudication_path)
    fm = p["frozen_method"]
    sel = adj["selected_numerical_settings"]
    fit = adj["structural_fit"]
    checks = [
        int(sel["ecutwfc_ry"]) == int(fm["ecutwfc_ry"]),
        int(sel["ecutrho_ry"]) == int(fm["ecutrho_ry"]),
        abs(float(fit["a_angstrom"]) - float(fm["bulk_a_angstrom"])) < 1e-12,
        abs(float(fit["c_angstrom"]) - float(fm["bulk_c_angstrom"])) < 1e-12,
    ]
    if not all(checks):
        raise SystemExit("SCIENTIFIC_HOLD: frozen bulk settings mismatch")
    return p, src, adj


def source_layer_rows(src):
    rows = {}
    for r in src.get("raw_records", []):
        if r.get("kind") == "slab_scf" and r.get("first_stage_requested") == "layers":
            rows[int(r["layers"])] = {
                "layers": int(r["layers"]),
                "surface_excess_ev_per_surface_atom": float(r["surface_excess_ev_per_surface_atom"]),
                "origin": "source_run",
            }

    # The source convergence ladder reuses the already selected L7 slab from the
    # k-mesh/vacuum stages rather than recomputing L7 in the later layer stage.
    # Recover that exact selected baseline record when it is therefore absent
    # from first_stage_requested == "layers". This changes only record routing;
    # no energy, threshold, geometry, method, or acceptance rule is changed.
    selected_kmesh = src.get("selected_kmesh")
    selected_vacuum = src.get("selected_total_vacuum_angstrom")
    if selected_kmesh and selected_vacuum is not None:
        candidates = []
        for r in src.get("raw_records", []):
            if r.get("kind") != "slab_scf":
                continue
            if list(r.get("kmesh") or []) != [int(x) for x in selected_kmesh]:
                continue
            if abs(float(r.get("total_vacuum_angstrom")) - float(selected_vacuum)) > 1e-12:
                continue
            candidates.append(r)
        by_layer = {}
        for r in candidates:
            by_layer.setdefault(int(r["layers"]), []).append(r)
        for layer, matches in by_layer.items():
            if layer in rows:
                continue
            if len(matches) != 1:
                raise SystemExit(
                    f"MECHANICAL_HOLD: selected source condition has {len(matches)} records for L{layer}"
                )
            r = matches[0]
            rows[layer] = {
                "layers": layer,
                "surface_excess_ev_per_surface_atom": float(r["surface_excess_ev_per_surface_atom"]),
                "origin": "source_selected_baseline",
            }
    return [rows[k] for k in sorted(rows)]


def suffix_decision(rows, tol, minimum_layers=7):
    rows = sorted(rows, key=lambda r: int(r["layers"]))
    ref = float(rows[-1]["surface_excess_ev_per_surface_atom"])
    deltas = [abs(float(r["surface_excess_ev_per_surface_atom"]) - ref) for r in rows]
    selected = None
    for i, r in enumerate(rows[:-1]):
        if int(r["layers"]) < int(minimum_layers):
            continue
        if all(d <= tol for d in deltas[i:]):
            selected = int(r["layers"])
            break
    return selected, deltas


def run_case(args):
    p, src, adj = load_contract(args.protocol, args.source_root, args.bulk_adjudication)
    layer = int(args.layers)
    allowed = [int(x) for x in p["extension"]["new_layers"]]
    if layer not in allowed:
        raise SystemExit(f"SCIENTIFIC_HOLD: layer {layer} not prospectively authorized")
    kmesh = src.get("selected_kmesh")
    vacuum = src.get("selected_total_vacuum_angstrom")
    if not kmesh or vacuum is None:
        raise SystemExit("SCIENTIFIC_HOLD: source HOLD lacks selected kmesh/vacuum")
    fm = p["frozen_method"]
    ebulk = float(src["fresh_bulk_reference"]["energy_ev_per_atom"])
    pseudo_dir = Path(args.pseudo_dir).resolve()
    tag = f"ru0001_extension_L{layer}"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    txt = slab_input(
        float(fm["bulk_a_angstrom"]), float(fm["bulk_c_angstrom"]), layer, float(vacuum),
        int(fm["ecutwfc_ry"]), int(fm["ecutrho_ry"]), tuple(int(x) for x in kmesh),
        pseudo_dir, "__OUTDIR__", tag,
    )
    row = execute_qe(out / "qe", Path(args.pw).resolve(), txt, int(p["runtime"]["per_scf_timeout_seconds"]), tag)
    gamma = (float(row["energy_ev"]) - layer * ebulk) / 2.0
    result = {
        "schema": "h-ru0001-layer-extension-case-v0.1",
        "status": "VALID_EXTENSION_CASE",
        "layers": layer,
        "surface_excess_ev_per_surface_atom": gamma,
        "energy_ev": float(row["energy_ev"]),
        "source_bulk_energy_ev_per_atom": ebulk,
        "selected_total_vacuum_angstrom": float(vacuum),
        "selected_kmesh": [int(x) for x in kmesh],
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "raw_execution": row,
    }
    write(out / f"RU_L{layer}_EXTENSION_RESULT.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


def adjudicate(args):
    p, src, _ = load_contract(args.protocol, args.source_root, args.bulk_adjudication)
    old = source_layer_rows(src)
    expected_old = [int(x) for x in p["source_evidence"]["prior_layers"]]
    if [r["layers"] for r in old] != expected_old:
        raise SystemExit("SCIENTIFIC_HOLD: source layer ladder does not match frozen extension contract")
    # Reproduce the already-declared source deltas before using it as the extension base.
    _, source_deltas = suffix_decision(old, float(p["frozen_method"]["absolute_surface_excess_tolerance_ev_per_surface_atom"]))
    declared = [float(x) for x in p["source_evidence"]["prior_layer_deltas_to_terminal_ev_per_surface_atom"]]
    if len(source_deltas) != len(declared) or any(abs(a-b) > 1e-10 for a,b in zip(source_deltas, declared)):
        raise SystemExit("SCIENTIFIC_HOLD: source layer values fail frozen provenance cross-check")
    new = []
    for layer in p["extension"]["new_layers"]:
        f = find_one(args.case_root, f"RU_L{int(layer)}_EXTENSION_RESULT.json")
        r = load(f)
        if r.get("status") != "VALID_EXTENSION_CASE" or int(r["layers"]) != int(layer):
            raise SystemExit("SCIENTIFIC_HOLD: invalid extension case record")
        new.append({"layers": int(layer), "surface_excess_ev_per_surface_atom": float(r["surface_excess_ev_per_surface_atom"]), "origin": "extension"})
    rows = sorted(old + new, key=lambda r: r["layers"])
    expected = expected_old + [int(x) for x in p["extension"]["new_layers"]]
    if [r["layers"] for r in rows] != expected:
        raise SystemExit("SCIENTIFIC_HOLD: complete layer ladder mismatch")
    tol = float(p["frozen_method"]["absolute_surface_excess_tolerance_ev_per_surface_atom"])
    selected, deltas = suffix_decision(rows, tol, int(p["extension"]["minimum_eligible_layers"]))
    passed = selected is not None
    result = {
        "schema": "h-ru0001-layer-extension-adjudication-v0.1",
        "status": p["decision"]["pass_status"] if passed else p["decision"]["hold_status"],
        "selected_layers": selected,
        "terminal_reference_layers": int(p["extension"]["terminal_reference_layers"]),
        "tolerance_ev_per_surface_atom": tol,
        "layer_rows": rows,
        "deltas_to_L19_ev_per_surface_atom": deltas,
        "next_gate": p["decision"]["pass_next_gate"] if passed else p["decision"]["hold_next_gate"],
        "scientific_settings_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
    }
    write(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--protocol", required=True)
    common.add_argument("--source-root", required=True)
    common.add_argument("--bulk-adjudication", required=True)
    r = sub.add_parser("run-case", parents=[common])
    r.add_argument("--layers", required=True, type=int)
    r.add_argument("--pw", required=True)
    r.add_argument("--pseudo-dir", required=True)
    r.add_argument("--out", required=True)
    a = sub.add_parser("adjudicate", parents=[common])
    a.add_argument("--case-root", required=True)
    a.add_argument("--out", required=True)
    args = ap.parse_args()
    run_case(args) if args.cmd == "run-case" else adjudicate(args)


if __name__ == "__main__":
    main()
