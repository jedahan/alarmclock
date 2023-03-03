import random
import sys
import time
from math import floor

from enum import Enum, IntEnum

Color = IntEnum("Color", ["OFF", "GREEN", "RED", "YELLOW"], start=0)


class Terminal(Enum):
    OFF = "\033[90m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    END = "\033[0m"


from adafruit_framebuf import FrameBuffer, GS2_HMSB
from adafruit_platformdetect import Detector
detector = Detector()

RASPBERRY_PI = detector.board.any_raspberry_pi
MATRIX_WIDTH = 8

if RASPBERRY_PI:
    import board
    import busio
    from adafruit_ht16k33 import matrix


def makeFramebuffer(width=32, height=8, colors=2):
    """
    The framebuffer can be thought of as a virtual image, where
    we can map each *nibble* to one of the pixels in the display.

    Although we can manipulate the panels directly, its easier
    to build an image, then draw the entire image to the display.
    """
    bits_per_byte = 8
    buffer = bytearray(width * height * colors // bits_per_byte)

    return FrameBuffer(buffer, width, height, GS2_HMSB)


def draw(panel, framebuffer, chosen_animation):
    """
    draw puts an image onto pixels

    This is a 'blit' function - it takes the bits in a buffer, and
    for each bit that is set to 1, sets the display to RED, ORANGE, or YELLOW
    """
    print(chr(27) + "[2J")  # clear the terminal
    print(chosen_animation)
    log(framebuffer)

    if not RASPBERRY_PI:
        return

    panel.fill(Color.OFF.value)

    width, height = framebuffer.width, framebuffer.height

    for x in range(width):
        for y in range(height):
            color = framebuffer.pixel(x, y)
            panel[x, y] = color


def fill(panel, framebuffer):
    """
    fill all pixels
    """
    color = random.choice(list(Color))
    framebuffer.fill(color.value)
    yield framebuffer


def corners(panel, framebuffer):
    """
    draw the bounding corners of each panel
    """

    width = MATRIX_WIDTH - 1

    for number in list(range(4)):
        x = number * MATRIX_WIDTH
        framebuffer.pixel(x=x, y=0, color=2)
        framebuffer.pixel(x=x, y=width, color=3)
        framebuffer.pixel(x=x+width, y=0, color=3)
        framebuffer.pixel(x=x+width, y=width, color=2)

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
        color = random.choice(list(Color)).value
        x = random.randint(0, framebuffer.width - 1)
        y = random.randint(0, framebuffer.height - 1)

        framebuffer.pixel(x, y, color)
        time.sleep(random.random())
        yield framebuffer


# ascii printer for very small framebuffers!
def log(framebuffer):
    buf = framebuffer.buf
    end = Terminal.END.value
    print("┏", end="")
    print("━" * (framebuffer.width), end="")
    print("┓")
    for y in range(framebuffer.height):
        print("┃", end="")
        for x in range(framebuffer.width):
            pixel = framebuffer.pixel(x, y)
            color = list(Terminal)[pixel].value
            print(f"{color}█{end}", end="")
        print("┃")
    print("┗", end="")
    print("━" * (framebuffer.width), end="")
    print("┛")


def run():
    """
    Make sure to follow the adafruit raspberry pi guide on enabling i2c

    On non-pi systems, will visualize in the terminal

        python3 blinkenlights.py [animation] [address address address...]

    Where animation is one of blinkenlights, numbers, corners, outline, or fill

    If the panels are in the incorrect order, pass the hex-encoded addresses like so:

        python3 blinkenlights.py 0x70 0x74 0x71 0x72
    """

    #if len(sys.argv) > 1:
    #    animation = sys.argv[1:].first(lambda arg: "x" not in arg)

    if RASPBERRY_PI:
        bus = board.I2C()
        addresses = (
            bus.scan()
            if len(sys.argv) < 2
            else [int(address, 16) for address in sys.argv]
        )
        print(f"{addresses=}")

        panel = matrix.Matrix8x8x2(bus, addresses)

        # Clear the screen and turn the brightness down a bit
        panel.fill(Color.OFF)
        panel.brightness = 0.5

    else:
        panel = None

    animations = {
            "blinkenlights": blinkenlights,
            "numbers": numbers,
            "corners": corners,
            "outline": outline,
            "fill": fill
    }

    random_animation = random.choice(list(animations.keys()))

    chosen_animation = sys.argv[1] if len(sys.argv) == 2 else random_animation

    animation = animations[chosen_animation]

    framebuffer = makeFramebuffer()

    for frame in animation(panel, framebuffer):
        draw(panel, frame, chosen_animation)


if __name__ == "__main__":
    run()
