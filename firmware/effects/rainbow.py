import math
from galactic import GalacticUnicorn


class RainbowEffect:
    def __init__(self, graphics, gu):
        self.graphics = graphics
        self.gu = gu
        self.width = GalacticUnicorn.WIDTH
        self.height = GalacticUnicorn.HEIGHT
        self.phase = 0
        self.hue_offset = 0.0
        self.stripe_width = 3.0
        self.speed = 5.0
        self.hue_map = [self._from_hsv(x / self.width, 1.0, 1.0) for x in range(self.width)]

    def init(self):
        pass

    @staticmethod
    @micropython.native
    def _from_hsv(h, s, v):
        i = math.floor(h * 6.0)
        f = h * 6.0 - i
        v *= 255.0
        p = v * (1.0 - s)
        q = v * (1.0 - f * s)
        t = v * (1.0 - (1.0 - f) * s)

        i = int(i) % 6
        if i == 0:
            return int(v), int(t), int(p)
        if i == 1:
            return int(q), int(v), int(p)
        if i == 2:
            return int(p), int(v), int(t)
        if i == 3:
            return int(p), int(q), int(v)
        if i == 4:
            return int(t), int(p), int(v)
        if i == 5:
            return int(v), int(p), int(q)
        return 0, 0, 0

    @micropython.native
    def draw(self):
        self.phase += self.speed
        phase_percent = self.phase / 15
        width = self.width
        height = self.height
        hue_map = self.hue_map
        stripe_width = self.stripe_width
        hue_offset = self.hue_offset
        graphics = self.graphics

        for x in range(width):
            colour = hue_map[int((x + (hue_offset * width)) % width)]
            for y in range(height):
                v = ((math.sin((x + y) / stripe_width + phase_percent) + 1.5) / 2.5)
                graphics.set_pen(graphics.create_pen(
                    int(colour[0] * v), int(colour[1] * v), int(colour[2] * v)
                ))
                graphics.pixel(x, y)
