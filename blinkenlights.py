import sys
import time
from math import floor

RASPBERRY_PI = False

if RASPBERRY_PI:
    import board
    import busio
    from adafruit_ht16k33 import matrix

from adafruit_framebuf import FrameBuffer, MVLSB

from enum import IntEnum

Color = IntEnum("Color", ["OFF", "GREEN", "RED", "YELLOW"])


def makeFramebuffer(width=32, height=8):
    """
    The framebuffer can be thought of as a virtual image, where
    we can map each *bit* to one of the pixels in the display.

    Although we can manipulate the panels directly, its easier
    to build an image, then draw the entire image to the display.
    """
    buffer = bytearray(width)  # 1 bytes tall x 8 wide x 4 panels = 32 bytes
    return FrameBuffer(buffer, width, height, MVLSB)


def draw(panels, framebuffer, color=Color.RED):
    """
    draw expects the panels to be ordered from left to right

    This is a 'blit' function - it takes the bits in a buffer, and
    for each bit that is set to 1, sets the display to RED, ORANGE, or YELLOW
    """
    for panel in panels:
        panel.fill(Color.OFF)

    width, height = framebuffer.width, framebuffer.height

    for x in range(width):
        panel = panels[floor(x / width * len(panels))]
        for y in range(height):
            if framebuffer.pixel(x, y):
                panel[width - x, y + 1] = color


def numbers(panels: list[any], framebuffer):
    """
    For each panel in panels, write the panel number

    If there are 4 panels, you should see 1 2 3 4

    If the numbers are out of order, change the order in the addresses array
    """
    framebuffer.fill(0)
    panel_width = int(framebuffer.width / len(panels))

    for panel, number in enumerate(panels):
        x = (number - 1) * panel_width
        framebuffer.text(f"{number}", x, y=0, color=1)

    display(framebuffer)

    if RASPBERRY_PI:
        draw(panels, framebuffer, color=random.choice(Color))


def blinkenlights(panels):
    """testing app - random colors on all the pixels"""
    while True:
        panel = random.choice(panels)
        color = random.choice(Color)
        x = random.randint(0, 7)
        y = random.randint(0, 7)

        panel[x, y] = color
        time.sleep(random.random())

# ascii printer for very small framebuffers!
def display(framebuffer):
    print("." * (framebuffer.width + 2))
    for y in range(framebuffer.height):
        print(".", end="")
        for x in range(framebuffer.width):
            if framebuffer.pixel(x, y):
                print("*", end="")
            else:
                print(" ", end="")
        print(".")
    print("." * (framebuffer.width + 2))


def run():
    """
    Make sure to follow the adafruit raspberry pi guide on enabling i2c

    If the panels are in the incorrect order, pass the hex-encoded addresses like so:

        python3 blinkenlights.py 0x70 0x74 0x71 0x72
    """

    if RASPBERRY_PI:
        bus = board.I2C()
        addresses = bus.scan() if len(sys.argv) < 2 else [ int(address, 16) for address in sys.argv ]
        info(f"{addresses=}")

        panels = [matrix.Matrix8x8x2(bus) for address in addresses]

        # Clear the screen and turn the brightness down a bit
        for panel in panels:
            panel.fill(Color.OFF)
            panel.brightness = 0.5

    else:
        panels = [ 1, 2, 3, 4]

    # TODO: Add signal handling to switch between 'apps'
    # app = random.choice([blinkenlight, numbers])
    framebuffer = makeFramebuffer()
    numbers(panels, framebuffer)
    #app(panels, framebuffer)


if __name__ == "__main__":
    run()
