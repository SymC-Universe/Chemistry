#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

EOS_PAIRS = [(e,k) for e in (80,90,100,110,120,130) for k in (14,16,18,20)] + [(140,22),(150,24)]
DECISION = 'na-cu001-bulk-extension-decision-v0.4'
SUMMARIES = 'na-cu001-bulk-extension-all-summaries-v0.4'
RAW_COMPLETE = 'na-cu001-bulk-extension-raw-complete-v0.4'
REQUIRED_GATE_STEPS = {
    3: 'Initialize fail-closed decision evidence',
    4: 'Run actions/download-artifact@v4',
    5: 'Run actions/download-artifact@v4',
    6: 'Audit reference and select only a joint-pass candidate',
    8: 'Run actions/upload-artifact@v4',
    9: 'Run actions/upload-artifact@v4',
}
AGGREGATE_UPLOAD_STEP = 10

def fail(msg: str) -> None:
    raise SystemExit(f'HOLD: {msg}')

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
    by_number = {int(s.get('number')): s for s in (gate.get('steps') or []) if s.get('number') is not None}
    bad_required = []
    for number, expected_name in REQUIRED_GATE_STEPS.items():
        step = by_number.get(number)
        if not step or step.get('name') != expected_name or step.get('conclusion') != 'success':
            bad_required.append({'number':number,'expected_name':expected_name,'actual':step})
    if bad_required:
        fail(f'gate scientific/evidence step sequence failed: {bad_required}')
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
    aggregate_step = by_number.get(AGGREGATE_UPLOAD_STEP)
    aggregate_conclusion = aggregate_step.get('conclusion') if aggregate_step else None
    if not aggregate_present:
        if gate.get('conclusion') == 'success':
            fail('gate says success but redundant aggregate raw artifact is absent')
        if not aggregate_step or aggregate_step.get('name') != 'Run actions/upload-artifact@v4' or aggregate_conclusion not in {'failure','cancelled'}:
            fail(f'aggregate raw artifact absent without isolated step-10 upload failure: {aggregate_step!r}')
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
        'gate_required_steps': [
            {'number':n,'name':by_number[n].get('name'),'conclusion':by_number[n].get('conclusion')}
            for n in sorted(REQUIRED_GATE_STEPS)
        ],
        'aggregate_raw_artifact': {
            'required_for_scientific_closure': False,
            'present': aggregate_present,
            'upload_step_number': AGGREGATE_UPLOAD_STEP,
            'upload_step_conclusion': aggregate_conclusion,
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
