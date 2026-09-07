#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
V2 = HERE / 'pbe_l15_l17_site_depth_diagnostic_v2.py'
spec = importlib.util.spec_from_file_location('depth_v2_probe', V2)
if spec is None or spec.loader is None:
    raise SystemExit('MECHANICAL_HOLD: cannot load v0.2 runner')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--protocol', required=True)
    ap.add_argument('--surface-protocol', required=True)
    ap.add_argument('--stage-a-result', required=True)
    ap.add_argument('--bundle', required=True)
    ap.add_argument('--pseudo-dir', required=True)
    ap.add_argument('--pw', required=True)
    ap.add_argument('--l15-root', required=True)
    ap.add_argument('--l17-root', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    p = m.load_protocol_v2(Path(args.protocol).resolve())
    base, surface, bundle = m.v1.verify_runtime(args, p)
    source = m.v1.source_for_depth('L15', Path(args.l15_root).resolve(), Path(args.l17_root).resolve(), p)
    cell, atoms, geom = m.matched_geometry_v2(source, 'L15', 'top', p)

    out_root = Path(args.out).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    checkpoint = out_root / 'qe_checkpoint'
    checkpoint.mkdir(parents=True, exist_ok=True)
    inp = out_root / 'probe.in'
    out = out_root / 'probe.out'

    text = base.qe_input(
        calculation='scf',
        prefix='co_cu111_l15l17_resource_probe',
        cell=cell,
        atoms=atoms,
        kmesh=8,
        protocol=surface,
        bundle=bundle,
        pseudo_dir=Path(args.pseudo_dir).resolve(),
        outdir=checkpoint,
    )
    text = m.add_control_fields(text, 'from_scratch', 30)
    inp.write_text(text)

    env = dict(os.environ)
    env['OMP_NUM_THREADS'] = '1'
    env['OPENBLAS_NUM_THREADS'] = '1'
    env['MKL_NUM_THREADS'] = '1'
    start = time.time()
    timed_out = False
    with inp.open('rb') as fi, out.open('wb') as fo:
        proc = subprocess.Popen([str(Path(args.pw).resolve())], stdin=fi, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        assert proc.stdout is not None
        deadline = start + 60.0
        while True:
            line = proc.stdout.readline()
            if line:
                fo.write(line)
                fo.flush()
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            if proc.poll() is not None:
                break
            if time.time() >= deadline:
                timed_out = True
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
                break
        # Drain any buffered final output.
        rest = proc.stdout.read()
        if rest:
            fo.write(rest)
            fo.flush()
            sys.stdout.buffer.write(rest)
            sys.stdout.buffer.flush()
        rc = proc.returncode

    raw = out.read_text(errors='replace')
    lower = raw.lower()
    clean_stop = 'maximum cpu time exceeded' in lower and 'job done' in lower
    memory_lines = [line for line in raw.splitlines() if 'ram per process' in line.lower() or 'estimated max dynamical ram' in line.lower() or 'estimated max scf ram' in line.lower() or 'estimated static dynamical ram' in line.lower() or 'estimated static scf ram' in line.lower() or 'estimated max' in line.lower() and 'ram' in line.lower()]
    allocation_lines = [line for line in raw.splitlines() if 'allocate' in line.lower() or 'memory' in line.lower() and ('error' in line.lower() or 'cannot' in line.lower())]

    status = 'MECHANICAL_ROUTE_SUPPORTS_SHORT_EXACT_CHECKPOINT_TEST' if clean_stop else ('MECHANICAL_ROUTE_SURVIVES_60S_BUT_QE_DID_NOT_CLEAN_STOP' if timed_out else 'MECHANICAL_QE_EXIT_BEFORE_CLEAN_CHECKPOINT')
    result = {
        'schema': 'co-cu111-l15-l17-2x2-resource-probe-result-v0.1',
        'status': status,
        'scientific_energy_adjudication_allowed': False,
        'original_l17_hold_preserved': True,
        'depth': 'L15',
        'site': 'top',
        'supercell': [2, 2],
        'kmesh': 8,
        'coverage_ML': 0.25,
        'qe_max_seconds': 30,
        'wrapper_timeout_seconds': 60,
        'elapsed_seconds': time.time() - start,
        'pw_returncode': rc,
        'wrapper_timeout': timed_out,
        'clean_qe_max_seconds_checkpoint': clean_stop,
        'geometry_evidence': geom,
        'memory_diagnostic_lines': memory_lines,
        'allocation_diagnostic_lines': allocation_lines,
        'raw_input_sha256': m.v1.sha256(inp),
        'raw_output_sha256': m.v1.sha256(out),
    }
    if clean_stop:
        try:
            result['checkpoint_manifest_sha256'] = m.write_checkpoint_manifest(out_root)
        except SystemExit:
            result['checkpoint_manifest_sha256'] = None
            result['status'] = 'MECHANICAL_HOLD_CLEAN_STOP_WITHOUT_COMPLETE_CHECKPOINT'
    (out_root / 'RESOURCE_PROBE_RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
