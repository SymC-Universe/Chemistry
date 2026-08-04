#!/usr/bin/env bash
set -euo pipefail
V3=na_cu001_ci/run_computational_stage_v3.sh
WORKFLOW=.github/workflows/na-cu001-v04-slab-route-v1.yml

patch_v3_for_verified_packaging_exception() {
  local out="$1"
  python3 - "$V3" "$out" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
old='    [[ "$state" == "completed success" ]]'
new='    [[ "$state" == "completed success" || "$state" == "completed cancelled" ]]'
if old not in src: raise SystemExit('mechanical patch anchor missing: run-state check')
src=src.replace(old,new,1)
old="required={'na-cu001-bulk-extension-decision-v0.4','na-cu001-bulk-extension-all-summaries-v0.4','na-cu001-bulk-extension-raw-complete-v0.4'}"
new="required={'na-cu001-bulk-extension-decision-v0.4','na-cu001-bulk-extension-all-summaries-v0.4'}"
if old not in src: raise SystemExit('mechanical patch anchor missing: redundant aggregate requirement')
src=src.replace(old,new,1)
old='python3 na_cu001_ci/workflow_contract_linter_v3.py .github/workflows/na-cu001-computational-route-v3.yml'
new='python3 na_cu001_ci/workflow_contract_linter_v4_slab.py .github/workflows/na-cu001-v04-slab-route-v1.yml'
if old not in src: raise SystemExit('mechanical patch anchor missing: workflow linter')
src=src.replace(old,new,1)
src=src.replace('.github/workflows/na-cu001-computational-route-v3.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml', '.github/workflows/na-cu001-v04-slab-route-v1.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml',1)
Path(sys.argv[2]).write_text(src)
PY
  chmod +x "$out"
}

patch_v3_for_definitive_slab() {
  local out="$1"
  python3 - "$V3" "$out" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
old_runner='python3 na_cu001_ci/slab_runner_v3.py'
new_runner='python3 na_cu001_ci/slab_runner_v5.py'
runner_count=src.count(old_runner)
if runner_count != 2:
    raise SystemExit(f'mechanical patch anchor count for slab execution commands is {runner_count}, expected 2')
if 'from slab_runner_v3 import load_bulk_v04' not in src:
    raise SystemExit('mechanical patch anchor missing: v0.4 bulk helper import')
src=src.replace(old_runner,new_runner)
if 'from slab_runner_v5 import load_bulk_v04' in src:
    raise SystemExit('mechanical patch escaped into the v0.4 bulk helper import')
if src.count(new_runner) != 2:
    raise SystemExit('V5 execution command count is not exactly 2 after patching')
old_engine='ENGINE=na_cu001_ci/closure_engine_v3.py'
new_engine='ENGINE=na_cu001_ci/closure_engine_v4.py'
engine_count=src.count(old_engine)
if engine_count != 1:
    raise SystemExit(f'mechanical patch anchor count for closure engine is {engine_count}, expected 1')
src=src.replace(old_engine,new_engine,1)
Path(sys.argv[2]).write_text(src)
PY
  chmod +x "$out"
}

delegate_v3_with_definitive_slab() {
  local tmp
  tmp=$(mktemp)
  patch_v3_for_definitive_slab "$tmp"
  bash "$tmp" "$@"
}

case "${1:?stage required}" in
  prepare)
    sudo apt-get update
    sudo apt-get install -y gh python3 python3-numpy
    mkdir -p bulk_run_audit
    run_id="${BULK_EXTENSION_RUN_ID:?BULK_EXTENSION_RUN_ID required}"
    gh api --paginate "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}/jobs?filter=latest&per_page=100" > bulk_run_audit/jobs.json
    gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${run_id}/artifacts?per_page=100" > bulk_run_audit/artifacts.json
    python3 na_cu001_ci/bulk_v04_run_audit_v1.py --jobs bulk_run_audit/jobs.json --artifacts bulk_run_audit/artifacts.json --run-id "$run_id" --out bulk_run_audit/UPSTREAM_BULK_RUN_AUDIT.json
    python3 na_cu001_ci/test_bulk_v04_run_audit_v1.py
    python3 -m py_compile \
      na_cu001_ci/slab_runner_v4.py \
      na_cu001_ci/slab_runner_v5.py \
      na_cu001_ci/test_slab_runner_v4.py \
      na_cu001_ci/test_slab_runner_v5.py \
      na_cu001_ci/closure_engine_v4.py \
      na_cu001_ci/test_slab_handoff_v4.py \
      na_cu001_ci/workflow_contract_linter_v4_slab.py
    (cd na_cu001_ci && \
      python3 test_slab_runner_v4.py && \
      python3 test_slab_runner_v5.py && \
      python3 test_slab_handoff_v4.py)
    definitive_tmp=$(mktemp)
    patch_v3_for_definitive_slab "$definitive_tmp"
    bash -n "$definitive_tmp"
    grep -Fq 'from slab_runner_v3 import load_bulk_v04' "$definitive_tmp"
    test "$(grep -Fc 'python3 na_cu001_ci/slab_runner_v5.py' "$definitive_tmp")" -eq 2
    grep -Fq 'ENGINE=na_cu001_ci/closure_engine_v4.py' "$definitive_tmp"
    if grep -Fq 'from slab_runner_v5 import load_bulk_v04' "$definitive_tmp"; then
      echo 'HOLD: V5 patch altered the v0.4 bulk helper import' >&2
      exit 2
    fi
    tmp=$(mktemp)
    patch_v3_for_verified_packaging_exception "$tmp"
    GH_TOKEN="${GH_TOKEN:?GH_TOKEN required}" bash "$tmp" prepare
    cp bulk_run_audit/UPSTREAM_BULK_RUN_AUDIT.json base/
    sha256sum bulk_run_audit/jobs.json bulk_run_audit/artifacts.json base/UPSTREAM_BULK_RUN_AUDIT.json > base/UPSTREAM_BULK_RUN_AUDIT.sha256
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
  slab-case|slab-analyze)
    delegate_v3_with_definitive_slab "$@"
    ;;
  *)
    echo "unsupported C6-C7 stage: $1" >&2; exit 2
    ;;
esac
