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

# Define SEQUENCE_THRESHOLD globally
SEQUENCE_THRESHOLD = 16  # Number of consecutive presses to trigger debug commands

# Initialize press counts
left_press_count = 0
right_press_count = 0

# Initialize Password VariablesP
password_input = "AAAAAAAAAA"  # Initialize to "AAAAAAAAAA"
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
    """
    Draws the main menu screen with game rules, high score, and options.
    """
    try:
        print("Drawing Main Menu...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "Modulo 2048"
        rules_text = "" #"Swipe tiles to combine\nand reach 2048!"
        high_score_text = f"High Score: {high_score}"
        start_option = "A: Start Game"
        reset_option = "B: Reset Score"

        # Define positions with appropriate y-coordinates
        margin_top = 10  # Top margin in pixels
        spacing = 20      # Spacing between elements in pixels

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
    Draws the Game Over screen indicating whether the player has won or lost.
    
    Args:
        won (bool): True if the player has won, False otherwise.
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
        print(f"High Score '{high_score_text}' drawn at ({high_score_x}, {high_score_y}).")

        # Draw Restart Option
        restart_bbox = draw.textbbox((0, 0), restart_option, font=font)
        restart_width = restart_bbox[2] - restart_bbox[0]
        restart_height = restart_bbox[3] - restart_bbox[1]
        restart_x = (width - restart_width) / 2
        restart_y = high_score_y + high_score_height + spacing
        draw.text((restart_x, restart_y), restart_option, font=font, fill=(0, 255, 0))  # Green for Restart
        print(f"Restart Option '{restart_option}' drawn at ({restart_x}, {restart_y}).")

        # Draw Main Menu Option
        main_menu_bbox = draw.textbbox((0, 0), main_menu_option, font=font)
        main_menu_width = main_menu_bbox[2] - main_menu_bbox[0]
        main_menu_height = main_menu_bbox[3] - main_menu_bbox[1]
        main_menu_x = (width - main_menu_width) / 2
        main_menu_y = restart_y + restart_height + spacing
        draw.text((main_menu_x, main_menu_y), main_menu_option, font=font, fill=(255, 0, 0))  # Red for Main Menu
        print(f"Main Menu Option '{main_menu_option}' drawn at ({main_menu_x}, {main_menu_y}).")

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

        # Define positions using percentages for better alignment
        margin_top = height * 0.05  # 5% from top
        spacing = height * 0.05  # 5% spacing
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
    """
    Draws the Password Load screen accessed from the Main Menu.
    """
    try:
        print("Drawing Password Load Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "Enter"
        subtitle_text = "password"
        prompt_text = "Password:"
        password_display = password_input  

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

        # Draw Subtitle
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
        subtitle_x = (width - subtitle_width) / 2
        subtitle_y = title_y + title_height + spacing
        draw.text((subtitle_x, subtitle_y), subtitle_text, font=font, fill=(255, 255, 255))
        print(f"Subtitle '{subtitle_text}' drawn at ({subtitle_x}, {subtitle_y}).")

        # Draw Prompt Text
        prompt_bbox = draw.textbbox((0, 0), prompt_text, font=font)
        prompt_width = prompt_bbox[2] - prompt_bbox[0]
        prompt_height = prompt_bbox[3] - prompt_bbox[1]
        prompt_x = (width - prompt_width) / 2
        prompt_y = subtitle_y + subtitle_height + spacing
        draw.text((prompt_x, prompt_y), prompt_text, font=font, fill=(255, 255, 255))
        print(f"Prompt '{prompt_text}' drawn at ({prompt_x}, {prompt_y}).")

        # Draw Password
        password_bbox = draw.textbbox((0, 0), password_display, font=font)
        password_width = password_bbox[2] - password_bbox[0]
        password_height = password_bbox[3] - password_bbox[1]
        password_x = (width - password_width) / 2
        password_y = prompt_y + prompt_height + 10  # Slight spacing before password
        draw.text((password_x, password_y), password_display, font=font, fill=(0, 255, 0))
        print(f"Password '{password_display}' drawn at ({password_x}, {password_y}).")

        # Highlight Current Selection (if applicable)
        # Assuming you have a mechanism to highlight the current character
        # Here's a simple example for highlighting the first character
        # You can modify this based on your implementation
        if 0 <= current_selection < len(password_display):
            selected_char_x = password_x + (current_selection * (password_width / len(password_display)))
            selected_char_y = password_y
            draw.rectangle(
                [
                    selected_char_x - 2,
                    selected_char_y - 2,
                    selected_char_x + (password_width / len(password_display)) + 2,
                    selected_char_y + password_height + 2
                ],
                outline=(255, 0, 0),
                width=2
            )
            print(f"Current selection highlighted at index {current_selection}.")

        # Update the display
        disp.image(image)
        print("Password Load Screen displayed successfully.")
    except Exception as e:
        print("Error in draw_password_load_screen:", e)
        traceback.print_exc(file=sys.stdout)

def draw_password_save_screen():
    """
    Draws the Password Save screen accessed during gameplay.
    """
    try:
        print("Drawing Password Save Screen...")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define text content
        title_text = "Save Game"
        prompt_text = "Password:"
        password_display = password_input  # Should be the generated password

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

        # Draw Prompt Text
        prompt_bbox = draw.textbbox((0, 0), prompt_text, font=font)
        prompt_width = prompt_bbox[2] - prompt_bbox[0]
        prompt_height = prompt_bbox[3] - prompt_bbox[1]
        prompt_x = (width - prompt_width) / 2
        prompt_y = title_y + title_height + spacing
        draw.text((prompt_x, prompt_y), prompt_text, font=font, fill=(255, 255, 255))
        print(f"Prompt '{prompt_text}' drawn at ({prompt_x}, {prompt_y}).")

        # Draw Password
        password_bbox = draw.textbbox((0, 0), password_display, font=font)
        password_width = password_bbox[2] - password_bbox[0]
        password_height = password_bbox[3] - password_bbox[1]
        password_x = (width - password_width) / 2
        password_y = prompt_y + prompt_height + 10  # Slight spacing before password
        draw.text((password_x, password_y), password_display, font=font, fill=(0, 255, 0))
        print(f"Password '{password_display}' drawn at ({password_x}, {password_y}).")

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

def draw_error_message(message):
    """
    Draws an error message on the screen.
    
    Args:
        message (str): The error message to display.
    """
    try:
        print(f"Displaying error message: {message}")
        # Clear the background
        draw.rectangle((0, 0, width, height), outline=0, fill=BACKGROUND_COLOR)
        print("Background cleared.")

        # Define positions
        margin_top = (height - 40) / 2  # Center vertically for a 40-pixel high box
        box_height = 40
        box_width = len(message) * 10  # Approximate width based on message length
        box_x = (width - box_width) / 2
        box_y = margin_top

        # Draw a semi-transparent rectangle as a backdrop for the message
        draw.rectangle(
            [box_x - 10, box_y - 10, box_x + box_width + 10, box_y + box_height + 10],
            fill=(50, 50, 50)
        )
        print(f"Error box drawn at ({box_x - 10}, {box_y - 10}) to ({box_x + box_width + 10}, {box_y + box_height + 10}).")

        # Draw the error message text
        message_bbox = draw.textbbox((0, 0), message, font=font)
        message_width = message_bbox[2] - message_bbox[0]
        message_height = message_bbox[3] - message_bbox[1]
        message_x = (width - message_width) / 2
        message_y = box_y + (box_height - message_height) / 2
        draw.text((message_x, message_y), message, font=font, fill=(255, 0, 0))  # Red color for errors
        print(f"Error message '{message}' drawn at ({message_x}, {message_y}).")

        # Update the display
        disp.image(image)
        print(f"Error message '{message}' displayed successfully.")

        # Wait for a short duration before returning to the previous screen
        time.sleep(2)  # Display the message for 2 seconds

        # After displaying the message, return to the appropriate state
        if current_state == STATE_PASSWORD_LOAD:
            draw_password_load_screen()
        elif current_state == STATE_PASSWORD_SAVE:
            draw_password_save_screen()
        else:
            draw_main_menu()
    except Exception as e:
        print("Error in draw_error_message:", e)
        traceback.print_exc(file=sys.stdout)


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
    password_input = "AAAAAAAAAA"  # Reset to initial password
    current_selection = 0
    print("Initializing game grid.")
    add_random_tile()
    add_random_tile()
    draw_debug_grid()

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
                try:
                    print("Button B pressed: Reset high score.")
                    current_state = STATE_RESET_CONFIRM
                    # Reset high score and redraw main menu
                    high_score = 0
                    save_high_score(high_score)
                    print("High score reset to 0.")
                    draw_main_menu()
                    last_press_time = current_time
                except Exception as e:
                    print("Error resetting high score:", e)
                    traceback.print_exc(file=sys.stdout)

            # Handle Password Load (Button C from Main Menu)
            if not buttons['C'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button C pressed: Entering Password Load Mode.")
                current_state = STATE_PASSWORD_LOAD
                password_input = "AAAAAAAAAA"  
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
                # Generate the password before drawing the screen
                password_input = encoder.save_board_to_password(np.array(grid))
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
                try:
                    print("Button B pressed: Returning to main menu.")
                    current_state = STATE_MAIN_MENU
                    draw_main_menu()
                    # Reset press counters when returning to main menu
                    left_press_count = 0
                    right_press_count = 0
                    last_press_time = current_time
                except Exception as e:
                    print("Error returning to main menu:", e)
                    traceback.print_exc(file=sys.stdout)

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
                try:
                    print("Button B pressed: Returning to main menu.")
                    current_state = STATE_MAIN_MENU
                    draw_main_menu()
                    last_press_time = current_time
                except Exception as e:
                    print("Error returning to main menu:", e)
                    traceback.print_exc(file=sys.stdout)

        elif current_state == STATE_PASSWORD_LOAD:
            # Handle Up Button Press
            if not buttons['up'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                scroll_password(direction='UP')
                draw_password_load_screen()
                last_press_time = current_time

            # Handle Down Button Press
            if not buttons['down'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                scroll_password(direction='DOWN')
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
                        if np.any(loaded_board == 2048):
                            print("Invalid password. Board contains tile 2048.")
                            draw_error_message("Invalid Password!")
                            # Return to Password Load screen to allow user to enter a new password
                            current_state = STATE_PASSWORD_LOAD
                            draw_password_load_screen()
                        else:
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
                        draw_error_message("Invalid Password!")
                        current_state = STATE_MAIN_MENU
                        draw_main_menu()
                    finally:
                        last_press_time = current_time
                else:
                    print("Incomplete password. Please enter a 10-character password.")
                    draw_error_message("Incomplete Password!")
                    last_press_time = current_time
                        
            # Handle Cancel (Button B to return to Main Menu)
            elif not buttons['B'].value and (current_time - last_press_time) > DEBOUNCE_TIME:
                print("Button B pressed: Returning to Main Menu from Password Input Screen.")
                current_state = STATE_MAIN_MENU
                draw_main_menu()
                last_press_time = current_time

        elif current_state == STATE_PASSWORD_SAVE:
            # In Password Save screen, handle confirm and cancel
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
