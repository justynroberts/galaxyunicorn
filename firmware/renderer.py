import gc
import time
import ubinascii
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN

MODE_IDLE = "idle"
MODE_SCROLL = "scroll"
MODE_PIXELS = "pixels"
MODE_EFFECT = "effect"

# Font name to PicoGraphics font constant mapping
FONTS = {
    "bitmap5": "bitmap5",
    "bitmap6": "bitmap6",
    "bitmap7": "bitmap7",
    "bitmap8": "bitmap8",
    "bitmap10": "bitmap10",
    "font6": "font6",
    "font8": "font8",
    "font10": "font10",
}

# Approximate pixel height of each font at scale 1
FONT_HEIGHTS = {
    "bitmap5": 5,
    "bitmap6": 6,
    "bitmap7": 7,
    "bitmap8": 8,
    "bitmap10": 10,
    "font6": 6,
    "font8": 8,
    "font10": 10,
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

        self._clear_display()

    def _clear_display(self):
        self.graphics.set_pen(self.graphics.create_pen(0, 0, 0))
        self.graphics.clear()
        self.gu.update(self.graphics)

    def set_scroll(self, text, color, speed=1, scale=1, repeat=1, font="bitmap8"):
        self.mode = MODE_SCROLL
        self.scroll_text = text
        self.scroll_color = self.graphics.create_pen(*color)
        self.scroll_speed = max(1, min(5, speed))
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
