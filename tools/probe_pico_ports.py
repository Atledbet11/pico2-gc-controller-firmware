# tools/probe_cp_ports.py
# Finds your Pico's two COM ports and identifies which one is the DATA port
# by sending "PING" and looking for "PONG".
import time, serial
from serial.tools import list_ports

def try_ping(port, timeout=1.0):
    try:
        ser = serial.Serial(port, 115200, timeout=0.2)
    except Exception as e:
        return ("err", f"open failed: {e}")
    try:
        ser.reset_input_buffer(); ser.reset_output_buffer()
        time.sleep(0.05)
        ser.write(b"PING\n"); ser.flush()
        deadline = time.time() + timeout
        buf = bytearray()
        while time.time() < deadline:
            b = ser.read(1)
            if b:
                if b in b"\r\n":
                    if buf:
                        line = bytes(buf).decode("utf-8", "ignore").strip()
                        if line == "PONG":
                            return ("data", "PONG")
                        # Heuristics for REPL/console
                        if line.startswith("Traceback") or line.startswith("NameError") or line.endswith(">>>"):
                            return ("console", line[:60])
                        return ("other", line[:60])
                    else:
                        continue
                buf.extend(b)
        return ("timeout", "")
    finally:
        try: ser.close()
        except: pass

def main():
    # Find all ports for the same device (same VID/PID/SER)
    ports = list(list_ports.comports())
    candidates = []
    # Prefer grouping by same VID/PID + same serial number
    for p in ports:
        if p.vid == 0x2E8A:   # Raspberry Pi
            candidates.append(p)

    if not candidates:
        print("No Raspberry Pi serial devices found.")
        return

    # Group by serial number to find pairs
    groups = {}
    for p in candidates:
        key = (p.vid, p.pid, p.serial_number)
        groups.setdefault(key, []).append(p)

    for key, group in groups.items():
        vid, pid, serno = key
        print(f"\nDevice VID:PID={vid:04X}:{pid:04X} SER={serno}")
        for p in group:
            role, info = try_ping(p.device)
            tag = {"data":"(DATA)", "console":"(CONSOLE)", "timeout":"(no reply)", "err":"(open err)", "other":"(unknown)"}.get(role,"")
            print(f"  {p.device:<6} {tag:12}  {p.hwid}  {p.description}")
            if info:
                print(f"    note: {info}")

if __name__ == "__main__":
    main()
