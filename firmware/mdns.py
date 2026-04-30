import socket
import struct

MDNS_ADDR = "224.0.0.251"
MDNS_PORT = 5353


class MDNSResponder:
    def __init__(self, hostname, ip):
        self.hostname = hostname
        self.ip = ip
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", MDNS_PORT))
        mreq = struct.pack("4s4s",
                           socket.inet_aton(MDNS_ADDR),
                           socket.inet_aton("0.0.0.0"))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.settimeout(0)

    def poll(self):
        try:
            data, addr = self.sock.recvfrom(256)
            name = self.hostname + ".local"
            if name.encode() in data or self._match_query(data):
                response = self._build_response()
                self.sock.sendto(response, (MDNS_ADDR, MDNS_PORT))
        except OSError:
            pass

    def _match_query(self, data):
        # Check for our hostname in DNS query format (length-prefixed labels)
        try:
            hostname_labels = self.hostname.encode()
            local_labels = b"local"
            # Build DNS-encoded name: \x07display\x05local\x00
            encoded = bytes([len(hostname_labels)]) + hostname_labels
            encoded += bytes([len(local_labels)]) + local_labels + b"\x00"
            return encoded in data
        except Exception:
            return False

    def _build_response(self):
        # Build a minimal mDNS A record response
        name = self.hostname
        # Transaction ID (0), Flags (authoritative response)
        header = struct.pack("!HHHHHH", 0, 0x8400, 0, 1, 0, 0)

        # Answer: name + type A + class IN (cache flush) + TTL + rdlength + IP
        # Encode name as DNS labels
        answer_name = b""
        for label in [name, "local"]:
            label_bytes = label.encode()
            answer_name += bytes([len(label_bytes)]) + label_bytes
        answer_name += b"\x00"

        # Type A (1), Class IN with cache-flush bit (0x8001), TTL 120s, RDLENGTH 4
        answer_rr = struct.pack("!HHIH", 1, 0x8001, 120, 4)

        # IP address as 4 bytes
        ip_parts = self.ip.split(".")
        ip_bytes = bytes([int(p) for p in ip_parts])

        return header + answer_name + answer_rr + ip_bytes
