#!/usr/bin/env bash
set -euo pipefail

# PowerCell one-command launcher for shared-H v0.2 local replication/recovery.
# Default TOTAL wall window is 5.75 h, including setup/download, leaving margin
# before a nominal six-hour availability window.

TOTAL_HOURS="${1:-5.75}"
ROOT="/home/n8ofalltrades/.symc_shared_h_v02_powercell"
REPO="$ROOT/repo"
SOURCE="$ROOT/source"
SOURCE_ZIP="$ROOT/source_artifact_10527449397.zip"
RUNROOT="$ROOT/run"
LOG="$ROOT/POWER_CELL_RUN.log"
PIDFILE="$ROOT/POWER_CELL_RUN.pid"
BRANCH="bridge/h-ru0001-relax-pass-20260917"
REMOTE="https://github.com/SymC-Universe/Chemistry.git"
PW="/home/n8ofalltrades/.symc_chemistry_ru_bridge_v2_2/pw.x"
PW_SHA="2b1ede22d276b1d4dab3e31212f306e88ae57e00f33ce6b532b849493a457855"
ARTIFACT_ID="10527449397"
ARTIFACT_SHA="f2324898e0e7e14dae5c23c7a815e20b15900b57e05aff9020b56131c050a9d5"
ARTIFACT_URL="https://api.github.com/repos/SymC-Universe/Chemistry/actions/artifacts/$ARTIFACT_ID/zip"
H_COMMIT="0fb07d89d13407b0f00a0a3b8c21d7e387fb56f9"
H_PATH="libraries-pbe/nc-sg15-oncvpsp4/H.nc.pbe.z_1.oncvpsp4.sg15.v0.upf"
PSEUDO="$ROOT/H.nc.pbe.z_1.oncvpsp4.sg15.v0.upf"
PSEUDO_MD5="39a7d154f04d65093d603a437119a874"

START_EPOCH="$(date +%s)"
mkdir -p "$ROOT" "$RUNROOT"

if [[ -f "$PIDFILE" ]]; then
  oldpid="$(cat "$PIDFILE" || true)"
  if [[ -n "$oldpid" ]] && kill -0 "$oldpid" 2>/dev/null; then
    echo "A PowerCell shared-H v0.2 session is already running as PID $oldpid."
    echo "Monitor with: tail -f '$LOG'"
    exit 0
  fi
fi

for cmd in git curl python3 unzip sha256sum md5sum; do
  command -v "$cmd" >/dev/null || {
    echo "Missing required command: $cmd"
    exit 2
  }
done

[[ -x "$PW" ]] || {
  echo "Verified PowerCell QE binary not found/executable at: $PW"
  exit 2
}
echo "$PW_SHA  $PW" | sha256sum -c -
ldd "$PW" | tee "$ROOT/pw_ldd.txt"
if grep -q "not found" "$ROOT/pw_ldd.txt"; then
  echo "QE has unresolved shared-library dependencies."
  exit 2
fi

# Dedicated clone: never resets or alters the user's other Chemistry working tree.
if [[ ! -d "$REPO/.git" ]]; then
  git clone --depth 1 --branch "$BRANCH" "$REMOTE" "$REPO"
else
  git -C "$REPO" fetch --depth 1 origin "$BRANCH"
  git -C "$REPO" checkout -B powercell-shared-h-v02 FETCH_HEAD
fi

PROTOCOL="$REPO/systems/shared/H_PSEUDOPOTENTIAL_QUALIFICATION_RECOVERY_v0.2.json"
RUNNER="$REPO/systems/shared/powercell_shared_h_v02.py"
python3 -m json.tool "$PROTOCOL" >/dev/null
python3 -m py_compile "$RUNNER"

curl -L --fail --retry 5 --retry-delay 3   "https://raw.githubusercontent.com/unkcpz/sssp-verify-scripts/$H_COMMIT/$H_PATH"   -o "$PSEUDO"
echo "$PSEUDO_MD5  $PSEUDO" | md5sum -c -

# Exact parent artifact is needed for isolated-H exact restart. Reuse it if
# already verified from an earlier PowerCell session.
if [[ ! -f "$ROOT/PARENT_ARTIFACT_VERIFIED" ]]; then
  avail_kb="$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')"
  if (( avail_kb < 6500000 )); then
    echo "Need at least ~6.5 GB free disk for parent artifact + restart copies."
    df -h "$ROOT"
    exit 2
  fi
  rm -rf "$SOURCE"
  mkdir -p "$SOURCE"
  rm -f "$SOURCE_ZIP"

  echo "Downloading exact v0.1 qualification artifact (~2.04 GB)..."
  direct_ok=0
  if curl -L --fail --retry 3 --retry-delay 3 "$ARTIFACT_URL" -o "$SOURCE_ZIP"; then
    if echo "$ARTIFACT_SHA  $SOURCE_ZIP" | sha256sum -c -; then
      unzip -q "$SOURCE_ZIP" -d "$SOURCE"
      direct_ok=1
    else
      echo "Direct artifact ZIP digest mismatch; refusing it."
      rm -f "$SOURCE_ZIP"
    fi
  fi

  if (( direct_ok == 0 )); then
    if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then
      echo "Falling back to authenticated GitHub CLI artifact download..."
      rm -rf "$SOURCE"
      mkdir -p "$SOURCE"
      gh run download 35295414137         -R SymC-Universe/Chemistry         -n system3-shared-h-pseudopotential-qualification-v1         -D "$SOURCE"
    else
      echo
      echo "GitHub artifact download requires authentication on this machine."
      echo "Run:"
      echo "  sudo apt update && sudo apt install -y gh"
      echo "  gh auth login"
      echo "Then rerun this launcher. No computation has been started."
      exit 3
    fi
  fi

  python3 - "$SOURCE" <<'PY'
import json, pathlib, sys
root=pathlib.Path(sys.argv[1])
p=root/"H_PSEUDOPOTENTIAL_QUALIFICATION_RESULT.json"
if not p.is_file():
    raise SystemExit("Parent qualification result JSON missing")
r=json.loads(p.read_text())
if r.get("status")!="SHARED_H_PSEUDOPOTENTIAL_HOLD":
    raise SystemExit(f"Unexpected parent disposition: {r.get('status')}")
for tag in ("70","80"):
    q=root/f"atom_{tag}"/"qe_tmp"/f"H_atom_{tag}.save"/"data-file-schema.xml"
    if not q.is_file() or q.stat().st_size == 0:
        raise SystemExit(f"Missing exact atom restart checkpoint: {q}")
print("PARENT_V0_1_HOLD_AND_ATOM_CHECKPOINTS_VERIFIED")
PY
  printf '%s\n' "$ARTIFACT_ID $ARTIFACT_SHA" > "$ROOT/PARENT_ARTIFACT_VERIFIED"
fi

ELAPSED="$(( $(date +%s) - START_EPOCH ))"
TOTAL_SECONDS="$(python3 -c "print(int(float('$TOTAL_HOURS')*3600))")"
# Reserve ten minutes outside the QE session for clean shutdown before the
# user's total wall window expires.
REMAINING="$(( TOTAL_SECONDS - ELAPSED - 600 ))"
if (( REMAINING < 1800 )); then
  echo "Setup consumed too much of the requested wall window; refusing to start a short unsafe session."
  exit 4
fi
RUN_HOURS="$(python3 -c "print($REMAINING/3600.0)")"

echo
echo "PowerCell setup verified."
echo "Total requested wall window: $TOTAL_HOURS h"
echo "Setup elapsed: $ELAPSED s"
echo "QE session budget: $RUN_HOURS h"
echo "Queue: H2-70 -> H2-80 -> atom-70 -> atom-80"
echo "Only one QE process will run at a time."
echo "Each QE chunk uses CONTROL.max_seconds <= 3600 and writes an exact restart state."
echo

: > "$LOG"
nohup env   OMP_NUM_THREADS=1   OPENBLAS_NUM_THREADS=1   MKL_NUM_THREADS=1   python3 "$RUNNER"     --protocol "$PROTOCOL"     --pw "$PW"     --pseudo "$PSEUDO"     --source-root "$SOURCE"     --work-root "$RUNROOT"     --hours "$RUN_HOURS"     --order "h2-70,h2-80,atom-70,atom-80"     > "$LOG" 2>&1 &

pid=$!
echo "$pid" > "$PIDFILE"

echo "POWERCELL_SHARED_H_V02_STARTED PID=$pid"
echo "Monitor:"
echo "  tail -f '$LOG'"
echo "Session state:"
echo "  cat '$RUNROOT/POWER_CELL_SESSION.json'"
echo "Stop only if necessary:"
echo "  kill $pid"
echo
echo "The launcher will stop starting new QE chunks before the wall budget expires."
