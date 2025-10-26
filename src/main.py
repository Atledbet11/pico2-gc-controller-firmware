# /main.py
import sys, struct, json, time, micropython, machine
micropython.kbd_intr(-1)  # disable Ctrl-C on the input stream (USB CDC)  ⟶ important
# (restore with micropython.kbd_intr(3) if you ever need it)  # 3 == ^C

def read_exact(n: int) -> bytes:
    b = b""
    while len(b) < n:
        chunk = sys.stdin.buffer.read(n - len(b))
        if not chunk:
            time.sleep(0.002)
            continue
        b += chunk
    return b

while True:
    try:
        hdr = sys.stdin.buffer.read(4)
        if len(hdr) != 4:
            time.sleep(0.002); continue
        n = struct.unpack(">I", hdr)[0]
        if n == 0 or n > 65536:
            continue
        payload = read_exact(n)
        try:
            msg = json.loads(payload)
        except Exception:
            msg = {}
        if msg.get("type") == "ping":
            out = {"type": "pong"}
        # inside your request handler:
        elif msg.get("type") == "enter_maintenance":
            # create the one-boot flag and soft-reset; next boot will leave REPL attached
            open("MAINTENANCE", "w").close()
            machine.soft_reset()
        else:
            out = {"echo": msg}
        data = json.dumps(out).encode()
        sys.stdout.buffer.write(struct.pack(">I", len(data)) + data)
        sys.stdout.buffer.flush()
    except Exception:
        # swallow errors; never print tracebacks on the wire
        time.sleep(0.01)
