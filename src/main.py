# main.py - Pico 2 firmware skeleton (MicroPython)
import sys, time, gc
try:
    import ujson as json
    import ustruct as struct
except ImportError:
    import json, struct
try:
    import usb_cdc  # type: ignore
except Exception:
    usb_cdc = None

from machine import UART, Pin
from usbproto import recv_obj, send_obj

VERSION = "0.1.0"

class Transport:
    def __init__(self):
        self.dev = None
        # Prefer USB CDC "data" channel, then "console"
        if usb_cdc:
            try:
                self.dev = usb_cdc.data if getattr(usb_cdc, "data", None) else usb_cdc.console
            except Exception:
                self.dev = getattr(usb_cdc, "console", None)
        if self.dev is None:
            # Fallback to UART0 @115200 on GP0/GP1
            self.dev = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        # ensure non-blocking isn't required; we will loop read_n until satisfied

    def read_obj(self):
        return recv_obj(self.dev)

    def write_obj(self, obj):
        send_obj(self.dev, obj)

def dispatch(req):
    t = req.get("type")
    if t == "ping":
        return {"type": "pong", "ts": time.ticks_ms(), "version": VERSION}
    if t == "get_status":
        gc.collect()
        return {
            "type": "status",
            "uptime_ms": time.ticks_ms(),
            "heap_free": gc.mem_free(),
            "version": VERSION,
        }
    if t == "echo":
        return {"type": "echo", "data": req.get("data")}
    return {"type": "error", "code": "UNKNOWN_CMD", "message": "Unknown command: %s" % t}

def main():
    t = Transport()
    while True:
        try:
            req = t.read_obj()
            resp = dispatch(req)
            t.write_obj(resp)
        except Exception as e:
            # Best-effort error surface; keep loop alive
            try:
                t.write_obj({"type": "error", "code": "EXC", "message": str(e)})
            except Exception:
                pass

if __name__ == "__main__":
    main()
