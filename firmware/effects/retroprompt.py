import time


class RetroPromptEffect:
    def __init__(self, graphics, gu):
        self.graphics = graphics
        self.gu = gu

        self.c64 = [
            "                                                     ",
            "                                                     ",
            " OOOOO   OOOOOO    OO    OOOO    OO  OO      XXXXXXX ",
            " OO  OO  OO       OOOO   OO OO   OO  OO      XXXXXXX ",
            " OO  OO  OO      OO  OO  OO  OO  OO  OO      XXXXXXX ",
            " OOOOO   OOOO    OOOOOO  OO  OO   OOOO       XXXXXXX ",
            " OOOO    OO      OO  OO  OO  OO    OO        XXXXXXX ",
            " OO OO   OO      OO  OO  OO OO     OO    OO  XXXXXXX ",
            " OO  OO  OOOOOO  OO  OO  OOOO      OO    OO  XXXXXXX ",
            "                                             XXXXXXX ",
            "                                                     ",
        ]
        self.fg_c64 = (230, 210, 250)
        self.bg_c64 = (20, 20, 120)

        self.spectrum = [
            "                                                     ",
            "                                                     ",
            " O        OOOO    OOOO   OOOOO     O O  O O XXXXXXXX ",
            " O       O    O  O    O  O    O    O O  O O X XXXXXX ",
            " O       O    O  O    O  O    O             X XXXXXX ",
            " O       O    O  OOOOOO  O    O             X XXXXXX ",
            " O       O    O  O    O  O    O             X XXXXXX ",
            " OOOOOO   OOOO   O    O  OOOOO              X XXXXXX ",
            "                                            X      X ",
            "                                            XXXXXXXX ",
            "                                                     ",
        ]
        self.fg_spectrum = (0, 0, 0)
        self.bg_spectrum = (180, 150, 150)

        self.bbc_micro = [
            "                                                     ",
            "                                                     ",
            " OOOOO    OO    OOOO   OOO    OOOO      O            ",
            " O    O  O  O  O    O   O    O    O      O           ",
            " O    O O    O O        O    O            O          ",
            " OOOOO  O    O  OOOO    O    O             O         ",
            " O    O OOOOOO      O   O    O            O          ",
            " O    O O    O O    O   O    O    O      O           ",
            " OOOOO  O    O  OOOO   OOO    OOOO      O            ",
            "                                             XXXXXXX ",
            "                                                     ",
        ]
        self.fg_bbc = (255, 255, 255)
        self.bg_bbc = (0, 0, 0)

        self.prompts = [
            (self.c64, self.fg_c64, self.bg_c64),
            (self.spectrum, self.fg_spectrum, self.bg_spectrum),
            (self.bbc_micro, self.fg_bbc, self.bg_bbc),
        ]

    def init(self):
        pass

    @micropython.native
    def draw(self):
        time_ms = time.ticks_ms()
        idx = (time_ms // 3000) % 3
        image, fg, bg = self.prompts[idx]

        graphics = self.graphics
        fg_pen = graphics.create_pen(fg[0], fg[1], fg[2])
        bg_pen = graphics.create_pen(bg[0], bg[1], bg[2])
        blink = (time_ms // 300) % 2

        for y in range(len(image)):
            row = image[y]
            for x in range(len(row)):
                pixel = row[x]
                if pixel == 'O':
                    graphics.set_pen(fg_pen)
                elif pixel == 'X' and blink:
                    graphics.set_pen(fg_pen)
                else:
                    graphics.set_pen(bg_pen)
                graphics.pixel(x, y)
