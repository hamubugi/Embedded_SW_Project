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

# Define Game States
STATE_MAIN_MENU = 'MAIN_MENU'
STATE_GAME = 'GAME'
STATE_RESET_CONFIRM = 'RESET_CONFIRM'
STATE_GAME_OVER = 'GAME_OVER'

# Initialize the current state
current_state = STATE_MAIN_MENU

# Define Grid Parameters
GRID_SIZE = 4  # 4x4 grid for 2048
TILE_SIZE = 55  # Size of each tile in pixels
TILE_THICKNESS = 4  # Thickness of grid lines in pixels
GRID_COLOR = (255, 255, 255)  # White grid lines

# Calculate total grid width and height
TOTAL_GRID_SIZE = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * TILE_THICKNESS

# Calculate offsets to center the grid on the display
offset_x = (width - TOTAL_GRID_SIZE) // 2
offset_y = (height - TOTAL_GRID_SIZE) // 2

# Define Colors
BACKGROUND_COLOR = (0, 0, 0)  # Black background
EMPTY_TILE_COLOR = (205, 193, 180)
TILE_COLORS = {
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

# Initialize game variables
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

def draw_main_menu():
    """
    Draws the main menu screen with game rules, high score, and options.
    """
    # Clear the image buffer
    draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

    # Define text content
    title_text = "2048 Game"
    rules_text = "Swipe tiles to combine and reach 2048!"
    high_score_text = f"High Score: {high_score}"
    start_option = "A: Start Game"
    reset_option = "B: Reset High Score"

    # Define positions with adjusted spacing
    # Start from 10% of the screen height
    current_y = height * 0.1

    # Draw Title
    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    title_x = (width - text_width) / 2
    title_y = current_y
    draw.text((title_x, title_y), title_text, font=font, fill=(255, 255, 255))
    current_y += text_height + 20  # Move down for next text

    # Draw Rules
    bbox = draw.textbbox((0, 0), rules_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    rules_x = (width - text_width) / 2
    rules_y = current_y
    draw.text((rules_x, rules_y), rules_text, font=font, fill=(255, 255, 255))
    current_y += text_height + 20

    # Draw High Score
    bbox = draw.textbbox((0, 0), high_score_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    high_score_x = (width - text_width) / 2
    high_score_y = current_y
    draw.text((high_score_x, high_score_y), high_score_text, font=font, fill=(255, 255, 255))
    current_y += text_height + 40  # Extra space before options

    # Draw Start Option
    bbox = draw.textbbox((0, 0), start_option, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    start_x = (width - text_width) / 2
    start_y = current_y
    draw.text((start_x, start_y), start_option, font=font, fill=(0, 255, 0))  # Green for Start
    current_y += text_height + 20

    # Draw Reset Option
    bbox = draw.textbbox((0, 0), reset_option, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    reset_x = (width - text_width) / 2
    reset_y = current_y
    draw.text((reset_x, reset_y), reset_option, font=font, fill=(255, 0, 0))  # Red for Reset

    # Update the display
    disp.image(image)

def draw_reset_confirm():
    """
    Draws the reset confirmation screen.
    """
    # Clear the image buffer
    draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

    # Define text content
    confirm_text = "Press B again to confirm reset"

    # Calculate text size and position
    bbox = draw.textbbox((0, 0), confirm_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) / 2
    text_y = (height - text_height) / 2

    # Draw text
    draw.text((text_x, text_y), confirm_text, font=font, fill=(255, 255, 255))

    # Update the display
    disp.image(image)

def draw_game_over_screen(won=False):
    """
    Draws the game over screen showing the result and options.
    """
    # Clear the image buffer
    draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

    # Define text content
    if won:
        result_text = "You Won!"
    else:
        result_text = "Game Over!"
    high_score_text = f"High Score: {high_score}"
    restart_option = "A: Restart Game"
    main_menu_option = "B: Main Menu"

    # Calculate positions with adequate spacing
    current_y = height * 0.4  # Start from 40% of the screen height

    # Draw Result Text
    bbox = draw.textbbox((0, 0), result_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    result_x = (width - text_width) / 2
    result_y = current_y
    draw.text((result_x, result_y), result_text, font=font, fill=(255, 255, 255))
    current_y += text_height + 20

    # Draw High Score
    bbox = draw.textbbox((0, 0), high_score_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    high_score_x = (width - text_width) / 2
    high_score_y = current_y
    draw.text((high_score_x, high_score_y), high_score_text, font=font, fill=(255, 255, 255))
    current_y += text_height + 40

    # Draw Restart Option
    bbox = draw.textbbox((0, 0), restart_option, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    restart_x = (width - text_width) / 2
    restart_y = current_y
    draw.text((restart_x, restart_y), restart_option, font=font, fill=(0, 255, 0))  # Green for Restart
    current_y += text_height + 20

    # Draw Main Menu Option
    bbox = draw.textbbox((0, 0), main_menu_option, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    main_menu_x = (width - text_width) / 2
    main_menu_y = current_y
    draw.text((main_menu_x, main_menu_y), main_menu_option, font=font, fill=(255, 0, 0))  # Red for Main Menu

    # Update the display
    disp.image(image)

def draw_game():
    """
    Draws the 2048 game grid and blocks on the display.
    """
    # Clear the image buffer
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

def reset_game():
    global grid, game_state, score
    grid = logic.start_game()
    game_state = 'GAME NOT OVER'
    score = 0
    draw_game()

def handle_main_menu_buttons():
    global current_state
    # Handle Start Game (Button A)
    if not buttons['A'].value:
        current_state = STATE_GAME
        # Initialize game variables
        reset_game()
        time.sleep(DEBOUNCE_TIME)

    # Handle Reset High Score (Button B)
    if not buttons['B'].value:
        current_state = STATE_RESET_CONFIRM
        draw_reset_confirm()
        time.sleep(DEBOUNCE_TIME)

def handle_reset_confirm_buttons():
    global high_score, current_state
    # Confirm Reset (Button B)
    if not buttons['B'].value:
        high_score = 0
        save_high_score(high_score)
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)

    # Optional: Cancel Reset (Button A)
    elif not buttons['A'].value:
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)

def handle_game_over_buttons(won=False):
    global current_state, score, grid, game_state
    # Restart Game (Button A)
    if not buttons['A'].value:
        current_state = STATE_GAME
        reset_game()
        time.sleep(DEBOUNCE_TIME)

    # Return to Main Menu (Button B)
    if not buttons['B'].value:
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)

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
    draw_game()

# Initial draw based on current state
draw_main_menu()

# Debounce variables
last_press_time = 0
DEBOUNCE_TIME = 0.2  # seconds

while True:
    current_time = time.time()

    if current_state == STATE_MAIN_MENU:
        handle_main_menu_buttons()

    elif current_state == STATE_RESET_CONFIRM:
        handle_reset_confirm_buttons()

    elif current_state == STATE_GAME:
        # During the game, handle button presses for movement
        if not buttons['up'].value and current_time - last_press_time > DEBOUNCE_TIME:
            handle_move('UP')
            last_press_time = current_time

        if not buttons['down'].value and current_time - last_press_time > DEBOUNCE_TIME:
            handle_move('DOWN')
            last_press_time = current_time

        if not buttons['left'].value and current_time - last_press_time > DEBOUNCE_TIME:
            handle_move('LEFT')
            last_press_time = current_time

        if not buttons['right'].value and current_time - last_press_time > DEBOUNCE_TIME:
            handle_move('RIGHT')
            last_press_time = current_time

        if game_state in ['WON', 'LOST']:
            current_state = STATE_GAME_OVER
            draw_game_over_screen(won=(game_state == 'WON'))

    elif current_state == STATE_GAME_OVER:
        handle_game_over_buttons(won=(game_state == 'WON'))

    # Sleep to reduce CPU usage
    time.sleep(0.05)
