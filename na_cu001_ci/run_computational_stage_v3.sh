#!/usr/bin/env bash
set -euxo pipefail

PROTOCOL=na_cu001_ci/method_protocol_v0.2.json
ENGINE=na_cu001_ci/closure_engine_v3.py
PLAN=na_cu001_ci/integration_closure_plan_v0.3.json

cleanup_restart_scratch() { find . -type d -name tmp -prune -exec rm -rf {} + 2>/dev/null || true; }
trap cleanup_restart_scratch EXIT
runtime() { sudo apt-get update; sudo apt-get install -y openmpi-bin libopenmpi-dev libopenblas-dev liblapack-dev libfftw3-dev python3-numpy; }

delegate_v2_stage() {
  local tmp
  tmp=$(mktemp)
  sed \
    -e 's#ENGINE=na_cu001_ci/closure_engine_v2.py#ENGINE=na_cu001_ci/closure_engine_v3.py#' \
    -e 's#na_cu001_ci/slab_runner_v2.py#na_cu001_ci/slab_runner_v3.py#g' \
    na_cu001_ci/run_computational_stage_v2.sh > "$tmp"
  chmod +x "$tmp"
  bash "$tmp" "$@"
}

case "${1:?stage required}" in
  prepare)
    sudo apt-get update
    sudo apt-get install -y gfortran make m4 perl curl ca-certificates jq libopenblas-dev liblapack-dev libfftw3-dev libopenmpi-dev openmpi-bin python3-numpy python3-yaml gh
    mkdir -p base base/bulk_summaries imported_decision imported_summaries qe_bundle/bin qe_bundle/pseudos qe_bundle/meta sssp_archive "$RUNNER_TEMP/qe-src"
    run_id="${BULK_EXTENSION_RUN_ID:?BULK_EXTENSION_RUN_ID must be the independently audited v0.4 run}"
    state=$(gh run view "$run_id" --repo "$GITHUB_REPOSITORY" --json status,conclusion --jq '.status + " " + (.conclusion // "")')
    [[ "$state" == "completed success" ]]
    gh run download "$run_id" --repo "$GITHUB_REPOSITORY" --name na-cu001-bulk-extension-decision-v0.4 --dir imported_decision
    gh run download "$run_id" --repo "$GITHUB_REPOSITORY" --name na-cu001-bulk-extension-all-summaries-v0.4 --dir imported_summaries
    result=$(find imported_decision -type f -name BULK_CONVERGENCE_RESULT_V0.4.json -print -quit)
    handoff=$(find imported_decision -type f -name BULK_HANDOFF_V0.4.json -print -quit)
    test -n "$result"; test -n "$handoff"
    cp "$result" base/BULK_CONVERGENCE_RESULT.json
    cp "$handoff" base/BULK_HANDOFF.json
    cp na_cu001_ci/bulk_extension_protocol_v0.1.json base/bulk_extension_protocol_v0.1.json
    find imported_summaries -type f -name 'summary_e*_k*.json' -exec cp {} base/bulk_summaries/ \;
    test "$(find base/bulk_summaries -maxdepth 1 -type f -name 'summary_e*_k*.json' | wc -l)" -eq 46

    python3 - <<'PYDECISION'
import hashlib,json
from pathlib import Path
root=Path('imported_decision')
manifest=next(root.rglob('DECISION_MANIFEST.sha256'))
for line in manifest.read_text().splitlines():
    if not line.strip(): continue
    expected,path=line.split(None,1); candidate=root/Path(path).name
    if candidate.name=='DECISION_MANIFEST.sha256': continue
    if not candidate.is_file(): raise SystemExit(f'HOLD: decision manifest file missing: {candidate.name}')
    actual=hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual!=expected: raise SystemExit(f'HOLD: decision manifest mismatch: {candidate.name}')
result=json.loads(Path('base/BULK_CONVERGENCE_RESULT.json').read_text())
if result.get('schema')!='na-cu001-bulk-selection-v0.4' or result.get('gate')!='PASS' or result.get('status')!='PASS':
    raise SystemExit('HOLD: imported v0.4 decision is not PASS')
if Path(next(root.rglob('GATE_EXIT_CODE.txt'))).read_text().strip()!='0':
    raise SystemExit('HOLD: imported v0.4 gate exit code is not zero')
PYDECISION

    gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}/artifacts?per_page=100" > base/upstream_artifacts_api.json
    python3 - <<'PYART'
import json,os
from pathlib import Path
payload=json.loads(Path('base/upstream_artifacts_api.json').read_text())
rows=[]
for x in payload.get('artifacts',[]):
    name=x.get('name','')
    if name.startswith('na-cu001-bulk-extension-'):
        rows.append({k:x.get(k) for k in ('id','name','size_in_bytes','digest','expired','created_at','expires_at')})
required={'na-cu001-bulk-extension-decision-v0.4','na-cu001-bulk-extension-all-summaries-v0.4','na-cu001-bulk-extension-raw-complete-v0.4'}
required|={f'na-cu001-bulk-extension-raw-e{e}_k{k}' for e,k in [(e,k) for e in (80,90,100,110,120,130) for k in (14,16,18,20)]+[(140,22),(150,24)]}
by={x['name']:x for x in rows}
missing=sorted(required-set(by))
invalid=sorted(name for name in required&set(by) if by[name]['expired'] or not str(by[name].get('digest','')).startswith('sha256:'))
if missing or invalid: raise SystemExit(f'HOLD: upstream bulk artifacts incomplete missing={missing} invalid={invalid}')
out={'schema':'na-cu001-upstream-bulk-artifacts-v0.1','status':'PASS','repository':os.environ.get('GITHUB_REPOSITORY'),'run_id':int(os.environ['BULK_EXTENSION_RUN_ID']),'artifacts':[by[n] for n in sorted(required)]}
Path('base/UPSTREAM_BULK_ARTIFACTS.json').write_text(json.dumps(out,indent=2)+'\n')
PYART
    rm base/upstream_artifacts_api.json

    python3 na_cu001_ci/bulk_v04_downstream_bridge_v1.py \
      --result base/BULK_CONVERGENCE_RESULT.json \
      --handoff base/BULK_HANDOFF.json \
      --protocol base/bulk_extension_protocol_v0.1.json \
      --summaries base/bulk_summaries \
      --out base/BULK_V04_DOWNSTREAM_BRIDGE.json

    curl -L --retry 5 --retry-delay 5 https://gitlab.com/QEF/q-e/-/archive/qe-7.6/q-e-qe-7.6.tar.gz -o "$RUNNER_TEMP/qe-7.6.tar.gz"
    echo "945c8f16ab330c8f0b30f4de1a9a088b85038476fcd819394e641f4d2d8b7d51  $RUNNER_TEMP/qe-7.6.tar.gz" | sha256sum -c -
    tar -xzf "$RUNNER_TEMP/qe-7.6.tar.gz" -C "$RUNNER_TEMP/qe-src" --strip-components=1
    (cd "$RUNNER_TEMP/qe-src" && ./configure MPIF90=mpif90 F90=gfortran CC=mpicc && make -j2 pw neb)
    cp "$RUNNER_TEMP/qe-src/bin/pw.x" "$RUNNER_TEMP/qe-src/bin/neb.x" qe_bundle/bin/
    chmod +x qe_bundle/bin/pw.x qe_bundle/bin/neb.x
    sha256sum qe_bundle/bin/pw.x qe_bundle/bin/neb.x > qe_bundle/meta/engine_binaries.sha256

    curl -L --retry 5 --retry-delay 5 https://raw.githubusercontent.com/unkcpz/sssp-verify-scripts/refs/heads/main/2-experiments/finalized_scripts/010-extract-eff-lib/SSSP-lib-pbe-eff-v2.tar.gz -o qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz
    echo "67c59659953f32b87ebf1e7e59b5cdd55bcaca02b518532098c339c0d11193c2  qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz" | sha256sum -c -
    tar -xzf qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz -C sssp_archive
    cp "$(find sssp_archive -type f -name 'Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf' -print -quit)" qe_bundle/pseudos/
    echo "b31028b2bae60cd9903260715a49b4c6d2b6dc654558c87023fa5206e427a16d  qe_bundle/pseudos/Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf" | sha256sum -c -

    python3 na_cu001_ci/na_pseudo_probe_v2.py --archive-root sssp_archive --archive qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz --protocol "$PROTOCOL" --out base/NA_PSEUDO_PROBE.json
    python3 "$ENGINE" resolve-na --protocol "$PROTOCOL" --probe base/NA_PSEUDO_PROBE.json --bulk-handoff base/BULK_HANDOFF.json --pseudo-root sssp_archive --pseudo-dir qe_bundle/pseudos --pw qe_bundle/bin/pw.x --out-dir base/na_reference_raw --out base/NA_PSEUDO_HANDOFF.json --np 1

    python3 -m py_compile na_cu001_ci/*.py
    python3 na_cu001_ci/test_closure_engine.py
    python3 na_cu001_ci/test_closure_engine_v2.py
    python3 na_cu001_ci/test_negative_gates_v2.py
    python3 na_cu001_ci/test_bulk_extension_v1.py
    python3 na_cu001_ci/test_bulk_v04_downstream_bridge_v1.py
    python3 na_cu001_ci/test_v04_surface_entrypoints_v1.py
    python3 na_cu001_ci/workflow_contract_linter_v3.py .github/workflows/na-cu001-computational-route-v3.yml
    python3 na_cu001_ci/artifact_contract_linter_v3.py --plan "$PLAN" --stage-script na_cu001_ci/run_computational_stage_v3.sh
    printf '%s\n' "$GITHUB_SHA" > base/COMPUTATIONAL_SOURCE_COMMIT.txt
    { find na_cu001_ci -maxdepth 2 -type f \( -name '*.py' -o -name '*.json' -o -name '*.md' -o -name '*.tex' -o -name '*.sh' \) -print; \
      printf '%s\n' .github/workflows/na-cu001-computational-route-v3.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml; } \
      | LC_ALL=C sort | xargs sha256sum > base/SOURCE_CODE_MANIFEST.sha256
    ;;

  slab-case)
    runtime; chmod +x qe_bundle/bin/pw.x
    layers="$2"; vacuum="$3"; tag="$4"; mkdir -p "slab_outputs/$tag"
    meshes=$(python3 - <<'PY'
from pathlib import Path
from na_cu001_ci.slab_runner_v2 import registered_kmeshes
from na_cu001_ci.slab_runner_v3 import load_bulk_v04
b=load_bulk_v04(Path('base/BULK_HANDOFF.json'),Path('base/BULK_CONVERGENCE_RESULT.json'))
print(' '.join(map(str,registered_kmeshes(b['bulk_kmesh']))))
PY
)
    for kmesh in $meshes; do
      python3 na_cu001_ci/slab_runner_v3.py run --layers "$layers" --vacuum "$vacuum" --kmesh "$kmesh" \
        --handoff base/BULK_HANDOFF.json --bulk-result base/BULK_CONVERGENCE_RESULT.json \
        --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out "slab_outputs/$tag" --np 2
    done
    ;;

  slab-analyze)
    mkdir -p stage2
    python3 na_cu001_ci/slab_runner_v3.py analyze --records slab_outputs --out stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json
    python3 "$ENGINE" slab-handoff --slab-result stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json --bulk-handoff base/BULK_HANDOFF.json --out stage2/SLAB_HANDOFF.json
    ;;

  finalize)
    mkdir -p closure raw
    cp base/BULK_HANDOFF.json base/BULK_CONVERGENCE_RESULT.json base/BULK_V04_DOWNSTREAM_BRIDGE.json base/bulk_extension_protocol_v0.1.json base/UPSTREAM_BULK_ARTIFACTS.json base/NA_PSEUDO_PROBE.json base/NA_PSEUDO_HANDOFF.json closure/
    cp -r base/bulk_summaries closure/bulk_summaries
    cp stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json stage2/SLAB_HANDOFF.json stage3/ELECTROSTATIC_CONSISTENCY.json stage4/RELAXED_CLEAN_SURFACE_HANDOFF.json stage6/ADSORPTION_SITE_HANDOFF.json closure/
    cp stage7_primary/ENDPOINTS_PRIMARY.json stage7_expanded/ENDPOINTS_EXPANDED.json stage9_primary/PATH_PRIMARY.json stage9_expanded/PATH_EXPANDED.json closure/
    cp stage11_primary/CI_PRIMARY.json stage11_expanded/CI_EXPANDED.json stage13/MOBILITY_CONVERGENCE.json stage14/HESSIAN_PLAN.json stage14_final/ACTIVE_REGION_HESSIAN.json stage15/SADDLE_HANDOFF.json stage16/BARRIER_SENSITIVITY.json closure/
    cp "$PROTOCOL" na_cu001_ci/validation_selection_protocol_v0.1.json na_cu001_ci/public_evidence_candidates.json closure/
    cp na_cu001_ci/COMPUTATIONAL_PROCESS_AMENDMENT_v1.1.md na_cu001_ci/BULK_EXTENSION_AMENDMENT_v1.2.md na_cu001_ci/REPRODUCIBILITY_GUIDE_INSERT_v1.1.tex na_cu001_ci/REPRODUCIBILITY_GUIDE_CHECKPOINT_INSERT_v1.2.tex na_cu001_ci/COMPUTATIONAL_CHECKPOINT_LEDGER.md closure/
    cp na_cu001_ci/checkpoints/C6_V04_BRIDGE_PREFLIGHT.md na_cu001_ci/checkpoints/C6_V04_SURFACE_ENTRYPOINT_PREFLIGHT.md closure/
    cp base/COMPUTATIONAL_SOURCE_COMMIT.txt base/SOURCE_CODE_MANIFEST.sha256 closure/
    sha256sum -c closure/SOURCE_CODE_MANIFEST.sha256 | tee closure/SOURCE_MANIFEST_VERIFICATION.txt
    mkdir -p closure/source
    while read -r expected source_path; do cp --parents "$source_path" closure/source/; done < closure/SOURCE_CODE_MANIFEST.sha256
    python3 "$ENGINE" barrier --ci closure/CI_PRIMARY.json --saddle closure/SADDLE_HANDOFF.json --sensitivity closure/BARRIER_SENSITIVITY.json --mobility-gate closure/MOBILITY_CONVERGENCE.json --out closure/BARRIER_COORDINATE.json
    python3 "$ENGINE" atlas --barrier closure/BARRIER_COORDINATE.json --public-evidence closure/public_evidence_candidates.json --out closure/ATLAS_ADMISSION_RECORD.json
    python3 na_cu001_ci/tier_linter_v2.py closure/BARRIER_COORDINATE.json closure/ATLAS_ADMISSION_RECORD.json
    mkdir -p raw/bulk_v04_compact
    cp -r imported_decision imported_summaries base/UPSTREAM_BULK_ARTIFACTS.json raw/bulk_v04_compact/
    cp -r base/na_reference_raw stage3_raw stage4_raw ads_records stage7_raw_primary stage7_raw_expanded neb_records stage11_raw_primary stage11_raw_expanded hessian_centers hessian_records stage15_raw sensitivity_records raw/ || true
    python3 "$ENGINE" manifest --root raw --out closure/RAW_ARTIFACT_INDEX.json
    python3 na_cu001_ci/validate_integration_chain_v3.py --plan "$PLAN" --artifacts closure --raw-root raw --out closure/INTEGRATION_READINESS.json
    python3 "$ENGINE" manifest --root closure --out closure/COMPUTATIONAL_MANIFEST.json
    ;;

  *)
    delegate_v2_stage "$@"
    ;;
esac
