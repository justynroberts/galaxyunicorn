import ujson
import uos

CONFIG_FILE = "wifi.cfg"


def save(ssid, password):
    data = ujson.dumps({"ssid": ssid, "password": password})
    with open(CONFIG_FILE, "w") as f:
        f.write(data)


def load():
    try:
        with open(CONFIG_FILE, "r") as f:
            return ujson.loads(f.read())
    except (OSError, ValueError):
        return None


def clear():
    try:
        uos.remove(CONFIG_FILE)
        return True
    except OSError:
        return False


def exists():
    try:
        uos.stat(CONFIG_FILE)
        return True
    except OSError:
        return False
