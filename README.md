# Galaxy Unicorn

Web-controlled firmware and React UI for the **Pimoroni Galactic Unicorn** -- a 53x11 RGB LED matrix driven by a Raspberry Pi Pico W.

Send scrolling text, render images, draw pixel art, and trigger visual effects from any browser on your network.

## Architecture

Two components:

- **Firmware** (MicroPython on Pico W) -- lightweight HTTP API server on port 8080. Receives commands, renders to the LED matrix.
- **Web App** (Vite + React + TypeScript + Tailwind) -- dark-themed control panel. Handles image processing, pixel art editing, animation generation, and sends compact payloads to the device.

```
firmware/           MicroPython deployed to Pico W
  main.py           Boot, Wi-Fi, cooperative main loop
  config.py         Wi-Fi credentials, port, defaults
  server.py         HTTP router with CORS
  renderer.py       Display state machine (idle/scroll/pixels/effect)
  effects/          Built-in visual effects (fire, rainbow, supercomputer, retroprompt)

web/                React web app
  src/
    App.tsx         Tabbed UI: Message | Effects | Animate | Pixel Art | Image
    hooks/          Device polling, pixel grid state with undo/redo
    lib/            HTTP client, image processor, color utilities, animations
    components/     UI: color picker, preview, message composer, editors

backup/             Original device code before rebuild
```

## Quick Start

### Firmware

1. Edit Wi-Fi credentials in `firmware/config.py`
2. Deploy to the Pico W:

```bash
mpremote connect /dev/cu.usbmodem1101 mkdir :effects
mpremote connect /dev/cu.usbmodem1101 cp firmware/config.py :config.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/renderer.py :renderer.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/server.py :server.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/main.py :main.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/__init__.py :effects/__init__.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/fire.py :effects/fire.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/rainbow.py :effects/rainbow.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/supercomputer.py :effects/supercomputer.py
mpremote connect /dev/cu.usbmodem1101 cp firmware/effects/retroprompt.py :effects/retroprompt.py
mpremote connect /dev/cu.usbmodem1101 reset
```

The device prints its IP address to serial and scrolls it on the display at boot.

### Web App

```bash
cd web
npm install
npm run dev
```

Open the URL shown by Vite. Enter the device IP in the connection field (top of the page).

## API

Full reference: [API.md](API.md)

| Method | Path | Description |
|--------|------|-------------|
| GET | /status | Device state: mode, brightness, effect, IP, memory, uptime |
| POST | /message | Scrolling text with color, speed, scale, font selection |
| POST | /pixels | Raw 53x11 RGB frame (base64). Used for images, pixel art, animation. |
| POST | /effect | Start a built-in effect (fire, rainbow, supercomputer, retroprompt) |
| POST | /brightness | Set brightness (0.0 - 1.0) |
| POST | /clear | Clear display, return to idle |

### Examples

```bash
# Send a message
curl -X POST http://<ip>:8080/message \
  -d '{"text":"Hello","color":[0,255,0],"speed":1,"font":"bitmap8"}'

# Start an effect
curl -X POST http://<ip>:8080/effect -d '{"name":"fire"}'

# Set brightness
curl -X POST http://<ip>:8080/brightness -d '{"value":0.8}'

# Clear
curl -X POST http://<ip>:8080/clear
```

## Fonts

Eight bitmap fonts tested and verified on the 11px display:

| Font | Height | Notes |
|------|--------|-------|
| bitmap5 | 5px | Smallest, good for dense info |
| bitmap6 | 6px | Compact |
| bitmap7 | 7px | Balanced |
| bitmap8 | 8px | Default, clear and readable |
| bitmap10 | 10px | Large, fills the display |
| font6 | 6px | Alternative 6px style |
| font8 | 8px | Alternative 8px style |
| font10 | 10px | Alternative 10px style |

## Effects

| Effect | Description |
|--------|-------------|
| fire | Rising flame simulation with heat map |
| rainbow | Diagonal HSV rainbow stripes |
| supercomputer | Random blinking amber LEDs |
| retroprompt | C64, ZX Spectrum, BBC Micro boot screens |

## Web App Features

- **Message tab** -- compose scrolling text with color picker, font/speed/scale controls
- **Effects tab** -- one-click activation of built-in effects
- **Animate tab** -- procedural animations (plasma, matrix rain, sparkle, wave, etc.) streamed at configurable FPS
- **Pixel Art tab** -- 53x11 grid editor with pencil, flood fill, eraser, and undo/redo
- **Image tab** -- drag-and-drop image upload with resize modes (stretch/fit/crop) and Floyd-Steinberg dithering
- **Live preview** -- canvas rendering of LED dots with glow effect
- **Brightness slider** -- real-time brightness adjustment
- **Device status** -- connection indicator with configurable IP

## Hardware

- **Display**: Pimoroni Galactic Unicorn, 53 x 11 RGB LEDs
- **MCU**: Raspberry Pi Pico W (RP2040 + CYW43439 Wi-Fi)
- **Connection**: USB-C (serial + power), Wi-Fi (HTTP API)
- **Memory**: ~200KB usable MicroPython heap
- **Firmware**: Pimoroni MicroPython with PicoGraphics and GalacticUnicorn libraries

## License

MIT
