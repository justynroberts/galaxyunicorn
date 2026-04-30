import random
from galactic import GalacticUnicorn


class SupercomputerEffect:
    def __init__(self, graphics, gu):
        self.graphics = graphics
        self.gu = gu
        self.width = GalacticUnicorn.WIDTH
        self.height = GalacticUnicorn.HEIGHT
        self.colour = (230, 150, 0)
        self.lifetime = None
        self.age = None

    def init(self):
        w = self.width
        h = self.height
        self.lifetime = [[1.0 + random.uniform(0.0, 0.1) for _ in range(h)] for _ in range(w)]
        self.age = [[random.uniform(0.0, 1.0) * self.lifetime[x][y] for y in range(h)] for x in range(w)]

    @micropython.native
    def draw(self):
        width = self.width
        height = self.height
        lifetime = self.lifetime
        age = self.age
        colour = self.colour
        graphics = self.graphics

        for y in range(height):
            for x in range(width):
                if age[x][y] >= lifetime[x][y]:
                    age[x][y] = 0.0
                    lifetime[x][y] = 1.0 + random.uniform(0.0, 0.1)
                age[x][y] += 0.025

        for y in range(height):
            for x in range(width):
                if age[x][y] < lifetime[x][y] * 0.3:
                    graphics.set_pen(graphics.create_pen(colour[0], colour[1], colour[2]))
                elif age[x][y] < lifetime[x][y] * 0.5:
                    decay = (lifetime[x][y] * 0.5 - age[x][y]) * 5.0
                    graphics.set_pen(graphics.create_pen(
                        int(decay * colour[0]), int(decay * colour[1]), int(decay * colour[2])
                    ))
                else:
                    graphics.set_pen(0)
                graphics.pixel(x, y)
