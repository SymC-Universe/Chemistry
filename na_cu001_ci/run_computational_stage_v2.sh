#!/usr/bin/env bash
set -euxo pipefail

PROTOCOL=na_cu001_ci/method_protocol_v0.2.json
ENGINE=na_cu001_ci/closure_engine_v2.py

cleanup_restart_scratch() { find . -type d -name tmp -prune -exec rm -rf {} + 2>/dev/null || true; }
trap cleanup_restart_scratch EXIT
runtime() { sudo apt-get update; sudo apt-get install -y openmpi-bin libopenmpi-dev libopenblas-dev liblapack-dev libfftw3-dev python3-numpy; }

case "${1:?stage required}" in
  prepare)
    sudo apt-get update
    sudo apt-get install -y gfortran make m4 perl curl ca-certificates libopenblas-dev liblapack-dev libfftw3-dev libopenmpi-dev openmpi-bin python3-numpy python3-yaml gh
    mkdir -p base imported_bulk qe_bundle/bin qe_bundle/pseudos qe_bundle/meta sssp_archive holdout_raw "$RUNNER_TEMP/qe-src"
    run_id="${BULK_RUN_ID:-30803996866}"
    state=$(gh run view "$run_id" --repo "$GITHUB_REPOSITORY" --json status,conclusion --jq '.status + " " + (.conclusion // "")')
    [[ "$state" == "completed success" ]]
    gh run download "$run_id" --repo "$GITHUB_REPOSITORY" --name na-cu001-bulk-decision-handoff --dir imported_bulk
    mkdir -p base/bulk_summaries
    find imported_bulk -type f -name 'summary_e*_k*.json' -exec cp {} base/bulk_summaries/ \;
    test "$(find base/bulk_summaries -type f -name 'summary_e*_k*.json' | wc -l)" -eq 20

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

    python3 na_cu001_ci/bulk_runner_v2.py run --ecut 80 --kmesh 16 --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out holdout_raw/e80_k16 --np 2
    cp holdout_raw/e80_k16/summary_e80_k16.json base/bulk_summaries/
    python3 na_cu001_ci/bulk_runner_v2.py analyze --summaries base/bulk_summaries --reference-ecut 80 --reference-kmesh 16 --out base/BULK_CONVERGENCE_RESULT.json
    python3 na_cu001_ci/bulk_runner_v2.py handoff --result base/BULK_CONVERGENCE_RESULT.json --out base/BULK_HANDOFF.json

    python3 na_cu001_ci/na_pseudo_probe_v2.py --archive-root sssp_archive --archive qe_bundle/meta/SSSP-lib-pbe-eff-v2.tar.gz --protocol "$PROTOCOL" --out base/NA_PSEUDO_PROBE.json
    python3 "$ENGINE" resolve-na --protocol "$PROTOCOL" --probe base/NA_PSEUDO_PROBE.json --bulk-handoff base/BULK_HANDOFF.json --pseudo-root sssp_archive --pseudo-dir qe_bundle/pseudos --pw qe_bundle/bin/pw.x --out-dir holdout_raw/na_reference --out base/NA_PSEUDO_HANDOFF.json --np 1
    python3 -m py_compile na_cu001_ci/*.py
    python3 na_cu001_ci/test_closure_engine.py
    python3 na_cu001_ci/test_closure_engine_v2.py
    python3 na_cu001_ci/test_negative_gates_v2.py
    python3 na_cu001_ci/workflow_contract_linter_v2.py .github/workflows/na-cu001-computational-route-v2.yml
    python3 na_cu001_ci/artifact_contract_linter_v2.py --plan na_cu001_ci/integration_closure_plan_v0.2.json --stage-script na_cu001_ci/run_computational_stage_v2.sh
    printf '%s\n' "$GITHUB_SHA" > base/COMPUTATIONAL_SOURCE_COMMIT.txt
    { find na_cu001_ci -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' -o -name '*.md' -o -name '*.tex' -o -name '*.sh' \) -print;       printf '%s\n' .github/workflows/na-cu001-computational-route-v2.yml .github/workflows/na-cu001-na-pseudo-probe-v2.yml; }       | LC_ALL=C sort | xargs sha256sum > base/SOURCE_CODE_MANIFEST.sha256
    ;;
  slab-case)
    runtime; chmod +x qe_bundle/bin/pw.x
    layers="$2"; vacuum="$3"; tag="$4"; mkdir -p "slab_outputs/$tag"
    meshes=$(python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,'na_cu001_ci')
from slab_runner import load_bulk,registered_kmeshes
b=load_bulk(Path('base/BULK_HANDOFF.json'),Path('base/BULK_CONVERGENCE_RESULT.json'))
print(' '.join(map(str,registered_kmeshes(b['bulk_kmesh']))))
PY
)
    for kmesh in $meshes; do python3 na_cu001_ci/slab_runner_v2.py run --layers "$layers" --vacuum "$vacuum" --kmesh "$kmesh" --handoff base/BULK_HANDOFF.json --bulk-result base/BULK_CONVERGENCE_RESULT.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out "slab_outputs/$tag" --np 2; done
    ;;
  slab-analyze)
    mkdir -p stage2
    python3 na_cu001_ci/slab_runner_v2.py analyze --records slab_outputs --out stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json
    python3 "$ENGINE" slab-handoff --slab-result stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json --bulk-handoff base/BULK_HANDOFF.json --out stage2/SLAB_HANDOFF.json
    ;;
  parity)
    runtime; mkdir -p stage3 stage3_raw; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" parity --protocol "$PROTOCOL" --slab-handoff stage2/SLAB_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage3_raw/parity --out stage3/ELECTROSTATIC_CONSISTENCY.json --np 2
    ;;
  clean)
    runtime; mkdir -p stage4 stage4_raw; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" clean --protocol "$PROTOCOL" --slab-handoff stage2/SLAB_HANDOFF.json --parity-handoff stage3/ELECTROSTATIC_CONSISTENCY.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage4_raw --out stage4/RELAXED_CLEAN_SURFACE_HANDOFF.json --np 2
    ;;
  adsorption-case)
    runtime; mobility="$2"; site="$3"; height="$4"; tag="$5"; mkdir -p "ads_records/$tag"; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" adsorption-run --protocol "$PROTOCOL" --mobility "$mobility" --site "$site" --height "$height" --clean-handoff stage4/RELAXED_CLEAN_SURFACE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --parity-handoff stage3/ELECTROSTATIC_CONSISTENCY.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "ads_records/$tag" --np 2
    ;;
  adsorption-analyze)
    mkdir -p stage6
    python3 "$ENGINE" adsorption-analyze --protocol "$PROTOCOL" --records ads_records --clean-handoff stage4/RELAXED_CLEAN_SURFACE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --parity-handoff stage3/ELECTROSTATIC_CONSISTENCY.json --out stage6/ADSORPTION_SITE_HANDOFF.json
    ;;
  endpoints)
    runtime; mobility="$2"; mkdir -p "stage7_$mobility" "stage7_raw_$mobility"; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" endpoints --protocol "$PROTOCOL" --mobility "$mobility" --adsorption-handoff stage6/ADSORPTION_SITE_HANDOFF.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "stage7_raw_$mobility" --out "stage7_$mobility/ENDPOINTS_${mobility^^}.json" --np 2
    ;;
  neb-case)
    runtime; mobility="$2"; images="$3"; mkdir -p "neb_records/${mobility}_n${images}"; chmod +x qe_bundle/bin/neb.x
    python3 "$ENGINE" neb-run --protocol "$PROTOCOL" --images "$images" --endpoints-handoff "stage7_$mobility/ENDPOINTS_${mobility^^}.json" --na-handoff base/NA_PSEUDO_HANDOFF.json --neb qe_bundle/bin/neb.x --pseudo-dir qe_bundle/pseudos --out-dir "neb_records/${mobility}_n${images}" --np 2
    ;;
  neb-analyze)
    mobility="$2"; mkdir -p "stage9_$mobility"
    python3 "$ENGINE" neb-analyze --protocol "$PROTOCOL" --mobility "$mobility" --records neb_records --endpoints-handoff "stage7_$mobility/ENDPOINTS_${mobility^^}.json" --na-handoff base/NA_PSEUDO_HANDOFF.json --out "stage9_$mobility/PATH_${mobility^^}.json"
    ;;
  ci)
    runtime; mobility="$2"; mkdir -p "stage11_$mobility" "stage11_raw_$mobility"; chmod +x qe_bundle/bin/neb.x
    python3 "$ENGINE" ci --protocol "$PROTOCOL" --path-handoff "stage9_$mobility/PATH_${mobility^^}.json" --endpoints-handoff "stage7_$mobility/ENDPOINTS_${mobility^^}.json" --na-handoff base/NA_PSEUDO_HANDOFF.json --neb qe_bundle/bin/neb.x --pseudo-dir qe_bundle/pseudos --out-dir "stage11_raw_$mobility" --out "stage11_$mobility/CI_${mobility^^}.json" --np 2
    ;;
  mobility-gate)
    mkdir -p stage13
    python3 "$ENGINE" mobility-gate --protocol "$PROTOCOL" --primary-ci stage11_primary/CI_PRIMARY.json --expanded-ci stage11_expanded/CI_EXPANDED.json --primary-endpoints stage7_primary/ENDPOINTS_PRIMARY.json --expanded-endpoints stage7_expanded/ENDPOINTS_EXPANDED.json --primary-path stage9_primary/PATH_PRIMARY.json --expanded-path stage9_expanded/PATH_EXPANDED.json --out stage13/MOBILITY_CONVERGENCE.json
    ;;
  hessian-plan)
    mkdir -p stage14
    python3 "$ENGINE" hessian-plan --protocol "$PROTOCOL" --mobility-gate stage13/MOBILITY_CONVERGENCE.json --primary-endpoints stage7_primary/ENDPOINTS_PRIMARY.json --expanded-endpoints stage7_expanded/ENDPOINTS_EXPANDED.json --primary-ci stage11_primary/CI_PRIMARY.json --expanded-ci stage11_expanded/CI_EXPANDED.json --out stage14/HESSIAN_PLAN.json
    ;;
  hessian-center)
    runtime; center="$2"; mkdir -p "hessian_centers/$center"; chmod +x qe_bundle/bin/pw.x
    kmesh=$(python3 -c "import json;print(json.load(open('stage14/HESSIAN_PLAN.json'))['method']['kmesh'])")
    python3 "$ENGINE" hessian-center --protocol "$PROTOCOL" --center "$center" --plan stage14/HESSIAN_PLAN.json --na-handoff base/NA_PSEUDO_HANDOFF.json --kmesh "$kmesh" --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "hessian_centers/$center/raw" --out "hessian_centers/$center/record.json" --np 2
    ;;
  hessian-case)
    runtime; center="$2"; region="$3"; delta="$4"; slot="$5"; tag="$center-$region-$delta-$slot"; mkdir -p "hessian_records/$tag"; chmod +x qe_bundle/bin/pw.x
    kmesh=$(python3 -c "import json;print(json.load(open('stage14/HESSIAN_PLAN.json'))['method']['kmesh'])")
    python3 "$ENGINE" hessian-case --protocol "$PROTOCOL" --center "$center" --region "$region" --delta "$delta" --slot "$slot" --plan stage14/HESSIAN_PLAN.json --na-handoff base/NA_PSEUDO_HANDOFF.json --kmesh "$kmesh" --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "hessian_records/$tag/raw" --out "hessian_records/$tag/record.json" --np 2
    ;;
  hessian-analyze)
    mkdir -p stage14_final
    python3 "$ENGINE" hessian-analyze --protocol "$PROTOCOL" --plan stage14/HESSIAN_PLAN.json --mobility-gate stage13/MOBILITY_CONVERGENCE.json --records hessian_records --centers hessian_centers --out stage14_final/ACTIVE_REGION_HESSIAN.json
    ;;
  connectivity)
    runtime; mkdir -p stage15 stage15_raw; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" connectivity --protocol "$PROTOCOL" --plan stage14/HESSIAN_PLAN.json --hessian stage14_final/ACTIVE_REGION_HESSIAN.json --endpoints stage7_primary/ENDPOINTS_PRIMARY.json --ci stage11_primary/CI_PRIMARY.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir stage15_raw --out stage15/SADDLE_HANDOFF.json --np 2
    ;;
  sensitivity-case)
    runtime; variant="$2"; mkdir -p "sensitivity_records/$variant"; chmod +x qe_bundle/bin/pw.x
    python3 "$ENGINE" sensitivity-case --protocol "$PROTOCOL" --variant "$variant" --endpoints stage7_primary/ENDPOINTS_PRIMARY.json --ci stage11_primary/CI_PRIMARY.json --na-handoff base/NA_PSEUDO_HANDOFF.json --pw qe_bundle/bin/pw.x --pseudo-dir qe_bundle/pseudos --out-dir "sensitivity_records/$variant/raw" --out "sensitivity_records/$variant/record.json" --np 2
    ;;
  sensitivity-analyze)
    mkdir -p stage16
    python3 "$ENGINE" sensitivity-analyze --protocol "$PROTOCOL" --records sensitivity_records --mobility-gate stage13/MOBILITY_CONVERGENCE.json --path-handoff stage9_primary/PATH_PRIMARY.json --ci stage11_primary/CI_PRIMARY.json --out stage16/BARRIER_SENSITIVITY.json
    ;;
  finalize)
    mkdir -p closure raw
    cp base/BULK_HANDOFF.json base/BULK_CONVERGENCE_RESULT.json base/NA_PSEUDO_PROBE.json base/NA_PSEUDO_HANDOFF.json closure/
    cp -r base/bulk_summaries closure/bulk_summaries
    cp stage2/CLEAN_SLAB_CONVERGENCE_RESULT.json stage2/SLAB_HANDOFF.json stage3/ELECTROSTATIC_CONSISTENCY.json stage4/RELAXED_CLEAN_SURFACE_HANDOFF.json stage6/ADSORPTION_SITE_HANDOFF.json closure/
    cp stage7_primary/ENDPOINTS_PRIMARY.json stage7_expanded/ENDPOINTS_EXPANDED.json stage9_primary/PATH_PRIMARY.json stage9_expanded/PATH_EXPANDED.json closure/
    cp stage11_primary/CI_PRIMARY.json stage11_expanded/CI_EXPANDED.json stage13/MOBILITY_CONVERGENCE.json stage14/HESSIAN_PLAN.json stage14_final/ACTIVE_REGION_HESSIAN.json stage15/SADDLE_HANDOFF.json stage16/BARRIER_SENSITIVITY.json closure/
    cp "$PROTOCOL" na_cu001_ci/validation_selection_protocol_v0.1.json na_cu001_ci/public_evidence_candidates.json closure/
    cp na_cu001_ci/COMPUTATIONAL_PROCESS_AMENDMENT_v1.1.md na_cu001_ci/REPRODUCIBILITY_GUIDE_INSERT_v1.1.tex closure/
    cp base/COMPUTATIONAL_SOURCE_COMMIT.txt base/SOURCE_CODE_MANIFEST.sha256 closure/
    sha256sum -c closure/SOURCE_CODE_MANIFEST.sha256 | tee closure/SOURCE_MANIFEST_VERIFICATION.txt
    mkdir -p closure/source
    while read -r expected source_path; do cp --parents "$source_path" closure/source/; done < closure/SOURCE_CODE_MANIFEST.sha256
    python3 "$ENGINE" barrier --ci closure/CI_PRIMARY.json --saddle closure/SADDLE_HANDOFF.json --sensitivity closure/BARRIER_SENSITIVITY.json --mobility-gate closure/MOBILITY_CONVERGENCE.json --out closure/BARRIER_COORDINATE.json
    python3 "$ENGINE" atlas --barrier closure/BARRIER_COORDINATE.json --public-evidence closure/public_evidence_candidates.json --out closure/ATLAS_ADMISSION_RECORD.json
    python3 na_cu001_ci/tier_linter_v2.py closure/BARRIER_COORDINATE.json closure/ATLAS_ADMISSION_RECORD.json
    cp -r holdout_raw stage3_raw stage4_raw ads_records stage7_raw_primary stage7_raw_expanded neb_records stage11_raw_primary stage11_raw_expanded hessian_centers hessian_records stage15_raw sensitivity_records raw/ || true
    python3 "$ENGINE" manifest --root raw --out closure/RAW_ARTIFACT_INDEX.json
    python3 na_cu001_ci/validate_integration_chain_v2.py --plan na_cu001_ci/integration_closure_plan_v0.2.json --artifacts closure --raw-root raw --out closure/INTEGRATION_READINESS.json
    python3 "$ENGINE" manifest --root closure --out closure/COMPUTATIONAL_MANIFEST.json
    ;;
  *) echo "unknown stage: $1" >&2; exit 64;;
esac
