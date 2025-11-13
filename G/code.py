import supervisor, usb_cdc

# Keep your data connection stable while editing:
supervisor.runtime.autoreload = False

# Prefer the data CDC; if it's None, fall back to console so we still have a path.
data_port = getattr(usb_cdc, "data", None) or usb_cdc.console

from app.usb_comm.server import run_server
run_server(data_port)
