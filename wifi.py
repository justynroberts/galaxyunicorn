import time
import ujson
import network
import socket
import _thread
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN

# Wi-Fi Credentials
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

# Initialize Galactic Unicorn and graphics
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY_GALACTIC_UNICORN)
WIDTH, HEIGHT = graphics.get_bounds()
gu.set_brightness(0.5)

# Message queue and lock for thread safety
message_queue = []
queue_lock = _thread.allocate_lock()

# Function to connect to Wi-Fi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("[DEBUG] Connecting to Wi-Fi...")
    timeout = 10
    start_time = time.time()
    while not wlan.isconnected() and time.time() - start_time < timeout:
        time.sleep(1)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"[DEBUG] Connected to Wi-Fi. IP: {ip}")
        return ip
    else:
        print("[DEBUG] Failed to connect to Wi-Fi.")
        return None

# Threaded server function
def start_server():
    print("[DEBUG] Server thread starting")
    addr = ('0.0.0.0', 8080)
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(addr)
        server.listen(1)
        print("[DEBUG] Server is listening on", addr)
    except Exception as e:
        print(f"[DEBUG] Failed to bind or listen: {e}")
        return

    while True:
        try:
            cl, client_addr = server.accept()
            print(f"[DEBUG] Client connected from {client_addr}")
            request = cl.recv(1024)
            print(f"[DEBUG] Request received: {request}")

            # Send basic HTTP response
            cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello from Pico W!")
            cl.close()
        except Exception as e:
            print(f"[DEBUG] Error handling client: {e}")

# Main function
def main():
    ip = connect_to_wifi()
    if not ip:
        print("[DEBUG] Unable to start server without Wi-Fi")
        return

    print("[DEBUG] Starting server thread")
    _thread.start_new_thread(start_server, ())

    # Main loop (simulate message processing)
    while True:
        time.sleep(1)  # Keep the main thread alive
        print("[DEBUG] Main loop heartbeat")

if __name__ == "__main__":
    main()
