import random
import numpy as np

# _pass.py

import numpy as np

class BoardEncoder:
    def __init__(self):
        self.CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        self.BASE = len(self.CHARSET)
        
        # Define tile mappings
        self.TILE_VALUES = [
            (0, 'empty'),        # 0
            (2, 'normal'),       # 1
            (4, 'normal'),       # 2
            (8, 'normal'),       # 3
            (16, 'normal'),      # 4
            (32, 'normal'),      # 5
            (64, 'normal'),      # 6
            (128, 'normal'),     # 7
            (256, 'normal'),     # 8
            (512, 'normal'),     # 9
            (1024, 'normal'),    # 10
            (2048, 'normal'),    # 11
            (2, 'modulo'),       # 12
            (4, 'modulo'),       # 13
            (8, 'modulo'),       # 14
            (16, 'modulo'),      # 15
            (32, 'modulo'),      # 16
        ]
        self.MAX_TILE_INDEX = len(self.TILE_VALUES) - 1

    def encode(self, number):
        """Encodes a number to a password string."""
        if number == 0:
            return self.CHARSET[0]
        chars = []
        while number > 0:
            number, remainder = divmod(number, self.BASE)
            chars.append(self.CHARSET[remainder])
        return ''.join(reversed(chars)).rjust(10, self.CHARSET[0])  # Ensure length is 10

    def decode(self, password):
        """Decodes a password string to a number."""
        number = 0
        for char in password:
            number = number * self.BASE + self.CHARSET.index(char)
        return number

    def board_to_number(self, board):
        """Converts a board to a number."""
        number = 0
        for row in board:
            for cell in row:
                tile_tuple = (cell['value'], cell['type'])
                try:
                    tile_index = self.TILE_VALUES.index(tile_tuple)
                except ValueError:
                    raise ValueError(f"Tile {tile_tuple} is not in TILE_VALUES.")
                number = number * (self.MAX_TILE_INDEX + 1) + tile_index
        return number

    def number_to_board(self, number):
        """Converts a number back to a board."""
        board = []
        for _ in range(4):
            row = []
            for _ in range(4):
                tile_index = number % (self.MAX_TILE_INDEX + 1)
                number = number // (self.MAX_TILE_INDEX + 1)
                if tile_index > self.MAX_TILE_INDEX:
                    raise ValueError(f"Invalid tile index {tile_index}.")
                value, tile_type = self.TILE_VALUES[tile_index]
                row.insert(0, {'value': value, 'type': tile_type})
            board.insert(0, row)
        return board

    def save_board_to_password(self, board):
        """Encodes the board into a password string."""
        board_number = self.board_to_number(board)
        password = self.encode(board_number)
        return password
