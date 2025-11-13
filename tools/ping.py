# tools/ping.py
# Usage: python tools/ping.py COM3
import sys, time, serial

def read_line(ser, timeout_s=3.0):
    deadline = time.time() + timeout_s
    buf = bytearray()
    while time.time() < deadline:
        b = ser.read(1)
        if b:
            if b in b"\r\n":
                if buf:
                    return bytes(buf).decode("utf-8", "replace")
                else:
                    continue
            buf.extend(b)
        else:
            time.sleep(0.001)
    raise TimeoutError("timeout waiting for line")

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM3"
    ser = serial.Serial(port, 115200, timeout=0.2)
    try:
        # start clean
        ser.reset_input_buffer(); ser.reset_output_buffer()
        time.sleep(0.05)

        ser.write(b"PING\n"); ser.flush()
        reply = read_line(ser, 3.0)
        print("REPLY:", reply)
    finally:
        ser.close()

if __name__ == "__main__":
    main()
