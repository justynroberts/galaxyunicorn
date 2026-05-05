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

# Show "Connecting..." in cyan while trying to join saved WiFi
renderer.set_scroll("Connecting", [0, 200, 255], speed=3, scale=1, repeat=0, font="bitmap6")
for _ in range(40):
    renderer.tick()
    time.sleep_ms(15)

# Connect with stored credentials.
# Make sure AP is fully off before bringing STA up — the captive-portal
# AP can survive a soft reboot, and trying to connect with both up
# silently fails on this firmware.
try:
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    time.sleep(1)
except Exception:
    pass

try:
    network.hostname(HOSTNAME)
except Exception:
    pass

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
time.sleep(1)
try:
    wlan.config(hostname=HOSTNAME)
except Exception:
    pass

print("[boot] connecting to", c["ssid"])
wlan.connect(c["ssid"], c["password"])

start = time.time()
while not wlan.isconnected() and time.time() - start < 25:
    time.sleep(1)

if not wlan.isconnected():
    print("[boot] connect failed - portal mode")
    run_portal()  # never returns

ip = wlan.ifconfig()[0]
print("[boot] connected", ip)

# Sync clock to NTP (best effort, non-fatal)
try:
    import timesync
    if timesync.sync():
        print("[boot] NTP synced")
    else:
        print("[boot] NTP sync failed (clock will retry on first use)")
except Exception as e:
    print("[boot] timesync import failed:", e)

server = Server(renderer, EFFECTS, ip, PORT)
server.start(time.time())
print("[boot] HTTP server on port", PORT)

# Send-only mDNS announcer — broadcasts <hostname>.local periodically.
# Doesn't bind port 5353 so it doesn't conflict with the firmware's
# native mDNS; just sends unsolicited A records to the multicast group.
mdns = None
try:
    from mdns import MDNSAnnouncer
    mdns = MDNSAnnouncer(HOSTNAME, ip)
    mdns.start()
    print("[boot] mDNS announcing:", HOSTNAME + ".local ->", ip)
except Exception as e:
    print("[boot] mDNS failed:", e)

# Boot indicator: scroll IP in green so you know it's online and on what address
renderer.set_scroll(ip, [0, 255, 0], speed=3, scale=1, repeat=2, font="bitmap6")

gc.collect()
print("[boot] free mem:", gc.mem_free())

# Throttle renderer to ~30 fps so it doesn't saturate the LED PIO/SPI
RENDER_INTERVAL_MS = 33
last_render = time.ticks_ms()
last_ntp_check = time.time()

while True:
    try:
        server.poll()
    except Exception as e:
        print("[main] server.poll error:", e)

    if mdns:
        try:
            mdns.poll()
        except Exception:
            pass

    # Re-sync NTP every hour
    if time.time() - last_ntp_check > 3600:
        try:
            import timesync
            timesync.maybe_resync()
        except Exception:
            pass
        last_ntp_check = time.time()

    now = time.ticks_ms()
    if time.ticks_diff(now, last_render) >= RENDER_INTERVAL_MS:
        try:
            renderer.tick()
        except Exception as e:
            print("[main] renderer.tick error:", e)
        last_render = now

    time.sleep_ms(5)
