#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

EOS_PAIRS = [(e,k) for e in (80,90,100,110,120,130) for k in (14,16,18,20)] + [(140,22),(150,24)]
DECISION = 'na-cu001-bulk-extension-decision-v0.4'
SUMMARIES = 'na-cu001-bulk-extension-all-summaries-v0.4'
RAW_COMPLETE = 'na-cu001-bulk-extension-raw-complete-v0.4'

def fail(msg: str) -> None:
    raise SystemExit(f'HOLD: {msg}')

def step_map(job: dict) -> dict[str, str | None]:
    return {str(s.get('name')): s.get('conclusion') for s in (job.get('steps') or [])}

def audit(jobs_payload: dict, artifacts_payload: dict, run_id: int) -> dict:
    jobs = jobs_payload.get('jobs', [])
    by_name = {j.get('name'): j for j in jobs}
    prep = by_name.get('prepare-engine')
    if not prep or prep.get('status') != 'completed' or prep.get('conclusion') != 'success':
        fail('prepare-engine is not completed success')
    eos = [j for j in jobs if str(j.get('name','')).startswith('extension-eos ')]
    if len(eos) != 26:
        fail(f'expected 26 extension-eos jobs, found {len(eos)}')
    bad_eos = sorted(j.get('name') for j in eos if j.get('status') != 'completed' or j.get('conclusion') != 'success')
    if bad_eos:
        fail(f'non-success EOS jobs: {bad_eos}')
    gate = by_name.get('extension-gate')
    if not gate or gate.get('status') != 'completed' or gate.get('conclusion') not in {'success','cancelled','failure'}:
        fail('extension-gate has no admissible terminal record')
    steps = step_map(gate)
    required_success = [
        'Audit matrix completeness, reference validity, and source hashes',
        'Audit reference, select candidate, and build compact decision',
        'Upload compact decision and PASS-only handoff',
        'Upload all EOS summaries used by the decision',
    ]
    missing_success = [name for name in required_success if steps.get(name) != 'success']
    if missing_success:
        fail(f'gate scientific/evidence steps not successful: {missing_success}')
    artifacts = artifacts_payload.get('artifacts', [])
    by_art = {a.get('name'): a for a in artifacts}
    required = {DECISION, SUMMARIES}
    required |= {f'na-cu001-bulk-extension-raw-e{e}_k{k}' for e,k in EOS_PAIRS}
    missing = sorted(required - set(by_art))
    if missing:
        fail(f'missing required artifacts: {missing}')
    invalid = []
    for name in sorted(required):
        a = by_art[name]
        if a.get('expired') or int(a.get('size_in_bytes') or 0) <= 0 or not str(a.get('digest','')).startswith('sha256:'):
            invalid.append(name)
    if invalid:
        fail(f'invalid or unhashed artifacts: {invalid}')
    aggregate_present = RAW_COMPLETE in by_art
    aggregate_step = steps.get('Upload complete retained raw extension evidence')
    if not aggregate_present:
        if gate.get('conclusion') == 'success':
            fail('gate says success but redundant aggregate raw artifact is absent')
        if aggregate_step not in {'failure','cancelled'}:
            fail(f'aggregate raw artifact absent without isolated upload failure, step={aggregate_step!r}')
    other_bad = []
    for j in jobs:
        name = str(j.get('name',''))
        if name == 'extension-gate' or name == 'prepare-engine' or name.startswith('extension-eos '):
            continue
        if j.get('conclusion') not in {None,'success','skipped'}:
            other_bad.append((name,j.get('conclusion')))
    if other_bad:
        fail(f'unexpected failed jobs: {other_bad}')
    return {
        'schema': 'na-cu001-bulk-v04-run-audit-v0.1',
        'status': 'PASS',
        'run_id': run_id,
        'scientific_gate': 'PASS',
        'prepare_job': 'success',
        'eos_jobs_verified': 26,
        'scf_records_expected': 276,
        'gate_conclusion': gate.get('conclusion'),
        'gate_required_steps': {k: steps.get(k) for k in required_success},
        'aggregate_raw_artifact': {
            'required_for_scientific_closure': False,
            'present': aggregate_present,
            'upload_step_conclusion': aggregate_step,
            'classification': 'REDUNDANT_AGGREGATE_PACKAGING_FAILURE' if not aggregate_present else 'PRESENT',
        },
        'canonical_artifacts': [
            {k: by_art[name].get(k) for k in ('id','name','size_in_bytes','digest','expired','created_at','expires_at')}
            for name in sorted(required)
        ],
    }

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--jobs',required=True)
    ap.add_argument('--artifacts',required=True)
    ap.add_argument('--run-id',required=True,type=int)
    ap.add_argument('--out',required=True)
    ns=ap.parse_args()
    out=audit(json.loads(Path(ns.jobs).read_text()),json.loads(Path(ns.artifacts).read_text()),ns.run_id)
    Path(ns.out).write_text(json.dumps(out,indent=2)+'\n')
    print(f"PASS bulk v0.4 run audit: {out['eos_jobs_verified']} EOS jobs; aggregate raw is noncanonical")

if __name__=='__main__': main()
