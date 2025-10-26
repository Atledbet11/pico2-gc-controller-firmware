# Pico 2 Controller Firmware (MicroPython)

MicroPython firmware for Raspberry Pi Pico 2 that speaks a tiny, robust, length‑prefixed JSON protocol over USB (CDC) or UART.

## Quick start

1. Flash MicroPython for your Pico 2 (RP2350) to the board (drag‑and‑drop the UF2).
2. Copy `src/` onto the Pico's storage so that `main.py` runs on boot.
3. Connect via USB. A CDC serial port should appear (Windows: COMx, Linux: `/dev/ttyACM*`).
4. From a host machine, use the companion **Controller API** to `ping` and exchange messages.

> If your MicroPython build doesn't expose a USB CDC "data" port, this firmware will fall back to the console CDC device. It can also fall back to UART0 (GP0/GP1) at 115200 baud if USB CDC is unavailable.

## Message framing

- 4‑byte big‑endian length header
- Followed by UTF‑8 JSON payload
- Example request: `{"type":"ping"}` → response: `{"type":"pong","ts":12345,"version":"0.1.0"}`

See `docs/protocol.md` for full details.

## Repo layout
- `src/main.py` – entrypoint, transport + dispatcher loop
- `src/usbproto.py` – common helpers for length‑prefixed JSON
- `docs/protocol.md` – wire format, commands, and error codes

## Development tips

- Use a serial terminal (115200 8N1) only for debugging; normal operation communicates via the protocol.
- For UART fallback, wire:
  - UART0 TX = GP0, RX = GP1 (check your board pinout)
  - GND common between host adapter and Pico 2
- Keep messages small (< 1KB) for snappy response; the firmware streams reads/writes safely either way.
