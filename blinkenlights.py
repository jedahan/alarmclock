import random
import sys
import time
from math import floor
import RPi.GPIO as GPIO

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
    import digitalio
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


def draw(panels, framebuffer):
    """
    draw puts an image onto pixels

    This is a 'blit' function - it takes the bits in a buffer, and
    for each bit that is set to 1, sets the display to RED, ORANGE, or YELLOW
    """
    #print(chr(27) + "[2J")  # clear the terminal
    #log(framebuffer)

    if not RASPBERRY_PI:
        return

    width, height = framebuffer.width, framebuffer.height
    panel_width = int(width / len(panels))

    for y in range(framebuffer.height):
        for x in range(framebuffer.width):
            pixel = framebuffer.pixel(x, y)
            color = list(Color)[pixel].value
            panel_number = floor(x / width * len(panels))
            panel = panels[panel_number]
            physical_x = panel_width - int(x % panel_width) - 1
            panel.pixel(physical_x, y, color)

    for panel in panels:
        panel.show()


def fill(panels, framebuffer):
    """ fill all pixels """
    color = random.choice(list(Color))
    framebuffer.fill(color.value)
    yield framebuffer


def corners(panels, framebuffer):
    """ draw the bounding corners of each panel """

    width = MATRIX_WIDTH - 1

    for number in list(range(4)):
        x = number * MATRIX_WIDTH
        framebuffer.pixel(x=x, y=0, color=2)
        framebuffer.pixel(x=x, y=width, color=3)
        framebuffer.pixel(x=x+width, y=0, color=3)
        framebuffer.pixel(x=x+width, y=width, color=2)

    yield framebuffer


def outline(panels, framebuffer):
    """ draw an outline of the entire display """
    framebuffer.rect(0, 0, framebuffer.width, framebuffer.height, color=True)

    yield framebuffer


def numbers(panels, framebuffer):
    """
    For each panel in panels, write the panel number

    If there are 4 panels, you should see 0 1 2 3

    If the numbers are out of order, change the order in the addresses array
    """
    for number in range(len(panels)):
        offset = number * MATRIX_WIDTH
        framebuffer.text(f"{number}", x=offset, y=1, color=True)

    yield framebuffer


def blinkenlights(panels, framebuffer):
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

    panels = []

    framebuffer = makeFramebuffer()

    animations = [
      blinkenlights,
      numbers,
      corners,
      outline,
      fill
    ]

    animation_index = random.randint(0, len(animations)-1)

    if RASPBERRY_PI:
        bus = board.I2C()
        addresses = (
            bus.scan()
            if len(sys.argv) < 2
            else [int(address, 16) for address in sys.argv[1:]]
        )

        panels = [matrix.Matrix8x8x2(bus, address, auto_write=False) for address in addresses]

        for index, panel in enumerate(panels):
            panel.fill(index or 1)
            print(f"{panel.i2c_device[0].device_address}")
            panel.brightness = 0.5

    print(f"{animation_index=}")
    animation = animations[animation_index](panels, framebuffer)

    def increment_animation(channel):
        nonlocal animation_index
        nonlocal animation
        nonlocal framebuffer
        for panel in panels:
            panel.fill(Color.OFF.value)
        animation_index = (animation_index + 1) % len(animations)
        animation = animations[animation_index](panel, framebuffer)
        framebuffer = makeFramebuffer()

    channel = 18
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(channel, GPIO.RISING, callback=increment_animation)

    while True:
        current_animation_index = animation_index

        for frame in animation:
            if animation_index != current_animation_index:
                break
            draw(panels, frame)

if __name__ == "__main__":
    run()
