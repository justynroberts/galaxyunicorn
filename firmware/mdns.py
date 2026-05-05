import socket
import struct
import time

MDNS_ADDR = "224.0.0.251"
MDNS_PORT = 5353


class MDNSAnnouncer:
    """Periodically sends unsolicited mDNS A-record announcements.

    Doesn't bind port 5353 (the firmware's native mDNS already has it),
    only sends multicast announcements. Modern OS mDNS resolvers cache
    these so `<hostname>.local` resolves on the network for the TTL.
    """

    def __init__(self, hostname, ip, interval_sec=30, ttl=60):
        self.hostname = hostname
        self.ip = ip
        self.interval_ms = interval_sec * 1000
        self.ttl = ttl
        self.sock = None
        self.last_send = 0
        self.packet = b""

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # No bind — send-only.
        self.packet = self._build_announcement()
        self._send()
        # Send a couple of initial announcements so caches populate fast.
        time.sleep_ms(200)
        self._send()
        self.last_send = time.ticks_ms()

    def poll(self):
        if not self.sock:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_send) >= self.interval_ms:
            self._send()
            self.last_send = now

    def _send(self):
        try:
            self.sock.sendto(self.packet, (MDNS_ADDR, MDNS_PORT))
        except Exception:
            pass

    def stop(self):
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.sock = None

    def _build_announcement(self):
        # Unsolicited mDNS response (RFC 6762 section 8.3).
        # Header: ID=0, flags=0x8400 (response, authoritative),
        # QDCOUNT=0, ANCOUNT=1, NSCOUNT=0, ARCOUNT=0
        header = struct.pack("!HHHHHH", 0, 0x8400, 0, 1, 0, 0)

        # Name in DNS label form: <len><hostname><len>local<00>
        name_bytes = b""
        for label in (self.hostname, "local"):
            b = label.encode()
            name_bytes += bytes([len(b)]) + b
        name_bytes += b"\x00"

        # Type A (1), class IN with cache-flush bit set (0x8001), TTL, rdlength=4
        rr = struct.pack("!HHIH", 1, 0x8001, self.ttl, 4)

        # IP address as four bytes
        ip_bytes = bytes(int(p) for p in self.ip.split("."))

        return header + name_bytes + rr + ip_bytes


# Backwards-compat alias for any old import paths
MDNSResponder = MDNSAnnouncer
