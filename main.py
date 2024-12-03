# main.py

import time
from PIL import Image, ImageDraw, ImageFont
import hardware_setup  # Import the hardware setup
import os  # For high score persistence
import traceback

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
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 24

# Load font with fallback
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    print(f"Font loaded successfully from {FONT_PATH}.")
except IOError:
    # Fallback to a default font if the specified font is not found
    font = ImageFont.load_default()
    print("Default font loaded as fallback.")

# Initialize a 4x4 debug grid for terminal display
debug_grid = [
    [2, 0, 0, 2],
    [0, 4, 4, 0],
    [0, 0, 8, 0],
    [16, 0, 0, 16]
]

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
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)

        # Define text content
        title_text = "2048 Game"
        rules_text = "Swipe tiles to combine\nand reach 2048!"
        high_score_text = f"High Score: {high_score}"
        start_option = "A: Start Game"
        reset_option = "B: Reset High Score"

        # Define positions
        # Since the grid fills the display, adjust positions to fit

        # Draw Title
        title_bbox = draw.textbbox((0, 0), title_text, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (width - title_width) / 2
        title_y = 10  # Top margin
        draw.text((title_x, title_y), title_text, font=font, fill=(255, 255, 255))
        print("Title drawn.")

        # Draw Rules
        rules_bbox = draw.textbbox((0, 0), rules_text, font=font)
        rules_width = rules_bbox[2] - rules_bbox[0]
        rules_height = rules_bbox[3] - rules_bbox[1]
        rules_x = (width - rules_width) / 2
        rules_y = title_y + title_height + 10
        draw.multiline_text((rules_x, rules_y), rules_text, font=font, fill=(255, 255, 255), align="center")
        print("Rules drawn.")

        # Draw High Score
        high_score_bbox = draw.textbbox((0, 0), high_score_text, font=font)
        high_score_width = high_score_bbox[2] - high_score_bbox[0]
        high_score_height = high_score_bbox[3] - high_score_bbox[1]
        high_score_x = (width - high_score_width) / 2
        high_score_y = rules_y + rules_height + 20
        draw.text((high_score_x, high_score_y), high_score_text, font=font, fill=(255, 255, 255))
        print("High score drawn.")

        # Draw Start Option
        start_bbox = draw.textbbox((0, 0), start_option, font=font)
        start_width = start_bbox[2] - start_bbox[0]
        start_height = start_bbox[3] - start_bbox[1]
        start_x = (width - start_width) / 2
        start_y = high_score_y + high_score_height + 30
        draw.text((start_x, start_y), start_option, font=font, fill=(0, 255, 0))  # Green for Start
        print("Start option drawn.")

        # Draw Reset Option
        reset_bbox = draw.textbbox((0, 0), reset_option, font=font)
        reset_width = reset_bbox[2] - reset_bbox[0]
        reset_height = reset_bbox[3] - reset_bbox[1]
        reset_x = (width - reset_width) / 2
        reset_y = start_y + start_height + 10
        draw.text((reset_x, reset_y), reset_option, font=font, fill=(255, 0, 0))  # Red for Reset
        print("Reset option drawn.")

        # Update the display
        disp.image(image)
        print("Main Menu displayed successfully.")
    except Exception as e:
        print("Error in draw_main_menu:", e)
        traceback.print_exc(file=sys.stdout)

def draw_debug_grid():
    """
    Draws a static grid on the display for debugging purposes and prints it to the terminal.
    """
    try:
        print("Drawing Debug Grid...")
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

        # Draw the blocks (tiles) based on the debug_grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = debug_grid[row][col]
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
                    print(f"Tile drawn at ({row}, {col}) with value {value}.")

        # Update the display with the drawn image
        disp.image(image)
        print("Debug Grid displayed successfully on the display.")
        
        # Print the grid to the terminal
        print("Current Debug Grid State:")
        print_grid(debug_grid)
        
    except Exception as e:
        print("Error in draw_debug_grid:", e)
        traceback.print_exc(file=sys.stdout)

def print_grid(grid):
    """
    Prints the 4x4 grid to the terminal in a formatted manner.
    
    Args:
        grid (list of list of int): The 4x4 grid to print.
    """
    separator = "+----+----+----+----+"
    print(separator)
    for row in grid:
        row_display = ""
        for num in row:
            if num != 0:
                row_display += f"|{str(num).center(4)}"
            else:
                row_display += f"|    "
        row_display += "|"
        print(row_display)
        print(separator)

def log_button_press(button_name):
    """
    Logs the button press to the terminal.
    
    Args:
        button_name (str): The name of the button pressed.
    """
    print(f"Button '{button_name}' pressed.")

# Initial draw of the main menu
draw_main_menu()

# Debounce variables
last_press_time = 0
DEBOUNCE_TIME = 0.2  # seconds

try:
    while True:
        current_time = time.time()

        if current_state == STATE_MAIN_MENU:
            # Handle Start Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Starting game.")
                current_state = STATE_GAME
                # For debugging, draw the grid and print it to the terminal
                draw_debug_grid()
                last_press_time = current_time

            # Handle Reset High Score (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Reset high score.")
                current_state = STATE_RESET_CONFIRM
                # Reset high score and redraw main menu
                high_score = 0
                save_high_score(high_score)
                print("High score reset to 0.")
                draw_main_menu()
                last_press_time = current_time

        elif current_state == STATE_GAME:
            # During the game, handle button presses for movement
            # Since handle_move is removed, just log button presses

            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                log_button_press('Up')
                last_press_time = current_time

            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                log_button_press('Down')
                last_press_time = current_time

            if not buttons['left'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                log_button_press('Left')
                last_press_time = current_time

            if not buttons['right'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                log_button_press('Right')
                last_press_time = current_time

            # Handle Restart Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Restarting game.")
                current_state = STATE_GAME
                # Redraw the debug grid and print it to the terminal
                draw_debug_grid()
                last_press_time = current_time

            # Handle Return to Main Menu (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to main menu.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                last_press_time = current_time

        elif current_state == STATE_RESET_CONFIRM:
            # Since handle_move is removed, any confirmation actions are already done
            # Just transition back to main menu
            current_state = STATE_MAIN_MENU
            draw_main_menu()

        elif current_state == STATE_GAME_OVER:
            # Since handle_move is removed, Game Over state isn't functional
            # Just return to main menu
            print("Game Over state detected, returning to main menu.")
            current_state = STATE_MAIN_MENU
            draw_main_menu()

        # Sleep to reduce CPU usage
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Program terminated by user.")
except Exception as e:
    print("Unexpected error:", e)
    traceback.print_exc(file=sys.stdout)
