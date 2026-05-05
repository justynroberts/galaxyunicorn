import gc
import time
import ubinascii
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN

MODE_IDLE = "idle"
MODE_SCROLL = "scroll"
MODE_PIXELS = "pixels"
MODE_EFFECT = "effect"
MODE_CLOCK = "clock"

# Font name to PicoGraphics font constant mapping.
# Many other names (bitmap5/7/10, font6/font10, bitmap14_outline) are
# silent aliases for these in the firmware — same width, same look.
FONTS = {
    "bitmap6": "bitmap6",
    "bitmap8": "bitmap8",
    "font8": "font8",
    "sans": "sans",
    "gothic": "gothic",
    "cursive": "cursive",
    "serif": "serif",
    "serif_italic": "serif_italic",
}

# Approximate pixel height of each font at scale 1
FONT_HEIGHTS = {
    "bitmap6": 6,
    "bitmap8": 8,
    "font8": 16,
    "sans": 14,
    "gothic": 14,
    "cursive": 14,
    "serif": 14,
    "serif_italic": 14,
}


class Renderer:
    def __init__(self):
        self.gu = GalacticUnicorn()
        self.graphics = PicoGraphics(DISPLAY_GALACTIC_UNICORN)
        self.width, self.height = self.graphics.get_bounds()
        self.gu.set_brightness(0.5)

        self.mode = MODE_IDLE
        self.effect_name = None
        self.current_effect = None

        # Scroll state
        self.scroll_text = ""
        self.scroll_color = None
        self.scroll_speed = 1
        self.scroll_scale = 1
        self.scroll_repeat = 1
        self.scroll_repeat_count = 0
        self.scroll_x = 0
        self.scroll_font = "bitmap8"

        # Clock state
        self.clock_zone = "UK"
        self.clock_color = None
        self.clock_seconds = False
        self.clock_chunky = False
        self._clock_last_str = ""

        self._clear_display()

    def _clear_display(self):
        self.graphics.set_pen(self.graphics.create_pen(0, 0, 0))
        self.graphics.clear()
        self.gu.update(self.graphics)

    def set_scroll(self, text, color, speed=1, scale=1, repeat=1, font="bitmap8"):
        self.mode = MODE_SCROLL
        self.scroll_text = text
        self.scroll_color = self.graphics.create_pen(*color)
        self.scroll_speed = max(1, min(10, speed))
        self.scroll_scale = max(1, min(3, scale))
        self.scroll_repeat = repeat
        self.scroll_repeat_count = 0
        self.scroll_x = self.width
        self.scroll_font = font if font in FONTS else "bitmap8"
        self.current_effect = None
        self.effect_name = None
        gc.collect()

    def set_pixels(self, b64_data):
        self.mode = MODE_PIXELS
        self.current_effect = None
        self.effect_name = None
        gc.collect()
        raw = ubinascii.a2b_base64(b64_data)
        n = min(self.width * self.height, len(raw) // 3)
        for i in range(n):
            r = raw[i * 3]
            g = raw[i * 3 + 1]
            b = raw[i * 3 + 2]
            x = i % self.width
            y = i // self.width
            self.graphics.set_pen(self.graphics.create_pen(r, g, b))
            self.graphics.pixel(x, y)
        del raw
        self.gu.update(self.graphics)
        gc.collect()

    def set_clock(self, zone="UK", color=(0, 255, 200), seconds=False, chunky=False):
        self.mode = MODE_CLOCK
        self.clock_zone = zone
        self.clock_color = self.graphics.create_pen(*color)
        self.clock_seconds = seconds
        self.clock_chunky = chunky
        self._clock_last_str = ""
        self.current_effect = None
        self.effect_name = None
        gc.collect()

    def set_effect(self, name, effects_registry):
        if name not in effects_registry:
            return False
        self.mode = MODE_EFFECT
        self.effect_name = name
        effect_class = effects_registry[name]
        self.current_effect = effect_class(self.graphics, self.gu)
        self.current_effect.init()
        gc.collect()
        return True

    def set_brightness(self, value):
        value = max(0.0, min(1.0, value))
        self.gu.set_brightness(value)
        if self.mode == MODE_PIXELS or self.mode == MODE_IDLE:
            self.gu.update(self.graphics)

    def clear(self):
        self.mode = MODE_IDLE
        self.current_effect = None
        self.effect_name = None
        self._clear_display()
        gc.collect()

    def get_brightness(self):
        return self.gu.get_brightness()

    def tick(self):
        if self.mode == MODE_SCROLL:
            self._tick_scroll()
        elif self.mode == MODE_EFFECT:
            self._tick_effect()
        elif self.mode == MODE_CLOCK:
            self._tick_clock()

    def _tick_scroll(self):
        self.graphics.set_pen(self.graphics.create_pen(0, 0, 0))
        self.graphics.clear()
        self.graphics.set_pen(self.scroll_color)

        self.graphics.set_font(self.scroll_font)
        base_height = FONT_HEIGHTS.get(self.scroll_font, 8)
        text_height = base_height * self.scroll_scale
        # Round up for better visual centering (shift down slightly)
        y = max(0, (self.height - text_height + 1) // 2)

        self.graphics.text(self.scroll_text, self.scroll_x, y, scale=self.scroll_scale)
        self.gu.update(self.graphics)
        self.scroll_x -= self.scroll_speed

        text_width = self.graphics.measure_text(self.scroll_text, self.scroll_scale)
        if self.scroll_x < -text_width:
            self.scroll_repeat_count += 1
            if self.scroll_repeat > 0 and self.scroll_repeat_count >= self.scroll_repeat:
                self.mode = MODE_IDLE
                self._clear_display()
            else:
                self.scroll_x = self.width

    def _tick_effect(self):
        if self.current_effect:
            self.current_effect.draw()
            self.gu.update(self.graphics)

    def _tick_clock(self):
        try:
            import timesync
        except Exception:
            return
        t = timesync.now_for_zone(self.clock_zone)
        if t is None:
            text = "--:--"
        else:
            h, m, s = t
            if self.clock_seconds:
                text = "{:02d}:{:02d}:{:02d}".format(h, m, s)
            else:
                text = "{:02d}:{:02d}".format(h, m)
        # Only redraw when display string changes
        if text == self._clock_last_str:
            return
        self._clock_last_str = text

        self.graphics.set_pen(self.graphics.create_pen(0, 0, 0))
        self.graphics.clear()
        self.graphics.set_pen(self.clock_color)

        if self.clock_chunky:
            self._draw_chunky(text)
        else:
            self.graphics.set_font("bitmap8")
            text_width = self.graphics.measure_text(text, 1)
            x = max(0, (self.width - text_width) // 2)
            y = max(0, (self.height - 8 + 1) // 2)
            self.graphics.text(text, x, y, scale=1)

        self.gu.update(self.graphics)

    # 7-segment style digits: a, b, c, d, e, f, g
    # Each digit is 5 wide x 9 tall.
    _SEG_DIGITS = {
        "0": "abcdef",
        "1": "bc",
        "2": "abdeg",
        "3": "abcdg",
        "4": "bcfg",
        "5": "acdfg",
        "6": "acdefg",
        "7": "abc",
        "8": "abcdefg",
        "9": "abcdfg",
        "-": "g",
    }

    def _draw_seg_digit(self, x, y, digit):
        # Special-case digits that would otherwise have top/bottom gaps
        # (1, 4, 7) so the full 11px cell is used.
        if digit == "1":
            self.graphics.rectangle(x + 2, y + 0, 2, 11)  # centered full-height bar
            self.graphics.rectangle(x + 0, y + 2, 4, 2)   # top serif
            self.graphics.rectangle(x + 0, y + 9, 6, 2)   # base
            return
        if digit == "4":
            self.graphics.rectangle(x + 0, y + 0, 2, 5)   # left top vertical
            self.graphics.rectangle(x + 5, y + 0, 2, 11)  # right full vertical
            self.graphics.rectangle(x + 0, y + 4, 7, 2)   # middle full-width
            return
        if digit == "7":
            self.graphics.rectangle(x + 0, y + 0, 7, 2)   # full-width top bar
            self.graphics.rectangle(x + 5, y + 1, 2, 10)  # right full vertical
            return

        segs = self._SEG_DIGITS.get(digit, "")
        # Digit cell: 7 wide x 11 tall with 2px-thick strokes.
        if "a" in segs:
            self.graphics.rectangle(x + 1, y, 5, 2)
        if "f" in segs:
            self.graphics.rectangle(x, y + 1, 2, 4)
        if "b" in segs:
            self.graphics.rectangle(x + 5, y + 1, 2, 4)
        if "g" in segs:
            self.graphics.rectangle(x + 1, y + 4, 5, 2)
        if "e" in segs:
            self.graphics.rectangle(x, y + 6, 2, 4)
        if "c" in segs:
            self.graphics.rectangle(x + 5, y + 6, 2, 4)
        if "d" in segs:
            self.graphics.rectangle(x + 1, y + 9, 5, 2)

    def _draw_chunky(self, text):
        # Digit cell: 7 wide x 11 tall. Colon: 2 wide. Gap between: 1px.
        # HH:MM => 7+1+7+2+1+7+1+7 = 33px wide  (centered in 53)
        digit_w = 7
        gap = 1
        colon_w = 2
        w = 0
        for i, ch in enumerate(text):
            w += colon_w if ch == ":" else digit_w
            if i < len(text) - 1:
                w += gap
        x = max(0, (self.width - w) // 2)
        y = 0  # fills full 11px height

        for ch in text:
            if ch == ":":
                self.graphics.rectangle(x, y + 2, 2, 2)
                self.graphics.rectangle(x, y + 7, 2, 2)
                x += colon_w + gap
            else:
                self._draw_seg_digit(x, y, ch)
                x += digit_w + gap
