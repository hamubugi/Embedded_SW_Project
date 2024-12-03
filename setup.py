# hardware_setup.py

import board
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# Grid Parameters
GRID_SIZE = 4  # 4x4 grid for 2048
TILE_SIZE = 55  # Size of each tile in pixels
TILE_THICKNESS = 4  # Thickness of grid lines in pixels
GRID_COLOR = (255, 255, 255)  # White grid lines

# Calculate total grid width and height
TOTAL_GRID_SIZE = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * TILE_THICKNESS

# Offsets to center the grid on the display
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240
offset_x = (DISPLAY_WIDTH - TOTAL_GRID_SIZE) // 2
offset_y = (DISPLAY_HEIGHT - TOTAL_GRID_SIZE) // 2

# Display setup
def init_display():
    cs_pin = DigitalInOut(board.CE0)
    dc_pin = DigitalInOut(board.D25)
    reset_pin = DigitalInOut(board.D24)
    BAUDRATE = 24000000

    spi = board.SPI()
    disp = st7789.ST7789(
        spi,
        height=DISPLAY_HEIGHT,
        width=DISPLAY_WIDTH,
        y_offset=80,
        rotation=180,  # Adjust based on your display orientation
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
    )
    return disp

# Define a font
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 24

try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except IOError:
    # Fallback to default font if the specified font is not found
    font = ImageFont.load_default()

# Backlight setup
def init_backlight():
    backlight = DigitalInOut(board.D26)
    backlight.switch_to_output()
    backlight.value = True
    return backlight

# Joystick input pins setup
def init_buttons():
    button_A = DigitalInOut(board.D5)
    button_A.direction = Direction.INPUT
    button_A.pull = Pull.UP

    button_B = DigitalInOut(board.D6)
    button_B.direction = Direction.INPUT
    button_B.pull = Pull.UP

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

    return {
        'A': button_A,
        'B': button_B,
        'left': button_L,
        'right': button_R,
        'up': button_U,
        'down': button_D
    }

# Initialize all hardware components and expose them
disp = init_display()
backlight = init_backlight()
buttons = init_buttons()

# Create blank image for drawing
width = disp.width  # Should be 240
height = disp.height  # Should be 240
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)
