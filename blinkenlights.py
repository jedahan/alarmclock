import time
import board
import busio
from adafruit_ht16k33 import matrix

from enum import IntEnum
Color = IntEnum('Color', ['OFF', 'GREEN', 'RED', 'YELLOW'])

def drawNumber(panel, number):
    return

def displayPanelNumbers(panels: list[any]):
    for panel in panels:
        panel.fill(COLORS.OFF)
        panel.brightness = 0.5

    for panel, number in enumerate(panels):
        drawNumber(panel, number)

# Each panel can share an i2c bus, and be individually addressed
# After following the i2c guide on raspberrypi.org docs,
# These addresses were found by running i2cdetect -l
i2c = busio.I2C(board.SCL, board.SDA)

# TODO: Order these addresses from left to right on the physical display
addresses = [ 0x70, 0x71, 0x72, 0x74 ]
panels = [matrix.Matrix8x8x2(address) for address in addresses]

# Set a random pixel to a random color or off
def blinkenlight():
    panel = random.choice(panels)
    color = random.choice(COLORS)
    x = random.randint(0, 7)
    y = random.randint(0, 7)

    panel[x, y] = color

while True:
    blinkenlight()
    time.sleep(random.random())
