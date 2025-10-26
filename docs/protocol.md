# Protocol (Firmware <-> Host)

**Transport:** USB CDC (preferred) with automatic fallback to UART0 (115200 8N1).  
**Framing:** 4‑byte big‑endian length prefix + UTF‑8 JSON payload.

## Request / Response format

```jsonc
// Request
{ "type": "ping" }

// Response
{ "type": "pong", "ts": 12345, "version": "0.1.0" }
```

### Error shape
```jsonc
{ "type": "error", "code": "UNKNOWN_CMD", "message": "..." }
```

## Built-in commands

- `ping` → `pong`
- `get_status` → `{uptime_ms, heap_free, version}`
- `echo` (with `data`) → echoes back `data`
- Future commands can be added under `dispatch()` in `main.py`.
