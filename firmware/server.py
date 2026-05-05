import gc
import ujson
import socket


class Server:
    def __init__(self, renderer, effects_registry, ip_address, port=8080):
        self.renderer = renderer
        self.effects = effects_registry
        self.ip = ip_address
        self.port = port
        self.sock = None
        self._start_time = 0

    def start(self, start_time):
        self._start_time = start_time
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(1)
        self.sock.settimeout(0.5)

    def poll(self):
        try:
            cl, addr = self.sock.accept()
        except OSError:
            return
        # _handle_client must NOT propagate exceptions back to poll's
        # accept-timeout handler, otherwise OSError from a busted client
        # would be swallowed silently.
        self._handle_client(cl)

    def _handle_client(self, cl):
        try:
            cl.settimeout(5)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = cl.recv(512)
                if not chunk:
                    return
                data += chunk

            header_end = data.index(b"\r\n\r\n") + 4
            header_str = data[:header_end].decode()
            body = data[header_end:]

            # Parse Content-Length and read remaining body
            content_length = 0
            for line in header_str.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":")[1].strip())
                    break

            while len(body) < content_length:
                chunk = cl.recv(512)
                if not chunk:
                    break
                body += chunk

            # Parse request line
            request_line = header_str.split("\r\n")[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                self._send(cl, 400, {"error": "bad request"})
                return
            method = parts[0]
            path = parts[1]

            # Handle OPTIONS preflight
            if method == "OPTIONS":
                self._send(cl, 204, None)
                return

            # Route dispatch
            if method == "GET" and path == "/status":
                self._handle_status(cl)
            elif method == "POST" and path == "/message":
                self._handle_message(cl, body)
            elif method == "POST" and path == "/pixels":
                self._handle_pixels(cl, body)
            elif method == "POST" and path == "/effect":
                self._handle_effect(cl, body)
            elif method == "POST" and path == "/brightness":
                self._handle_brightness(cl, body)
            elif method == "POST" and path == "/clear":
                self._handle_clear(cl)
            elif method == "GET" and path == "/wifi/status":
                self._handle_wifi_status(cl)
            elif method == "POST" and path == "/wifi/reset":
                self._handle_wifi_reset(cl)
            else:
                self._send(cl, 404, {"error": "not found"})

        except Exception as e:
            try:
                self._send(cl, 500, {"error": str(e)})
            except Exception:
                pass
        finally:
            cl.close()

    def _parse_json(self, body):
        if not body:
            return {}
        result = ujson.loads(body.decode())
        del body
        gc.collect()
        return result

    def _send(self, cl, status, data):
        status_text = {200: "OK", 204: "No Content", 400: "Bad Request",
                       404: "Not Found", 500: "Internal Server Error"}
        st = status_text.get(status, "OK")

        if data is not None:
            body = ujson.dumps(data).encode()
            headers = (
                "HTTP/1.1 {} {}\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Content-Type: application/json\r\n"
                "Content-Length: {}\r\n"
                "Connection: close\r\n\r\n"
            ).format(status, st, len(body))
            cl.sendall(headers.encode() + body)
        else:
            headers = (
                "HTTP/1.1 {} {}\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                "Access-Control-Allow-Headers: Content-Type\r\n"
                "Content-Length: 0\r\n"
                "Connection: close\r\n\r\n"
            ).format(status, st)
            cl.sendall(headers.encode())

    def _handle_status(self, cl):
        import time
        self._send(cl, 200, {
            "mode": self.renderer.mode,
            "brightness": self.renderer.get_brightness(),
            "effect": self.renderer.effect_name,
            "ip": self.ip,
            "free_mem": gc.mem_free(),
            "uptime": time.time() - self._start_time,
        })

    def _handle_message(self, cl, body):
        data = self._parse_json(body)
        text = data.get("text", "")
        color = data.get("color", [255, 255, 255])
        speed = data.get("speed", 1)
        scale = data.get("scale", 1)
        repeat = data.get("repeat", 1)
        font = data.get("font", "bitmap8")
        if not text:
            self._send(cl, 400, {"error": "text is required"})
            return
        self.renderer.set_scroll(text, color, speed, scale, repeat, font)
        self._send(cl, 200, {"status": "ok", "mode": "scroll"})

    def _handle_pixels(self, cl, body):
        data = self._parse_json(body)
        pixels = data.get("pixels", "")
        if not pixels:
            self._send(cl, 400, {"error": "pixels is required"})
            return
        self.renderer.set_pixels(pixels)
        self._send(cl, 200, {"status": "ok", "mode": "pixels"})

    def _handle_effect(self, cl, body):
        data = self._parse_json(body)
        name = data.get("name", "")
        if not name:
            self._send(cl, 400, {"error": "name is required"})
            return
        if not self.renderer.set_effect(name, self.effects):
            self._send(cl, 400, {"error": "unknown effect: " + name})
            return
        self._send(cl, 200, {"status": "ok", "mode": "effect", "effect": name})

    def _handle_brightness(self, cl, body):
        data = self._parse_json(body)
        value = data.get("value", 0.5)
        self.renderer.set_brightness(value)
        self._send(cl, 200, {"status": "ok", "brightness": value})

    def _handle_clear(self, cl):
        self.renderer.clear()
        self._send(cl, 200, {"status": "ok", "mode": "idle"})

    def _handle_wifi_status(self, cl):
        import credential_store
        creds = credential_store.load()
        configured = bool(creds and creds.get("ssid"))
        self._send(cl, 200, {
            "configured": configured,
            "ssid": creds.get("ssid") if configured else None,
        })

    def _handle_wifi_reset(self, cl):
        import credential_store
        import machine
        credential_store.clear()
        self._send(cl, 200, {"status": "ok", "rebooting": True})
        # Give response time to flush
        try:
            cl.close()
        except Exception:
            pass
        import time
        time.sleep(1)
        machine.reset()
