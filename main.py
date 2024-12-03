# main.py

import time
import random
from PIL import Image, ImageDraw, ImageFont
import hardware_setup  # Import the hardware setup
import os  # For high score persistence
import traceback
from _pass import BoardEncoder  # Import BoardEncoder from _pass.py
import numpy as np
import sys  # For exception tracing

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
STATE_HOW_TO_PLAY = 'HOW_TO_PLAY'
STATE_GAME = 'GAME'
STATE_RESET_CONFIRM = 'RESET_CONFIRM'
STATE_GAME_OVER = 'GAME_OVER'
STATE_PASSWORD_LOAD = 'PASSWORD_LOAD'
STATE_PASSWORD_SAVE = 'PASSWORD_SAVE'

# Initialize the current state
current_state = STATE_MAIN_MENU
print(f"Initial State: {current_state}")

# Define other global variables
encoder = BoardEncoder()

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
    0: EMPTY_TILE_COLOR,  # Empty tiles
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

# Initialize press counts
left_press_count = 0
right_press_count = 0

# Initialize Password Variables
password_input = ""
current_selection = 0  # Index for password input (0 to 9)

# Helper Functions
def add_random_tile():
    """
    Adds a random tile (2 or 4) to an empty spot on the board.
    """
    empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if grid[i][j] == 0]
    if not empty_cells:
        return
    i, j = random.choice(empty_cells)
    grid[i][j] = random.choice([2, 4])
    print(f"Added tile {grid[i][j]} at position ({i}, {j}).")

def print_debug_grid():
    """
    Prints the current grid state and scores to the terminal for debugging.
    """
    print("\nCurrent Grid State:")
    for row in grid:
        print("+------+------+------+------+")  # Adjust based on grid drawing
        print("|", end="")
        for cell in row:
            if cell == 0:
                print(f" {'.':<4}|", end="")  # Represent empty cells with '.'
            else:
                print(f" {cell:<4}|", end="")
        print()
    print("+------+------+------+------+")
    print(f"Score: {score}  High Score: {high_score}\n")

def draw_debug_grid():
    """
    Draws the grid and tiles on the display.
    """
    try:
        print("Drawing Debug Grid...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Draw Grid Lines
        for i in range(GRID_SIZE + 1):
            # Horizontal lines
            draw.line(
                (offset_x, offset_y + i * (TILE_SIZE + TILE_THICKNESS),
                 offset_x + TOTAL_GRID_SIZE, offset_y + i * (TILE_SIZE + TILE_THICKNESS)),
                fill=GRID_COLOR, width=TILE_THICKNESS
            )
            # Vertical lines
            draw.line(
                (offset_x + i * (TILE_SIZE + TILE_THICKNESS), offset_y,
                 offset_x + i * (TILE_SIZE + TILE_THICKNESS), offset_y + TOTAL_GRID_SIZE),
                fill=GRID_COLOR, width=TILE_THICKNESS
            )

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Draw Tiles
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                value = grid[i][j]
                if value != 0:
                    # Determine tile position
                    x1 = offset_x + j * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                    y1 = offset_y + i * (TILE_SIZE + TILE_THICKNESS) + TILE_THICKNESS
                    x2 = x1 + TILE_SIZE
                    y2 = y1 + TILE_SIZE
                    tile_color = TILE_COLORS.get(value, (60, 58, 50))  # Default color if value not found
                    draw.rectangle([x1, y1, x2, y2], fill=tile_color)
                    # Draw the number on the tile
                    text = str(value)
                    text_x = x1 + (TILE_SIZE - len(text) * average_char_width) / 2
                    text_y = y1 + (TILE_SIZE - average_char_height) / 2
                    draw.text((text_x, text_y), text, font=font, fill=TEXT_COLOR)
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
    global high_score  # Ensure high_score is accessible
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
        password_option = "C: Load Password"

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Define positions
        margin_top = 10
        spacing = 20
        current_y = margin_top

        # Draw Title
        title_x = (width - len(title_text) * average_char_width) / 2
        draw.text((title_x, current_y), title_text, font=font, fill=(255, 255, 255))
        print(f"Title '{title_text}' drawn at ({title_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Rules
        lines = rules_text.split('\n')
        for line in lines:
            line_x = (width - len(line) * average_char_width) / 2
            draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255))
            print(f"Instruction '{line}' drawn at ({line_x}, {current_y}).")
            current_y += average_char_height + 5  # Small spacing between lines
        current_y += spacing

        # Draw High Score
        high_score_x = (width - len(high_score_text) * average_char_width) / 2
        draw.text((high_score_x, current_y), high_score_text, font=font, fill=(255, 255, 255))
        print(f"High Score '{high_score_text}' drawn at ({high_score_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Start Option
        start_x = (width - len(start_option) * average_char_width) / 2
        draw.text((start_x, current_y), start_option, font=font, fill=(0, 255, 0))  # Green for Start
        print(f"Start Option '{start_option}' drawn at ({start_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Reset Option
        reset_x = (width - len(reset_option) * average_char_width) / 2
        draw.text((reset_x, current_y), reset_option, font=font, fill=(255, 0, 0))  # Red for Reset
        print(f"Reset Option '{reset_option}' drawn at ({reset_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Password Option
        password_x = (width - len(password_option) * average_char_width) / 2
        draw.text((password_x, current_y), password_option, font=font, fill=(0, 0, 255))  # Blue for Password
        print(f"Password Option '{password_option}' drawn at ({password_x}, {current_y}).")

        # Update the display
        disp.image(image)
        print("Main Menu displayed successfully.")
    except Exception as e:
        print("Error in draw_main_menu:", e)
        traceback.print_exc(file=sys.stdout)

def draw_game_over_screen(won=False):
    global high_score  # Ensure high_score is accessible
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

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Define positions
        margin_top = 10
        spacing = 20
        current_y = margin_top

        # Draw Result Text
        result_x = (width - len(result_text) * average_char_width) / 2
        draw.text((result_x, current_y), result_text, font=font, fill=(255, 255, 255))
        print(f"Result text '{result_text}' drawn at ({result_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw High Score
        high_score_x = (width - len(high_score_text) * average_char_width) / 2
        draw.text((high_score_x, current_y), high_score_text, font=font, fill=(255, 255, 255))
        print(f"High score text '{high_score_text}' drawn at ({high_score_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Restart Option
        restart_x = (width - len(restart_option) * average_char_width) / 2
        draw.text((restart_x, current_y), restart_option, font=font, fill=(0, 255, 0))  # Green for Restart
        print(f"Restart option '{restart_option}' drawn at ({restart_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Main Menu Option
        main_menu_x = (width - len(main_menu_option) * average_char_width) / 2
        draw.text((main_menu_x, current_y), main_menu_option, font=font, fill=(255, 0, 0))  # Red for Main Menu
        print(f"Main Menu option '{main_menu_option}' drawn at ({main_menu_x}, {current_y}).")

        # Update the display
        disp.image(image)
        print("Game Over Screen displayed successfully.")
    except Exception as e:
        print("Error in draw_game_over_screen:", e)
        traceback.print_exc(file=sys.stdout)

def draw_how_to_play():
    try:
        print("Drawing How to Play Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "How to Play"
        instructions = [
            "Use the 4-way joystick to move the tiles.",
            "Button A: Reset the board.",
            "Button B: Return to Main Menu.",
            "Button C: Save/Load using Password."
        ]

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Define positions
        margin_top = 10
        spacing = 20
        current_y = margin_top

        # Draw Title
        title_x = (width - len(title_text) * average_char_width) / 2
        draw.text((title_x, current_y), title_text, font=font, fill=(255, 255, 255))
        print(f"Title '{title_text}' drawn at ({title_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Instructions
        for line in instructions:
            line_x = (width - len(line) * average_char_width) / 2
            draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255))
            print(f"Instruction '{line}' drawn at ({line_x}, {current_y}).")
            current_y += average_char_height + 5  # Small spacing between lines

        # Update the display
        disp.image(image)
        print("How to Play Screen displayed successfully.")
    except Exception as e:
        print("Error in draw_how_to_play:", e)
        traceback.print_exc(file=sys.stdout)

def draw_password_load_screen():
    global password_input, current_selection
    """
    Draws the Password Load screen accessed from the Main Menu.
    """
    try:
        print("Drawing Password Load Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "Load Game via Password"
        instructions = [
            "Use Up/Down to change character.",
            "Use Left/Right to navigate positions.",
            "Press C to confirm.",
            "Press C again to cancel."
        ]

        # Ensure password_input is 10 characters
        if len(password_input) < 10:
            password_input += encoder.CHARSET[0] * (10 - len(password_input))
        current_password = password_input

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Define positions
        margin_top = 10
        spacing = 20
        current_y = margin_top

        # Draw Title
        title_x = (width - len(title_text) * average_char_width) / 2
        draw.text((title_x, current_y), title_text, font=font, fill=(255, 255, 255))
        print(f"Title '{title_text}' drawn at ({title_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Instructions
        for line in instructions:
            line_x = (width - len(line) * average_char_width) / 2
            draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255))
            print(f"Instruction '{line}' drawn at ({line_x}, {current_y}).")
            current_y += average_char_height + 5  # Small spacing between lines

        # Draw Current Password
        password_text = "Password: " + ''.join(current_password)
        password_x = (width - len(password_text) * average_char_width) / 2
        draw.text((password_x, current_y + 20), password_text, font=font, fill=(0, 255, 0))
        print(f"Password '{password_text}' drawn at ({password_x}, {current_y + 20}).")

        # Highlight Current Selection
        # Calculate position of current character
        char_width = average_char_width
        char_x_start = password_x + len("Password: ") * char_width
        char_y = current_y + 20
        char_x = char_x_start + (current_selection * char_width)
        draw.rectangle([char_x - 2, char_y - 2, char_x + char_width, char_y + average_char_height - 8], outline=(255, 0, 0), width=2)
        print(f"Current selection highlighted at index {current_selection}.")

        # Update the display
        disp.image(image)
        print("Password Load Screen displayed successfully.")
    except Exception as e:
        print("Error in draw_password_load_screen:", e)
        traceback.print_exc(file=sys.stdout)

def draw_password_save_screen():
    global password_input
    """
    Draws the Password Save screen accessed during gameplay.
    """
    try:
        print("Drawing Password Save Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "Save Game via Password"
        instructions = [
            "Press C to confirm.",
            "Press C again to cancel."
        ]

        # Encode current board to password
        password_input = encoder.save_board_to_password(np.array(grid))
        current_password = password_input
        print(f"Board saved as password: {current_password}")

        # Approximate character width and height
        average_char_width = 8
        average_char_height = 20

        # Define positions
        margin_top = 10
        spacing = 20
        current_y = margin_top

        # Draw Title
        title_x = (width - len(title_text) * average_char_width) / 2
        draw.text((title_x, current_y), title_text, font=font, fill=(255, 255, 255))
        print(f"Title '{title_text}' drawn at ({title_x}, {current_y}).")
        current_y += average_char_height + spacing

        # Draw Instructions
        for line in instructions:
            line_x = (width - len(line) * average_char_width) / 2
            draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255))
            print(f"Instruction '{line}' drawn at ({line_x}, {current_y}).")
            current_y += average_char_height + 5  # Small spacing between lines

        # Draw Generated Password
        password_text = "Password: " + ''.join(current_password)
        password_x = (width - len(password_text) * average_char_width) / 2
        draw.text((password_x, current_y + 20), password_text, font=font, fill=(0, 255, 0))
        print(f"Password '{password_text}' drawn at ({password_x}, {current_y + 20}).")

        # Update the display
        disp.image(image)
        print("Password Save Screen displayed successfully.")
    except Exception as e:
        print("Error in draw_password_save_screen:", e)
        traceback.print_exc(file=sys.stdout)

def scroll_password(direction='UP'):
    """
    Scroll through the charset to change a character in the password.

    Args:
        direction (str): 'UP' to increment, 'DOWN' to decrement.

    Returns:
        str: Updated password string.
    """
    global password_input, current_selection
    # Ensure password is 10 characters
    if len(password_input) < 10:
        password_input += encoder.CHARSET[0] * (10 - len(password_input))

    # Update the current character based on direction
    current_char = password_input[current_selection]
    char_index = encoder.CHARSET.index(current_char)

    if direction == 'UP':
        char_index = (char_index + 1) % encoder.BASE
    elif direction == 'DOWN':
        char_index = (char_index - 1) % encoder.BASE

    # Replace the character in the password
    new_password = list(password_input)
    new_password[current_selection] = encoder.CHARSET[char_index]
    password_input = ''.join(new_password)

    print(f"Password updated: {password_input}")
    return password_input

def calculate_score_from_board(board):
    """
    Calculates the score based on the board state.

    Args:
        board (numpy.ndarray): 4x4 board.

    Returns:
        int: Calculated score.
    """
    # Example: Sum of all tile values
    return int(np.sum(board))

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

def initialize_game():
    """
    Initializes the game by resetting the grid and adding two random tiles.
    """
    global grid, score, left_press_count, right_press_count, password_input, current_selection
    grid = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ]
    score = 0
    left_press_count = 0
    right_press_count = 0
    password_input = ""
    current_selection = 0
    print("Initializing game grid.")
    add_random_tile()
    add_random_tile()
    draw_debug_grid()

def log_button_press(button_name):
    """
    Logs the button press to the terminal.
    """
    print(f"Button '{button_name}' pressed.")

# Main Game Loop
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

            # Handle Password Load (Button C from Main Menu)
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button C pressed: Entering Password Load Mode.")
                current_state = STATE_PASSWORD_LOAD
                password_input = ""
                current_selection = 0
                draw_password_load_screen()
                last_press_time = current_time

        elif current_state == STATE_HOW_TO_PLAY:
            # Handle Return to Main Menu (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to Main Menu.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                last_press_time = current_time

        elif current_state == STATE_GAME:
            # Handle directional button presses

            # Handle Up Button Press
            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('UP')
                # Any non-sequence button press resets the sequence
                left_press_count = 0
                right_press_count = 0
                last_press_time = current_time

            # Handle Down Button Press
            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('DOWN')
                # Any non-sequence button press resets the sequence
                left_press_count = 0
                right_press_count = 0
                last_press_time = current_time

            # Handle Left Button Press
            if not buttons['left'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('LEFT')
                left_press_count += 1  # Increment left press counter
                print(f"Left Button Press Count: {left_press_count}")
                if left_press_count >= SEQUENCE_THRESHOLD:
                    print("Left button pressed 16 times: Triggering Game Over (Lose).")
                    current_state = STATE_GAME_OVER
                    draw_game_over_screen(won=False)
                last_press_time = current_time

            # Handle Right Button Press
            if not buttons['right'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                handle_move('RIGHT')
                right_press_count += 1  # Increment right press counter
                print(f"Right Button Press Count: {right_press_count}")
                if right_press_count >= SEQUENCE_THRESHOLD:
                    print("Right button pressed 16 times: Triggering Game Over (Win).")
                    current_state = STATE_GAME_OVER
                    draw_game_over_screen(won=True)
                last_press_time = current_time

            # Handle Password Save (Button C during Game)
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button C pressed: Entering Password Save Mode.")
                current_state = STATE_PASSWORD_SAVE
                draw_password_save_screen()
                last_press_time = current_time

            # Handle Restart Game (Button A)
            if not buttons['A'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button A pressed: Restarting game.")
                current_state = STATE_GAME
                initialize_game()
                # Reset press counters upon restart
                left_press_count = 0
                right_press_count = 0
                last_press_time = current_time

            # Handle Return to Main Menu (Button B)
            if not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to main menu.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                # Reset press counters when returning to main menu
                left_press_count = 0
                right_press_count = 0
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

        elif current_state == STATE_PASSWORD_LOAD:
            # Handle Up Button Press
            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                password_input = scroll_password(direction='UP')
                draw_password_load_screen()
                last_press_time = current_time

            # Handle Down Button Press
            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                password_input = scroll_password(direction='DOWN')
                draw_password_load_screen()
                last_press_time = current_time

            # Handle Left Button Press to move selection left
            if not buttons['left'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                current_selection = (current_selection - 1) % 10
                print(f"Password character selection moved to index {current_selection}.")
                draw_password_load_screen()
                last_press_time = current_time

            # Handle Right Button Press to move selection right
            if not buttons['right'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                current_selection = (current_selection + 1) % 10
                print(f"Password character selection moved to index {current_selection}.")
                draw_password_load_screen()
                last_press_time = current_time

            # Handle Confirm (Button C)
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                if len(password_input) == 10:
                    print(f"Password entered: {password_input}")
                    try:
                        loaded_number = encoder.decode(password_input)
                        loaded_board = encoder.number_to_board(loaded_number)
                        # Update the game grid
                        grid = loaded_board.tolist()  # Convert numpy array to list
                        # Update the score appropriately
                        score = calculate_score_from_board(loaded_board)
                        print("Board loaded from password.")
                        # Transition back to game
                        current_state = STATE_GAME
                        draw_debug_grid()
                    except Exception as e:
                        print("Invalid password. Could not load board.")
                        # Optionally, display an error message
                        # For simplicity, return to main menu
                        current_state = STATE_MAIN_MENU
                        draw_main_menu()
                    finally:
                        last_press_time = current_time
                else:
                    print("Incomplete password. Please enter a 10-character password.")
                    # Optionally, display an error message
                    last_press_time = current_time

            # Handle Cancel (Pressing C again without confirming)
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Password operation canceled.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                last_press_time = current_time

        elif current_state == STATE_PASSWORD_SAVE:
            # In Password Save screen, only handle confirm and cancel
            # Pressing C confirms the save
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Password Save confirmed.")
                current_state = STATE_GAME
                draw_debug_grid()
                last_press_time = current_time

            # Pressing C again cancels the save
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Password Save canceled.")
                current_state = STATE_GAME
                draw_debug_grid()
                last_press_time = current_time

        # Sleep to reduce CPU usage
        time.sleep(0.05)

except KeyboardInterrupt:
    print("Program terminated by user.")
except Exception as e:
    print("Unexpected error:", e)
    traceback.print_exc(file=sys.stdout)
