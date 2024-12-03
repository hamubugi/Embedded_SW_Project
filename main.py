# main.py

import time
import random
from colorsys import hsv_to_rgb
from PIL import Image, ImageDraw, ImageFont
import logic  # Import the game logic
import hardware_setup  # Import the hardware setup
import os  # For high score persistence

# Access hardware components from hardware_setup
disp = hardware_setup.disp
backlight = hardware_setup.backlight
buttons = hardware_setup.buttons
image = hardware_setup.image
draw = hardware_setup.draw
width = hardware_setup.width
height = hardware_setup.height

# Access grid constants
GRID_SIZE = hardware_setup.GRID_SIZE
TILE_SIZE = hardware_setup.TILE_SIZE
TILE_THICKNESS = hardware_setup.TILE_THICKNESS
GRID_COLOR = hardware_setup.GRID_COLOR
TOTAL_GRID_SIZE = hardware_setup.TOTAL_GRID_SIZE
offset_x = hardware_setup.offset_x
offset_y = hardware_setup.offset_y

# Define Colors
BACKGROUND_COLOR = (0, 0, 0)  # Black background
EMPTY_TILE_COLOR = (205, 193, 180)
TILE_COLORS = hardware_setup.TILE_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

TEXT_COLOR = (119, 110, 101)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 24

# Load font with fallback
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except IOError:
    # Fallback to a default font if the specified font is not found
    font = ImageFont.load_default()

# Initialize game
grid = logic.start_game()
game_state = 'GAME NOT OVER'
score = 0
high_score = 0  # Initialize high score

# High Score Persistence Setup
HIGH_SCORE_FILE = "high_score.txt"

def load_high_score():
    if not os.path.exists(HIGH_SCORE_FILE):
        return 0
    with open(HIGH_SCORE_FILE, 'r') as f:
        try:
            return int(f.read())
        except ValueError:
            return 0

def save_high_score(new_high_score):
    with open(HIGH_SCORE_FILE, 'w') as f:
        f.write(str(new_high_score))

# Load high score at the start
high_score = load_high_score()

def draw_grid():
    """
    Draws the 2048 game grid and blocks on the display.
    """
    # Clear the background
    draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

    # Draw grid lines
    for i in range(GRID_SIZE + 1):
        # Vertical lines
        x = offset_x + i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([x, offset_y, x + TILE_THICKNESS, offset_y + TOTAL_GRID_SIZE], fill=GRID_COLOR)

        # Horizontal lines
        y = offset_y + i * (TILE_SIZE + TILE_THICKNESS)
        draw.rectangle([offset_x, y, offset_x + TOTAL_GRID_SIZE, y + TILE_THICKNESS], fill=GRID_COLOR)

    # Draw the blocks (tiles)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = grid[row][col]
            if value != 0:
                # Calculate block position
                x_pos = offset_x + col * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                y_pos = offset_y + row * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS

                # Determine block color
                block_color = TILE_COLORS.get(value, (60, 58, 50))  # Default color if value exceeds 2048

                # Draw the block rectangle
                draw.rectangle(
                    [x_pos, y_pos, x_pos + TILE_SIZE, y_pos + TILE_SIZE],
                    fill=block_color
                )

                # Draw the block value
                text = str(value)

                # Calculate text size and position using textbbox
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                text_x = x_pos + (TILE_SIZE - text_width) / 2
                text_y = y_pos + (TILE_SIZE - text_height) / 2

                # Choose text color based on tile value for better visibility
                if value <= 4:
                    text_color = (119, 110, 101)  # Dark text
                else:
                    text_color = (255, 255, 255)  # White text

                draw.text((text_x, text_y), text, font=font, fill=text_color)

    # Draw game state
    if game_state == 'WON':
        status_text = "You Won!"
    elif game_state == 'LOST':
        status_text = "Game Over!"
    else:
        status_text = "Use Buttons to Play"

    # Calculate status text position
    bbox = draw.textbbox((0, 0), status_text, font=font)
    status_width = bbox[2] - bbox[0]
    status_height = bbox[3] - bbox[1]
    status_x = (width - status_width) / 2
    status_y = offset_y + TOTAL_GRID_SIZE + 20  # Positioned below the grid

    draw.text((status_x, status_y), status_text, font=font, fill=(255, 255, 255))

    # Draw scores
    score_text = f"Score: {score}  High: {high_score}"
    bbox = draw.textbbox((0, 0), score_text, font=font)
    score_width = bbox[2] - bbox[0]
    score_height = bbox[3] - bbox[1]
    score_x = (width - score_width) / 2
    score_y = offset_y - score_height - 10  # Positioned above the grid

    draw.text((score_x, score_y), score_text, font=font, fill=(255, 255, 255))

    # Update the display with the drawn image
    disp.image(image)

def handle_move(direction):
    global grid, game_state, score, high_score
    if game_state != 'GAME NOT OVER':
        return
    if direction == 'LEFT':
        grid, changed, move_score = logic.move_left(grid)
    elif direction == 'RIGHT':
        grid, changed, move_score = logic.move_right(grid)
    elif direction == 'UP':
        grid, changed, move_score = logic.move_up(grid)
    elif direction == 'DOWN':
        grid, changed, move_score = logic.move_down(grid)
    else:
        return

    if changed:
        score += move_score
        logic.add_new_2(grid)
        if score > high_score:
            high_score = score
            save_high_score(high_score)
    game_state = logic.get_current_state(grid)
    draw_grid()

def reset_game():
    global grid, game_state, score
    grid = logic.start_game()
    game_state = 'GAME NOT OVER'
    score = 0
    draw_grid()

# Initial draw
draw_grid()

# Debounce variables
last_press_time = 0
DEBOUNCE_TIME = 0.2  # seconds

while True:
    current_time = time.time()

    # Handle Up Button
    if not buttons['up'].value and current_time - last_press_time > DEBOUNCE_TIME:
        handle_move('UP')
        last_press_time = current_time

    # Handle Down Button
    if not buttons['down'].value and current_time - last_press_time > DEBOUNCE_TIME:
        handle_move('DOWN')
        last_press_time = current_time

    # Handle Left Button
    if not buttons['left'].value and current_time - last_press_time > DEBOUNCE_TIME:
        handle_move('LEFT')
        last_press_time = current_time

    # Handle Right Button
    if not buttons['right'].value and current_time - last_press_time > DEBOUNCE_TIME:
        handle_move('RIGHT')
        last_press_time = current_time

    # Handle Reset Button (Button A)
    if not buttons['A'].value and current_time - last_press_time > DEBOUNCE_TIME:
        reset_game()
        last_press_time = current_time

    # Optional: Add more functionalities or handle other buttons if needed

    time.sleep(0.1)  # Adjust sleep time as needed
