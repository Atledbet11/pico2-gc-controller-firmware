# Ultra-simple line protocol on usb_cdc.{data|console}:
#   PING    -> PONG
#   ECHO x  -> ECHO:x
#   STATUS  -> STATUS:UP
#
# Newlines terminate commands. No framing/MAGIC yet — keep it human-testable.

import time

def _readline(port, timeout_ms=3000):
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    buf = bytearray()
    while time.monotonic() < deadline:
        n = port.in_waiting
        if n:
            b = port.read(1)
            if not b:
                continue
            c = b[0]
            if c in (10, 13):  # \n or \r
                if buf:
                    return bytes(buf).decode("utf-8", "replace").strip()
                # ignore empty lines
            else:
                buf.append(c)
        else:
            time.sleep(0.001)
    return None  # timeout

def _writeln(port, s):
    port.write((s + "\n").encode("utf-8"))

def run_server(port):
    # Make reads non-blocking-ish; writes default-ok.
    try:
        port.timeout = 0
        port.write_timeout = None
    except Exception:
        pass

    while True:
        line = _readline(port, timeout_ms=10_000)
        if line is None:
            continue
        cmd = line.strip()
        if not cmd:
            continue

        if cmd == "PING":
            _writeln(port, "PONG")
        elif cmd.startswith("ECHO "):
            _writeln(port, "ECHO:" + cmd[5:])
        elif cmd == "STATUS":
            _writeln(port, "STATUS:UP")
        else:
            _writeln(port, "ERR")
