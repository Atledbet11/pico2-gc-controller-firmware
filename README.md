# Pico 2 Controller Firmware (MicroPython)

MicroPython firmware for Raspberry Pi Pico 2 that speaks a tiny, robust, length‑prefixed JSON protocol over USB (CDC) or UART.

## Quick start

1. Flash MicroPython for your Pico 2 (RP2350) to the board (drag‑and‑drop the UF2).
2. Run bootstrap.ps1 (windows) or bootstrap.sh (linux) - to setup .venv for mpremote used to install to the pico
    - powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\bootstrap.ps1
3. Run upload_to_pico.py which should install the files in /src directory to the pico.
    - powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\upload.ps1
    - powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\upload.ps1 --clean --yes --port COM3
4. Verify
    - .\.venv\Scripts\Activate.ps1
    - python -m mpremote connect COM3 fs ls   # expect /main.py and /usbproto.py
    - deactivate

> If your MicroPython build doesn't expose a USB CDC "data" port, this firmware will fall back to the console CDC device. It can also fall back to UART0 (GP0/GP1) at 115200 baud if USB CDC is unavailable.

## Message framing

- 4‑byte big‑endian length header
- Followed by UTF‑8 JSON payload
- Example request: `{"type":"ping"}` → response: `{"type":"pong","ts":12345,"version":"0.1.0"}`

See `docs/protocol.md` for full details.

## Repo layout
- `src/main.py` – entrypoint, transport + dispatcher loop
- `src/usbproto.py` – common helpers for length‑prefixed JSON
- `docs/protocol.md` – wire format, commands, and error codes

## Development tips

- Use a serial terminal (115200 8N1) only for debugging; normal operation communicates via the protocol.
- For UART fallback, wire:
  - UART0 TX = GP0, RX = GP1 (check your board pinout)
  - GND common between host adapter and Pico 2
- Keep messages small (< 1KB) for snappy response; the firmware streams reads/writes safely either way.

## Deploying to the Pico 2 (MicroPython)
# Prerequisites

MicroPython UF2 is already flashed on the Pico 2 (RP2350).

A data-capable micro-USB cable.

The repo contains src/main.py, src/usbproto.py, and the tools/ folder:

tools/
  upload_to_pico.py
  upload.ps1       # Windows helper
  upload.sh        # Linux/macOS helper
  requirements-dev.txt


The uploader copies:

src/main.py → :/main.py

src/usbproto.py → :/usbproto.py
so the firmware runs automatically on boot.

One-click upload (recommended)
Windows (PowerShell)

From the repo root:

# Auto-detect the Pico and prompt before uploading
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\upload.ps1

# Or specify the serial port explicitly
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\upload.ps1 -Port COM3

Linux / macOS

From the repo root:

# Make the helper executable once:
chmod +x tools/upload.sh

# Auto-detect the Pico and prompt before uploading
./tools/upload.sh

# Or specify the serial port explicitly
./tools/upload.sh /dev/ttyACM0


The helper scripts will:

Create/activate a local .venv

Install mpremote + pyserial

Run the Python uploader with sensible defaults

Using the Python uploader directly

You can also call the Python tool (useful in CI or custom scripts):

# List candidate devices and exit
python tools/upload_to_pico.py --list

# Auto-detect device and prompt for confirmation
python tools/upload_to_pico.py

# Explicit port + prompt
python tools/upload_to_pico.py --port COM3
python tools/upload_to_pico.py --port /dev/ttyACM0

# Non-interactive (skip confirmation) and soft reset after upload
python tools/upload_to_pico.py --yes --reset


Arguments

--list — print detected Pico-like ports and exit

--port <NAME> — override auto-detection (e.g., COM3, /dev/ttyACM0)

--yes, -y — do not prompt for confirmation

--reset — soft reset the board after copying files

--src-root <DIR> — repo root containing src/ (default: current directory)

--clean — remove files that are not in /src

--dry-run — preview intended for --clean installs

VS Code task (optional)

If .vscode/tasks.json is present with an “Upload to Pico” task, you can run:

Terminal → Run Build Task… (or Ctrl+Shift+B)
This typically runs:

python tools/upload_to_pico.py --yes --reset

Verifying the device

Open a REPL:

python -m mpremote connect COM3 repl


Exit with Ctrl+].

From the API repo’s CLI (example):

cd ..\pico2-controller-api\cmd\gcpctl
go run . ping --port COM3


You should see a {"type":"pong", ...} response.
