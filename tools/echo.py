# Usage: python tools/echo.py COM5 "hello world"
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
    if len(sys.argv) < 2:
        print("Usage: python tools/echo.py COMx [message]")
        sys.exit(1)
    port = sys.argv[1]
    msg  = sys.argv[2] if len(sys.argv) > 2 else "hello"
    ser = serial.Serial(port, 115200, timeout=0.2)
    try:
        ser.reset_input_buffer(); ser.reset_output_buffer(); time.sleep(0.05)
        ser.write(f"ECHO {msg}\n".encode("utf-8")); ser.flush()
        print("REPLY:", read_line(ser, 3.0))
    finally:
        ser.close()

if __name__ == "__main__":
    main()
