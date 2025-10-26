# /boot.py  (put this in src/boot.py; your uploader copies it to device root)
from machine import Pin
import os

# Hardware maintenance trigger: hold GP2 LOW at power-on/reset
MAINT_PIN = Pin(2, Pin.IN, Pin.PULL_UP)

# Optional: also allow a one-boot file flag created from firmware/host
MAINT_FLAG = "MAINTENANCE"

def in_maintenance() -> bool:
    try:
        if MAINT_FLAG in os.listdir():
            # consume the flag so the next reboot returns to production
            try: os.remove(MAINT_FLAG)
            except OSError: pass
            return True
    except Exception:
        pass
    # GP2 low = maintenance
    try:
        return MAINT_PIN.value() == 0
    except Exception:
        return False

try:
    if not in_maintenance():
        # Production: detach REPL so USB-CDC is a clean data pipe
        os.dupterm(None, 0)
        # (slot 0 is always present; passing None detaches the REPL on that slot)
except Exception:
    # Never let boot fail because of REPL juggling
    pass
