import random



# give it the board and the ai's color, it returns the best (x, y) move
def get_best_move(board, ai_color):
    human_color = "white" if ai_color == "black" else "black"

    # step 1 check if ai can win right now
    win_move = find_winning_move(board, ai_color)
    if win_move:
        return win_move

    # step 2  check if human is about to win and block them
    block_move = find_winning_move(board, human_color)
    if block_move:
        return block_move

    # step 3 check if ai can make 4 in a row
    attack_move = find_threat_move(board, ai_color, 4)
    if attack_move:
        return attack_move

    # step 4  check if human has 3 in a row and block it
    defend_move = find_threat_move(board, human_color, 3)
    if defend_move:
        return defend_move

    # step 5  if nothing urgent, play the best scored square
    return find_best_scored_move(board, ai_color, human_color)


# looks for a move that immediately wins or needs to be blocked
def find_winning_move(board, color):
    for y in range(10):
        for x in range(10):
            if board[y][x] is None:
                # try placing here
                board[y][x] = color
                if check_win(board, x, y, color):
                    # undo and return this move
                    board[y][x] = None
                    return (x, y)
                board[y][x] = None
    return None


# looks for a move that creates or blocks N stones in a row
def find_threat_move(board, color, count):
    for y in range(10):
        for x in range(10):
            if board[y][x] is None:
                board[y][x] = color
                if count_max_in_row(board, x, y, color) >= count:
                    board[y][x] = None
                    return (x, y)
                board[y][x] = None
    return None


# scores every empty square and picks the best one
def find_best_scored_move(board, ai_color, human_color):
    best_score = -1
    best_move = None

    # if board is empty just play in the middle
    if is_board_empty(board):
        return (4, 4)

    for y in range(10):
        for x in range(10):
            if board[y][x] is None:
                score = score_square(board, x, y, ai_color, human_color)
                if score > best_score:
                    best_score = score
                    best_move = (x, y)

    # fallback just in case — pick any empty square
    if best_move is None:
        empty = [(x, y) for y in range(10) for x in range(10) if board[y][x] is None]
        best_move = random.choice(empty)

    return best_move


# gives a score to a square based on how good it is for attack and defense
def score_square(board, x, y, ai_color, human_color):
    score = 0

    # bonus for being near the center
    center = 4.5
    distance = abs(x - center) + abs(y - center)
    score += max(0, 10 - distance)

    # score for how many ai stones are nearby
    board[y][x] = ai_color
    score += count_max_in_row(board, x, y, ai_color) * 3
    board[y][x] = None

    # score for how many human stones are nearby (defensive value)
    board[y][x] = human_color
    score += count_max_in_row(board, x, y, human_color) * 2
    board[y][x] = None

    return score


# counts the longest line of matching stones through a given square
def count_max_in_row(board, x, y, color):
    directions = [
        (1, 0),
        (0, 1),
        (1, 1),
        (1, -1),
    ]

    max_count = 0

    for dx, dy in directions:
        count = 1

        # look in positive direction
        i = 1
        while True:
            nx, ny = x + dx*i, y + dy*i
            if 0 <= nx < 10 and 0 <= ny < 10 and board[ny][nx] == color:
                count += 1
                i += 1
            else:
                break

        # look in negative direction
        i = 1
        while True:
            nx, ny = x - dx*i, y - dy*i
            if 0 <= nx < 10 and 0 <= ny < 10 and board[ny][nx] == color:
                count += 1
                i += 1
            else:
                break

        if count > max_count:
            max_count = count

    return max_count


# checks if a move wins the game — same logic as server.py
def check_win(board, x, y, color):
    directions = [
        (1, 0),
        (0, 1),
        (1, 1),
        (1, -1),
    ]

    for dx, dy in directions:
        count = 1

        i = 1
        while True:
            nx, ny = x + dx*i, y + dy*i
            if 0 <= nx < 10 and 0 <= ny < 10 and board[ny][nx] == color:
                count += 1
                i += 1
            else:
                break

        i = 1
        while True:
            nx, ny = x - dx*i, y - dy*i
            if 0 <= nx < 10 and 0 <= ny < 10 and board[ny][nx] == color:
                count += 1
                i += 1
            else:
                break

        if count >= 5:
            return True

    return False


# checks if the board is completely empty
def is_board_empty(board):
    for row in board:
        for cell in row:
            if cell is not None:
                return False
    return True