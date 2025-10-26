#!/usr/bin/env python3
"""
Simple USB ping→pong test for the Pico protocol (length-prefixed JSON).

Usage examples:
  python tools/test_usb.py --port COM3
  python tools/test_usb.py --auto --count 5 --interval 0.2
  python tools/test_usb.py --port COM3 --json '{"type":"echo","msg":"hi"}'
"""

import argparse, json, struct, sys, time
import serial
from serial.tools import list_ports

RPI_VID = 0x2E8A  # Raspberry Pi

def find_port() -> str | None:
    cands = [p.device for p in list_ports.comports() if getattr(p, "vid", None) == RPI_VID]
    return cands[0] if len(cands) == 1 else None

def read_exact(ser: serial.Serial, n: int, timeout_s: float) -> bytes:
    """Read exactly n bytes or raise TimeoutError."""
    buf = bytearray()
    deadline = time.time() + timeout_s
    while len(buf) < n:
        chunk = ser.read(n - len(buf))
        if chunk:
            buf.extend(chunk)
        elif time.time() > deadline:
            raise TimeoutError(f"read_exact timeout: got {len(buf)}/{n} bytes")
    return bytes(buf)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="Serial port (e.g. COM3 or /dev/ttyACM0).")
    ap.add_argument("--auto", action="store_true", help="Auto-pick the Pico by USB VID (2E8A) if --port not given.")
    ap.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200).")
    ap.add_argument("--timeout", type=float, default=1.0, help="Read timeout seconds (default: 1.0).")
    ap.add_argument("--count", type=int, default=1, help="How many pings to send (default: 1).")
    ap.add_argument("--interval", type=float, default=0.3, help="Delay between pings in seconds (default: 0.3).")
    ap.add_argument("--json", dest="payload", default='{"type":"ping"}',
                    help='JSON to send (default: {"type":"ping"}).')
    args = ap.parse_args()

    port = args.port
    if not port and args.auto:
        port = find_port()
        if not port:
            print("ERROR: could not auto-detect a Pico (VID 2E8A). Use --port.", file=sys.stderr)
            sys.exit(2)
    if not port:
        ap.error("please provide --port or --auto")

    payload = args.payload.encode("utf-8")
    frame = struct.pack(">I", len(payload)) + payload  # 4-byte big-endian length + JSON

    # Open cleanly each time: assert DTR/RTS, brief settle, flush input.
    with serial.Serial(port, args.baud, timeout=args.timeout, write_timeout=args.timeout) as ser:
        ser.dtr = True
        ser.rts = True
        time.sleep(0.05)
        ser.reset_input_buffer()

        for i in range(args.count):
            # send
            ser.write(frame)
            ser.flush()
            # recv header
            hdr = read_exact(ser, 4, args.timeout)
            n = struct.unpack(">I", hdr)[0]
            if n == 0 or n > 65536:
                print(f"[{i}] bad length: {n} (header={hdr!r})", file=sys.stderr)
                sys.exit(3)
            # recv payload
            body = read_exact(ser, n, args.timeout)
            try:
                msg = json.loads(body)
            except Exception:
                msg = {"_raw": body.decode("utf-8", "replace")}
            print(f"[{i}] ← {msg}")
            if i + 1 < args.count:
                time.sleep(args.interval)

    print("OK")

if __name__ == "__main__":
    main()
