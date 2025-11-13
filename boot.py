# CircuitPython boot settings: enable console (REPL) and data CDC.
import usb_cdc
usb_cdc.enable(console=True, data=True)  # requires hard reset to re-enumerate
