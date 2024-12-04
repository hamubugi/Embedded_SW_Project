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

    def save_board_to_password(self, board):
        """
        Convenience method to convert a board directly to a password

        Args:
            board (numpy.ndarray): 4x4 board with tile values

        Returns:
            str: 10-character encoded password
        """
        board_number = self.board_to_number(board)
        return self.encode(board_number)

# Function to get user input and generate password
def input_tiles_and_generate_password():
    encoder = BoardEncoder()
    valid_tiles = encoder.TILE_VALUES
    tile_values = []

    print("Please input 16 tile values for the board.")
    print(f"Valid tile values are: {valid_tiles}")

    while len(tile_values) < 16:
        try:
            value = int(input(f"Enter tile value for position {len(tile_values)+1}: "))
            if value in valid_tiles:
                tile_values.append(value)
            else:
                print(f"Invalid tile value. Please enter one of {valid_tiles}.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

    board = np.array(tile_values).reshape((4, 4))
    password = encoder.save_board_to_password(board)

    print("\nGenerated Board:")
    print(board)
    print(f"\nEncoded Password: {password}")

# Run the function
if __name__ == "__main__":
    input_tiles_and_generate_password()
