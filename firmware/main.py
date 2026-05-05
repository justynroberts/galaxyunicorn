import time
import network
import machine
import gc
from config import PORT, DEFAULT_BRIGHTNESS, HOSTNAME, AP_SSID, AP_IP
from renderer import Renderer
from server import Server
from effects import EFFECTS
import credential_store


renderer = Renderer()
renderer.set_brightness(DEFAULT_BRIGHTNESS)


def run_portal():
    from portal import CaptivePortal
    renderer.set_scroll("Setup mode - join " + AP_SSID, [255, 200, 0], 1, 1, 0, "bitmap6")
    for _ in range(80):
        renderer.tick()
        time.sleep_ms(20)

    portal = CaptivePortal(AP_SSID, AP_IP, renderer=renderer)
    portal.start()
    renderer.set_scroll("Setup at " + AP_IP, [0, 255, 200], 1, 1, 0, "bitmap6")
    print("[boot] portal at", AP_IP)

    while portal.result is None:
        portal.poll()
        renderer.tick()
        time.sleep_ms(5)

    creds = portal.result
    credential_store.save(creds["ssid"], creds["password"])

    renderer.set_scroll("Saved! Rebooting...", [0, 255, 0], 1, 1, 1, "bitmap6")
    for _ in range(120):
        renderer.tick()
        time.sleep_ms(20)
    portal.stop()
    time.sleep(1)
    machine.reset()


# Boot flow
c = credential_store.load()
if not c or not c.get("ssid"):
    run_portal()  # never returns

# Connect with stored credentials
try:
    network.hostname(HOSTNAME)
except Exception:
    pass

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
try:
    wlan.config(hostname=HOSTNAME)
except Exception:
    pass

print("[boot] connecting to", c["ssid"])
wlan.connect(c["ssid"], c["password"])

start = time.time()
while not wlan.isconnected() and time.time() - start < 20:
    time.sleep(1)

if not wlan.isconnected():
    print("[boot] connect failed - portal mode")
    run_portal()  # never returns

ip = wlan.ifconfig()[0]
print("[boot] connected", ip)

server = Server(renderer, EFFECTS, ip, PORT)
server.start(time.time())
print("[boot] HTTP server on port", PORT)

# mDNS skipped — port 5353 is bound by the firmware's native mDNS,
# and our extra responder leaks a half-bound socket on startup.

renderer.clear()
gc.collect()
print("[boot] free mem:", gc.mem_free())

# Throttle renderer to ~30 fps so it doesn't saturate the LED PIO/SPI
RENDER_INTERVAL_MS = 33
last_render = time.ticks_ms()

while True:
    try:
        server.poll()
    except Exception as e:
        print("[main] server.poll error:", e)

    now = time.ticks_ms()
    if time.ticks_diff(now, last_render) >= RENDER_INTERVAL_MS:
        try:
            renderer.tick()
        except Exception as e:
            print("[main] renderer.tick error:", e)
        last_render = now

    time.sleep_ms(5)
