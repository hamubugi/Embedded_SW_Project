# main.py

import time
import copy
import random
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

# Modulo Game Configuration
MODULO_Y = None  # The modulo base
MODULO_N = None  # The N-th number we're looking for
MAX_MODULO_BASE = 20  # Maximum modulo base
MAX_BLOCK_VALUE = 2048  # Maximum block value

# Spawn Mechanics
SPAWN_CHANCE = 1.0  # 100% chance of spawning a new block after each move
MODULO_BLOCK_CHANCE = 0.1  # 10% chance of spawning a modulo block

# Initialize block positions
blocks = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # Empty grid

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
# Modulo Game Mechanics Functions
# -----------------------------

def roll_modulo_parameters():
    global MODULO_Y, MODULO_N
    MODULO_Y = random.randint(5, MAX_MODULO_BASE)
    MODULO_N = random.randint(1, 10)
    print(f"Game Modulo Rules: Find the {MODULO_N}-th number satisfying x ≡ z (mod {MODULO_Y})")
    return MODULO_Y, MODULO_N

def find_nth_modulo_number(x, y, n):
    if y <= 0:
        raise ValueError("Modulo base must be positive")
    z = x % y
    if z == 0:
        z = y
    count = 0
    while True:
        if z % y == x % y:
            count += 1
            if count == n:
                return z
        z += y
        if z > MAX_BLOCK_VALUE:
            break
    return z

def spawn_new_block():
    global blocks
    empty_cells = [
        (row, col)
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
        if blocks[row][col] == 0
    ]
    if not empty_cells:
        return False
    row, col = random.choice(empty_cells)
    if random.random() < MODULO_BLOCK_CHANCE:
        # Modulo block (pink)
        if MODULO_Y:
            # Assign a value that is a multiple of MODULO_Y
            blocks[row][col] = MODULO_Y * random.randint(1, 3)  # Start with small multiples
            print(f"Spawned modulo block at ({row},{col}) with value {blocks[row][col]}")
        else:
            # If MODULO_Y not set, default to 2
            blocks[row][col] = 2
    else:
        # Normal block (yellow)
        blocks[row][col] = 2 if random.random() < 0.9 else 4
    return True

def is_modulo_block(value):
    return MODULO_Y and value % MODULO_Y == 0

def merge_blocks(block1, block2):
    if is_modulo_block(block1) == is_modulo_block(block2):
        if MODULO_Y and MODULO_N:
            return find_nth_modulo_number(block1, MODULO_Y, MODULO_N)
        else:
            return block1 + block2
    return None

# -----------------------------
# Existing Game Functions
# -----------------------------

def draw_grid():
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=(0, 0, 0))
    for i in range(GRID_SIZE + 1):
        x = i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([x, 0, x + TILE_THICKNESS, disp.height], fill=(255, 255, 255))
        y = i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([0, y, disp.width, y + TILE_THICKNESS], fill=(255, 255, 255))
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if blocks[row][col] != 0:
                display_row = row
                display_col = GRID_SIZE - 1 - col
                x_pos = display_col * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                y_pos = display_row * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                if is_modulo_block(blocks[row][col]):
                    block_color = (255, 105, 180)  # Pink
                    print(f"Block at ({row},{col}) with value {blocks[row][col]} is a modulo block.")
                else:
                    block_color = (255, 255, 0)  # Yellow
                draw.rectangle(
                    [x_pos, y_pos, x_pos + TILE_SIZE, y_pos + TILE_SIZE],
                    fill=block_color
                )
                text = str(blocks[row][col])
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x_pos + (TILE_SIZE - text_width) // 2
                text_y = y_pos + (TILE_SIZE - text_height) // 2
                draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))
    disp.image(image)

# The rest of your code remains unchanged...


def slide_blocks(direction):
    global blocks, animation_queue
    """
    Modified slide_blocks to incorporate new merging and block spawning logic
    """
    row_offset, col_offset = DIRECTIONS[direction]
    moved = False

    # Initialize merged positions to prevent multiple merges
    merged_positions = set()

    # Determine traversal order based on direction
    if direction in ["up", "left"]:
        start, end, step = 0, GRID_SIZE, 1
    else:  # "down" or "right"
        start, end, step = GRID_SIZE - 1, -1, -1

    for _ in range(GRID_SIZE):
        any_block_moved = False
        new_blocks = copy.deepcopy(blocks)
        for row in range(start, end, step):
            for col in range(start, end, step):
                current_value = blocks[row][col]
                if current_value == 0:
                    continue
                next_row = row + row_offset
                next_col = col + col_offset
                if 0 <= next_row < GRID_SIZE and 0 <= next_col < GRID_SIZE:
                    next_value = blocks[next_row][next_col]
                    if next_value == 0:
                        # Move block
                        new_blocks[next_row][next_col] = current_value
                        new_blocks[row][col] = 0
                        moved = True
                        any_block_moved = True
                    elif (next_row, next_col) not in merged_positions:
                        merged_value = merge_blocks(current_value, next_value)
                        if merged_value:
                            # Merge blocks
                            new_blocks[next_row][next_col] = merged_value
                            new_blocks[row][col] = 0
                            merged_positions.add((next_row, next_col))
                            moved = True
                            any_block_moved = True
        if any_block_moved:
            blocks = copy.deepcopy(new_blocks)
            animation_queue.append(copy.deepcopy(blocks))
        else:
            break

    # Spawn new block after move
    if moved:
        spawn_new_block()
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
    # Roll modulo parameters at game start
    roll_modulo_parameters()

    # Initial block spawn
    spawn_new_block()
    spawn_new_block()

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
