import gc
import ujson
import socket


ROOT_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galactic Unicorn</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,system-ui,sans-serif;padding:20px;min-height:100vh}
.box{max-width:480px;margin:30px auto;background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:24px}
h1{font-size:22px;margin-bottom:6px;background:linear-gradient(90deg,#0ff,#f0f);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p.sub{color:#888;font-size:13px;margin-bottom:18px}
.row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #222;font-size:13px}
.row:last-child{border-bottom:0}
.k{color:#888}.v{color:#0ff;font-family:monospace}
h2{font-size:13px;color:#aaa;margin:18px 0 8px;text-transform:uppercase;letter-spacing:1px}
ul{list-style:none}
li{padding:5px 0;font-family:monospace;font-size:12px;color:#ccc}
.m{color:#888}.p{color:#0f9}.q{color:#f93}
form{margin-top:18px}
input,button{width:100%;background:#0a0a0a;border:1px solid #333;color:#fff;padding:10px;border-radius:8px;font-size:14px;font-family:inherit}
input{margin-bottom:8px}
input:focus{outline:none;border-color:#0ff}
button{background:#0ff;color:#000;font-weight:600;cursor:pointer;border:none}
button:hover{background:#fff}
button.ghost{background:transparent;color:#888;border:1px solid #333;margin-top:8px}
button.ghost:hover{color:#f66;border-color:#a00}
</style></head><body>
<div class="box">
<h1>Galactic Unicorn</h1>
<p class="sub">53x11 RGB display</p>
<div class="row"><span class="k">IP</span><span class="v">{IP}</span></div>
<div class="row"><span class="k">Mode</span><span class="v">{MODE}</span></div>
<div class="row"><span class="k">Effect</span><span class="v">{EFFECT}</span></div>
<div class="row"><span class="k">Brightness</span><span class="v">{BR}</span></div>
<div class="row"><span class="k">Free memory</span><span class="v">{MEM} KB</span></div>
<div class="row"><span class="k">Uptime</span><span class="v">{UP}s</span></div>
<form id="f">
<input id="t" placeholder="Send a message" required>
<button type="submit">Scroll on display</button>
</form>
<button class="ghost" onclick="if(confirm('Reset Wi-Fi and reboot?'))fetch('/wifi/reset',{method:'POST'})">Reset Wi-Fi</button>
<h2>Endpoints</h2><ul>
<li><span class="m">GET</span> /status</li>
<li><span class="p">POST</span> /message <span class="q">{text,color,speed,scale,repeat,font}</span></li>
<li><span class="p">POST</span> /pixels <span class="q">{pixels:base64}</span></li>
<li><span class="p">POST</span> /effect <span class="q">{name}</span></li>
<li><span class="p">POST</span> /brightness <span class="q">{value:0..1}</span></li>
<li><span class="p">POST</span> /clear</li>
<li><span class="m">GET</span> /wifi/status</li>
<li><span class="p">POST</span> /wifi/reset</li>
</ul>
</div>
<script>
document.getElementById('f').onsubmit=async e=>{e.preventDefault();
const t=document.getElementById('t').value;
await fetch('/message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,color:[0,255,0],speed:1,repeat:1})});
document.getElementById('t').value='';};
</script></body></html>
"""


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
            if method == "GET" and path == "/":
                self._handle_root(cl)
                return
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

    def _handle_root(self, cl):
        import time
        uptime = int(time.time() - self._start_time)
        html = ROOT_HTML
        html = html.replace("{IP}", self.ip)
        html = html.replace("{MODE}", self.renderer.mode)
        html = html.replace("{EFFECT}", self.renderer.effect_name or "-")
        html = html.replace("{BR}", str(self.renderer.get_brightness()))
        html = html.replace("{MEM}", str(gc.mem_free() // 1024))
        html = html.replace("{UP}", str(uptime))
        body = html.encode("utf-8")
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).format(len(body))
        cl.sendall(headers.encode() + body)

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
