# main.py

import time
import copy  # For deep copy
from PIL import ImageFont
import setup  # Import the setup module we just created

# Import hardware components from setup.py
disp = setup.disp
draw = setup.draw
buttons = setup.buttons
image = setup.image

# -----------------------------
# Game Configuration and Setup
# -----------------------------

# Grid parameters
GRID_SIZE = 4  # 4x4 grid
TILE_THICKNESS = 4  # Thickness of the grid lines
TILE_SIZE = (
    disp.width - (GRID_SIZE + 1) * TILE_THICKNESS
) // GRID_SIZE  # Size of each tile including space for lines

# Initialize block positions
blocks = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # Empty grid
blocks[3][3] = 2  # Start block at position (3,3)

# Adjusted directions due to display rotation
DIRECTIONS = {
    "left": (0, -1),   # Move left in array indices
    "right": (0, 1),   # Move right in array indices
    "up": (1, 0),      # Move up in array indices
    "down": (-1, 0),   # Move down in array indices
}

# Animation queue to store intermediate states for smooth movement
animation_queue = []

# Font setup
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SIZE = 24
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# -----------------------------
# Function Definitions
# -----------------------------

def draw_grid():
    """
    Draws the grid and the blocks on the display.
    """
    # Clear the background
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=(0, 0, 0))

    # Draw grid lines
    for i in range(GRID_SIZE + 1):
        # Vertical lines
        x = i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([x, 0, x + TILE_THICKNESS, disp.height], fill=(255, 255, 255))

        # Horizontal lines
        y = i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([0, y, disp.width, y + TILE_THICKNESS], fill=(255, 255, 255))

    # Draw the blocks
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if blocks[row][col] != 0:
                # Adjust coordinates for rotation
                display_row = row  # Row index remains the same
                display_col = GRID_SIZE - 1 - col  # Invert column index due to rotation

                x_pos = display_col * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                y_pos = display_row * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS

                # Draw the block rectangle
                block_color = (255, 255, 0)  # Yellow block
                draw.rectangle(
                    [x_pos, y_pos, x_pos + TILE_SIZE, y_pos + TILE_SIZE],
                    fill=block_color
                )

                # Draw the block value centered within the block
                text = str(blocks[row][col])

                # Calculate text size and position
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                text_x = x_pos + (TILE_SIZE - text_width) // 2
                text_y = y_pos + (TILE_SIZE - text_height) // 2

                # Draw the text
                draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    # Update the display with the drawn image
    disp.image(image)

def slide_blocks(direction):
    """
    Slides the blocks in the given direction with animation.
    Args:
        direction (str): The direction in which to slide the blocks ('left', 'right', 'up', 'down').
    Returns:
        bool: True if any block moved, False otherwise.
    """
    global blocks, animation_queue
    row_offset, col_offset = DIRECTIONS[direction]
    moved = False

    # Iterate multiple times to handle step-by-step sliding
    for _ in range(GRID_SIZE - 1):
        any_block_moved = False
        new_blocks = copy.deepcopy(blocks)
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                next_row = row + row_offset
                next_col = col + col_offset
                if (
                    0 <= next_row < GRID_SIZE
                    and 0 <= next_col < GRID_SIZE
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

def get_direction_pressed():
    """
    Checks the joystick input and returns the corresponding direction.
    Returns:
        str or None: The direction pressed ('left', 'right', 'up', 'down'), or None if no direction is pressed.
    """
    if not buttons['left'].value:  # Left button pressed
        return "right"  # Due to rotation, left button moves right in array
    elif not buttons['right'].value:  # Right button pressed
        return "left"
    elif not buttons['up'].value:  # Up button pressed
        return "down"
    elif not buttons['down'].value:  # Down button pressed
        return "up"
    else:
        return None

# -----------------------------
# Main Game Loop
# -----------------------------

def main():
    """
    The main game loop.
    """
    while True:
        # Check for joystick input
        direction_pressed = get_direction_pressed()

        # Slide blocks if a direction button was pressed and no ongoing animation
        if direction_pressed and not animation_queue:
            if slide_blocks(direction_pressed):
                pass  # Additional logic can be added here in the future

        # Handle animation
        if animation_queue:
            blocks[:] = animation_queue.pop(0)
            draw_grid()
            time.sleep(0.1)  # Control animation speed
        else:
            draw_grid()  # Ensure the grid is redrawn

        time.sleep(0.01)  # Small delay to avoid rapid movement

if __name__ == "__main__":
    main()
