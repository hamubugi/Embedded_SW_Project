# test_logic.py
import logic

# Test case where the game is lost
lost_grid = [
    [2, 4, 2, 4],
    [4, 2, 4, 2],
    [2, 4, 2, 4],
    [4, 2, 4, 2]
]

state = logic.get_current_state(lost_grid)
print(f"Test Grid State: {state}")  # Expected: 'LOST'
