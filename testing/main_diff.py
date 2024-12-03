# main.py

import time
import random
from PIL import Image, ImageDraw, ImageFont
import logic  # Ensure logic.py is in the same directory
import hardware_setup  # Ensure hardware_setup.py is correctly set up
import os  # For high score persistence
import sys
import traceback

# Initial debug statement to confirm the program has started
print("Starting 2048 Game...")

# Access hardware components from hardware_setup
disp = hardware_setup.disp
backlight = hardware_setup.backlight
buttons = hardware_setup.buttons
image = hardware_setup.image
draw = hardware_setup.draw
width = hardware_setup.width
height = hardware_setup.height
font = hardware_setup.font  # Ensure hardware_setup.py exposes the font

# Define Game States
STATE_MAIN_MENU = 'MAIN_MENU'
STATE_GAME = 'GAME'
STATE_RESET_CONFIRM = 'RESET_CONFIRM'
STATE_GAME_OVER = 'GAME_OVER'

# Initialize the current state
current_state = STATE_MAIN_MENU
print(f"Initial State: {current_state}")

# Define Grid Parameters
GRID_SIZE = 4  # 4x4 grid for 2048
TILE_SIZE = 55  # Size of each tile in pixels
TILE_THICKNESS = 4  # Thickness of grid lines in pixels
GRID_COLOR = (255, 255, 255)  # White grid lines

# Calculate total grid width and height
TOTAL_GRID_SIZE = GRID_SIZE * TILE_SIZE + (GRID_SIZE + 1) * TILE_THICKNESS
print(f"Total Grid Size: {TOTAL_GRID_SIZE}x{TOTAL_GRID_SIZE} pixels")

# Calculate offsets to center the grid on the display
offset_x = (width - TOTAL_GRID_SIZE) // 2
offset_y = (height - TOTAL_GRID_SIZE) // 2
print(f"Grid Offsets - X: {offset_x}, Y: {offset_y}")

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

# Initialize game variables
grid = logic.start_game()
game_state = 'GAME_NOT_OVER'
score = 0
high_score = 0  # Initialize high score

# High Score Persistence Setup
HIGH_SCORE_FILE = "high_score.txt"

def load_high_score():
    if not os.path.exists(HIGH_SCORE_FILE):
        print("High score file not found. Initializing to 0.")
        return 0
    with open(HIGH_SCORE_FILE, 'r') as f:
        try:
            hs = int(f.read())
            print(f"High score loaded: {hs}")
            return hs
        except ValueError:
            print("High score file corrupted. Resetting to 0.")
            return 0

def save_high_score(new_high_score):
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            f.write(str(new_high_score))
        print(f"High score saved: {new_high_score}")
    except Exception as e:
        print("Error saving high score:", e)
        traceback.print_exc(file=sys.stdout)

# Load high score at the start
high_score = load_high_score()

def draw_main_menu():
    """
    Draws the main menu screen with game rules, high score, and options.
    """
    try:
        print("Drawing Main Menu...")
        # Clear the image buffer
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

        # Define text content
        title_text = "2048 Game"
        rules_text = "Swipe tiles to combine\nand reach 2048!"
        high_score_text = f"High Score: {high_score}"
        start_option = "A: Start Game"
        reset_option = "B: Reset High Score"

        # Define positions with adjusted spacing
        current_y = height * 0.1  # Start from 10% of the screen height

        # Draw Title
        title_bbox = draw.textbbox((0, 0), title_text, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (width - title_width) / 2
        draw.text((title_x, current_y), title_text, font=font, fill=(255, 255, 255))
        print("Title drawn.")
        current_y += title_height + 20  # Move down for next text

        # Draw Rules
        draw.multiline_text((0, current_y), rules_text, font=font, fill=(255, 255, 255), align="center")
        print("Rules drawn.")
        rules_bbox = draw.textbbox((0, current_y), rules_text, font=font)
        rules_height = rules_bbox[3] - rules_bbox[1]
        current_y += rules_height + 20

        # Draw High Score
        high_score_bbox = draw.textbbox((0, 0), high_score_text, font=font)
        high_score_width = high_score_bbox[2] - high_score_bbox[0]
        high_score_x = (width - high_score_width) / 2
        draw.text((high_score_x, current_y), high_score_text, font=font, fill=(255, 255, 255))
        print("High score drawn.")
        current_y += high_score_bbox[3] - high_score_bbox[1] + 40  # Extra space before options

        # Draw Start Option
        start_bbox = draw.textbbox((0, 0), start_option, font=font)
        start_width = start_bbox[2] - start_bbox[0]
        start_x = (width - start_width) / 2
        draw.text((start_x, current_y), start_option, font=font, fill=(0, 255, 0))  # Green for Start
        print("Start option drawn.")
        current_y += start_bbox[3] - start_bbox[1] + 20

        # Draw Reset Option
        reset_bbox = draw.textbbox((0, 0), reset_option, font=font)
        reset_width = reset_bbox[2] - reset_bbox[0]
        reset_x = (width - reset_width) / 2
        draw.text((reset_x, current_y), reset_option, font=font, fill=(255, 0, 0))  # Red for Reset
        print("Reset option drawn.")

        # Update the display
        disp.image(image)
        print("Main Menu displayed.")
    except Exception as e:
        print("Error in draw_main_menu:", e)
        traceback.print_exc(file=sys.stdout)

def draw_reset_confirm():
    """
    Draws the reset confirmation screen.
    """
    try:
        print("Drawing Reset Confirmation Screen...")
        # Clear the image buffer
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

        # Define text content
        confirm_text = "Press B again\nto confirm reset"

        # Calculate text size and position
        confirm_bbox = draw.textbbox((0, 0), confirm_text, font=font)
        confirm_width = confirm_bbox[2] - confirm_bbox[0]
        confirm_height = confirm_bbox[3] - confirm_bbox[1]
        confirm_x = (width - confirm_width) / 2
        confirm_y = (height - confirm_height) / 2

        # Draw text
        draw.multiline_text((confirm_x, confirm_y), confirm_text, font=font, fill=(255, 255, 255), align="center")
        print("Reset confirmation screen drawn.")

        # Update the display
        disp.image(image)
    except Exception as e:
        print("Error in draw_reset_confirm:", e)
        traceback.print_exc(file=sys.stdout)

def draw_game_over_screen(won=False):
    """
    Draws the game over screen showing the result and options.
    """
    try:
        print("Drawing Game Over Screen...")
        # Clear the image buffer
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

        # Define text content
        result_text = "You Won!" if won else "Game Over!"
        high_score_text = f"High Score: {high_score}"
        restart_option = "A: Restart Game"
        main_menu_option = "B: Main Menu"

        # Define positions with adequate spacing
        current_y = height * 0.3  # Start from 30% of the screen height

        # Draw Result Text
        result_bbox = draw.textbbox((0, 0), result_text, font=font)
        result_width = result_bbox[2] - result_bbox[0]
        result_height = result_bbox[3] - result_bbox[1]
        result_x = (width - result_width) / 2
        draw.text((result_x, current_y), result_text, font=font, fill=(255, 255, 255))
        print("Result text drawn.")
        current_y += result_height + 20

        # Draw High Score
        high_score_bbox = draw.textbbox((0, 0), high_score_text, font=font)
        high_score_width = high_score_bbox[2] - high_score_bbox[0]
        high_score_x = (width - high_score_width) / 2
        draw.text((high_score_x, current_y), high_score_text, font=font, fill=(255, 255, 255))
        print("High score drawn on Game Over screen.")
        current_y += high_score_bbox[3] - high_score_bbox[1] + 40

        # Draw Restart Option
        restart_bbox = draw.textbbox((0, 0), restart_option, font=font)
        restart_width = restart_bbox[2] - restart_bbox[0]
        restart_x = (width - restart_width) / 2
        draw.text((restart_x, current_y), restart_option, font=font, fill=(0, 255, 0))  # Green for Restart
        print("Restart option drawn on Game Over screen.")
        current_y += restart_bbox[3] - restart_bbox[1] + 20

        # Draw Main Menu Option
        main_menu_bbox = draw.textbbox((0, 0), main_menu_option, font=font)
        main_menu_width = main_menu_bbox[2] - main_menu_bbox[0]
        main_menu_x = (width - main_menu_width) / 2
        draw.text((main_menu_x, current_y), main_menu_option, font=font, fill=(255, 0, 0))  # Red for Main Menu
        print("Main Menu option drawn on Game Over screen.")

        # Update the display
        disp.image(image)
        print("Game Over screen displayed.")
    except Exception as e:
        print("Error in draw_game_over_screen:", e)
        traceback.print_exc(file=sys.stdout)

def draw_game():
    """
    Draws the 2048 game grid and blocks on the display.
    """
    try:
        print("Drawing Game Screen...")
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
                    text_color = (119, 110, 101) if value <= 4 else (255, 255, 255)

                    draw.text((text_x, text_y), text, font=font, fill=text_color)

        # Draw game state
        if game_state == 'WON':
            status_text = "You Won!"
        elif game_state == 'LOST':
            status_text = "Game Over!"
        else:
            status_text = "Use Buttons to Play"

        # Calculate status text position
        status_bbox = draw.textbbox((0, 0), status_text, font=font)
        status_width = status_bbox[2] - status_bbox[0]
        status_height = status_bbox[3] - status_bbox[1]
        status_x = (width - status_width) / 2
        status_y = offset_y + TOTAL_GRID_SIZE + 20  # Positioned below the grid

        draw.text((status_x, status_y), status_text, font=font, fill=(255, 255, 255))
        print(f"Game State Displayed: {status_text}")

        # Draw scores
        score_text = f"Score: {score}  High: {high_score}"
        score_bbox = draw.textbbox((0, 0), score_text, font=font)
        score_width = score_bbox[2] - score_bbox[0]
        score_height = score_bbox[3] - score_bbox[1]
        score_x = (width - score_width) / 2
        score_y = offset_y - score_height - 10  # Positioned above the grid

        draw.text((score_x, score_y), score_text, font=font, fill=(255, 255, 255))
        print(f"Score Displayed: {score_text}")

        # Update the display with the drawn image
        disp.image(image)
        print("Game screen updated.")
    except Exception as e:
        print("Error in draw_game:", e)
        traceback.print_exc(file=sys.stdout)

def reset_game():
    global grid, game_state, score
    print("Resetting game...")
    grid = logic.start_game()
    game_state = 'GAME_NOT_OVER'
    score = 0
    draw_game()
    print("Game has been reset.")

def handle_main_menu_buttons():
    global current_state
    # Handle Start Game (Button A)
    if not buttons['A'].value:
        print("Button A pressed: Starting game.")
        current_state = STATE_GAME
        # Initialize game variables
        reset_game()
        time.sleep(DEBOUNCE_TIME)  # Debounce

    # Handle Reset High Score (Button B)
    if not buttons['B'].value:
        print("Button B pressed: Reset high score.")
        current_state = STATE_RESET_CONFIRM
        draw_reset_confirm()
        time.sleep(DEBOUNCE_TIME)  # Debounce

def handle_reset_confirm_buttons():
    global high_score, current_state
    # Confirm Reset (Button B)
    if not buttons['B'].value:
        print("Button B pressed again: Confirming reset.")
        high_score = 0
        save_high_score(high_score)
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)  # Debounce

    # Optional: Cancel Reset (Button A)
    elif not buttons['A'].value:
        print("Button A pressed: Canceling reset.")
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)  # Debounce

def handle_game_over_buttons(won=False):
    global current_state, score, grid, game_state
    # Restart Game (Button A)
    if not buttons['A'].value:
        print("Button A pressed: Restarting game.")
        current_state = STATE_GAME
        reset_game()
        time.sleep(DEBOUNCE_TIME)  # Debounce

    # Return to Main Menu (Button B)
    if not buttons['B'].value:
        print("Button B pressed: Returning to main menu.")
        current_state = STATE_MAIN_MENU
        draw_main_menu()
        time.sleep(DEBOUNCE_TIME)  # Debounce

def handle_move(direction):
    global grid, game_state, score, high_score
    if game_state != 'GAME_NOT_OVER':
        print(f"Ignoring move {direction} since game state is {game_state}.")
        return
    try:
        print(f"Handling move: {direction}")
        if direction == 'LEFT':
            grid, changed, move_score = logic.move_left(grid)
        elif direction == 'RIGHT':
            grid, changed, move_score = logic.move_right(grid)
        elif direction == 'UP':
            grid, changed, move_score = logic.move_up(grid)
        elif direction == 'DOWN':
            grid, changed, move_score = logic.move_down(grid)
        else:
            print(f"Invalid move direction: {direction}")
            return

        if changed:
            print(f"Move {direction} changed the grid. Score increased by {move_score}.")
            score += move_score
            logic.add_new_2(grid)
            print("Added a new tile after move.")
            if score > high_score:
                high_score = score
                save_high_score(high_score)
        else:
            print(f"Move {direction} did not change the grid.")

        game_state = logic.get_current_state(grid)
        print(f"Game State after move: {game_state}")
        draw_game()
    except Exception as e:
        print(f"Error handling move {direction}:", e)
        traceback.print_exc(file=sys.stdout)

# Initial draw based on current state
draw_main_menu()

# Debounce variables
last_press_time = 0
DEBOUNCE_TIME = 0.2  # seconds

try:
    while True:
        current_time = time.time()

        if current_state == STATE_MAIN_MENU:
            handle_main_menu_buttons()

        elif current_state == STATE_RESET_CONFIRM:
            handle_reset_confirm_buttons()

        elif current_state == STATE_GAME:
            # During the game, handle button presses for movement
            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button Up pressed.")
                handle_move('UP')
                last_press_time = current_time

            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button Down pressed.")
                handle_move('DOWN')
                last_press_time = current_time

            if not buttons['left'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button Left pressed.")
                handle_move('LEFT')
                last_press_time = current_time

            if not buttons['right'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button Right pressed.")
                handle_move('RIGHT')
                last_press_time = current_time

            if game_state in ['WON', 'LOST']:
                print(f"Transitioning to {STATE_GAME_OVER} state.")
                current_state = STATE_GAME_OVER
                draw_game_over_screen(won=(game_state == 'WON'))

        elif current_state == STATE_GAME_OVER:
            handle_game_over_buttons(won=(game_state == 'WON'))

        # Sleep to reduce CPU usage
        time.sleep(0.05)
except KeyboardInterrupt:
    print("Game terminated by user.")
except Exception as e:
    print("Unexpected error:", e)
    traceback.print_exc(file=sys.stdout)
