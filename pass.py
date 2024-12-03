import random
import numpy as np

class BoardEncoder:
    def __init__(self):
        self.CHARSET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        self.BASE = len(self.CHARSET)
        # Tile values from 2^1 to 2^10
        self.TILE_VALUES = [2**i for i in range(1, 11)]

    def board_to_number(self, board):
        """
        Convert a 4x4 board to a unique number
        
        Args:
            board (numpy.ndarray): 4x4 board with values from 2^1 to 2^10
        
        Returns:
            int: Unique number representation of the board
        """
        number = 0
        for row in board:
            for cell in row:
                # Find the index of the cell value in TILE_VALUES
                tile_index = self.TILE_VALUES.index(cell)
                # Shift and add
                number = number * len(self.TILE_VALUES) + tile_index
        return number

    def number_to_board(self, number):
        """
        Reconstruct a board from a unique number
        
        Args:
            number (int): Unique number representation of the board
        
        Returns:
            numpy.ndarray: 4x4 board with values from 2^1 to 2^10
        """
        board = np.zeros((4, 4), dtype=int)
        for i in range(3, -1, -1):
            for j in range(3, -1, -1):
                # Get the tile index
                tile_index = number % len(self.TILE_VALUES)
                # Convert index back to tile value
                board[i, j] = self.TILE_VALUES[tile_index]
                # Shift number
                number //= len(self.TILE_VALUES)
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