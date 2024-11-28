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
SPAWN_CHANCE = 0.2  # 20% chance of spawning a new block after each move
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
    """
    Randomly determine the modulo parameters at game start.
    """
    global MODULO_Y, MODULO_N
    
    # Randomly choose the modulo base between 5 and MAX_MODULO_BASE
    MODULO_Y = random.randint(5, MAX_MODULO_BASE)
    
    # Randomly choose N (which number in the sequence we want)
    MODULO_N = random.randint(1, 10)
    
    print(f"Game Modulo Rules: {MODULO_N}-th number satisfying x = z (mod {MODULO_Y})")
    return MODULO_Y, MODULO_N

def find_nth_modulo_number(x, y, n):
    """
    Find the N-th number Z that satisfies X = Z (mod Y)
    """
    if y <= 0:
        raise ValueError("Modulo base must be positive")
    
    candidates = []
    z = x  # Start from x itself
    
    # Find first n numbers that satisfy the modulo condition
    while len(candidates) < n:
        if z % y == x % y:
            candidates.append(z)
        z += 1
        
        # Prevent infinite loops or extremely large numbers
        if z > MAX_BLOCK_VALUE:
            break
    
    # Return the nth number found, or the last candidate
    return candidates[n-1] if len(candidates) >= n else candidates[-1]

def spawn_new_block():
    """
    Spawn a new block on an empty grid cell.
    Modulo blocks have a small chance of spawning.
    """
    # Find empty cells
    empty_cells = [
        (row, col) 
        for row in range(GRID_SIZE) 
        for col in range(GRID_SIZE) 
        if blocks[row][col] == 0
    ]
    
    if not empty_cells:
        return False
    
    # Choose a random empty cell
    row, col = random.choice(empty_cells)
    
    # Determine block type and value
    if random.random() < MODULO_BLOCK_CHANCE:
        # Modulo block (pink)
        blocks[row][col] = random.choice([2, 4, 8])  # Modulo blocks start smaller
    else:
        # Normal block (yellow)
        blocks[row][col] = 2 if random.random() < 0.9 else 4
    
    return True

def is_modulo_block(value):
    """
    Check if a block is a modulo block
    """
    return MODULO_Y and value % MODULO_Y == 0

def merge_blocks(block1, block2):
    """
    Determine how blocks merge based on their type
    """
    # If blocks are the same type (both normal or both modulo)
    if is_modulo_block(block1) == is_modulo_block(block2):
        if MODULO_Y and MODULO_N:
            return find_nth_modulo_number(block1, MODULO_Y, MODULO_N)
        else:
            return block1 + block2
    
    # If different types, can't merge
    return None

# -----------------------------
# Existing Game Functions
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

                # Determine block color
                if is_modulo_block(blocks[row][col]):
                    block_color = (255, 105, 180)  # Pink for modulo blocks
                else:
                    block_color = (255, 255, 0)  # Yellow for normal blocks

                # Draw the block rectangle
                draw.rectangle(
                    [x_pos, y_pos, x_pos + TILE_SIZE, y_pos + TILE_SIZE],
                    fill=block_color
                )

                # Draw the block value
                text = str(blocks[row][col])

                # Add modulo parameters for modulo blocks
                if is_modulo_block(blocks[row][col]) and MODULO_Y and MODULO_N:
                    text += f"\n(mod {MODULO_Y}, {MODULO_N})"

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
    Modified slide_blocks to incorporate new merging and block spawning logic
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
                
                if (0 <= next_row < GRID_SIZE and 0 <= next_col < GRID_SIZE):
                    # Merge condition
                    if (blocks[row][col] != 0 and blocks[next_row][next_col] != 0):
                        merged_value = merge_blocks(
                            blocks[row][col], 
                            blocks[next_row][next_col]
                        )
                        
                        if merged_value:
                            new_blocks[next_row][next_col] = merged_value
                            new_blocks[row][col] = 0
                            moved = True
                            any_block_moved = True
                    
                    # Movement condition
                    elif (blocks[row][col] != 0 and blocks[next_row][next_col] == 0):
                        new_blocks[next_row][next_col] = blocks[row][col]
                        new_blocks[row][col] = 0
                        moved = True
                        any_block_moved = True
        
        if any_block_moved:
            blocks = new_blocks
            animation_queue.append(copy.deepcopy(blocks))
        else:
            break  # Stop if no more moves possible

    # Spawn new block after move
    if moved and random.random() < SPAWN_CHANCE:
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