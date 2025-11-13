#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-default}"
MOUNT="${2:-${CPY_MOUNT:-}}"

find_mount() {
  if [[ -n "$MOUNT" ]]; then
    [[ -d "$MOUNT" ]] || { echo "Mount path '$MOUNT' not found." >&2; exit 1; }
    echo "$MOUNT"; return
  fi
  # Common locations
  for d in /Volumes/CIRCUITPY "/media/$USER/CIRCUITPY" "/run/media/$USER/CIRCUITPY" /mnt/CIRCUITPY; do
    [[ -d "$d" ]] && { echo "$d"; return; }
  done
  # Fallback: search for boot_out.txt
  for d in /media/*/* /run/media/*/* /mnt/* /Volumes/*; do
    [[ -d "$d" ]] || continue
    [[ -f "$d/boot_out.txt" || -f "$d/code.py" ]] && { echo "$d"; return; }
  done
  echo "CIRCUITPY not found. Pass path as 2nd arg or set CPY_MOUNT." >&2
  exit 1
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

dst_root="$(find_mount)"
echo "CIRCUITPY: $dst_root"

src_boot="$repo_root/boot.py"
src_code="$repo_root/code.py"
src_lib="$repo_root/lib"

[[ -f "$src_boot" ]] || { echo "Missing $src_boot"; exit 1; }
[[ -f "$src_code" ]] || { echo "Missing $src_code"; exit 1; }

dst_boot="$dst_root/boot.py"
dst_code="$dst_root/code.py"
dst_lib="$dst_root/lib"

if [[ "$MODE" == "clean" ]]; then
  echo "Clean mode: removing $dst_lib ..."
  rm -rf "$dst_lib"
  sleep 0.1
fi

# Copy order: lib -> code.py -> boot.py
if [[ -d "$src_lib" ]]; then
  echo "Copying lib/ ..."
  mkdir -p "$dst_lib"
  # Use rsync if available (faster), else cp -R
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete-excluded "$src_lib"/ "$dst_lib"/
  else
    cp -R "$src_lib"/. "$dst_lib"/
  fi
fi

echo "Copying code.py ..."
cp -f "$src_code" "$dst_code"

echo "Copying boot.py ..."
cp -f "$src_boot" "$dst_boot"

# Flush writes
sync || true
echo "Done."
echo "If you changed boot.py, press RESET (or replug) to re-enumerate dual CDC."
