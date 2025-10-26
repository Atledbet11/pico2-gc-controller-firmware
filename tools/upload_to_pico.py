#!/usr/bin/env python3
"""
Upload/sync all *.py in ./src to a Pico running MicroPython via mpremote.

Mapping
- ./src/main.py (if present at src root) -> :/main.py
- ./src/boot.py (if present at src root) -> :/boot.py
- all other ./src/** -> :/app/<relative-path-from-src>

Clean
- --clean: enumerate files on the device in /app (and root /main.py, /boot.py
  if they appear in the local manifest) and remove anything not present locally.
- --dry-run: show what would be removed/copied, without changing device.

Examples
  python tools/upload_to_pico.py                  # auto-detect, prompt
  python tools/upload_to_pico.py --port COM3      # explicit port
  python tools/upload_to_pico.py --clean --yes    # clean sync w/o prompt
  python tools/upload_to_pico.py --list           # list candidate devices
"""
from __future__ import annotations
import argparse, os, sys, subprocess, textwrap
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from serial.tools import list_ports
except Exception:
    print("pyserial is required. Install with: pip install pyserial", file=sys.stderr)
    raise

APP_ROOT = "/app"     # safe subtree to own for your project on the device
RPI_VID  = 0x2E8A     # Raspberry Pi

# ---------- mpremote helpers ----------
def mp_cmd(port: str, *args: str) -> List[str]:
    return [sys.executable, "-m", "mpremote", "connect", port, *args]

def mp_run(port: str, *args: str) -> None:
    cmd = mp_cmd(port, *args)
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)

def mp_out(port: str, *args: str) -> str:
    cmd = mp_cmd(port, *args)
    print(">", " ".join(cmd))
    cp = subprocess.run(cmd, capture_output=True, text=True)
    if cp.returncode != 0:
        raise subprocess.CalledProcessError(cp.returncode, cmd, cp.stdout, cp.stderr)
    return cp.stdout

# ---------- device discovery ----------
def looks_like_pico(p) -> bool:
    manu = (getattr(p, "manufacturer", None) or "").lower()
    prod = (getattr(p, "product", None) or "").lower()
    desc = (getattr(p, "description", None) or "").lower()
    if getattr(p, "vid", None) == RPI_VID:
        return True
    return any(s for s in (manu, prod, desc) if "raspberry" in s or "pico" in s or "micropython" in s)

def find_candidates():
    return [p for p in list_ports.comports() if looks_like_pico(p)]

def choose_port() -> str:
    cands = find_candidates()
    if not cands:
        print("No Pico-like serial ports found (board must be in MicroPython mode, not BOOTSEL).", file=sys.stderr)
        sys.exit(3)
    if len(cands) == 1:
        return cands[0].device
    print("Multiple candidates:")
    for i, p in enumerate(cands, 1):
        vid = f"{getattr(p,'vid',None) or 0:04x}"
        pid = f"{getattr(p,'pid',None) or 0:04x}"
        print(f"  [{i}] {p.device} {vid}:{pid} {(p.manufacturer or 'Unknown')} {(p.product or '')} {(p.description or '')}")
    while True:
        s = input(f"Select [1-{len(cands)}]: ").strip()
        if s.isdigit() and 1 <= int(s) <= len(cands):
            return cands[int(s)-1].device
        print("Invalid selection.")

# ---------- manifest build ----------
def build_manifest(src_root: Path) -> Dict[str, Path]:
    """
    Return mapping of device destination path -> local file.
    """
    src_dir = src_root / "src"
    if not src_dir.is_dir():
        print(f"ERROR: missing ./src directory at {src_dir}", file=sys.stderr)
        sys.exit(2)

    manifest: Dict[str, Path] = {}

    for p in sorted(src_dir.rglob("*.py")):
        rel = p.relative_to(src_dir)
        if rel.parent == Path(".") and rel.name in ("main.py", "boot.py"):
            dest = f"/{rel.name}"
        else:
            # keep relative layout under /app
            dest = f"{APP_ROOT}/{str(rel).replace(os.sep, '/')}"
        manifest[dest] = p

    return manifest

# ---------- remote listing & cleaning ----------
LIST_SCRIPT = r"""
import os
def walk(d):
    try:
        lst = []
        for e in os.ilistdir(d):
            name = e[0]
            path = d.rstrip('/') + '/' + name if d != '/' else '/' + name
            try:
                is_dir = (e[1] & 0x4000) != 0  # best-effort DIR bit
            except:
                try:
                    is_dir = (os.stat(path)[0] & 0x4000) != 0
                except:
                    is_dir = False
            if is_dir:
                lst += walk(path)
            else:
                lst.append(path)
        return lst
    except Exception:
        return []
paths = []
# Project subtree:
paths += walk(%(APP_ROOT)r)
# Root files we might manage (only if present in local manifest):
for n in (%(root_candidates)r):
    try:
        os.stat(n)
        paths.append(n)
    except:
        pass
print("\n".join(paths))
"""

def list_device_files(port: str, managed_root_files: List[str]) -> List[str]:
    code = LIST_SCRIPT % {"APP_ROOT": APP_ROOT, "root_candidates": tuple(managed_root_files)}
    out = mp_out(port, "exec", code)
    return [line.strip() for line in out.splitlines() if line.strip()]

def ensure_parent_dirs(port: str, dests: list[str]) -> None:
    """
    Ensure all parent directories for the given device paths exist.
    dests are device paths like '/app/foo/bar.py' (no leading ':').
    """
    import subprocess

    # collect unique parent dirs
    dirs = set()
    for dp in dests:
        dp = dp.lstrip(":")  # be tolerant if caller passed ':'
        parent = "/".join(dp.split("/")[:-1])
        if parent and parent != "/":
            dirs.add(parent)

    # make each directory level-by-level; ignore "already exists" errors
    for d in sorted(dirs, key=lambda s: s.count("/")):
        parts = [p for p in d.strip("/").split("/") if p]
        cur = ""
        for part in parts:
            cur = (cur + "/" + part) if cur else "/" + part
            try:
                mp_run(port, "mkdir", f":{cur}")
            except subprocess.CalledProcessError:
                # ok if it already exists
                pass

def remove_remote_paths(port: str, paths: list[str]) -> None:
    for p in sorted(paths, key=lambda s: s.count("/"), reverse=True):
        rp = p if p.startswith(":") else f":{p}"
        mp_run(port, "rm", rp)

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__ or ""))
    ap.add_argument("--port", help="Serial port (e.g. COM3 or /dev/ttyACM0).")
    ap.add_argument("--src-root", default=".", help="Repo root where ./src lives.")
    ap.add_argument("--clean", action="store_true", help=f"Sync-clean: remove device files under {APP_ROOT} and managed root files not present locally.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without modifying the device.")
    ap.add_argument("--yes", "-y", action="store_true", help="Do not prompt for confirmation.")
    ap.add_argument("--list", action="store_true", help="List Pico-like devices and exit.")
    ap.add_argument("--reset", action="store_true", help="Soft reset after upload.")
    args = ap.parse_args()

    if args.list:
        cands = find_candidates()
        if not cands:
            print("(no matching devices found)")
            sys.exit(0)
        for p in cands:
            vid = f"{getattr(p,'vid',None) or 0:04x}"
            pid = f"{getattr(p,'pid',None) or 0:04x}"
            print(f"{p.device} {vid}:{pid} {(p.manufacturer or 'Unknown')} {(p.product or '')} {(p.description or '')}")
        sys.exit(0)

    port = args.port or choose_port()
    manifest = build_manifest(Path(args.src_root))

    # Which root files are "managed" (only those in the local manifest):
    managed_roots = sorted([p for p in ("/main.py", "/boot.py") if p in manifest])

    # Dry-run preview
    plan_lines = []
    if args.clean:
        remote_now = list_device_files(port, managed_roots)
        local_set  = set(manifest.keys())
        to_remove = []
        if args.clean:
            remote_now = list_device_files(port, managed_roots)
            local_set  = set(manifest.keys())
            for p in remote_now:
                if (p.startswith(APP_ROOT + "/") or p in managed_roots) and p not in local_set:
                    to_remove.append(p)
        for p in to_remove:
            plan_lines.append(f"DEL  {p}")
    else:
        to_remove = []

    for dest, src in manifest.items():
        plan_lines.append(f"COPY {src} -> :{dest}")

    if not args.yes:
        print("\nPlan:")
        for line in plan_lines:
            print(" ", line)
        if args.dry_run:
            print("\n--dry-run set; no changes will be made.")
            sys.exit(0)
        ans = input("Proceed? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)
    elif args.dry_run:
        # non-interactive dry-run
        for line in plan_lines:
            print(line)
        sys.exit(0)

    # Apply
    if args.clean and to_remove:
        remove_remote_paths(port, [f":{p.lstrip(':')}" if not p.startswith(":") else p for p in to_remove])

    # Make sure parent dirs exist on device for all destinations
    ensure_parent_dirs(port, list(manifest.keys()))

    # Copy files
    for dest, src in manifest.items():
        mp_run(port, "cp", str(src), f":{dest}")

    if args.reset:
        try:
            mp_run(port, "soft-reset")
        except subprocess.CalledProcessError:
            pass

    print("Upload complete to", port)

if __name__ == "__main__":
    main()
