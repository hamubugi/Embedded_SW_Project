# main.py

import time
import random
from PIL import Image, ImageDraw, ImageFont
import hardware_setup  # Import the hardware setup
import os  # For high score persistence
import traceback
import sys

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

# Initialize the game grid
grid = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0]
]

# Initialize the score
score = 0

# Debounce variables
last_press_time = 0
DEBOUNCE_TIME = 0.2  # seconds

# Sequence tracking variables for debugging
current_sequence_button = None  # Tracks the current button in the sequence ('LEFT' or 'RIGHT')
current_sequence_count = 0        # Counts consecutive presses of the current button
SEQUENCE_THRESHOLD = 16           # Number of consecutive presses required to trigger debug commands

def print_debug_grid():
    """
    Prints the current grid to the terminal in a 4x4 matrix format.
    """
    print("\nCurrent Grid State:")
    print("+------+------+------+------+")  # Top border
    for row in grid:
        row_display = "|"
        for cell in row:
            if cell == 0:
                row_display += "      |"
            else:
                row_display += f" {cell:^4} |"
        print(row_display)
        print("+------+------+------+------+")  # Separator
    print(f"Score: {score}  High Score: {high_score}\n")  # Display scores

def add_random_tile():
    """
    Adds a random tile (2 or 4) to an empty cell in the grid.
    """
    empty_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if grid[r][c] == 0]
    if not empty_cells:
        print("No empty cells available to add a new tile.")
        return False  # Indicate that no tile was added

    row, col = random.choice(empty_cells)
    new_value = random.choices([2, 4], weights=[90, 10])[0]  # 90% chance for 2, 10% for 4
    grid[row][col] = new_value
    print(f"Added {new_value} at position ({row}, {col}).")
    return True  # Indicate that a tile was added

def draw_debug_grid():
    """
    Draws the current grid on the display and prints it to the terminal for debugging.
    """
    try:
        print("Drawing Debug Grid...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Draw grid lines
        for i in range(GRID_SIZE + 1):
            # Vertical lines
            x = offset_x + i * (TILE_SIZE + TILE_THICKNESS)
            draw.rectangle([x, offset_y, x + TILE_THICKNESS, offset_y + TOTAL_GRID_SIZE], fill=GRID_COLOR)
            print(f"Vertical grid line {i} drawn at x={x}.")

            # Horizontal lines
            y = offset_y + i * (TILE_SIZE + TILE_THICKNESS)
            draw.rectangle([offset_x, y, offset_x + TOTAL_GRID_SIZE, y + TILE_THICKNESS], fill=GRID_COLOR)
            print(f"Horizontal grid line {i} drawn at y={y}.")

        # Draw the tiles on the display based on the grid
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
                    print(f"Block drawn at ({row}, {col}) with value {value}.")

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
                    print(f"Text '{text}' drawn at ({text_x}, {text_y}).")

        # Update the display with the drawn image
        disp.image(image)
        print("Debug Grid displayed successfully.")

        # Print the debug grid to the terminal
        print_debug_grid()
    except Exception as e:
        print("Error in draw_debug_grid:", e)
        traceback.print_exc(file=sys.stdout)

def draw_main_menu():
    """
    Draws the main menu screen with game rules, high score, and options.
    """
    try:
        print("Drawing Main Menu...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "2048 Game"
        rules_text = "Swipe tiles to combine\nand reach 2048!"
        high_score_text = f"High Score: {high_score}"
        start_option = "A: Start Game"
        reset_option = "B: Reset High Score"

        # Define positions with appropriate y-coordinates
        margin_top = 10  # Top margin
        spacing = 20      # Spacing between elements

        # Draw Title
        title_bbox = draw.textbbox((0, 0), title_text, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (width - title_width) / 2
        title_y = margin_top
        draw.text((title_x, title_y), title_text, font=font, fill=(255, 255, 255))
        print(f"Title '{title_text}' drawn at ({title_x}, {title_y}).")

        # Draw Rules
        rules_bbox = draw.textbbox((0, 0), rules_text, font=font)
        rules_width = rules_bbox[2] - rules_bbox[0]
        rules_height = rules_bbox[3] - rules_bbox[1]
        rules_x = (width - rules_width) / 2
        rules_y = title_y + title_height + spacing
        draw.multiline_text((rules_x, rules_y), rules_text, font=font, fill=(255, 255, 255), align="center")
        print(f"Rules drawn at ({rules_x}, {rules_y}).")

        # Draw High Score
        high_score_bbox = draw.textbbox((0, 0), high_score_text, font=font)
        high_score_width = high_score_bbox[2] - high_score_bbox[0]
        high_score_height = high_score_bbox[3] - high_score_bbox[1]
        high_score_x = (width - high_score_width) / 2
        high_score_y = rules_y + rules_height + spacing
        draw.text((high_score_x, high_score_y), high_score_text, font=font, fill=(255, 255, 255))
        print(f"High Score '{high_score_text}' drawn at ({high_score_x}, {high_score_y}).")

        # Draw Start Option
        start_bbox = draw.textbbox((0, 0), start_option, font=font)
        start_width = start_bbox[2] - start_bbox[0]
        start_height = start_bbox[3] - start_bbox[1]
        start_x = (width - start_width) / 2
        start_y = high_score_y + high_score_height + spacing
        draw.text((start_x, start_y), start_option, font=font, fill=(0, 255, 0))  # Green for Start
        print(f"Start Option '{start_option}' drawn at ({start_x}, {start_y}).")

        # Draw Reset Option
        reset_bbox = draw.textbbox((0, 0), reset_option, font=font)
        reset_width = reset_bbox[2] - reset_bbox[0]
        reset_height = reset_bbox[3] - reset_bbox[1]
        reset_x = (width - reset_width) / 2
        reset_y = start_y + start_height + spacing
        draw.text((reset_x, reset_y), reset_option, font=font, fill=(255, 0, 0))  # Red for Reset
        print(f"Reset Option '{reset_option}' drawn at ({reset_x}, {reset_y}).")

        # Update the display
        disp.image(image)
        print("Main Menu displayed successfully.")
    except Exception as e:
        print("Error in draw_main_menu:", e)
        traceback.print_exc(file=sys.stdout)

def draw_game_over_screen(won=False):
    """
    Draws the game over screen showing the result and options.
    """
    try:
        print("Drawing Game Over Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        result_text = "You Won!" if won else "Game Over!"
        high_score_text = f"High Score: {high_score}"
        restart_option = "A: Restart Game"
        main_menu_option = "B: Main Menu"

        # Define positions with appropriate y-coordinates
        margin_top = 10  # Top margin
        spacing = 20      # Spacing between elements

        # Draw Result Text
        result_bbox = draw.textbbox((0, 0), result_text, font=font)
        result_width = result_bbox[2] - result_bbox[0]
        result_height = result_bbox[3] - result_bbox[1]
        result_x = (width - result_width) / 2
        result_y = margin_top
        draw.text((result_x, result_y), result_text, font=font, fill=(255, 255, 255))
        print(f"Result text '{result_text}' drawn at ({result_x}, {result_y}).")

        # Draw High Score
        high_score_bbox = draw.textbbox((0, 0), high_score_text, font=font)
        high_score_width = high_score_bbox[2] - high_score_bbox[0]
        high_score_height = high_score_bbox[3] - high_score_bbox[1]
        high_score_x = (width - high_score_width) / 2
        high_score_y = result_y + result_height + spacing
        draw.text((high_score_x, high_score_y), high_score_text, font=font, fill=(255, 255, 255))
        print(f"High score text '{high_score_text}' drawn at ({high_score_x}, {high_score_y}).")

        # Draw Restart Option
        restart_bbox = draw.textbbox((0, 0), restart_option, font=font)
        restart_width = restart_bbox[2] - restart_bbox[0]
        restart_height = restart_bbox[3] - restart_bbox[1]
        restart_x = (width - restart_width) / 2
        restart_y = high_score_y + high_score_height + spacing
        draw.text((restart_x, restart_y), restart_option, font=font, fill=(0, 255, 0))  # Green for Restart
        print(f"Restart option '{restart_option}' drawn at ({restart_x}, {restart_y}).")

        # Draw Main Menu Option
        main_menu_bbox = draw.textbbox((0, 0), main_menu_option, font=font)
        main_menu_width = main_menu_bbox[2] - main_menu_bbox[0]
        main_menu_height = main_menu_bbox[3] - main_menu_bbox[1]
        main_menu_x = (width - main_menu_width) / 2
        main_menu_y = restart_y + restart_height + spacing
        draw.text((main_menu_x, main_menu_y), main_menu_option, font=font, fill=(255, 0, 0))  # Red for Main Menu
        print(f"Main Menu option '{main_menu_option}' drawn at ({main_menu_x}, {main_menu_y}).")

        # Update the display
        disp.image(image)
        print("Game Over Screen displayed successfully.")

        # Print the debug grid to the terminal
        print_debug_grid()
    except Exception as e:
        print("Error in draw_game_over_screen:", e)
        traceback.print_exc(file=sys.stdout)

def log_button_press(button_name):
    """
    Logs the button press to the terminal.
    """
    print(f"Button '{button_name}' pressed.")

def initialize_game():
    """
    Initializes the game by resetting the grid and adding two random tiles.
    """
    global grid, score, current_sequence_button, current_sequence_count
    grid = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    score = 0
    current_sequence_button = None
    current_sequence_count = 0
    print("Initializing game grid.")
    add_random_tile()
    add_random_tile()
    draw_debug_grid()

def handle_move(direction):
    """
    Handles the move logic based on the direction input.
    """
    global grid, score, high_score, current_state

    # Define movement functions
    def transpose(matrix):
        return [list(row) for row in zip(*matrix)]

    def reverse(matrix):
        return [row[::-1] for row in matrix]

    def compress(row):
        """Compresses the non-zero elements of the row to the left."""
        new_row = [num for num in row if num != 0]
        new_row += [0] * (GRID_SIZE - len(new_row))
        return new_row

    def merge(row):
        """Merges the row after compression."""
        global score  # Use global instead of nonlocal
        for i in range(GRID_SIZE - 1):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                row[i + 1] = 0
                score += row[i]
        return row

    def move_left():
        new_grid = []
        changed = False
        for row in grid:
            compressed_row = compress(row)
            merged_row = merge(compressed_row)
            final_row = compress(merged_row)
            new_grid.append(final_row)
            if final_row != row:
                changed = True
        return new_grid, changed, score

    # Capture the grid state before the move
    previous_grid = [row.copy() for row in grid]

    if direction == 'LEFT':
        grid, changed, move_score = move_left()
    elif direction == 'RIGHT':
        grid = reverse(grid)
        grid, changed, move_score = move_left()
        grid = reverse(grid)
    elif direction == 'UP':
        grid = transpose(grid)
        grid, changed, move_score = move_left()
        grid = transpose(grid)
    elif direction == 'DOWN':
        grid = transpose(grid)
        grid = reverse(grid)
        grid, changed, move_score = move_left()
        grid = reverse(grid)
        grid = transpose(grid)
    else:
        print(f"Invalid move direction: {direction}")
        return

    if changed:
        add_random_tile()
        draw_debug_grid()

        if score > high_score:
            high_score = score
            save_high_score(high_score)
            print(f"New high score achieved: {high_score}")

        # Check for game over conditions here
        game_state = check_game_state()
        if game_state == 'WON':
            print("Congratulations! You've reached 2048!")
            current_state = STATE_GAME_OVER
            draw_game_over_screen(won=True)
        elif game_state == 'LOST':
            print("No more moves left. Game Over!")
            current_state = STATE_GAME_OVER
            draw_game_over_screen(won=False)
    else:
        print(f"Move '{direction}' did not change the grid.")

def check_game_state():
    """
    Checks the current game state: WON, LOST, or GAME_NOT_OVER.
    """
    # Check for a winning tile
    for row in grid:
        if 2048 in row:
            return 'WON'

    # Check for any empty cells
    for row in grid:
        if 0 in row:
            return 'GAME_NOT_OVER'

    # Check for possible merges horizontally
    for row in grid:
        for i in range(len(row)-1):
            if row[i] == row[i+1]:
                return 'GAME_NOT_OVER'

    # Check for possible merges vertically
    for col in range(GRID_SIZE):
        for row in range(len(grid)-1):
            if grid[row][col] == grid[row+1][col]:
                return 'GAME_NOT_OVER'

    # No moves left
    return 'LOST'

try:
    # Initial draw of the main menu
    draw_main_menu()

    while True:
        current_time = time.time()

        if current_state == STATE_MAIN_MENU:
            # Handle Start Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Starting game.")
                current_state = STATE_GAME
                initialize_game()
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
            # Handle directional button presses

            # Handle Up Button Press
            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('UP')
                # Any non-sequence button press resets the sequence
                current_sequence_button = None
                current_sequence_count = 0
                last_press_time = current_time

            # Handle Down Button Press
            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('DOWN')
                # Any non-sequence button press resets the sequence
                current_sequence_button = None
                current_sequence_count = 0
                last_press_time = current_time

            # Handle Left Button Press
            if not buttons['left'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('LEFT')
                if current_sequence_button == 'LEFT':
                    current_sequence_count += 1
                else:
                    current_sequence_button = 'LEFT'
                    current_sequence_count = 1
                print(f"Left Button Press Count: {current_sequence_count}")
                if current_sequence_count >= SEQUENCE_THRESHOLD:
                    print("Left button pressed 16 times consecutively: Triggering Game Over (Lose).")
                    current_state = STATE_GAME_OVER
                    draw_game_over_screen(won=False)
                    # Reset sequence after triggering
                    current_sequence_button = None
                    current_sequence_count = 0
                last_press_time = current_time

            # Handle Right Button Press
            if not buttons['right'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('RIGHT')
                if current_sequence_button == 'RIGHT':
                    current_sequence_count += 1
                else:
                    current_sequence_button = 'RIGHT'
                    current_sequence_count = 1
                print(f"Right Button Press Count: {current_sequence_count}")
                if current_sequence_count >= SEQUENCE_THRESHOLD:
                    print("Right button pressed 16 times consecutively: Triggering Game Over (Win).")
                    current_state = STATE_GAME_OVER
                    draw_game_over_screen(won=True)
                    # Reset sequence after triggering
                    current_sequence_button = None
                    current_sequence_count = 0
                last_press_time = current_time

            # Handle Restart Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Restarting game.")
                current_state = STATE_GAME
                initialize_game()
                # Reset sequence upon restart
                current_sequence_button = None
                current_sequence_count = 0
                last_press_time = current_time

            # Handle Return to Main Menu (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to main menu.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                # Reset sequence when returning to main menu
                current_sequence_button = None
                current_sequence_count = 0
                last_press_time = current_time

        elif current_state == STATE_RESET_CONFIRM:
            # Any confirmation actions are already done
            # Just transition back to main menu
            current_state = STATE_MAIN_MENU
            draw_main_menu()

        elif current_state == STATE_GAME_OVER:
            # Handle Restart or Return to Main Menu

            # Handle Restart Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Restarting game.")
                current_state = STATE_GAME
                initialize_game()
                last_press_time = current_time

            # Handle Return to Main Menu (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to main menu.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                last_press_time = current_time

        # Sleep to reduce CPU usage
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Program terminated by user.")
except Exception as e:
    print("Unexpected error:", e)
    traceback.print_exc(file=sys.stdout)
