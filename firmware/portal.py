import gc
import time
import socket
import network
import ujson
from mdns import MDNSResponder


def _log(*args):
    msg = " ".join(str(a) for a in args)
    print(msg)
    try:
        with open("boot.log", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


PORTAL_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galactic Unicorn Setup</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,system-ui,sans-serif;padding:20px;min-height:100vh}
.box{max-width:420px;margin:30px auto;background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:24px}
h1{font-size:22px;margin-bottom:6px;background:linear-gradient(90deg,#0ff,#f0f);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p.sub{color:#888;font-size:13px;margin-bottom:20px}
label{display:block;font-size:13px;color:#aaa;margin:14px 0 6px}
select,input{width:100%;background:#0a0a0a;border:1px solid #333;color:#fff;padding:11px;border-radius:8px;font-size:14px}
select:focus,input:focus{outline:none;border-color:#0ff}
button{width:100%;background:#0ff;color:#000;border:none;padding:13px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;margin-top:18px}
button:hover{background:#fff}
button.ghost{background:transparent;color:#888;border:1px solid #333;margin-top:8px}
button.ghost:hover{color:#fff;border-color:#666}
#msg{margin-top:16px;padding:12px;border-radius:8px;font-size:13px;display:none}
.ok{background:#0a3a1a;color:#4f9;border:1px solid #0a6}
.err{background:#3a0a0a;color:#f66;border:1px solid #a00}
.info{background:#0a1a3a;color:#6af;border:1px solid #06a}
.bar{display:inline-block;width:6px;height:10px;background:#444;margin-right:1px;vertical-align:middle;border-radius:1px}
.bar.on{background:#0ff}
</style></head><body>
<div class="box">
<h1>Galactic Unicorn</h1>
<p class="sub">Connect your display to Wi-Fi</p>
<form id="f">
<label>Network</label>
<select name="ssid" id="ssid" required>__OPTIONS__</select>
<label>Password</label>
<input type="password" name="password" id="pw" autocomplete="off">
<button type="submit" id="btn">Connect</button>
<button type="button" class="ghost" id="refresh">Refresh networks</button>
</form>
<div id="msg"></div>
</div>
<script>
const f=document.getElementById('f'),m=document.getElementById('msg'),b=document.getElementById('btn'),r=document.getElementById('refresh'),sel=document.getElementById('ssid');
function show(t,c){m.textContent=t;m.className=c;m.style.display='block'}
function bars(rssi){let n=rssi>=-55?4:rssi>=-65?3:rssi>=-75?2:1;return '['+'='.repeat(n)+' '.repeat(4-n)+']'}
r.onclick=async()=>{
  r.disabled=true;r.textContent='Scanning... (~6s)';show('Rescanning networks. Wi-Fi may briefly drop.','info');
  try{
    const resp=await fetch('/rescan',{method:'POST'});
    const j=await resp.json();
    sel.innerHTML='';
    if(!j.networks||!j.networks.length){sel.innerHTML='<option value="">No networks found</option>'}
    else{j.networks.forEach(n=>{const o=document.createElement('option');o.value=n.ssid;o.textContent=bars(n.rssi)+' '+n.ssid;sel.appendChild(o)})}
    show('Found '+(j.networks?j.networks.length:0)+' networks.','ok');
  }catch(err){show('Rescan failed: '+err.message,'err')}
  finally{r.disabled=false;r.textContent='Refresh networks'}
};
f.onsubmit=async e=>{e.preventDefault();
  const s=sel.value,p=document.getElementById('pw').value;
  b.disabled=true;b.textContent='Testing connection...';show('Connecting to '+s+'...','info');
  try{
    const resp=await fetch('/connect',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'ssid='+encodeURIComponent(s)+'&password='+encodeURIComponent(p)});
    const j=await resp.json();
    if(j.ok){show('Connected! Saving and rebooting in 3s...','ok');setTimeout(()=>show('The display has rejoined your network. You can close this page.','ok'),3000)}
    else{show('Failed: '+(j.error||'unknown error'),'err');b.disabled=false;b.textContent='Connect'}
  }catch(err){show('Network error: '+err.message,'err');b.disabled=false;b.textContent='Connect'}
};
</script></body></html>"""


CAPTIVE_DETECT_PATHS = (
    "/hotspot-detect.html",
    "/library/test/success.html",
    "/generate_204",
    "/gen_204",
    "/connecttest.txt",
    "/redirect",
    "/canonical.html",
    "/success.txt",
    "/ncsi.txt",
)


class CaptivePortal:
    def __init__(self, ap_ssid, ap_ip, renderer=None):
        self.ap_ssid = ap_ssid
        self.ap_ip = ap_ip
        self.renderer = renderer
        self.networks = []
        self.http_sock = None
        self.dns_sock = None
        self.dhcp = None
        self.mdns = None
        self.ap = None
        self.result = None  # None | {"ssid":..., "password":...}

    def scan_networks(self, passes=5):
        # Drop AP if it's up so the radio can fully scan.
        ap_was_up = self.ap and self.ap.active()
        if ap_was_up:
            try:
                self.ap.active(False)
                time.sleep_ms(500)
            except Exception:
                pass

        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        time.sleep(2)

        seen = {}
        for attempt in range(passes):
            try:
                raw = sta.scan()
            except Exception as e:
                _log("[portal] scan error:", e)
                raw = []
            for entry in raw:
                try:
                    ssid = entry[0].decode("utf-8", "ignore").strip()
                    rssi = entry[3]
                    if not ssid:
                        continue
                    if ssid not in seen or rssi > seen[ssid]:
                        seen[ssid] = rssi
                except Exception:
                    continue
            _log("[portal] scan pass", attempt + 1, "found", len(seen), "unique")
            time.sleep_ms(800)

        sta.active(False)
        time.sleep_ms(300)

        self.networks = sorted(seen.items(), key=lambda x: -x[1])
        _log("[portal] scanned", len(self.networks), "networks total")
        gc.collect()

        # Bring AP back up if we took it down
        if ap_was_up:
            try:
                self.ap.active(True)
                while not self.ap.active():
                    time.sleep_ms(100)
                _log("[portal] AP restored after scan")
            except Exception as e:
                _log("[portal] AP restore failed:", e)

    def start(self):
        if not self.networks:
            self.scan_networks()

        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(False)
        time.sleep_ms(200)
        self.ap.config(essid=self.ap_ssid, security=0)
        self.ap.active(True)
        while not self.ap.active():
            time.sleep_ms(100)
        _log("[portal] AP up:", self.ap.ifconfig())

        # DNS server
        self.dns_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dns_sock.bind(("0.0.0.0", 53))
        self.dns_sock.setblocking(False)

        # HTTP server
        self.http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.http_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.http_sock.bind(("0.0.0.0", 80))
        self.http_sock.listen(3)
        self.http_sock.settimeout(0.05)

        # mDNS responder: setup.local -> AP IP
        try:
            self.mdns = MDNSResponder("setup", self.ap_ip)
            self.mdns.start()
            _log("[portal] mDNS: setup.local ->", self.ap_ip)
        except Exception as e:
            _log("[portal] mDNS failed:", e)
            self.mdns = None

        gc.collect()
        _log("[portal] free mem:", gc.mem_free())

    def poll(self):
        # DNS
        for _ in range(4):
            if not self._poll_dns():
                break
        # mDNS
        if self.mdns:
            try:
                self.mdns.poll()
            except Exception:
                pass
        # HTTP
        try:
            cl, addr = self.http_sock.accept()
            self._handle_http(cl)
        except OSError:
            pass

    def _poll_dns(self):
        try:
            data, addr = self.dns_sock.recvfrom(256)
        except OSError:
            return False
        try:
            # Extract queried name for logging
            name_parts = []
            i = 12
            while i < len(data) and data[i] != 0:
                length = data[i]
                if length == 0 or i + 1 + length > len(data):
                    break
                name_parts.append(data[i + 1:i + 1 + length].decode("utf-8", "ignore"))
                i += 1 + length
            qname = ".".join(name_parts)
            _log("[portal] DNS", addr[0], "->", qname)
            self.dns_sock.sendto(self._build_dns_response(data), addr)
        except Exception as e:
            _log("[portal] dns err:", e)
        return True

    def _build_dns_response(self, query):
        # Transaction ID + flags (response, authoritative, no error)
        resp = query[:2] + b"\x81\x80"
        # QDCOUNT (echo) + ANCOUNT=1 + NSCOUNT=0 + ARCOUNT=0
        resp += query[4:6] + b"\x00\x01\x00\x00\x00\x00"
        # Find end of question section (qname + qtype + qclass)
        i = 12
        while i < len(query) and query[i] != 0:
            i += query[i] + 1
        qend = i + 5  # null + qtype(2) + qclass(2)
        resp += query[12:qend]
        # Answer: pointer to qname, type A, class IN, TTL 60, rdlength 4, IP
        resp += b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
        resp += bytes(int(p) for p in self.ap_ip.split("."))
        return resp

    def _handle_http(self, cl):
        try:
            try:
                peer = cl.getpeername()
            except Exception:
                peer = ("?", 0)
            cl.settimeout(3)
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = cl.recv(512)
                if not chunk:
                    return
                data += chunk
                if len(data) > 4096:
                    return

            header_end = data.index(b"\r\n\r\n") + 4
            header_str = data[:header_end].decode("utf-8", "ignore")
            body = data[header_end:]

            content_length = 0
            for line in header_str.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    try:
                        content_length = int(line.split(":", 1)[1].strip())
                    except Exception:
                        content_length = 0
                    break

            while len(body) < content_length:
                chunk = cl.recv(512)
                if not chunk:
                    break
                body += chunk

            request_line = header_str.split("\r\n", 1)[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                self._send_404(cl)
                return
            method, path = parts[0], parts[1]
            _log("[portal] HTTP", peer[0], method, path)

            # Strip query string
            qmark = path.find("?")
            if qmark >= 0:
                path = path[:qmark]

            if method == "POST" and path == "/connect":
                self._handle_connect(cl, body)
            elif method == "GET" and path == "/":
                self._send_portal(cl)
            elif method == "POST" and path == "/rescan":
                self._handle_rescan(cl)
            elif method == "GET" and path in CAPTIVE_DETECT_PATHS:
                self._send_redirect(cl)
            else:
                self._send_redirect(cl)

        except Exception as e:
            _log("[portal] http err:", e)
            try:
                self._send_404(cl)
            except Exception:
                pass
        finally:
            try:
                cl.close()
            except Exception:
                pass
            gc.collect()

    def _send_portal(self, cl):
        opts = []
        for ssid, rssi in self.networks:
            bars = self._signal_bars(rssi)
            # Escape HTML in SSIDs
            safe = ssid.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            opts.append('<option value="{}">{} {}</option>'.format(safe, bars, safe))
        if not opts:
            opts.append('<option value="">No networks found - tap Refresh</option>')
        html = PORTAL_HTML.replace("__OPTIONS__", "".join(opts))
        body = html.encode("utf-8")
        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Content-Length: {}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).format(len(body))
        cl.sendall(headers.encode() + body)

    def _send_redirect(self, cl):
        loc = "http://{}/".format(self.ap_ip)
        headers = (
            "HTTP/1.1 302 Found\r\n"
            "Location: {}\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        ).format(loc)
        cl.sendall(headers.encode())

    def _send_404(self, cl):
        cl.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")

    def _send_json(self, cl, status, data):
        body = ujson.dumps(data).encode()
        st = "OK" if status == 200 else "Bad Request"
        headers = (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n\r\n"
        ).format(status, st, len(body))
        cl.sendall(headers.encode() + body)

    def _signal_bars(self, rssi):
        # rssi typically -30 (great) to -90 (poor)
        if rssi >= -55:
            n = 4
        elif rssi >= -65:
            n = 3
        elif rssi >= -75:
            n = 2
        else:
            n = 1
        return "[" + "=" * n + " " * (4 - n) + "]"

    def _parse_form(self, body):
        result = {}
        try:
            text = body.decode("utf-8", "ignore")
        except Exception:
            return result
        for pair in text.split("&"):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            result[self._url_decode(k)] = self._url_decode(v)
        return result

    def _url_decode(self, s):
        s = s.replace("+", " ")
        out = ""
        i = 0
        while i < len(s):
            if s[i] == "%" and i + 2 < len(s):
                try:
                    out += chr(int(s[i + 1:i + 3], 16))
                    i += 3
                    continue
                except Exception:
                    pass
            out += s[i]
            i += 1
        return out

    def _handle_rescan(self, cl):
        _log("[portal] manual rescan requested")
        if self.renderer:
            try:
                self.renderer.set_scroll("Scanning...", [255, 200, 0], 1, 1, 0, "bitmap6")
            except Exception:
                pass
        self.scan_networks(passes=6)
        nets = [{"ssid": s, "rssi": r} for s, r in self.networks]
        self._send_json(cl, 200, {"networks": nets})

    def _handle_connect(self, cl, body):
        form = self._parse_form(body)
        ssid = form.get("ssid", "").strip()
        password = form.get("password", "")

        if not ssid:
            self._send_json(cl, 400, {"ok": False, "error": "ssid required"})
            return

        _log("[portal] testing connection to:", ssid)
        if self.renderer:
            try:
                self.renderer.set_scroll("Testing " + ssid, [0, 200, 255], 1, 1, 1, "bitmap6")
            except Exception:
                pass

        ok, err = self._test_connection(ssid, password)
        if ok:
            self._send_json(cl, 200, {"ok": True})
            self.result = {"ssid": ssid, "password": password}
        else:
            self._send_json(cl, 200, {"ok": False, "error": err})

    def _test_connection(self, ssid, password):
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        time.sleep_ms(300)
        try:
            sta.disconnect()
        except Exception:
            pass
        time.sleep_ms(200)

        try:
            sta.connect(ssid, password)
        except Exception as e:
            return False, "connect failed: " + str(e)

        timeout = 12
        start = time.time()
        while not sta.isconnected() and time.time() - start < timeout:
            time.sleep_ms(250)

        connected = sta.isconnected()
        if connected:
            ip = sta.ifconfig()[0]
            _log("[portal] test connection ok:", ip)
            sta.disconnect()
            sta.active(False)
            time.sleep_ms(300)
            return True, None

        # Diagnose status
        try:
            status = sta.status()
        except Exception:
            status = -1
        sta.active(False)

        msg = "could not connect (timeout)"
        # MicroPython STAT codes vary; -3 typically wrong password
        if status in (-3, 2):
            msg = "wrong password or auth failed"
        elif status == -2:
            msg = "network not found"
        return False, msg

    def stop(self):
        try:
            if self.http_sock:
                self.http_sock.close()
        except Exception:
            pass
        try:
            if self.dns_sock:
                self.dns_sock.close()
        except Exception:
            pass
        try:
            if self.dhcp:
                self.dhcp.stop()
        except Exception:
            pass
        try:
            if self.mdns and self.mdns.sock:
                self.mdns.sock.close()
        except Exception:
            pass
        try:
            if self.ap:
                self.ap.active(False)
        except Exception:
            pass
        gc.collect()
