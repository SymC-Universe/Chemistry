#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any

PREFIX = "co_cu111_clean_l15_extension"
NATIVE_SCHEMA = "co-cu111-l15-native-restart-chunk-v0.1"
DEPLOY_SCHEMA = "co-cu111-l15-native-restart-deployment-v0.1"
QUAL_SCHEMA = "co-cu111-qe-native-restart-qualification-result-v0.1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    x = json.loads(path.read_text())
    if not isinstance(x, dict):
        raise SystemExit(f"MECHANICAL_CHECKPOINT_HOLD: JSON root is not object: {path}")
    return x


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def find_one(root: Path, name: str) -> Path:
    xs = [p for p in root.rglob(name) if p.is_file()]
    if len(xs) != 1:
        raise SystemExit(f"MECHANICAL_CHECKPOINT_HOLD: expected one {name} under {root}, found {len(xs)}")
    return xs[0]


def recursive_manifest(root: Path) -> dict[str, Any]:
    rows = []
    total = 0
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        total += size
        rows.append({"path": rel, "sha256": sha256(p), "size_bytes": size})
    return {"schema": "qe-native-restart-recursive-manifest-v0.1", "file_count": len(rows), "size_bytes": total, "files": rows}


def verify_manifest(root: Path, manifest_path: Path) -> dict[str, Any]:
    exp = load_json(manifest_path)
    got = recursive_manifest(root)
    if exp != got:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: restart-state recursive manifest mismatch")
    return got


def imports():
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import pbe_surface_convergence_extension_v1 as ext  # type: ignore
    return ext


def inject_restart(control_text: str, restart_mode: str, max_seconds: int) -> str:
    out = []
    inserted = False
    for line in control_text.splitlines():
        out.append(line)
        if line.strip().startswith("calculation="):
            out += [
                f" restart_mode='{restart_mode}',",
                " disk_io='medium',",
                f" max_seconds={int(max_seconds)},",
            ]
            inserted = True
    if not inserted:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: failed to inject native restart controls")
    return "\n".join(out) + "\n"


def qualification(deploy: dict[str, Any], root: Path) -> tuple[dict[str, Any], Path]:
    path = find_one(root, "QE_NATIVE_RESTART_QUALIFICATION_RESULT.json")
    q = load_json(path)
    frozen = deploy["qualification"]
    if q.get("schema") != QUAL_SCHEMA or q.get("status") != frozen["required_status"]:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: native restart qualification is not PASS")
    if abs(float(q["energy_absolute_difference_ev"]) - float(frozen["energy_absolute_difference_ev"])) > 1e-15:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: restart qualification energy drift")
    if abs(float(q["force_component_absolute_difference_max_ev_per_angstrom"]) - float(frozen["force_component_absolute_difference_max_ev_per_angstrom"])) > 1e-15:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: restart qualification force drift")
    if q.get("direct_one_rank") is not True or q.get("scientific_settings_changed") is not False:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: restart qualification provenance drift")
    return q, path


def load_deployment(path: Path) -> dict[str, Any]:
    d = load_json(path)
    if d.get("schema") != DEPLOY_SCHEMA or d.get("status") != "FROZEN_BEFORE_NATIVE_L15_PRODUCTION_RESULTS":
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: wrong/unfrozen native deployment")
    sc = d["scientific_contract"]
    exact = {
        "rung": "L15/V32/K28", "exchange_correlation": "PBE", "ecutwfc_ry": 90,
        "ecutrho_ry": 900, "layers": 15, "vacuum_angstrom": 32.0, "kmesh": 28,
        "assume_isolated": "esm", "esm_bc": "bc1", "electron_conv_thr": 1e-10,
        "electron_maxstep": 200, "mixing_beta": 0.3, "ion_dynamics": "bfgs",
        "force_gate_ev_per_angstrom": 0.02,
        "independent_scf_reproduction_gate_ev": 0.001,
        "surface_excess_convergence_max_ev_per_surface_atom": 0.001,
    }
    for k, v in exact.items():
        if sc.get(k) != v:
            raise SystemExit(f"SCIENTIFIC_HOLD: native deployment science drift: {k}")
    for k in ("scientific_settings_changed", "thresholds_changed", "acceptance_rule_changed", "kinetic_inputs_used", "new_scientific_rung_authorized"):
        if sc.get(k) is not False:
            raise SystemExit(f"SCIENTIFIC_HOLD: forbidden deployment change: {k}")
    ex = d["execution"]
    if ex.get("execution_mode") != "DIRECT_ONE_RANK" or ex.get("mpi_ranks") != 1:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: execution-mode drift")
    if int(ex["qe_max_seconds_per_chunk"]) != 16200 or int(ex["maximum_native_chunks"]) != 36:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: native chunk contract drift")
    return d


def compatibility_record(ext, p, segment: int, completion_segment: int, cell, final_atoms, energy_ev, force, inp: Path, out: Path, deployment_sha: str, qualification_sha: str) -> dict[str, Any]:
    return {
        "schema": ext.SEG_SCHEMA,
        "status": "RELAX_COMPLETE",
        "segment": segment,
        "logical_segment": segment,
        "completion_segment": completion_segment,
        "case_id": p["extension_audit"]["case_id"],
        "role": p["extension_audit"]["role"],
        "layers": 15,
        "vacuum_angstrom": 32.0,
        "kmesh": 28,
        "cell_angstrom": cell,
        "mpi_ranks": 1,
        "execution_mode": "DIRECT_ONE_RANK",
        "runner_label": "NATIVE_QE_RESTART_DIRECT_ONE_RANK",
        "thread_caps": {"OMP_NUM_THREADS": 1, "OPENBLAS_NUM_THREADS": 1, "MKL_NUM_THREADS": 1},
        "timed_out_by_wrapper": False,
        "pw_returncode": 0,
        "job_done": True,
        "bfgs_finished": True,
        "energy_ev": energy_ev,
        "latest_authoritative_max_movable_force_ev_per_angstrom": force,
        "input_atoms": None,
        "final_atoms": final_atoms,
        "next_trial_atoms": None,
        "source_evidence": {
            "source": "QE_NATIVE_RESTART_CHAIN",
            "native_deployment_sha256": deployment_sha,
            "qualification_result_sha256": qualification_sha,
            "completion_segment": completion_segment,
        },
        "carried_forward_without_recomputation": segment != completion_segment,
        "scientific_settings_changed": False,
        "scientific_settings_changed_after_extension_freeze": False,
        "numerical_grid_extended_from_original_protocol": True,
        "parallelization_changed": False,
        "thresholds_changed": False,
        "kinetic_inputs_used": False,
        "raw_hashes": {"relax_input_sha256": sha256(inp), "relax_output_sha256": sha256(out)},
        "surface_convergence_extension_protocol_sha256": sha256(Path(p["_protocol_path"])),
        "surface_protocol_sha256": p["frozen_sources"]["surface_protocol"]["sha256"],
        "rank_selection_sha256": p["frozen_sources"]["rank_selection_sha256"],
        "pw_sha256": p["frozen_sources"]["pw_x_sha256"],
        "elapsed_s": 0.0,
    }


def carry_complete(ext, p, deploy, qpath: Path, prior_root: Path, out_root: Path, segment: int) -> None:
    prior_native = load_json(prior_root / "chunk_out" / "NATIVE_L15_CHUNK.json")
    if prior_native.get("status") != "RELAX_COMPLETE":
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: carry requested from non-complete state")
    comp = load_json(prior_root / "chunk_out" / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json")
    if int(comp["segment"]) != segment - 1:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: complete-state segment chain mismatch")
    comp["segment"] = segment
    comp["logical_segment"] = segment
    comp["carried_forward_without_recomputation"] = True
    native = dict(prior_native)
    native["segment"] = segment
    native["status"] = "RELAX_COMPLETE"
    native["carried_forward_without_recomputation"] = True
    out_root.mkdir(parents=True, exist_ok=True)
    write_json(out_root / "NATIVE_L15_CHUNK.json", native)
    write_json(out_root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json", comp)
    ext_base, _, _ = ext.import_runtime()
    ext_base.stage_manifest(out_root, [out_root / "NATIVE_L15_CHUNK.json", out_root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json"])
    print(f"NATIVE_L15_STATUS=RELAX_COMPLETE\nCARRIED_FORWARD=true\nSEGMENT={segment}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--segment", type=int, required=True)
    ap.add_argument("--deployment", required=True)
    ap.add_argument("--restart-protocol", required=True)
    ap.add_argument("--extension-protocol", required=True)
    ap.add_argument("--hold-root", required=True)
    ap.add_argument("--l13-root", required=True)
    ap.add_argument("--qualification-root", required=True)
    ap.add_argument("--prior-root")
    ap.add_argument("--surface-protocol", required=True)
    ap.add_argument("--stage-a-result", required=True)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--pseudo-dir", required=True)
    ap.add_argument("--pw", required=True)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    segment = int(args.segment)
    if segment < 1 or segment > 36:
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: segment outside frozen native runway")
    deploy_path = Path(args.deployment).resolve(); deploy = load_deployment(deploy_path)
    restart = load_json(Path(args.restart_protocol).resolve())
    if restart.get("schema") != "co-cu111-qe-native-checkpoint-restart-protocol-v0.1":
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: restart protocol schema drift")
    q, qpath = qualification(deploy, Path(args.qualification_root).resolve())
    ext = imports(); pp = Path(args.extension_protocol).resolve(); p = ext.protocol(pp); p["_protocol_path"] = str(pp)
    ext.verify_source_hold(Path(args.hold_root).resolve(), p)
    l13, _ = ext.verify_l13_reference(Path(args.l13_root).resolve(), p)
    cell, original_seed, _seed_evidence = ext.seed_from_l13(l13, p)

    out_root = Path(args.out).resolve(); out_root.mkdir(parents=True, exist_ok=True)
    prior_root = Path(args.prior_root).resolve() if args.prior_root else None
    if segment > 1:
        if prior_root is None:
            raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: missing prior native artifact")
        prior_native = load_json(prior_root / "chunk_out" / "NATIVE_L15_CHUNK.json")
        if int(prior_native.get("segment", -1)) != segment - 1:
            raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: prior native segment mismatch")
        if prior_native.get("status") == "RELAX_COMPLETE":
            carry_complete(ext, p, deploy, qpath, prior_root, out_root, segment)
            return
        if prior_native.get("status") != "CHECKPOINT":
            raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: prior state is not resumable")
        manifest_path = prior_root / "chunk_out" / "checkpoint_manifest.json"
        state_root = prior_root / "restart_state"
        manifest = verify_manifest(state_root, manifest_path)
        if int(manifest["size_bytes"]) > int(deploy["execution"]["checkpoint_soft_max_bytes"]):
            raise SystemExit("MECHANICAL_CHECKPOINT_STORAGE_HOLD: prior restart state exceeds frozen storage bound")
        if Path("restart_state").exists(): shutil.rmtree("restart_state")
        shutil.copytree(state_root, "restart_state")
        restart_mode = "restart"
    else:
        if Path("restart_state").exists(): shutil.rmtree("restart_state")
        Path("restart_state").mkdir(parents=True)
        restart_mode = "from_scratch"

    base, old, _relay, surface, bundle, _sel = ext.runtime_context(args, p)
    cell2, template = base.clean_geometry(float(surface["inherited_stage_a_settings"]["bulk_lattice_constant_angstrom"]), 15, 32.0)
    if any(abs(float(a)-float(b)) > 1e-12 for ra, rb in zip(cell, cell2) for a, b in zip(ra, rb)):
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: L15 cell reconstruction mismatch")
    seed = old.apply_template(original_seed, template)

    run_dir = out_root / "run"; run_dir.mkdir(exist_ok=True)
    inp = run_dir / f"l15_native_seg{segment}.in"; out = run_dir / f"l15_native_seg{segment}.out"
    text = base.qe_input(
        calculation="relax", prefix=PREFIX, cell=cell2, atoms=seed, kmesh=28,
        protocol=surface, bundle=bundle, pseudo_dir=Path(args.pseudo_dir), outdir=Path("restart_state"),
    )
    text = inject_restart(text, restart_mode, int(deploy["execution"]["qe_max_seconds_per_chunk"]))
    inp.write_text(text)

    env = dict(os.environ); env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    start = time.time(); timed_out = False
    with inp.open("rb") as fi, out.open("wb") as fo:
        proc = subprocess.Popen([str(Path(args.pw).resolve())], stdin=fi, stdout=fo, stderr=subprocess.STDOUT, env=env)
        try:
            rc = proc.wait(timeout=int(deploy["execution"]["external_safety_timeout_seconds"]))
        except subprocess.TimeoutExpired:
            timed_out = True; proc.terminate()
            try: rc = proc.wait(timeout=30)
            except subprocess.TimeoutExpired: proc.kill(); rc = proc.wait(timeout=10)
    elapsed = time.time() - start
    raw = out.read_text(errors="replace")
    energies = [float(x) * base.RY_TO_EV for x in base.ENERGY_RE.findall(raw)]
    blocks = old.authoritative_force_blocks(raw, 15)
    latest_force = old.max_movable_force_ev_a(blocks[-1], seed) if blocks else None
    job_done = "JOB DONE." in raw
    bfgs_finished = "End of BFGS Geometry Optimization" in raw
    clean_stop = ("Maximum CPU time exceeded" in raw) and not timed_out

    common = {
        "schema": NATIVE_SCHEMA, "segment": segment, "case_id": p["extension_audit"]["case_id"],
        "restart_mode": restart_mode, "qe_max_seconds": int(deploy["execution"]["qe_max_seconds_per_chunk"]),
        "external_timeout_seconds": int(deploy["execution"]["external_safety_timeout_seconds"]),
        "external_wrapper_timeout": timed_out, "pw_returncode": rc, "elapsed_s": elapsed,
        "job_done": job_done, "bfgs_finished": bfgs_finished, "latest_authoritative_max_movable_force_ev_per_angstrom": latest_force,
        "repository_run_id": int(os.environ.get("GITHUB_RUN_ID", "0")), "repository_job": os.environ.get("GITHUB_JOB"),
        "repository_commit": os.environ.get("GITHUB_SHA"), "execution_mode": "DIRECT_ONE_RANK", "mpi_ranks": 1,
        "thread_caps": {"OMP_NUM_THREADS": 1, "OPENBLAS_NUM_THREADS": 1, "MKL_NUM_THREADS": 1},
        "scientific_settings_changed": False, "thresholds_changed": False, "kinetic_inputs_used": False,
        "deployment_sha256": sha256(deploy_path), "restart_protocol_sha256": sha256(Path(args.restart_protocol).resolve()),
        "extension_protocol_sha256": sha256(pp), "qualification_result_sha256": sha256(qpath),
        "pw_x_sha256": sha256(Path(args.pw).resolve()), "rank_selection_sha256": p["frozen_sources"]["rank_selection_sha256"],
        "qe_input_sha256": sha256(inp), "qe_output_sha256": sha256(out),
        "carried_forward_without_recomputation": False,
    }

    if timed_out:
        common["status"] = "MECHANICAL_CHECKPOINT_HOLD"; write_json(out_root / "NATIVE_L15_CHUNK.json", common)
        raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: external safety timeout fired; partial state is not an admissible checkpoint")

    if job_done and bfgs_finished and energies:
        final_atoms = base.parse_positions(raw, 15, seed)
        if final_atoms is None or not blocks:
            common["status"] = "MECHANICAL_CHECKPOINT_HOLD"; write_json(out_root / "NATIVE_L15_CHUNK.json", common)
            raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: completed relaxation lacks final geometry/forces")
        final_atoms = old.apply_template(final_atoms, template)
        final_force = old.max_movable_force_ev_a(blocks[-1], final_atoms)
        if final_force > float(p["frozen_method"]["force_gate_ev_per_angstrom"]):
            common.update(status="SCIENTIFIC_HOLD", final_force_ev_per_angstrom=final_force, final_energy_ev=energies[-1])
            write_json(out_root / "NATIVE_L15_CHUNK.json", common)
            raise SystemExit("SCIENTIFIC_HOLD: L15 completed but frozen force gate failed")
        common.update(status="RELAX_COMPLETE", completion_segment=segment, final_force_ev_per_angstrom=final_force, final_energy_ev=energies[-1], final_atoms=final_atoms)
        write_json(out_root / "NATIVE_L15_CHUNK.json", common)
        comp = compatibility_record(ext, p, segment, segment, cell2, final_atoms, energies[-1], final_force, inp, out, sha256(deploy_path), sha256(qpath))
        write_json(out_root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json", comp)
        base.stage_manifest(out_root, [out_root / "NATIVE_L15_CHUNK.json", out_root / "SURFACE_CONVERGENCE_EXTENSION_SEGMENT.json"])
        print(f"NATIVE_L15_STATUS=RELAX_COMPLETE\nSEGMENT={segment}\nL15_FORCE_EV_A={final_force}")
        return

    if clean_stop:
        save = Path("restart_state") / f"{PREFIX}.save"
        if not save.is_dir() or not (save / "data-file-schema.xml").is_file():
            common["status"] = "MECHANICAL_CHECKPOINT_HOLD"; write_json(out_root / "NATIVE_L15_CHUNK.json", common)
            raise SystemExit("MECHANICAL_CHECKPOINT_HOLD: QE clean-stop marker present but native save state is incomplete")
        manifest = recursive_manifest(Path("restart_state"))
        if int(manifest["size_bytes"]) > int(deploy["execution"]["checkpoint_soft_max_bytes"]):
            common.update(status="MECHANICAL_CHECKPOINT_STORAGE_HOLD", restart_state_size_bytes=int(manifest["size_bytes"]))
            write_json(out_root / "NATIVE_L15_CHUNK.json", common)
            raise SystemExit("MECHANICAL_CHECKPOINT_STORAGE_HOLD: native state exceeds frozen persistence bound")
        write_json(out_root / "checkpoint_manifest.json", manifest)
        common.update(status="CHECKPOINT", checkpoint_index=segment, clean_stop_requested_by_max_seconds=True,
                      restart_state_size_bytes=int(manifest["size_bytes"]), restart_file_count=int(manifest["file_count"]),
                      recursive_restart_manifest_sha256=sha256(out_root / "checkpoint_manifest.json"))
        write_json(out_root / "NATIVE_L15_CHUNK.json", common)
        print(f"NATIVE_L15_STATUS=CHECKPOINT\nSEGMENT={segment}\nRESTART_STATE_BYTES={manifest['size_bytes']}\nRESTART_FILES={manifest['file_count']}")
        return

    common["status"] = "MECHANICAL_CHECKPOINT_HOLD"; write_json(out_root / "NATIVE_L15_CHUNK.json", common)
    raise SystemExit(f"MECHANICAL_CHECKPOINT_HOLD: pw.x ended without RELAX_COMPLETE or a clean max_seconds checkpoint, rc={rc}")


if __name__ == "__main__":
    main()
