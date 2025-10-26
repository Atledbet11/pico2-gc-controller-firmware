# usbproto.py - helpers for length-prefixed JSON over a stream
import ustruct as struct
import ujson as json

def read_n(dev, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = dev.read(n - len(buf))
        if not chunk:
            # busy wait; on MicroPython this is common; consider sleep if needed
            continue
        buf.extend(chunk)
    return bytes(buf)

def recv_obj(dev):
    hdr = read_n(dev, 4)
    (length,) = struct.unpack('>I', hdr)
    payload = read_n(dev, length)
    return json.loads(payload)

def send_obj(dev, obj):
    payload = json.dumps(obj).encode('utf-8')
    hdr = struct.pack('>I', len(payload))
    dev.write(hdr)
    dev.write(payload)
    dev.flush() if hasattr(dev, "flush") else None
