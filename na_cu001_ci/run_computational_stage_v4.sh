#!/usr/bin/env bash
set -euo pipefail

V3=na_cu001_ci/run_computational_stage_v3.sh
WORKFLOW=.github/workflows/na-cu001-v04-slab-route-v1.yml
PINNED_QE_RUN_ID=30865116448
PINNED_QE_ARTIFACT=na-cu001-c7-qe
PINNED_QE_ARTIFACT_DIGEST=sha256:1f3547d02f99f7ed1a4537f0c35075e66021b33ffb2e026018015f1c58bfa6ef
PINNED_QE_ARTIFACT_SIZE=101484780
PINNED_CU_PSEUDO_SHA256=b31028b2bae60cd9903260715a49b4c6d2b6dc654558c87023fa5206e427a16d

runtime() {
  sudo apt-get update
  sudo apt-get install -y \
    openmpi-bin libopenmpi-dev libopenblas-dev liblapack-dev libfftw3-dev \
    python3-numpy
}

patch_v3_for_c7_prepare() {
  local out="$1"
  python3 - "$V3" "$out" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1]).read_text()

def replace_once(label: str, old: str, new: str) -> None:
    global src
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"mechanical patch anchor count for {label} is {count}, expected 1")
    src = src.replace(old, new, 1)

replace_once(
    "verified upstream run state",
    '    [[ "$state" == "completed success" ]]',
    '    [[ "$state" == "completed success" || "$state" == "completed cancelled" ]]',
)
replace_once(
    "redundant aggregate artifact",
    "required={'na-cu001-bulk-extension-decision-v0.4','na-cu001-bulk-extension-all-summaries-v0.4','na-cu001-bulk-extension-raw-complete-v0.4'}",
    "required={'na-cu001-bulk-extension-decision-v0.4','na-cu001-bulk-extension-all-summaries-v0.4'}",
)
replace_once(
    "C7 workflow linter",
    'python3 na_cu001_ci/workflow_contract_linter_v3.py .github/workflows/na-cu001-computational-route-v3.yml',
    'python3 na_cu001_ci/workflow_contract_linter_v4_slab.py .github/workflows/na-cu001-v04-slab-route-v1.yml',
)
replace_once(
    "C7 source workflow manifest",
    '.github/workflows/na-cu001-computational-route-v3.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml',
    '.github/workflows/na-cu001-v04-slab-route-v1.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml',
)

old_build = '''    curl -L --retry 5 --retry-delay 5 https://gitlab.com/QEF/q-e/-/archive/qe-7.6/q-e-qe-7.6.tar.gz -o "$RUNNER_TEMP/qe-7.6.tar.gz"
    echo "945c8f16ab330c8f0b30f4de1a9a088b85038476fcd819394e641f4d2d8b7d51  $RUNNER_TEMP/qe-7.6.tar.gz" | sha256sum -c -
    tar -xzf "$RUNNER_TEMP/qe-7.6.tar.gz" -C "$RUNNER_TEMP/qe-src" --strip-components=1
    (cd "$RUNNER_TEMP/qe-src" && ./configure MPIF90=mpif90 F90=gfortran CC=mpicc && make -j2 pw neb)
    cp "$RUNNER_TEMP/qe-src/bin/pw.x" "$RUNNER_TEMP/qe-src/bin/neb.x" qe_bundle/bin/
    chmod +x qe_bundle/bin/pw.x qe_bundle/bin/neb.x
    sha256sum qe_bundle/bin/pw.x qe_bundle/bin/neb.x > qe_bundle/meta/engine_binaries.sha256
'''
new_build = '''    qe_source_run=30865116448
    qe_artifact_name=na-cu001-c7-qe
    qe_artifact_digest=sha256:1f3547d02f99f7ed1a4537f0c35075e66021b33ffb2e026018015f1c58bfa6ef
    qe_artifact_size=101484780
    gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${qe_source_run}/artifacts?per_page=100" > base/qe_engine_artifacts_api.json
    python3 - <<'PYQE'
import json, os
from pathlib import Path
payload=json.loads(Path('base/qe_engine_artifacts_api.json').read_text())
name='na-cu001-c7-qe'
expected_digest='sha256:1f3547d02f99f7ed1a4537f0c35075e66021b33ffb2e026018015f1c58bfa6ef'
expected_size=101484780
matches=[row for row in payload.get('artifacts',[]) if row.get('name')==name]
if len(matches)!=1:
    raise SystemExit(f'HOLD: expected one pinned QE artifact, found {len(matches)}')
row=matches[0]
if row.get('expired'):
    raise SystemExit('HOLD: pinned QE artifact has expired')
if row.get('digest')!=expected_digest or int(row.get('size_in_bytes',-1))!=expected_size:
    raise SystemExit('HOLD: pinned QE artifact digest or size changed')
record={
    'schema':'na-cu001-pinned-qe-artifact-v0.1',
    'status':'PASS',
    'repository':os.environ.get('GITHUB_REPOSITORY'),
    'source_run_id':30865116448,
    'artifact_id':row.get('id'),
    'artifact_name':name,
    'artifact_digest':row.get('digest'),
    'artifact_size_in_bytes':row.get('size_in_bytes'),
    'artifact_created_at':row.get('created_at'),
    'artifact_expires_at':row.get('expires_at'),
}
Path('base/QE_ENGINE_ARTIFACT_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\\n')
PYQE
    rm -rf qe_bundle qe_bundle_import
    mkdir -p qe_bundle_import
    gh run download "$qe_source_run" --repo "$GITHUB_REPOSITORY" --name "$qe_artifact_name" --dir qe_bundle_import
    if [[ -d qe_bundle_import/qe_bundle ]]; then
      mv qe_bundle_import/qe_bundle qe_bundle
      rmdir qe_bundle_import
    else
      mv qe_bundle_import qe_bundle
    fi
    test -x qe_bundle/bin/pw.x || chmod +x qe_bundle/bin/pw.x
    test -x qe_bundle/bin/neb.x || chmod +x qe_bundle/bin/neb.x
    test -f qe_bundle/meta/engine_binaries.sha256
    sha256sum -c qe_bundle/meta/engine_binaries.sha256
    echo "b31028b2bae60cd9903260715a49b4c6d2b6dc654558c87023fa5206e427a16d  qe_bundle/pseudos/Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf" | sha256sum -c -
'''
replace_once("pinned QE engine import", old_build, new_build)
Path(sys.argv[2]).write_text(src)
PY
  chmod +x "$out"
}

case "${1:?stage required}" in
  prepare)
    sudo apt-get update
    sudo apt-get install -y gh python3 python3-numpy
    mkdir -p bulk_run_audit
    run_id="${BULK_EXTENSION_RUN_ID:?BULK_EXTENSION_RUN_ID required}"
    gh api --paginate "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}/jobs?filter=latest&per_page=100" > bulk_run_audit/jobs.json
    gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}/artifacts?per_page=100" > bulk_run_audit/artifacts.json
    python3 na_cu001_ci/bulk_v04_run_audit_v1.py \
      --jobs bulk_run_audit/jobs.json \
      --artifacts bulk_run_audit/artifacts.json \
      --run-id "$run_id" \
      --out bulk_run_audit/UPSTREAM_BULK_RUN_AUDIT.json
    python3 na_cu001_ci/test_bulk_v04_run_audit_v1.py
    python3 -m py_compile \
      na_cu001_ci/slab_runner_v4.py \
      na_cu001_ci/slab_runner_v5.py \
      na_cu001_ci/test_slab_runner_v4.py \
      na_cu001_ci/test_slab_runner_v5.py \
      na_cu001_ci/closure_engine_v4.py \
      na_cu001_ci/test_slab_handoff_v4.py \
      na_cu001_ci/workflow_contract_linter_v4_slab.py
    (
      cd na_cu001_ci
      python3 test_slab_runner_v4.py
      python3 test_slab_runner_v5.py
      python3 test_slab_handoff_v4.py
    )
    python3 na_cu001_ci/workflow_contract_linter_v4_slab.py "$WORKFLOW"

    prepared_v3=$(mktemp)
    patch_v3_for_c7_prepare "$prepared_v3"
    bash -n "$prepared_v3"
    grep -Fq 'qe_source_run=30865116448' "$prepared_v3"
    grep -Fq 'na-cu001-pinned-qe-artifact-v0.1' "$prepared_v3"
    if grep -Fq 'make -j2 pw neb' "$prepared_v3"; then
      echo 'HOLD: fragile QE source rebuild remains in C7 prepare' >&2
      exit 2
    fi
    GH_TOKEN="${GH_TOKEN:?GH_TOKEN required}" bash "$prepared_v3" prepare

    cp bulk_run_audit/UPSTREAM_BULK_RUN_AUDIT.json base/
    sha256sum \
      bulk_run_audit/jobs.json \
      bulk_run_audit/artifacts.json \
      base/UPSTREAM_BULK_RUN_AUDIT.json \
      > base/UPSTREAM_BULK_RUN_AUDIT.sha256
    test -f base/QE_ENGINE_ARTIFACT_PROVENANCE.json
    sha256sum \
      na_cu001_ci/slab_runner_v2.py \
      na_cu001_ci/slab_runner_v3.py \
      na_cu001_ci/slab_runner_v4.py \
      na_cu001_ci/slab_runner_v5.py \
      na_cu001_ci/test_slab_runner_v4.py \
      na_cu001_ci/test_slab_runner_v5.py \
      na_cu001_ci/closure_engine_v3.py \
      na_cu001_ci/closure_engine_v4.py \
      na_cu001_ci/test_slab_handoff_v4.py \
      na_cu001_ci/workflow_contract_linter_v4_slab.py \
      na_cu001_ci/run_computational_stage_v4.sh \
      .github/workflows/na-cu001-v04-slab-route-v1.yml \
      > base/SLAB_ENTRYPOINT_SOURCE_MANIFEST.sha256
    ;;

  slab-case-one)
    runtime
    chmod +x qe_bundle/bin/pw.x
    layers="${2:?layers required}"
    vacuum="${3:?vacuum required}"
    kmesh="${4:?kmesh required}"
    tag="${5:?tag required}"
    expected_tag="l${layers}_v${vacuum}_k${kmesh}"
    [[ "$tag" == "$expected_tag" ]] || {
      echo "HOLD: slab job tag mismatch expected=$expected_tag actual=$tag" >&2
      exit 2
    }
    python3 - "$layers" "$vacuum" "$kmesh" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'na_cu001_ci')
from slab_runner_v2 import LAYERS, VACUUM, registered_kmeshes
from slab_runner_v3 import load_bulk_v04
layers=int(sys.argv[1]); vacuum=float(sys.argv[2]); kmesh=int(sys.argv[3])
bulk=load_bulk_v04(Path('base/BULK_HANDOFF.json'), Path('base/BULK_CONVERGENCE_RESULT.json'))
if layers not in LAYERS or vacuum not in VACUUM or kmesh not in registered_kmeshes(bulk['bulk_kmesh']):
    raise SystemExit('HOLD: workflow supplied an unregistered slab point')
PY
    case_root="slab_outputs/$tag"
    mkdir -p "$case_root"
    set +e
    python3 na_cu001_ci/slab_runner_v5.py run \
      --layers "$layers" \
      --vacuum "$vacuum" \
      --kmesh "$kmesh" \
      --handoff base/BULK_HANDOFF.json \
      --bulk-result base/BULK_CONVERGENCE_RESULT.json \
      --pw qe_bundle/bin/pw.x \
      --pseudo-dir qe_bundle/pseudos \
      --out "$case_root" \
      --np 2
    rc=$?
    set -e
    find "$case_root" -type d \( -name tmp -o -name '*.save' \) -prune -exec rm -rf {} + 2>/dev/null || true
    find "$case_root" -type f \( \
      -name '*.wfc*' -o -name 'charge-density.dat' -o -name 'data-file-schema.xml' \
      \) -delete 2>/dev/null || true
    mapfile -d '' compact_files < <(
      find "$case_root" -type f \( \
        -name run_record.json -o -name 'cu001_*.in' -o -name 'cu001_*.out' \
        \) -print0 | sort -z
    )
    if (( ${#compact_files[@]} > 0 )); then
      printf '%s\0' "${compact_files[@]}" | xargs -0 sha256sum > "$case_root/COMPACT_EVIDENCE.sha256"
    fi
    exit "$rc"
    ;;

  slab-analyze)
    mkdir -p stage2
    python3 na_cu001_ci/slab_runner_v5.py analyze \
      --records slab_outputs \
      --out stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json
    python3 na_cu001_ci/closure_engine_v4.py slab-handoff \
      --slab-result stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json \
      --bulk-handoff base/BULK_HANDOFF.json \
      --out stage2/SLAB_HANDOFF.json
    ;;

  *)
    echo "unsupported C6-C7 stage: $1" >&2
    exit 2
    ;;
esac
