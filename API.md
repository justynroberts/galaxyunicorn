# Galactic Unicorn LED Display API

HTTP JSON API running on a Pimoroni Galactic Unicorn (53x11 RGB LED matrix, Raspberry Pi Pico W).

**Base URL:** `http://<device-ip>`

All endpoints return JSON. CORS is enabled for all origins. The device IP is printed to serial on boot and shown on the display.

---

## GET /status

Returns the current state of the display.

**Response:**

```json
{
  "mode": "idle",
  "brightness": 0.5,
  "effect": null,
  "ip": "192.168.3.43",
  "free_mem": 150176,
  "uptime": 42
}
```

| Field | Type | Description |
|-------|------|-------------|
| mode | string | Current display mode: `idle`, `scroll`, `pixels`, or `effect` |
| brightness | float | Current brightness level (0.0 - 1.0) |
| effect | string or null | Name of the active effect, or null if not in effect mode |
| ip | string | Device IP address on the local network |
| free_mem | int | Available heap memory in bytes (~150KB typical) |
| uptime | int | Seconds since boot |

**Example:**

```bash
curl http://192.168.3.43/status
```

---

## POST /message

Displays scrolling text across the LED matrix.

**Request body:**

```json
{
  "text": "Hello World",
  "color": [0, 255, 0],
  "speed": 1,
  "scale": 1,
  "repeat": 1,
  "font": "bitmap8"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | yes | -- | The text to scroll. Any printable ASCII. |
| color | [r, g, b] | no | [255, 255, 255] | RGB color, each value 0-255 |
| speed | int | no | 1 | Scroll speed in pixels per frame (1-5) |
| scale | int | no | 1 | Font scale multiplier (1-3). Scale 1 recommended for readability. |
| repeat | int | no | 1 | Number of times to scroll the text. 0 = loop forever. |
| font | string | no | "bitmap8" | Font name (see Fonts section below) |

**Response:**

```json
{
  "status": "ok",
  "mode": "scroll"
}
```

**Errors:**

- `400` if `text` is empty or missing

**Example:**

```bash
curl -X POST http://192.168.3.43/message \
  -d '{"text":"Hello","color":[255,0,0],"speed":2,"font":"bitmap7"}'
```

### Fonts

The display is 11 pixels tall. Fonts taller than 11px will be clipped. Text is automatically centered vertically.

| Font | Height | Description |
|------|--------|-------------|
| bitmap5 | 5px | Smallest. Good for dense information. |
| bitmap6 | 6px | Compact. Good for longer messages. |
| bitmap7 | 7px | Balanced size and readability. |
| bitmap8 | 8px | Default. Clear and readable. |
| bitmap10 | 10px | Large. Fills most of the display. |
| font6 | 6px | Alternative style, 6px tall. |
| font8 | 8px | Alternative style, 8px tall. |
| font10 | 10px | Alternative style, 10px tall. |

---

## POST /pixels

Sets every pixel on the display directly. Used for images, pixel art, and animation frames.

**Request body:**

```json
{
  "pixels": "<base64-encoded RGB data>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pixels | string | yes | Base64-encoded raw RGB byte array. 53 x 11 x 3 = 1749 bytes before encoding (~2332 chars base64). |

**Pixel format:**

The pixel data is a flat array of RGB triplets, row by row, left to right, top to bottom:

```
byte 0: pixel(0,0) red
byte 1: pixel(0,0) green
byte 2: pixel(0,0) blue
byte 3: pixel(1,0) red
byte 4: pixel(1,0) green
byte 5: pixel(1,0) blue
...
byte 1746: pixel(52,10) red
byte 1747: pixel(52,10) green
byte 1748: pixel(52,10) blue
```

Index formula: `offset = (y * 53 + x) * 3`

**Response:**

```json
{
  "status": "ok",
  "mode": "pixels"
}
```

**Errors:**

- `400` if `pixels` is empty or missing
- `500` if base64 decode fails or memory is insufficient

**Example (solid red screen):**

```bash
python3 -c "
import base64
# 53x11 pixels, all red
data = bytes([255, 0, 0] * (53 * 11))
print(base64.b64encode(data).decode())
" | xargs -I{} curl -X POST http://192.168.3.43/pixels -d '{"pixels":"{}"}'
```

**Example (generate from Python):**

```python
import base64, json, urllib.request

width, height = 53, 11
pixels = bytearray(width * height * 3)

# Draw a gradient
for y in range(height):
    for x in range(width):
        i = (y * width + x) * 3
        pixels[i]     = int(x / width * 255)   # red
        pixels[i + 1] = int(y / height * 255)  # green
        pixels[i + 2] = 128                     # blue

payload = json.dumps({"pixels": base64.b64encode(pixels).decode()}).encode()
req = urllib.request.Request("http://192.168.3.43/pixels", data=payload)
urllib.request.urlopen(req)
```

**Animation streaming:**

Send sequential `/pixels` requests at 3-10 fps. The browser-based web app generates frames client-side and sends them in sequence. Higher frame rates may be limited by network latency and the Pico W's single-threaded request handling.

---

## POST /effect

Starts a built-in visual effect. The effect runs continuously until another mode is activated or `/clear` is called.

**Request body:**

```json
{
  "name": "fire"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Effect name (see table below) |

**Available effects:**

| Name | Description |
|------|-------------|
| fire | Rising flame simulation using a heat map with orange/red/yellow palette |
| rainbow | Diagonal HSV rainbow stripes that scroll across the display |
| supercomputer | Random blinking amber LEDs simulating a retro mainframe |
| retroprompt | Cycles through C64, ZX Spectrum, and BBC Micro boot screens |

**Response:**

```json
{
  "status": "ok",
  "mode": "effect",
  "effect": "fire"
}
```

**Errors:**

- `400` if `name` is empty, missing, or not a recognized effect

**Example:**

```bash
curl -X POST http://192.168.3.43/effect -d '{"name":"rainbow"}'
```

---

## POST /brightness

Sets the display brightness.

**Request body:**

```json
{
  "value": 0.8
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| value | float | no | 0.5 | Brightness level from 0.0 (off) to 1.0 (max) |

**Response:**

```json
{
  "status": "ok",
  "brightness": 0.8
}
```

**Example:**

```bash
curl -X POST http://192.168.3.43/brightness -d '{"value":0.3}'
```

---

## POST /clear

Clears the display and returns to idle mode. No request body required.

**Response:**

```json
{
  "status": "ok",
  "mode": "idle"
}
```

**Example:**

```bash
curl -X POST http://192.168.3.43/clear
```

---

## Error Responses

All errors return JSON with an `error` field:

```json
{
  "error": "text is required"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request -- missing required field or invalid value |
| 404 | Unknown endpoint |
| 500 | Internal server error -- typically memory exhaustion on large payloads |

---

## CORS

All responses include:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

OPTIONS preflight requests return `204 No Content`.

---

## Technical Notes

- The Pico W handles one HTTP request at a time (single-threaded cooperative loop).
- Maximum ~5 concurrent TCP connections. The web app queues requests sequentially.
- The `/pixels` endpoint triggers garbage collection before and after decoding to manage the ~200KB heap.
- Text centering is automatic: `y = (11 - font_height * scale + 1) / 2`, rounded down, clamped to 0.
- Sending a new command to any endpoint immediately replaces the current display mode.
- The display retains its last state when idle (no automatic timeout or screensaver).
