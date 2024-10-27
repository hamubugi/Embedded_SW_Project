import time
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from digitalio import DigitalInOut, Direction, Pull
import board
import random
import copy

# Set up the display
cs_pin = DigitalInOut(board.CE0)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)
BAUDRATE = 24000000

spi = board.SPI()
disp = st7789.ST7789(
    spi,
    height=240,
    y_offset=80,
    rotation=180,  # Display is rotated by 180 degrees
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# Backlight
backlight = DigitalInOut(board.D26)
backlight.switch_to_output()
backlight.value = True

# Input setup (buttons)
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

# Create blank image for drawing
width = disp.width
height = disp.height
image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

# Define grid parameters
grid_size = 4  # 4x4 grid
tile_thickness = 4  # Thickness of the grid lines
tile_size = (width - (grid_size + 1) * tile_thickness) // grid_size  # Size of each tile including space for lines

# Initialize block positions
blocks = [[0 for _ in range(grid_size)] for _ in range(grid_size)]  # Empty grid
blocks[3][3] = 2  # Start block at (3,3) for testing

# Initialize animation queue
animation_queue = []

# Controls (directions)
directions = {
    "left": (0, -1),
    "right": (0, 1),
    "up": (1, 0),
    "down": (-1, 0),
}

# Function to spawn a new block at a random empty position
def spawn_new_block():
    empty_positions = [(row, col) for row in range(grid_size) for col in range(grid_size) if blocks[row][col] == 0]
    if empty_positions:  # If there are empty positions available
        row, col = random.choice(empty_positions)
        new_value = random.choice([2, 4])
        blocks[row][col] = new_value
        print(f"New block spawned at ({row}, {col}) with value {new_value}")  # Debug print
        draw_grid()  # Immediately draw grid after new block spawns
    else:
        print("No empty positions to spawn a new block.")  # Debug print

# Function to draw the grid and blocks (all blocks green for debugging)
def draw_grid():
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))  # Clear background

    # Draw grid lines
    for i in range(grid_size + 1):
        # Vertical lines
        x = i * (tile_size + tile_thickness)
        draw.rectangle([x, 0, x + tile_thickness, height], fill=(255, 255, 255))

        # Horizontal lines
        y = i * (tile_size + tile_thickness)
        draw.rectangle([0, y, width, y + tile_thickness], fill=(255, 255, 255))

    # Draw the blocks
    for row in range(grid_size):
        for col in range(grid_size):
            if blocks[row][col] != 0:
                # Adjust coordinates for rotation
                display_row = row  # Keep row index as is
                display_col = grid_size - 1 - col  # Invert column index

                x_pos = display_col * (tile_size + tile_thickness) + tile_thickness
                y_pos = display_row * (tile_size + tile_thickness) + tile_thickness

                block_color = (0, 255, 0)  # Green color for all blocks (for debugging)

                # Draw the block
                draw.rectangle([x_pos, y_pos, x_pos + tile_size, y_pos + tile_size], fill=block_color)

                # Draw block value in the center
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                text = str(blocks[row][col])

                # Calculate text bounding box to center it
                text_bbox = draw.textbbox((0, 0), text, font=fnt)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                text_x = x_pos + (tile_size - text_width) // 2
                text_y = y_pos + (tile_size - text_height) // 2

                # Draw the text in black
                draw.text((text_x, text_y), text, font=fnt, fill=(0, 0, 0))  # Black text

    disp.image(image)

# Modified slide_blocks function to include merging logic
def slide_blocks(direction):
    global blocks, animation_queue
    row_offset, col_offset = directions[direction]
    moved = False
    merged = [[False for _ in range(grid_size)] for _ in range(grid_size)]  # Track if a block has merged

    for step in range(grid_size - 1):
        any_block_moved = False
        new_blocks = copy.deepcopy(blocks)
        for row in range(grid_size):
            for col in range(grid_size):
                next_row = row + row_offset
                next_col = col + col_offset
                if (
                    0 <= next_row < grid_size
                    and 0 <= next_col < grid_size
                    and blocks[row][col] != 0
                ):
                    if blocks[next_row][next_col] == 0:  # If the next spot is empty, move the block
                        new_blocks[next_row][next_col] = blocks[row][col]
                        new_blocks[row][col] = 0
                        moved = True
                        any_block_moved = True
                    elif blocks[next_row][next_col] == blocks[row][col] and not merged[next_row][next_col]:  # Merge if values are equal and not already merged
                        new_blocks[next_row][next_col] = blocks[row][col] * 2  # Merge into a 2n block
                        new_blocks[row][col] = 0
                        merged[next_row][next_col] = True  # Mark as merged
                        moved = True
                        any_block_moved = True
        if any_block_moved:
            blocks = new_blocks
            animation_queue.append(copy.deepcopy(blocks))
        else:
            break  # Stop if no more moves possible

    if moved:
        print("Blocks moved")  # Debug print
        spawn_new_block()  # Spawn a new block after a successful move

    return moved

# Main game loop
while True:
    direction_pressed = None

    # Check Joystick input (adjusted for rotation)
    if not button_L.value:  # Left button pressed
        direction_pressed = "right"  # Due to rotation, left button moves right in array
    elif not button_R.value:  # Right button pressed
        direction_pressed = "left"
    elif not button_U.value:  # Up button pressed
        direction_pressed = "down"
    elif not button_D.value:  # Down button pressed
        direction_pressed = "up"

    # Slide blocks if a direction button was pressed and no ongoing animation
    if direction_pressed and not animation_queue:
        if slide_blocks(direction_pressed):
            print("Grid updated after move")  # Debug print
            draw_grid()  # Redraw grid only when blocks are moved or spawned

    # Handle animation
    if animation_queue:
        blocks = animation_queue.pop(0)
        draw_grid()
        print("Animation frame updated")  # Debug print
        time.sleep(0.1)  # Run the animation.

    time.sleep(0.01)  # Small delay to avoid multi-input
