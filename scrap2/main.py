# main.py

import time
import copy
import random
from PIL import ImageFont
import setup  # Import the setup module we created earlier

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

# Adjusted directions due to display rotation (fixed inverted controls)
DIRECTIONS = {
    "left": (0, 1),    # Left moves right in array indices (due to rotation)
    "right": (0, -1),  # Right moves left in array indices
    "up": (-1, 0),     # Up moves down in array indices
    "down": (1, 0),    # Down moves up in array indices
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
    
    print(f"Game Modulo Rules: Find the {MODULO_N}-th number satisfying x ≡ z (mod {MODULO_Y})")
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

def spawn_new_blocks():
    global blocks
    """
    Spawn one normal block and one modulo block on empty grid cells.
    """
    empty_cells = [
        (row, col)
        for row in range(GRID_SIZE)
        for col in range(GRID_SIZE)
        if blocks[row][col] == 0
    ]

    if not empty_cells:
        return False

    # Spawn normal block (2^n value)
    if empty_cells:
        row, col = random.choice(empty_cells)
        blocks[row][col] = random.choice([2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048])
        empty_cells.remove((row, col))

    # Spawn modulo block
    if empty_cells and MODULO_Y:
        row, col = random.choice(empty_cells)
        blocks[row][col] = MODULO_Y * random.randint(1, 3)  # Create modulo blocks (multiples of MODULO_Y)
        print(f"Spawned modulo block at ({row},{col}) with value {blocks[row][col]}")

    return True


def is_modulo_block(value):
    """
    Check if a block is a modulo block
    """
    return value != 0 and MODULO_Y and value % MODULO_Y == 0

def merge_blocks(block1, block2):
    """
    Determine how blocks merge based on their types.
    Blocks only merge if they are equal in value.
    If either block is a modulo block, use modulo merging rules.
    Otherwise, use normal merging rules.
    """
    if block1 != block2:
        return None  # Blocks must be equal to merge

    if MODULO_Y and MODULO_N:
        if is_modulo_block(block1) or is_modulo_block(block2):
            # Use modulo merging rules
            merged_value = find_nth_modulo_number(block1 + block2, MODULO_Y, MODULO_N)
            print(f"Merging modulo blocks: {block1} + {block2} = {merged_value}")
            return merged_value
        else:
            # Both are normal blocks; use normal merging rules
            merged_value = block1 + block2
            print(f"Merging normal blocks: {block1} + {block2} = {merged_value}")
            return merged_value
    else:
        # If modulo parameters are not set, default to normal merging
        merged_value = block1 + block2
        print(f"Merging blocks without modulo parameters: {block1} + {block2} = {merged_value}")
        return merged_value

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
            value = blocks[row][col]
            if value != 0:
                # No inversion of columns or rows
                display_row = row
                display_col = col

                x_pos = display_col * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                y_pos = display_row * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS

                # Determine block color
                if is_modulo_block(value):
                    block_color = (255, 105, 180)  # Pink for modulo blocks
                else:
                    block_color = (255, 255, 0)  # Yellow for normal blocks

                # Draw the block rectangle
                draw.rectangle(
                    [x_pos, y_pos, x_pos + TILE_SIZE, y_pos + TILE_SIZE],
                    fill=block_color
                )

                # Draw the block value
                text = str(value)

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
    global blocks, animation_queue
    """
    Slides the blocks in the given direction, handles merging, and spawns new blocks if any block moved.
    """
    moved = False
    new_blocks = copy.deepcopy(blocks)

    def move_and_merge_line(line):
        nonlocal moved
        new_line = [value for value in line if value != 0]
        i = 0
        while i < len(new_line) - 1:
            current_value = new_line[i]
            next_value = new_line[i + 1]
            if current_value == next_value:
                merged_value = merge_blocks(current_value, next_value)
                new_line[i] = merged_value
                del new_line[i + 1]
                moved = True
            i += 1
        new_line += [0] * (GRID_SIZE - len(new_line))
        return new_line

    if direction == "up":
        for col in range(GRID_SIZE):
            line = [blocks[row][col] for row in range(GRID_SIZE)]
            new_line = move_and_merge_line(line)
            for row in range(GRID_SIZE):
                new_blocks[row][col] = new_line[row]

    elif direction == "down":
        for col in range(GRID_SIZE):
            line = [blocks[row][col] for row in range(GRID_SIZE - 1, -1, -1)]
            new_line = move_and_merge_line(line)
            for idx, row in enumerate(range(GRID_SIZE - 1, -1, -1)):
                new_blocks[row][col] = new_line[idx]

    elif direction == "left":
        for row in range(GRID_SIZE):
            line = blocks[row]
            new_line = move_and_merge_line(line)
            new_blocks[row] = new_line

    elif direction == "right":
        for row in range(GRID_SIZE):
            line = blocks[row][::-1]
            new_line = move_and_merge_line(line)
            new_blocks[row] = new_line[::-1]

    if new_blocks != blocks:
        moved = True
        blocks[:] = new_blocks
        animation_queue.append(copy.deepcopy(blocks))
        spawn_new_blocks()
    else:
        print("No blocks moved or merged")

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

def check_game_over():
    """
    Checks if there are any valid moves left.
    Returns True if the game is over, False otherwise.
    """
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if blocks[row][col] == 0:
                return False  # Empty cell exists
            # Check right neighbor
            if col < GRID_SIZE - 1:
                if blocks[row][col] == blocks[row][col + 1]:
                    return False  # Merge is possible
            # Check down neighbor
            if row < GRID_SIZE - 1:
                if blocks[row][col] == blocks[row + 1][col]:
                    return False  # Merge is possible
    return True  # No moves left

def display_game_rules():
    """
    Display game rules on the screen using drawing methods
    """
    global MODULO_Y, MODULO_N

    # Clear the background to black
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=(0, 0, 0))

    # Prepare different text sizes using the same font
    title_font_size = 28
    rule_font_size = 18
    instruction_font_size = 16

    title_font = ImageFont.truetype(FONT_PATH, title_font_size)
    rule_font = ImageFont.truetype(FONT_PATH, rule_font_size)
    instruction_font = ImageFont.truetype(FONT_PATH, instruction_font_size)

    # Draw title (white text)
    title_text = "Modulo 2048"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((disp.width - title_width) // 2, 10), title_text, font=title_font, fill=(255, 255, 255))

    # Prepare rules text
    if MODULO_Y and MODULO_N:
        rules = [
            f"Find the {MODULO_N}-th number",
            f"satisfies x = z (mod {MODULO_Y})",
            "",
            "Merge blocks by matching:",
            "- Same type blocks",
            "- Following modulo rule",
        ]
    else:
        rules = [
            "Merge blocks with",
            "matching types",
            "Follow modulo sequence",
        ]

    # Draw rules text
    for i, line in enumerate(rules):
        bbox = draw.textbbox((0, 0), line, font=rule_font)
        line_width = bbox[2] - bbox[0]
        draw.text(((disp.width - line_width) // 2, 40 + i * 25), line, font=rule_font, fill=(200, 200, 200))

    # Draw instructions
    instructions = [
        "A: START GAME",
        "B: RE-ROLL RULES"
    ]
    for i, line in enumerate(instructions):
        bbox = draw.textbbox((0, 0), line, font=instruction_font)
        line_width = bbox[2] - bbox[0]
        draw.text(((disp.width - line_width) // 2, 190 + i * 25), line, font=instruction_font, fill=(255, 255, 255))

    # Draw a border
    draw.rectangle((0, 0, disp.width-1, disp.height-1), outline=(255, 255, 255))

    # Update the display
    disp.image(image)

def main():
    """
    The main game loop with rules screen.
    """
    # Initialize game with first set of modulo parameters
    roll_modulo_parameters()
    
    # Rules screen loop
    rules_screen = True
    while rules_screen:
        # Display game rules
        display_game_rules()
        
        # Wait for button press
        if not buttons['A'].value:  # A button pressed
            rules_screen = False
        elif not buttons['B'].value:  # B button pressed (re-roll rules)
            roll_modulo_parameters()
        
        time.sleep(0.2)  # Debounce delay
    
    # Initial block spawn after leaving rules screen
    spawn_new_blocks()
    
    while True:
        # Check for joystick input
        direction_pressed = get_direction_pressed()

        # Slide blocks if a direction button was pressed and no ongoing animation
        if direction_pressed and not animation_queue:
            if slide_blocks(direction_pressed):
                # Debug messages after each move
                print(f"\nAfter moving {direction_pressed}, the grid is:")
                for row in blocks:
                    print(row)
                # Print positions of modulo blocks
                for row in range(GRID_SIZE):
                    for col in range(GRID_SIZE):
                        if is_modulo_block(blocks[row][col]):
                            print(f"Modulo block at ({row},{col}) with value {blocks[row][col]}")

            else:
                print("No blocks moved or merged")

            if check_game_over():
                print("Game Over!")
                break  # Exit the game loop or handle game over accordingly

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
