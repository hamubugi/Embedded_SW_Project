# test_pass.py

import sys
import traceback
from _pass import BoardEncoder

def test_board_encoding_decoding():
    encoder = BoardEncoder()
    test_boards = []

    # Test board 1: Empty board
    board1 = [
        [{'value': 0, 'type': 'empty'} for _ in range(4)] for _ in range(4)
    ]
    test_boards.append(('Empty Board', board1))

    # Test board 2: Normal tiles only
    board2 = [
        [{'value': 2 ** ((i * 4 + j) % 11 + 1), 'type': 'normal'} for j in range(4)] for i in range(4)
    ]
    test_boards.append(('Normal Tiles Board', board2))

    # Test board 3: Modulo tiles only
    modulo_values = [2, 4, 8, 16, 32]
    board3 = [
        [{'value': modulo_values[(i * 4 + j) % 5], 'type': 'modulo'} for j in range(4)] for i in range(4)
    ]
    test_boards.append(('Modulo Tiles Board', board3))

    # Test board 4: Mixed normal and modulo tiles
    board4 = [
        [{'value': (2 ** ((i * 4 + j) % 11 + 1)) if (i + j) % 2 == 0 else modulo_values[(i * 4 + j) % 5],
        'type': 'normal' if (i + j) % 2 == 0 else 'modulo'}
        for j in range(4)] for i in range(4)
    ]

    test_boards.append(('Mixed Tiles Board', board4))

    # Test board 5: Winning board with 2048 tile
    board5 = [
        [{'value': 0, 'type': 'empty'} for _ in range(4)] for _ in range(4)
    ]
    board5[0][0] = {'value': 2048, 'type': 'normal'}
    test_boards.append(('Winning Board', board5))

    # Run tests
    for name, board in test_boards:
        print(f"Testing: {name}")
        try:
            # Encode the board to a password
            password = encoder.save_board_to_password(board)
            print(f"Encoded Password: {password}")

            # Decode the password back to a board
            decoded_number = encoder.decode(password)
            decoded_board = encoder.number_to_board(decoded_number)

            # Check if the original board and decoded board are the same
            if boards_are_equal(board, decoded_board):
                print("Success: Decoded board matches the original board.\n")
            else:
                print("Failure: Decoded board does not match the original board.")
                print("Original Board:")
                print_board(board)
                print("Decoded Board:")
                print_board(decoded_board)
                print()
        except Exception as e:
            print(f"Error during testing: {e}")
            traceback.print_exc(file=sys.stdout)
            print()

def boards_are_equal(board1, board2):
    for i in range(4):
        for j in range(4):
            tile1 = board1[i][j]
            tile2 = board2[i][j]
            if tile1 != tile2:
                return False
    return True

def print_board(board):
    for row in board:
        row_str = ''
        for tile in row:
            tile_type = 'M' if tile['type'] == 'modulo' else 'N' if tile['type'] == 'normal' else 'E'
            row_str += f"{tile['value']}{tile_type}\t"
        print(row_str)
    print()

if __name__ == '__main__':
    test_board_encoding_decoding()
