# main.py

import time
from PIL import Image, ImageDraw, ImageFont
from modules.setup import setup_hardware
import copy

# Setup the hardware (display, backlight, buttons)
hardware = setup_hardware()
disp = hardware["display"]
backlight = hardware["backlight"]
buttons = hardware["buttons"]

# 240x240 blank canvas
width = disp.width
height = disp.height
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Define grid parameters
grid_size = 4  # 4x4 grid
tile_thickness = 4  # Thickness of the grid lines
tile_size = (
    width - (grid_size + 1) * tile_thickness
) // grid_size  # Size of each tile including space for lines

# Initialize block positions
blocks = [[0 for _ in range(grid_size)] for _ in range(grid_size)]  # Empty grid
blocks[3][3] = 2  # Start block at (3,0)

# Adjusted directions due to display rotation
directions = {
    "left": (0, -1),   # Left moves left in array indices
    "right": (0, 1),   # Right moves right in array indices
    "up": (1, 0),     # Up moves up in array indices
    "down": (-1, 0),    # Down moves down in array indices
}

# Animation queue to store intermediate states for smooth movement
animation_queue = []

# Function to draw the grid and blocks
def draw_grid():
    draw.rectangle(
        (0, 0, width, height), outline=0, fill=(0, 0, 0)
    )  # Clear background

    # Draw grid lines
    for i in range(grid_size + 1):
        # Vertical lines
        x = i * (tile_size + tile_thickness)
        draw.rectangle(
            [x, 0, x + tile_thickness, height], fill=(255, 255, 255)
        )

        # Horizontal lines
        y = i * (tile_size + tile_thickness)
        draw.rectangle(
            [0, y, width, y + tile_thickness], fill=(255, 255, 255)
        )

    # Draw the blocks
    for row in range(grid_size):
        for col in range(grid_size):
            if blocks[row][col] != 0:
                # Adjust coordinates for rotation
                display_row = row  # Keep row index as is
                display_col = grid_size - 1 - col  # Invert column index

                x_pos = display_col * (tile_size + tile_thickness) + tile_thickness
                y_pos = display_row * (tile_size + tile_thickness) + tile_thickness

                # Draw a block
                block_color = (255, 255, 0)  # Yellow block
                draw.rectangle(
                    [x_pos, y_pos, x_pos + tile_size, y_pos + tile_size],
                    fill=block_color
                )

                # Draw block value in the center
                fnt = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
                )
                text = str(blocks[row][col])

                # Calculate text bounding box to center it
                text_bbox = draw.textbbox((0, 0), text, font=fnt)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                text_x = x_pos + (tile_size - text_width) // 2
                text_y = y_pos + (tile_size - text_height) // 2

                # Draw the text in black
                draw.text(
                    (text_x, text_y), text, font=fnt, fill=(0, 0, 0)
                )  # Black text

    disp.image(image)

# Function to slide blocks in the given direction with animation
def slide_blocks(direction):
    global blocks, animation_queue
    row_offset, col_offset = directions[direction]
    moved = False

    # Iterate multiple times to handle step-by-step sliding
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
                    and blocks[next_row][next_col] == 0
                ):
                    # Move block one step in the direction
                    new_blocks[next_row][next_col] = blocks[row][col]
                    new_blocks[row][col] = 0
                    moved = True
                    any_block_moved = True
        if any_block_moved:
            blocks = new_blocks
            animation_queue.append(copy.deepcopy(blocks))
        else:
            break  # Stop if no more moves possible

    return moved

# Main game loop
def main():
    while True:
        direction_pressed = None

        # Check Joystick input (adjusted for rotation)
        if not buttons["L"].value:  # Left button pressed
            direction_pressed = "right"  # Due to rotation, left button moves right in array
        elif not buttons["R"].value:  # Right button pressed
            direction_pressed = "left"
        elif not buttons["U"].value:  # Up button pressed
            direction_pressed = "down"
        elif not buttons["D"].value:  # Down button pressed
            direction_pressed = "up"

        # Slide blocks if a direction button was pressed and no ongoing animation
        if direction_pressed and not animation_queue:
            if slide_blocks(direction_pressed):
                pass  # Additional logic can be added here

        # Handle animation
        if animation_queue:
            blocks = animation_queue.pop(0)
            draw_grid()
            time.sleep(0.1)  # Run the animation.
        else:
            draw_grid()  # Grid update.

        time.sleep(0.01)  # Gives a short delay to avoid multi-input

if __name__ == "__main__":
    main()
