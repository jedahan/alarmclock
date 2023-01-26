import time
import board
import busio
from adafruit_ht16k33 import matrix
from adafruit_framebuf import FrameBuffer, MVLSB
from math import floor

from enum import IntEnum

Color = IntEnum("Color", ["OFF", "GREEN", "RED", "YELLOW"])


def makeBuffers(width=32, height=8):
    """
    The framebuffer can be thought of as a virtual image, where
    we can map each *bit* to one of the pixels in the display.

    Although we can manipulate the panels directly, its easier
    to build an image, then draw the entire image to the display.
    """
    width = 32
    height = 8
    buffer = bytearray(width)  # 1 bytes tall x 8 wide x 4 panels = 32 bytes
    framebuffer = FrameBuffer(buffer, width, height, MVLSB)
    return framebuffer, buffer


def draw(panels, buffer, color=Color.RED):
    """
    note that this takes *the underlying buffer*, not the framebuffer

    draw expects the panels to be ordered from left to right

    this is a 'blit' function - it takes the bits in a buffer, and
    for each bit that is set to 1, sets the display to RED, ORANGE, or YELLOW
    """
    width = len(buffer)

    for panel in panels:
        panel.fill(Color.OFF)

    for x in range(width):
        bite = buffer[x]
        panel = panels[floor(x / width * len(panels))]
        for y in range(height):
            bit = 1 << y & bite
            if bit:
                panel[width - x, y + 1] = color


def numbers(panels: list[any], framebuffer, buffer):
    """
    For each panel in panels, write the panel number

    If there are 4 panels, you should see 1 2 3 4

    If the numbers are out of order, change the order in the addresses array
    """
    framebuffer.fill(0)
    panel_width = len(framebuffer) / len(panels)

    for panel, number in enumerate(panels):
        x = number * panel_width
        framebuffer.text(f"{number}", x, y=0, color=1)

    draw(panels, buffer, color=random.choice(Color))


def blinkenlights(panels):
    """testing app - random colors on all the pixels"""
    while True:
        panel = random.choice(panels)
        color = random.choice(Color)
        x = random.randint(0, 7)
        y = random.randint(0, 7)

        panel[x, y] = color
        time.sleep(random.random())


def run():
    """
    Apps will be passed the panels, and a framebuffer
    """
    # Each panel can share an i2c bus, and be individually addressed
    # After following the i2c guide on raspberrypi.org docs,
    # These addresses were found by running i2cdetect -l

    # TODO: Order these addresses from left to right on the physical display
    addresses = [0x70, 0x71, 0x72, 0x74]
    bus = board.I2C()
    panels = [matrix.Matrix8x8x2(bus) for address in addresses]

    # Clear the screen and turn the brightness down a bit
    for panel in panels:
        panel.fill(Color.OFF)
        panel.brightness = 0.5

    # TODO: Add signal handling to switch between 'apps'
    app = random.choice([blinkenlight, numbers])
    framebuffer, buffer = makeBuffers()
    app(panels, framebuffer, buffer)


if __name__ == "__main__":
    run()
