from serial.tools import list_ports
for p in list_ports.comports():
    tag=""
    if "MI_00" in (p.hwid or ""): tag="(console/REPL)"
    if "MI_01" in (p.hwid or ""): tag="(data)"
    print(p.device, "|", p.hwid, "|", p.description, tag)
