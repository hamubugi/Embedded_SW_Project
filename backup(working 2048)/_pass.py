import random
import numpy as np

# _pass.py

import numpy as np

# _pass.py

import numpy as np

class BoardEncoder:
    def __init__(self):
        self.CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        self.TILE_VALUES = [0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]  # Include 0
        self.BASE = len(self.CHARSET)

    def board_to_number(self, board):
        number = 0
        total_tiles = len(self.TILE_VALUES)
        for cell in board.flatten():
            tile_index = self.TILE_VALUES.index(cell)
            number = number * total_tiles + tile_index
        return number

    def number_to_board(self, number):
        indices = []
        total_tiles = len(self.TILE_VALUES)
        while len(indices) < 16:
            indices.append(number % total_tiles)
            number = number // total_tiles
        indices.reverse()
        board = np.array([self.TILE_VALUES[index] for index in indices])
        return board.reshape((4, 4))

    def encode(self, number):
        chars = []
        while number > 0:
            chars.append(self.CHARSET[number % self.BASE])
            number = number // self.BASE
        # Pad the password to ensure it is always 10 characters long
        while len(chars) < 10:
            chars.append(self.CHARSET[0])
        return ''.join(reversed(chars))

    def decode(self, password):
        number = 0
        for char in password:
            number = number * self.BASE + self.CHARSET.index(char)
        return number

    def save_board_to_password(self, board):
        board_number = self.board_to_number(board)
        password = self.encode(board_number)
        return password

    def load_board_from_password(self, password):
        board_number = self.decode(password)
        board = self.number_to_board(board_number)
        return board


    def encode(self, number):
        """
        Encode a number to a 10-character password
        
        Args:
            number (int): Number to encode
        
        Returns:
            str: 10-character encoded password
        """
        if number < 0:
            return None
        
        encoded = []
        while number > 0 and len(encoded) < 10:
            number, remainder = divmod(number, self.BASE)
            encoded.append(self.CHARSET[remainder])
        
        # Pad with first character if needed
        while len(encoded) < 10:
            encoded.append(self.CHARSET[0])
        
        return ''.join(reversed(encoded))

    def decode(self, code):
        """
        Decode a 10-character password to a number
        
        Args:
            code (str): 10-character encoded password
        
        Returns:
            int: Decoded number
        """
        number = 0
        for char in code:
            number = number * self.BASE + self.CHARSET.index(char)
        return number

    def generate_filled_board(self):
        """
        Generate a random 4x4 board filled with values from 2^1 to 2^10
        
        Returns:
            numpy.ndarray: 4x4 board with unique values
        """
        # Create a list of 16 unique values
        board_values = random.sample(self.TILE_VALUES * 2, 16)
        
        # Reshape into 4x4 board
        board = np.array(board_values).reshape((4, 4))
        
        return board

    def save_board_to_password(self, board):
        """
        Convenience method to convert a board directly to a password
        
        Args:
            board (numpy.ndarray): 4x4 board with values from 2^1 to 2^10
        
        Returns:
            str: 10-character encoded password
        """
        board_number = self.board_to_number(board)
        return self.encode(board_number)

    def load_board_from_password(self, password):
        """
        Convenience method to convert a password directly to a board
        
        Args:
            password (str): 10-character encoded password
        
        Returns:
            numpy.ndarray: 4x4 board with values from 2^1 to 2^10
        """
        board_number = self.decode(password)
        return self.number_to_board(board_number)

# Optional: Pre-calculate total possible combinations
#TOTAL_COMBINATIONS = len([2**i for i in range(1, 11)]) ** 16