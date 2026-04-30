import time
import ujson
import network
import socket
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

# Message queue
message_queue = []
current_message = None
scroll_x = None

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

# Function to handle HTTP requests
def handle_request(cl):
    try:
        cl.settimeout(5)  # Set a timeout for client operations
        request_data = b""
        while True:
            chunk = cl.recv(1024)
            if not chunk:  # Client disconnected
                break
            request_data += chunk
            if b"\r\n\r\n" in request_data:  # End of headers
                break

        if not request_data:
            print("[DEBUG] Empty request received.")
            return

        # Parse HTTP request
        request_line = request_data.decode().split("\r\n")[0]
        method, path, _ = request_line.split()
        print(f"[DEBUG] Received request: {method} {path}")

        if method == "POST" and path == "/message":
            body = request_data.decode().split("\r\n\r\n", 1)[1]
            data = ujson.loads(body)

            # Extract message and color
            message = data.get("message", "No message")
            color = data.get("color", [255, 255, 255])  # Default to white
            print(f"[DEBUG] Received message: {message}, color: {color}")

            # Add to queue
            pen_color = graphics.create_pen(*color)
            message_queue.append((message, pen_color))
            print(f"[DEBUG] Message queued. Queue length: {len(message_queue)}")

            # Send HTTP response
            cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.send(ujson.dumps({"status": "queued"}).encode())
        else:
            print("[DEBUG] Unsupported method or path")
            cl.send(b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nUnsupported path or method.")
    except Exception as e:
        print(f"[DEBUG] Error handling request: {e}")
        cl.send(b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nError processing request.")
    finally:
        cl.close()

# Function to scroll text non-blocking
def update_scrolling():
    global current_message, scroll_x

    if current_message is None:
        if message_queue:
            # Start a new message
            current_message = message_queue.pop(0)
            scroll_x = WIDTH
            print(f"[DEBUG] Starting new message: {current_message[0]}")
        return

    # Update scrolling position
    message, color = current_message
    graphics.set_pen(0)  # Clear screen
    graphics.clear()
    graphics.set_pen(color)

    # Calculate scale and center vertically
    scale = 2  # Adjust font size here
    text_height = 6 * scale  # Estimate based on font metrics
    y = (HEIGHT - text_height) // 2  # Center vertically

    graphics.text(message, scroll_x, y, scale=scale)
    gu.update(graphics)
    scroll_x -= 1

    # Check if the message is done scrolling
    if scroll_x < -graphics.measure_text(message, scale):
        print(f"[DEBUG] Finished scrolling message: {message}")
        current_message = None

# Main function
def main():
    ip = connect_to_wifi()
    if not ip:
        print("[DEBUG] Unable to start server without Wi-Fi")
        return

    # Display the IP address as a message
    message_queue.append((f"My IP: {ip}", graphics.create_pen(0, 255, 0)))

    # Start the server
    addr = ('0.0.0.0', 8080)
    while True:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(addr)
            server.listen(5)  # Allow up to 5 queued connections
            print("[DEBUG] Server is listening on", addr)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print("[DEBUG] Address in use, resetting socket...")
                server.close()
                time.sleep(1)  # Wait before retrying
            else:
                print(f"[DEBUG] Failed to bind or listen: {e}")
                return

    # Main loop: handle server and display logic
    while True:
        # Check for new client connections
        try:
            server.settimeout(0.1)  # Non-blocking timeout
            cl, client_addr = server.accept()
            print(f"[DEBUG] Client connected from {client_addr}")
            handle_request(cl)
        except OSError as e:
            if e.errno == 110:  # Timeout-specific error
                pass  # Suppress timeout logs
            else:
                print(f"[DEBUG] Unexpected error accepting connection: {e}")

        # Update scrolling logic
        update_scrolling()
        time.sleep(0.005)  # Add a small delay to reduce CPU usage



if __name__ == "__main__":
    main()
