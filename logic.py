# logic.py

import random

def start_game():
    mat = []
    for i in range(4):
        mat.append([0] * 4)

    add_new_2(mat)
    add_new_2(mat)
    return mat

def add_new_2(mat):
    empty_cells = [(i, j) for i in range(4) for j in range(4) if mat[i][j] == 0]
    if not empty_cells:
        return
    r, c = random.choice(empty_cells)
    mat[r][c] = 2

def get_current_state(mat):
    for row in mat:
        if 2048 in row:
            return 'WON'
    for row in mat:
        if 0 in row:
            return 'GAME NOT OVER'
    for i in range(4):
        for j in range(4):
            if j < 3 and mat[i][j] == mat[i][j + 1]:
                return 'GAME NOT OVER'
            if i < 3 and mat[i][j] == mat[i + 1][j]:
                return 'GAME NOT OVER'
    return 'LOST'

def compress(mat):
    changed = False
    new_mat = []
    for i in range(4):
        new_mat.append([0] * 4)
    for i in range(4):
        pos = 0
        for j in range(4):
            if mat[i][j] != 0:
                new_mat[i][pos] = mat[i][j]
                if j != pos:
                    changed = True
                pos += 1
    return new_mat, changed

def merge(mat):
    changed = False
    score = 0  # Initialize score
    for i in range(4):
        for j in range(3):
            if mat[i][j] == mat[i][j + 1] and mat[i][j] != 0:
                mat[i][j] *= 2
                mat[i][j + 1] = 0
                score += mat[i][j]  # Add to score
                changed = True
    return mat, changed, score

def reverse(mat):
    new_mat = []
    for row in mat:
        new_mat.append(row[::-1])
    return new_mat

def transpose(mat):
    new_mat = []
    for i in range(4):
        new_mat.append([mat[j][i] for j in range(4)])
    return new_mat

def move_left(grid):
    new_grid, changed1 = compress(grid)
    new_grid, changed2, score = merge(new_grid)
    changed = changed1 or changed2
    new_grid, _ = compress(new_grid)
    return new_grid, changed, score

def move_right(grid):
    reversed_grid = reverse(grid)
    new_grid, changed, score = move_left(reversed_grid)
    new_grid = reverse(new_grid)
    return new_grid, changed, score

def move_up(grid):
    transposed_grid = transpose(grid)
    new_grid, changed, score = move_left(transposed_grid)
    new_grid = transpose(new_grid)
    return new_grid, changed, score

def move_down(grid):
    transposed_grid = transpose(grid)
    new_grid, changed, score = move_right(transposed_grid)
    new_grid = transpose(new_grid)
    return new_grid, changed, score
