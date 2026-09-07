#!/usr/bin/env bash
set -euxo pipefail

cleanup_restart_scratch() {
  find . -type d -name tmp -prune -exec rm -rf {} + 2>/dev/null || true
}
trap cleanup_restart_scratch EXIT

runtime() {
  sudo apt-get update
  sudo apt-get install -y openmpi-bin libopenmpi-dev libopenblas-dev liblapack-dev libfftw3-dev python3-numpy
}

case "${1:?stage required}" in
  prepare)
    sudo apt-get update
    sudo apt-get install -y gfortran make m4 perl curl ca-certificates libopenblas-dev liblapack-dev libfftw3-dev libopenmpi-dev openmpi-bin python3-numpy
    mkdir -p base imported_bulk qe_bundle/bin qe_bundle/pseudos qe_bundle/meta sssp_archive stage4_raw "$RUNNER_TEMP/qe-src"
    run_id="${BULK_RUN_ID:-30803996866}"
    ready=0
    for attempt in $(seq 1 150); do
      state=$(gh run view "$run_id" --repo "$GITHUB_REPOSITORY" --json status,conclusion --jq '.status + " " + (.conclusion // "")')
      status=${state%% *}; conclusion=${state#* }
      echo "bulk run $run_id: $state"
      if [[ "$status" == completed && "$conclusion" == success ]]; then ready=1; break; fi
      if [[ "$status" == completed && "$conclusion" != success ]]; then echo "HOLD: bulk run failed" >&2; exit 2; fi
      sleep 120
    done
    [[ "$ready" == 1 ]]
    gh run download "$run_id" --repo "$GITHUB_REPOSITORY" --name na-cu001-bulk-decision-handoff --dir imported_bulk
    cp "$(find imported_bulk -type f -name BULK_HANDOFF.json -print -quit)" base/BULK_HANDOFF.json
    cp "$(find imported_bulk -type f -name BULK_CONVERGENCE_RESULT.json -print -quit)" base/BULK_CONVERGENCE_RESULT.json
    curl -L --retry 5 --retry-delay 5 https://gitlab.com/QEF/q-e/-/archive/qe-7.6/q-e-qe-7.6.tar.gz -o "$RUNNER_TEMP/qe-7.6.tar.gz"
    sha256sum "$RUNNER_TEMP/qe-7.6.tar.gz" > qe_bundle/meta/qe_source.sha256
    tar -xzf "$RUNNER_TEMP/qe-7.6.tar.gz" -C "$RUNNER_TEMP/qe-src" --strip-components=1
    (cd "$RUNNER_TEMP/qe-src" && ./configure MPIF90=mpif90 F90=gfortran CC=mpicc && make -j2 pw neb)
    cp "$RUNNER_TEMP/qe-src/bin/pw.x" "$RUNNER_TEMP/qe-src/bin/neb.x" qe_bundle/bin/
    chmod +x qe_bundle/bin/pw.x qe_bundle/bin/neb.x
    sha256sum qe_bundle/bin/pw.x qe_bundle/bin/neb.x > qe_bundle/meta/engine_binaries.sha256
    curl -L --retry 5 --retry-delay 5 https://raw.githubusercontent.com/unkcpz/sssp-verify-scripts/refs/heads/main/2-experiments/finalized_scripts/010-extract-eff-lib/SSSP-lib-pbe-eff-v2.tar.gz -o qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz
    sha256sum qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz > qe_bundle/meta/sssp_archive.sha256
    tar -xzf qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz -C sssp_archive
    cp "$(find sssp_archive -type f -name 'Cu.paw.pbe.z_11.ld1.psl.v1.0.0-low.upf' -print -quit)" qe_bundle/pseudos/
    python3 na_cu001_ci/na_pseudo_probe.py --archive-root sssp_archive --archive qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz --out base/NA_PSEUDO_PROBE.json
    python3 na_cu001_ci/closure_engine.py resolve-na --na-probe base/NA_PSEUDO_PROBE.json --bulk-handoff base/BULK_HANDOFF.json --pseudo-root sssp_archive --pseudo-dir qe_bundle/pseudos --pw qe_bundle/bin/pw.x --out-dir stage4_raw --out base/NA_PSEUDO_HANDOFF.json --np 1
    sha256sum qe_bundle/pseudos/* > qe_bundle/meta/pseudopotentials.sha256
    python3 -m py_compile na_cu001_ci/closure_engine.py na_cu001_ci/slab_runner.py na_cu001_ci/na_pseudo_probe.py na_cu001_ci/validate_integration_chain.py
    python3 na_cu001_ci/test_closure_engine.py
    ;;
  slab-case)
    runtime; chmod +x qe_bundle/bin/pw.x
    layers="$2"; vacuum="$3"; tag="$4"
    case "$layers" in 5|7|9|11) ;; *) echo "unregistered layer count" >&2; exit 2;; esac
    case "$vacuum" in 12|16|20|24) ;; *) echo "unregistered vacuum" >&2; exit 2;; esac
    mkdir -p "slab_outputs/$tag"
    meshes=$(python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'na_cu001_ci')
from slab_runner import load_bulk, registered_kmeshes
b=load_bulk(Path('base/BULK_HANDOFF.json'),Path('base/BULK_CONVERGENCE_RESULT.json'))
print(' '.join(map(str,registered_kmeshes(b['bulk_kmesh']))))
PY
)
    for kmesh in $meshes; do
      python3 na_cu001_ci/slab_runner.py run --layers "$layers" --vacuum "$vacuum" --kmesh "$kmesh" --handoff base/BULK_HANDOFF.json --bulk-result base/BULK_CONVERGENCE_RESULT.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out "slab_outputs/$tag" --np 2
    done
    ;;
  slab-analyze)
    mkdir -p stage2
    python3 na_cu001_ci/slab_runner.py analyze --records slab_outputs --out stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json
    python3 na_cu001_ci/closure_engine.py slab-handoff --slab-result stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json --bulk-handoff base/BULK_HANDOFF.json --out stage2/SLAB_HANDOFF.json
    ;;
  clean)
    runtime; chmod +x qe_bundle/bin/pw.x; mkdir -p stage3 stage3_raw
    python3 na_cu001_ci/closure_engine.py clean-relax --slab-handoff stage2/SLAB_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage3_raw --out stage3/RELAXED_CLEAN_SURFACE_HANDOFF.json --np 2
    ;;
  adsorption-case)
    runtime; chmod +x qe_bundle/bin/pw.x; site="$2"; height="$3"; tag="$4"; mkdir -p "ads_records/$tag"
    python3 na_cu001_ci/closure_engine.py adsorption-run --site "$site" --height "$height" --clean-handoff stage3/RELAXED_CLEAN_SURFACE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "ads_records/$tag" --np 2
    ;;
  adsorption-analyze)
    mkdir -p stage5
    python3 na_cu001_ci/closure_engine.py adsorption-analyze --records ads_records --clean-handoff stage3/RELAXED_CLEAN_SURFACE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --out stage5/ADSORPTION_SITE_HANDOFF.json
    ;;
  endpoints)
    runtime; chmod +x qe_bundle/bin/pw.x; mkdir -p stage6 stage6_raw
    python3 na_cu001_ci/closure_engine.py endpoints --adsorption-handoff stage5/ADSORPTION_SITE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage6_raw --out stage6/ENDPOINTS_HANDOFF.json --np 2
    ;;
  neb-case)
    runtime; chmod +x qe_bundle/bin/neb.x; images="$2"; mkdir -p "neb_records/n$images"
    python3 na_cu001_ci/closure_engine.py neb-run --images "$images" --endpoints-handoff stage6/ENDPOINTS_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --neb qe_bundle/bin/neb.x --pseudo-dir qe_bundle/pseudos --out-dir "neb_records/n$images" --np 2
    ;;
  neb-analyze)
    mkdir -p stage7
    python3 na_cu001_ci/closure_engine.py neb-analyze --records neb_records --endpoints-handoff stage6/ENDPOINTS_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --out stage7/PATH_CONVERGENCE_HANDOFF.json
    ;;
  ci)
    runtime; chmod +x qe_bundle/bin/neb.x; mkdir -p stage8 stage8_raw
    python3 na_cu001_ci/closure_engine.py ci-neb --path-handoff stage7/PATH_CONVERGENCE_HANDOFF.json --endpoints-handoff stage6/ENDPOINTS_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --neb qe_bundle/bin/neb.x --pseudo-dir qe_bundle/pseudos --out-dir stage8_raw --out stage8/CI_NEB_HANDOFF.json --np 2
    ;;
  saddle)
    runtime; chmod +x qe_bundle/bin/pw.x; mkdir -p stage9 stage9_raw
    python3 na_cu001_ci/closure_engine.py saddle --endpoints-handoff stage6/ENDPOINTS_HANDOFF.json --ci-handoff stage8/CI_NEB_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage9_raw --out stage9/SADDLE_HANDOFF.json --np 2
    ;;
  finalize)
    mkdir -p closure
    cp base/BULK_HANDOFF.json base/BULK_CONVERGENCE_RESULT.json base/NA_PSEUDO_PROBE.json base/NA_PSEUDO_HANDOFF.json closure/
    cp stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json stage2/SLAB_HANDOFF.json stage3/RELAXED_CLEAN_SURFACE_HANDOFF.json stage5/ADSORPTION_SITE_HANDOFF.json stage6/ENDPOINTS_HANDOFF.json stage7/PATH_CONVERGENCE_HANDOFF.json stage8/CI_NEB_HANDOFF.json stage9/SADDLE_HANDOFF.json closure/
    cp na_cu001_ci/public_evidence_candidates.json closure/
    python3 na_cu001_ci/closure_engine.py barrier --path-handoff closure/PATH_CONVERGENCE_HANDOFF.json --ci-handoff closure/CI_NEB_HANDOFF.json --saddle-handoff closure/SADDLE_HANDOFF.json --out closure/BARRIER_COORDINATE.json
    python3 na_cu001_ci/closure_engine.py atlas --barrier-coordinate closure/BARRIER_COORDINATE.json --public-evidence closure/public_evidence_candidates.json --out closure/ATLAS_ADMISSION_RECORD.json
    test -d raw
    python3 na_cu001_ci/closure_engine.py manifest --root raw --out closure/RAW_ARTIFACT_INDEX.json
    python3 na_cu001_ci/validate_integration_chain.py --plan na_cu001_ci/integration_closure_plan.json --artifacts closure --raw-root raw --out closure/INTEGRATION_READINESS.json
    python3 na_cu001_ci/closure_engine.py manifest --root closure --out closure/COMPUTATIONAL_MANIFEST.json
    ;;
  *) echo "unknown stage: $1" >&2; exit 64;;
esac
