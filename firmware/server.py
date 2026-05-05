import gc
import ujson
import socket


ROOT_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galactic Unicorn</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,system-ui,sans-serif;padding:16px;min-height:100vh}
.box{max-width:520px;margin:20px auto;background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:22px}
h1{font-size:24px;margin-bottom:4px;background:linear-gradient(90deg,#0ff,#f0f);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p.sub{color:#888;font-size:13px;margin-bottom:18px}
h2{font-size:11px;color:#888;margin:18px 0 8px;text-transform:uppercase;letter-spacing:1.5px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;font-size:12px}
.grid div{display:flex;justify-content:space-between;padding:6px 8px;background:#0a0a0a;border-radius:6px}
.grid .k{color:#888}.grid .v{color:#0ff;font-family:monospace}
label{display:block;font-size:12px;color:#aaa;margin:10px 0 4px}
input,select,textarea,button{width:100%;background:#0a0a0a;border:1px solid #333;color:#fff;padding:10px;border-radius:8px;font-size:14px;font-family:inherit}
input:focus,select:focus,textarea:focus{outline:none;border-color:#0ff}
input[type=color]{height:40px;padding:2px;cursor:pointer}
input[type=range]{padding:0;height:8px;background:#222;border:0;-webkit-appearance:none}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;background:#0ff;border-radius:50%;cursor:pointer}
.r2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.r3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.r4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
button{background:#0ff;color:#000;font-weight:600;cursor:pointer;border:none}
button:hover{background:#fff;color:#000}
button.fx{background:#1a1a1a;color:#0ff;border:1px solid #0ff;padding:10px 6px;font-size:12px;font-weight:500}
button.fx:hover{background:#0ff;color:#000}
button.fx.active{background:#0ff;color:#000}
button.alt{background:#1a1a1a;color:#aaa;border:1px solid #333}
button.alt:hover{background:#222;color:#fff;border-color:#666}
button.danger{background:transparent;color:#888;border:1px solid #333;margin-top:8px}
button.danger:hover{color:#f66;border-color:#a00}
.flash{margin-top:10px;padding:8px;border-radius:6px;font-size:12px;display:none;text-align:center}
.ok{background:#0a3a1a;color:#4f9;display:block}
.err{background:#3a0a0a;color:#f66;display:block}
.row{display:flex;align-items:center;gap:8px}
.row span{font-family:monospace;color:#0ff;font-size:13px;min-width:40px;text-align:right}
</style></head><body>
<div class="box">
<h1>Galactic Unicorn</h1>
<p class="sub">53x11 RGB display</p>

<div class="grid">
<div><span class="k">IP</span><span class="v">{IP}</span></div>
<div><span class="k">Uptime</span><span class="v">{UP}s</span></div>
<div><span class="k">Mode</span><span class="v" id="vm">{MODE}</span></div>
<div><span class="k">Effect</span><span class="v" id="ve">{EFFECT}</span></div>
<div><span class="k">Memory</span><span class="v">{MEM}K</span></div>
<div><span class="k">Brightness</span><span class="v" id="vb">{BR}</span></div>
</div>

<h2>Message</h2>
<input id="t" placeholder="Type a message..." value="HELLO">
<div class="r3" style="margin-top:8px">
<div><label>Color</label><input type="color" id="c" value="#00ff00"></div>
<div><label>Speed <span id="sv">3</span></label><input type="range" id="s" min="1" max="10" value="3"></div>
<div><label>Font</label><select id="f"><option>bitmap8</option><option>bitmap6</option><option>font8</option><option>sans</option><option>gothic</option><option>cursive</option><option>serif</option><option>serif_italic</option></select></div>
</div>
<div class="r2" style="margin-top:8px">
<button id="send">Scroll once</button>
<button id="loop" class="alt">Scroll forever</button>
</div>

<h2>Effects</h2>
<div class="r4">
<button class="fx" data-fx="fire">Fire</button>
<button class="fx" data-fx="rainbow">Rainbow</button>
<button class="fx" data-fx="supercomputer">Supercomp</button>
<button class="fx" data-fx="retroprompt">Retro</button>
</div>

<h2>Clock</h2>
<div class="r3">
<select id="cz"><option>UK</option><option>Paris</option><option>NY</option><option>LA</option><option>Tokyo</option><option>Sydney</option><option>UTC</option></select>
<input type="color" id="cc" value="#00ffc8">
<label style="display:flex;align-items:center;gap:6px;color:#aaa;font-size:13px;background:#0a0a0a;border:1px solid #333;border-radius:8px;padding:0 10px;margin:0"><input type="checkbox" id="ck" style="width:auto">Chunky</label>
</div>
<button id="cb" style="margin-top:8px">Show clock</button>

<h2>Brightness <span id="bv" style="color:#0ff;float:right">50%</span></h2>
<input type="range" id="b" min="0" max="100" value="50">

<div class="r2" style="margin-top:14px">
<button class="alt" id="clr">Clear display</button>
<button class="danger" id="rwf">Reset Wi-Fi</button>
</div>

<div id="flash" class="flash"></div>
</div>

<script>
const $=id=>document.getElementById(id),flash=$('flash');
function note(t,ok){flash.textContent=t;flash.className='flash '+(ok?'ok':'err');setTimeout(()=>flash.style.display='none',2500)}
function hex2rgb(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)]}
async function api(p,b){
  const o={method:'POST',headers:{'Content-Type':'application/json'}};
  if(b)o.body=JSON.stringify(b);
  const r=await fetch(p,o);
  return r.json();
}
$('s').oninput=()=>$('sv').textContent=$('s').value;
$('b').oninput=async()=>{
  const v=$('b').value/100;
  $('bv').textContent=Math.round(v*100)+'%';
  await api('/brightness',{value:v});
};
async function sendMsg(repeat){
  try{
    await api('/message',{text:$('t').value,color:hex2rgb($('c').value),speed:+$('s').value,font:$('f').value,repeat:repeat});
    note('Sent: '+$('t').value,1);
  }catch(e){note('Failed',0)}
}
$('send').onclick=()=>sendMsg(1);
$('loop').onclick=()=>sendMsg(0);
document.querySelectorAll('.fx').forEach(b=>b.onclick=async()=>{
  document.querySelectorAll('.fx').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  await api('/effect',{name:b.dataset.fx});
  note(b.dataset.fx+' running',1);
});
$('clr').onclick=async()=>{
  document.querySelectorAll('.fx').forEach(x=>x.classList.remove('active'));
  await api('/clear');
  note('Cleared',1);
};
$('cb').onclick=async()=>{
  document.querySelectorAll('.fx').forEach(x=>x.classList.remove('active'));
  const r=await api('/clock',{zone:$('cz').value,color:hex2rgb($('cc').value),chunky:$('ck').checked});
  note(r.synced?'Clock '+r.zone+($('ck').checked?' chunky':''):'Clock set ('+r.zone+', NTP not synced yet)',r.synced);
};
$('rwf').onclick=()=>{if(confirm('Reset Wi-Fi and reboot?'))fetch('/wifi/reset',{method:'POST'})};

// Live status refresh every 3s
async function refresh(){
  try{
    const s=await(await fetch('/status')).json();
    $('vm').textContent=s.mode;
    $('ve').textContent=s.effect||'-';
    $('vb').textContent=s.brightness;
  }catch(e){}
}
setInterval(refresh,3000);
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
            elif method == "POST" and path == "/clock":
                self._handle_clock(cl, body)
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

    def _handle_clock(self, cl, body):
        import timesync
        data = self._parse_json(body)
        zone = data.get("zone", "UK")
        color = data.get("color", [0, 255, 200])
        seconds = bool(data.get("seconds", False))
        chunky = bool(data.get("chunky", False))
        if zone not in timesync.TIMEZONES:
            self._send(cl, 400, {"error": "unknown zone: " + zone,
                                 "zones": list(timesync.TIMEZONES.keys())})
            return
        if not timesync.is_synced():
            timesync.sync()
        self.renderer.set_clock(zone=zone, color=tuple(color), seconds=seconds, chunky=chunky)
        self._send(cl, 200, {"status": "ok", "mode": "clock", "zone": zone,
                             "synced": timesync.is_synced()})

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
