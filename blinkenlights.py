import random
import sys
import time
from math import floor

from enum import Enum, IntEnum

Color = IntEnum("Color", ["OFF", "GREEN", "RED", "YELLOW"])


class Terminal(Enum):
    OFF = "\033[90m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    END = "\033[0m"


from adafruit_framebuf import FrameBuffer, BICOLOR

RASPBERRY_PI = False
MATRIX_WIDTH = 8

if RASPBERRY_PI:
    import board
    import busio
    from adafruit_ht16k33 import matrix


def unpack(color):
    hi = (color >> 1) & 0x01
    lo = color & 0x01
    print(f"{hi=}, {lo=}")


def makeFramebuffer(width=32, height=8):
    """
    The framebuffer can be thought of as a virtual image, where
    we can map each *bit* to one of the pixels in the display.

    Although we can manipulate the panels directly, its easier
    to build an image, then draw the entire image to the display.
    """
    buffer = bytearray(width)  # 1 bytes tall x 8 wide x 4 panels = 32 bytes
    return FrameBuffer(buffer, width, height, BICOLOR)


def draw(panel, framebuffer):
    """
    draw puts an image onto pixels

    This is a 'blit' function - it takes the bits in a buffer, and
    for each bit that is set to 1, sets the display to RED, ORANGE, or YELLOW
    """
    log(framebuffer)

    if not RASPBERRY_PI:
        return

    panel.fill(Color.OFF)

    width, height = framebuffer.width, framebuffer.height

    for x in range(width):
        for y in range(height):
            color = framebuffer.pixel(x, y)
            panel[x, y] = color


def corners(panel, framebuffer):
    """
    draw the bounding corners of each panel
    """
    framebuffer.fill(Color.OFF)
    panels = int(framebuffer.width / MATRIX_WIDTH)

    for number in range(panels):
        offset = number * MATRIX_WIDTH
        first = offset + 0
        last = offset + MATRIX_WIDTH - 1
        framebuffer.pixel(x=first, y=first, color=True)
        framebuffer.pixel(x=first, y=last, color=True)
        framebuffer.pixel(x=last, y=first, color=True)
        framebuffer.pixel(x=last, y=last, color=True)

    yield framebuffer


def outline(panel, framebuffer):
    """
    draw an outline
    """
    framebuffer.rect(0, 0, framebuffer.width, framebuffer.height, color=True)

    yield framebuffer


def numbers(panel, framebuffer):
    """
    For each panel in panels, write the panel number

    If there are 4 panels, you should see 1 2 3 4

    If the numbers are out of order, change the order in the addresses array
    """
    panels = int(framebuffer.width / MATRIX_WIDTH)

    for number in range(panels):
        offset = number * MATRIX_WIDTH
        framebuffer.text(f"{number}", x=offset, y=1, color=True)

    yield framebuffer


def blinkenlights(panel, framebuffer):
    """random colors on all the pixels"""

    while True:
        color = random.choice(list(Color))
        x = random.randint(0, framebuffer.width - 1)
        y = random.randint(0, framebuffer.height - 1)

        framebuffer.pixel(x, y, color)
        time.sleep(random.random())
        yield framebuffer


# ascii printer for very small framebuffers!
def log(framebuffer):
    end = Terminal.END.value
    print(chr(27) + "[2J")  # clears the terminal
    print("┏", end="")
    print("━" * (framebuffer.width), end="")
    print("┓")
    for y in range(framebuffer.height):
        print("┃", end="")
        for x in range(framebuffer.width):
            pixel = framebuffer.pixel(x, y)
            print(f"{pixel=}")
            color = list(Terminal)[pixel].value
            print(f"{color}█{end}", end="")
        print("┃")
    print("┗", end="")
    print("━" * (framebuffer.width), end="")
    print("┛")


def run():
    """
    Make sure to follow the adafruit raspberry pi guide on enabling i2c

    If the panels are in the incorrect order, pass the hex-encoded addresses like so:

        python3 blinkenlights.py 0x70 0x74 0x71 0x72
    """

    if RASPBERRY_PI:
        bus = board.I2C()
        addresses = (
            bus.scan()
            if len(sys.argv) < 2
            else [int(address, 16) for address in sys.argv]
        )
        info(f"{addresses=}")

        panel = matrix.Matrix8x8x2(bus, addresses)

        # Clear the screen and turn the brightness down a bit
        panel.fill(Color.OFF)
        panel.brightness = 0.5

    else:
        panel = None

    animation = random.choice([blinkenlights, numbers, corners, outline])
    framebuffer = makeFramebuffer()

    for frame in animation(panel, framebuffer):
        draw(panel, frame)


if __name__ == "__main__":
    run()
