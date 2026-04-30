import time
import network
import gc
from config import SSID, PASSWORD, PORT, DEFAULT_BRIGHTNESS, HOSTNAME
from renderer import Renderer
from server import Server
from effects import EFFECTS


def connect_to_wifi():
    # Set hostname before connecting for native mDNS
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

    wlan.connect(SSID, PASSWORD)

    print("[boot] Connecting to Wi-Fi...")
    timeout = 15
    start = time.time()
    while not wlan.isconnected() and time.time() - start < timeout:
        time.sleep(1)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("[boot] Connected. IP:", ip)
        print("[boot] Hostname: {}.local".format(HOSTNAME))
        return ip
    else:
        print("[boot] Wi-Fi connection failed")
        return None


def main():
    # Initialize display
    renderer = Renderer()
    renderer.set_brightness(DEFAULT_BRIGHTNESS)

    # Connect to Wi-Fi
    ip = connect_to_wifi()
    if not ip:
        renderer.set_scroll("No Wi-Fi", [255, 0, 0], speed=1, scale=1, repeat=0)
        while True:
            renderer.tick()
            time.sleep_ms(10)
        return

    # Show IP on display
    renderer.set_scroll(ip, [0, 255, 0], speed=1, scale=1, repeat=2)

    # Start HTTP server
    start_time = time.time()
    server = Server(renderer, EFFECTS, ip, PORT)
    server.start(start_time)
    print("[boot] HTTP server on port", PORT)

    gc.collect()
    print("[boot] Free memory:", gc.mem_free())

    # Main cooperative loop
    while True:
        server.poll()
        renderer.tick()
        time.sleep_ms(5)


if __name__ == "__main__":
    main()
