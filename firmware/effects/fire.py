import random
from galactic import GalacticUnicorn


class FireEffect:
    def __init__(self, graphics, gu):
        self.graphics = graphics
        self.gu = gu
        self.width = GalacticUnicorn.WIDTH + 2
        self.height = GalacticUnicorn.HEIGHT + 4
        self.heat = [[0.0 for _ in range(self.height)] for _ in range(self.width)]
        self.fire_spawns = 5
        self.damping_factor = 0.97
        self.palette = None

    def init(self):
        self.palette = [
            self.graphics.create_pen(0, 0, 0),
            self.graphics.create_pen(20, 20, 20),
            self.graphics.create_pen(180, 30, 0),
            self.graphics.create_pen(220, 160, 0),
            self.graphics.create_pen(255, 255, 180),
        ]

    @micropython.native
    def _pen_from_value(self, value):
        if value < 0.15:
            return self.palette[0]
        elif value < 0.25:
            return self.palette[1]
        elif value < 0.35:
            return self.palette[2]
        elif value < 0.45:
            return self.palette[3]
        return self.palette[4]

    @micropython.native
    def draw(self):
        heat = self.heat
        width = self.width
        height = self.height
        graphics = self.graphics

        for x in range(width):
            heat[x][height - 1] = 0.0
            heat[x][height - 2] = 0.0

        for c in range(self.fire_spawns):
            x = random.randint(0, width - 4) + 2
            heat[x][height - 1] = 1.0
            heat[x + 1][height - 1] = 1.0
            heat[x - 1][height - 1] = 1.0
            heat[x][height - 2] = 1.0
            heat[x + 1][height - 2] = 1.0
            heat[x - 1][height - 2] = 1.0

        damping = self.damping_factor
        for y in range(0, height - 2):
            for x in range(1, width - 1):
                average = (
                    heat[x][y] + heat[x][y + 1] + heat[x][y + 2]
                    + heat[x - 1][y + 1] + heat[x + 1][y + 1]
                ) / 5.0
                heat[x][y] = average * damping

        dw = GalacticUnicorn.WIDTH
        dh = GalacticUnicorn.HEIGHT
        for y in range(dh):
            for x in range(dw):
                graphics.set_pen(self._pen_from_value(heat[x + 1][y]))
                graphics.pixel(x, y)
