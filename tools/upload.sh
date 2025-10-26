#!/usr/bin/env bash
# Upload helper for Pico (Linux/macOS).
# Forwards flags to tools/upload_to_pico.py and bootstraps .venv if needed.

set -euo pipefail

PORT=""
CLEAN=0
DRYRUN=0
YES=0
RESET=0
LIST=0
SRC_ROOT="."
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)      PORT="$2"; shift 2 ;;
    --clean)     CLEAN=1; shift ;;
    --dry-run)   DRYRUN=1; shift ;;
    --yes|-y)    YES=1; shift ;;
    --reset)     RESET=1; shift ;;
    --list)      LIST=1; shift ;;
    --src-root)  SRC_ROOT="$2"; shift 2 ;;
    --)          shift; EXTRA+=("$@"); break ;;
    *)           EXTRA+=("$1"); shift ;;
  esac
done

# Go to repo root (script dir/..)
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/.."

# Bootstrap venv if missing
if [[ ! -d ".venv" ]]; then
  echo "Bootstrapping .venv..."
  bash tools/bootstrap.sh
fi

# Activate venv and ensure tools
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r tools/requirements-dev.txt >/dev/null

# Build args for uploader
ARGS=()
[[ -n "$PORT" ]]        && ARGS+=("--port" "$PORT")
[[ $CLEAN -eq 1 ]]      && ARGS+=("--clean")
[[ $DRYRUN -eq 1 ]]     && ARGS+=("--dry-run")
[[ $YES -eq 1 ]]        && ARGS+=("--yes")
[[ $RESET -eq 1 ]]      && ARGS+=("--reset")
[[ $LIST -eq 1 ]]       && ARGS+=("--list")
[[ "$SRC_ROOT" != "." ]]&& ARGS+=("--src-root" "$SRC_ROOT")
ARGS+=("${EXTRA[@]}")

python tools/upload_to_pico.py "${ARGS[@]}"
