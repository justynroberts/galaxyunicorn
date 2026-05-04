import time
import network
import machine
import gc
from config import PORT, DEFAULT_BRIGHTNESS, HOSTNAME, AP_SSID, AP_IP
from renderer import Renderer
from server import Server
from effects import EFFECTS
import credential_store


def try_connect(ssid, password, timeout=15, hostname=HOSTNAME):
    try:
        network.hostname(hostname)
    except Exception:
        pass

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    try:
        wlan.config(hostname=hostname)
    except Exception:
        pass

    print("[boot] Connecting to", ssid, "...")
    wlan.connect(ssid, password)

    start = time.time()
    while not wlan.isconnected() and time.time() - start < timeout:
        time.sleep(1)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("[boot] Connected. IP:", ip)
        return ip

    print("[boot] Connection failed")
    try:
        wlan.disconnect()
    except Exception:
        pass
    wlan.active(False)
    return None


def run_portal(renderer):
    from portal import CaptivePortal

    renderer.set_scroll("Setup mode - join " + AP_SSID, [255, 200, 0], 1, 1, 0, "bitmap6")
    for _ in range(80):
        renderer.tick()
        time.sleep_ms(20)

    portal = CaptivePortal(AP_SSID, AP_IP, renderer=renderer)
    portal.start()

    renderer.set_scroll("Setup at " + AP_IP, [0, 255, 200], 1, 1, 0, "bitmap6")
    print("[boot] Portal running at", AP_IP)

    while portal.result is None:
        portal.poll()
        renderer.tick()
        time.sleep_ms(5)

    creds = portal.result
    print("[boot] Portal returned credentials, saving")

    credential_store.save(creds["ssid"], creds["password"])

    renderer.set_scroll("Saved! Rebooting...", [0, 255, 0], 1, 1, 1, "bitmap6")
    for _ in range(120):
        renderer.tick()
        time.sleep_ms(20)

    portal.stop()
    time.sleep(1)
    machine.reset()


def main():
    renderer = Renderer()
    renderer.set_brightness(DEFAULT_BRIGHTNESS)

    creds = credential_store.load()
    ip = None

    if creds and creds.get("ssid"):
        renderer.set_scroll("Connecting...", [0, 200, 255], 1, 1, 0, "bitmap6")
        for _ in range(20):
            renderer.tick()
            time.sleep_ms(10)
        ip = try_connect(creds["ssid"], creds["password"], timeout=15)

    if not ip:
        print("[boot] No credentials or connection failed - launching portal")
        run_portal(renderer)
        return  # machine.reset() inside run_portal

    # Show IP briefly, then start server
    renderer.set_scroll(ip, [0, 255, 0], speed=1, scale=1, repeat=2)

    start_time = time.time()
    server = Server(renderer, EFFECTS, ip, PORT)
    server.start(start_time)
    print("[boot] HTTP server on port", PORT)

    # Start mDNS so the device is reachable as display.local
    mdns = None
    try:
        from mdns import MDNSResponder
        mdns = MDNSResponder(HOSTNAME, ip)
        mdns.start()
        print("[boot] mDNS: {}.local -> {}".format(HOSTNAME, ip))
    except Exception as e:
        print("[boot] mDNS failed:", e)

    gc.collect()
    print("[boot] Free memory:", gc.mem_free())

    while True:
        server.poll()
        if mdns:
            try:
                mdns.poll()
            except Exception:
                pass
        renderer.tick()
        time.sleep_ms(5)


if __name__ == "__main__":
    main()
