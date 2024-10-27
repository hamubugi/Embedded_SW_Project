# my_module/hardware_setup.py

import time
from adafruit_rgb_display import st7789
from digitalio import DigitalInOut, Direction, Pull
import board

# Display and button setup function
def setup_hardware():
    # Setup display pins
    cs_pin = DigitalInOut(board.CE0)
    dc_pin = DigitalInOut(board.D25)
    reset_pin = DigitalInOut(board.D24)
    BAUDRATE = 24000000

    # Setup SPI for display
    spi = board.SPI()
    disp = st7789.ST7789(
        spi,
        height=240,
        y_offset=80,
        rotation=180,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
    )

    # Turn on the Backlight
    backlight = DigitalInOut(board.D26)
    backlight.switch_to_output()
    backlight.value = True

    # Setup buttons
    button_A = DigitalInOut(board.D5)
    button_A.direction = Direction.INPUT

    button_B = DigitalInOut(board.D6)
    button_B.direction = Direction.INPUT

    button_L = DigitalInOut(board.D27)
    button_L.direction = Direction.INPUT
    button_L.pull = Pull.UP

    button_R = DigitalInOut(board.D23)
    button_R.direction = Direction.INPUT
    button_R.pull = Pull.UP

    button_U = DigitalInOut(board.D17)
    button_U.direction = Direction.INPUT
    button_U.pull = Pull.UP

    button_D = DigitalInOut(board.D22)
    button_D.direction = Direction.INPUT
    button_D.pull = Pull.UP

    # Return display, backlight, and buttons in a dictionary
    return {
        "display": disp,
        "backlight": backlight,
        "buttons": {
            "A": button_A,
            "B": button_B,
            "L": button_L,
            "R": button_R,
            "U": button_U,
            "D": button_D
        }
    }
