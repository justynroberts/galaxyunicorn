# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hardware

**Pimoroni Galactic Unicorn** -- a 53x11 RGB LED matrix driven by a Raspberry Pi Pico W running MicroPython. Connected via USB-C, appearing as `/dev/cu.usbmodem1101` (serial port may vary).

- Display dimensions: 53 wide x 11 high pixels
- SDK: `galactic` (GalacticUnicorn) and `picographics` (PicoGraphics, DISPLAY_GALACTIC_UNICORN) -- Pimoroni MicroPython libraries in the firmware
- Brightness: `gu.set_brightness(0.0-1.0)`, gamma correction applied automatically
- Pico W connects to Wi-Fi and runs HTTP API server on port 80
- ~200KB usable heap, raw pixel frame = 1749 bytes (53x11x3 RGB)
- Available fonts: bitmap5, bitmap6, bitmap7, bitmap8, bitmap10, font6, font8, font10 (all fit within 11px height)
- Drawing primitives: pixel, line, circle, rectangle, triangle, polygon, text

## Project Structure

```
firmware/           -- MicroPython code deployed to Pico W
  main.py           -- Boot: Wi-Fi, hostname, HTTP server, cooperative main loop
  config.py         -- Wi-Fi creds, port, brightness defaults
  server.py         -- HTTP router, CORS, Content-Length body parsing
  renderer.py       -- Display state machine (idle/scroll/pixels/effect)
  mdns.py           -- mDNS responder (unused, native hostname used instead)
  effects/          -- Visual effect classes
    __init__.py     -- Registry: {name: class}
    fire.py         -- Rising flame heat simulation
    rainbow.py      -- HSV diagonal rainbow stripes
    supercomputer.py -- Amber blinking LEDs
    retroprompt.py  -- C64/Spectrum/BBC Micro boot screens

web/                -- React web app (Vite + TypeScript + Tailwind v3)
  src/
    App.tsx         -- Tabbed UI: Message | Effects | Pixel Art | Image
    hooks/          -- useDevice (polling/connection), usePixelGrid (editor state)
    lib/            -- api.ts (HTTP client), imageProcessor.ts, colorUtils.ts
    components/     -- UI components (see below)

backup/             -- Original device code before rebuild
```

## Device Interaction

```bash
# Deploy firmware
mpremote connect /dev/cu.usbmodem1101 cp firmware/main.py :main.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/fire.py :effects/fire.py

# Reset (boots main.py automatically)
mpremote connect /dev/cu.usbmodem1101 reset

# List files / read / REPL
mpremote connect /dev/cu.usbmodem1101 ls
mpremote connect /dev/cu.usbmodem1101 cat :filename.py
mpremote connect /dev/cu.usbmodem1101 repl
```

## Firmware API (port 80)

Full API reference with examples, payload formats, and error codes: **[API.md](API.md)**

Quick summary:

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | /status | -- | mode, brightness, effect, ip, free_mem, uptime |
| POST | /message | `{text, color:[r,g,b], speed:1-5, scale:1-3, repeat, font}` | Scrolling text |
| POST | /pixels | `{pixels:"<base64>"}` | Raw 53x11 RGB (1749 bytes), base64 encoded |
| POST | /effect | `{name:"fire\|rainbow\|supercomputer\|retroprompt"}` | Built-in effect |
| POST | /brightness | `{value:0.0-1.0}` | Set brightness |
| POST | /clear | -- | Clear display, idle mode |

## Firmware Architecture

- **Single-threaded cooperative loop**: poll HTTP (50ms timeout), tick renderer, sleep 5ms
- **Renderer state machine** (`renderer.py`): modes are `idle`, `scroll`, `pixels`, `effect`. API calls transition between modes. `gc.collect()` on transitions.
- **Effects as classes**: each receives `graphics` and `gu` in constructor, implements `init()` and `draw()`. Use `@micropython.native` on performance-critical methods.
- **Server** (`server.py`): parses Content-Length for proper body reading. Sequential request handling (one at a time).

## Web App

```bash
cd web
npm install
npm run dev        # Dev server on port 5199
npm run build      # Production build
```

- Vite + React 18 + TypeScript + Tailwind CSS v3.4.x
- Dark theme (Uber-style), Space Grotesk / Spline Sans Mono fonts
- Device URL stored in localStorage, defaults to http://192.168.3.43
- Polls /status every 3s, sequential request queue (Pico max 5 TCP connections)
- Image processing in browser: canvas resize to 53x11, Floyd-Steinberg dithering, base64 encode

## Key Constraints

- MicroPython: `ujson` not `json`, no `typing`, limited stdlib
- ~200KB heap: avoid large allocations, call `gc.collect()` on mode transitions
- `@micropython.native` not recognized by Python linters (use `# noqa: F821`)
- Display buffer flushed with `gu.update(graphics)` after drawing
- Pico W max 5 simultaneous TCP connections
- Wi-Fi credentials in `firmware/config.py`
- Tailwind must be v3.x (v4 has breaking changes)
