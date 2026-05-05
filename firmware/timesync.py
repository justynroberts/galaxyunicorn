import time
import ntptime
import machine


# Timezone presets: (offset_minutes, observes_european_DST, observes_us_DST)
TIMEZONES = {
    "UK":     (0,    True,  False),  # GMT/BST
    "Paris":  (60,   True,  False),  # CET/CEST
    "NY":     (-300, False, True),   # EST/EDT
    "LA":     (-480, False, True),   # PST/PDT
    "Tokyo":  (540,  False, False),  # JST (no DST)
    "Sydney": (600,  False, False),  # AEST (DST handled approximately)
    "UTC":    (0,    False, False),
}


_last_sync = 0
_synced = False


def sync(retries=3):
    """Sync RTC to NTP. Sets the device clock to UTC."""
    global _last_sync, _synced
    for _ in range(retries):
        try:
            ntptime.settime()
            _last_sync = time.time()
            _synced = True
            return True
        except Exception:
            time.sleep(1)
    return False


def is_synced():
    return _synced


def maybe_resync(interval_sec=3600):
    """Re-sync if it's been longer than interval since last successful sync."""
    if not _synced:
        sync()
        return
    if time.time() - _last_sync >= interval_sec:
        sync()


def _last_sunday(year, month):
    """Return (day, weekday) for the last Sunday of the given month."""
    # Find day-of-month for last day, walk back to Sunday
    if month == 12:
        next_month = (year + 1, 1)
    else:
        next_month = (year, month + 1)
    # First day of next month, then subtract one day
    t = time.mktime((next_month[0], next_month[1], 1, 0, 0, 0, 0, 0))
    t -= 86400
    tm = time.gmtime(t)
    # tm[6] is weekday: 0=Mon..6=Sun in MicroPython
    days_back = (tm[6] + 1) % 7  # Sun=6 -> 0, Mon=0 -> 1, etc.
    return tm[2] - days_back


def _eu_dst_active(utc_t):
    """European DST: last Sun of March 01:00 UTC to last Sun of October 01:00 UTC."""
    tm = time.gmtime(utc_t)
    year, month, day, hour = tm[0], tm[1], tm[2], tm[3]
    if month < 3 or month > 10:
        return False
    if 3 < month < 10:
        return True
    if month == 3:
        last_sun = _last_sunday(year, 3)
        if day < last_sun:
            return False
        if day > last_sun:
            return True
        return hour >= 1
    if month == 10:
        last_sun = _last_sunday(year, 10)
        if day < last_sun:
            return True
        if day > last_sun:
            return False
        return hour < 1
    return False


def _us_dst_active(utc_t):
    """US DST: 2nd Sun of March 02:00 local to 1st Sun of November 02:00 local.
    Approximated using UTC bounds."""
    tm = time.gmtime(utc_t)
    year, month, day = tm[0], tm[1], tm[2]
    if month < 3 or month > 11:
        return False
    if 3 < month < 11:
        return True
    if month == 3:
        # 2nd Sunday of March
        # Find first Sunday: day 1..7 where weekday==6 (Sun)
        for d in range(1, 8):
            t = time.mktime((year, 3, d, 0, 0, 0, 0, 0))
            if time.gmtime(t)[6] == 6:
                second_sun = d + 7
                break
        else:
            second_sun = 14
        return day >= second_sun
    if month == 11:
        for d in range(1, 8):
            t = time.mktime((year, 11, d, 0, 0, 0, 0, 0))
            if time.gmtime(t)[6] == 6:
                first_sun = d
                break
        else:
            first_sun = 7
        return day < first_sun
    return False


def now_for_zone(zone_name):
    """Returns (hour, minute, second) for the named timezone, applying DST."""
    if not _synced:
        return None
    tz = TIMEZONES.get(zone_name, TIMEZONES["UTC"])
    offset_min, eu_dst, us_dst = tz
    utc_t = time.time()
    if eu_dst and _eu_dst_active(utc_t):
        offset_min += 60
    if us_dst and _us_dst_active(utc_t):
        offset_min += 60
    local_t = utc_t + offset_min * 60
    tm = time.gmtime(local_t)
    return tm[3], tm[4], tm[5]
