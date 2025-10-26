#!/usr/bin/env bash
set -euo pipefail

PYTHON="python3"
VER="$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
MAJOR="${VER%%.*}"; REST="${VER#*.}"; MINOR="${REST%%.*}"
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]; }; then
  echo "Python 3.8+ required (found $VER)"; exit 1
fi

[ -d .venv ] || $PYTHON -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r tools/requirements-dev.txt
echo "Bootstrap complete. Venv: .venv"
