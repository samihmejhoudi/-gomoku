import asyncio
import websockets
import json
import random
import string
import subprocess
import sys
import socket
from ai_player import get_best_move

waiting_player = None
games = {}
rooms = {}


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase, k=6))


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


async def handle_player(websocket):
    global waiting_player

    try:
        name_msg = await websocket.recv()
        data = json.loads(name_msg)
        player_name = data.get("name", "Player")
        game_mode = data.get("mode", "human")
        room_code = data.get("room_code", None)
    except:
        return

    if game_mode == "ai":
        await start_ai_game(websocket, player_name)
        return

    if game_mode == "create_room":
        code = generate_room_code()
        rooms[code] = (websocket, player_name)

        await websocket.send(json.dumps({
            "type": "room_created",
            "code": code,
            "message": "Room created! Share your code with a friend."
        }))

        try:
            await websocket.wait_closed()
        finally:
            if code in rooms and rooms[code][0] == websocket:
                del rooms[code]
        return

    if game_mode == "join_room":
        if room_code not in rooms:
            await websocket.send(json.dumps({
                "type": "invalid_room",
                "message": "Room not found. Check the code and try again."
            }))
            return

        player1, player1_name = rooms.pop(room_code)
        player2 = websocket
        player2_name = player_name

        game = create_game(player1, player2)
        games[id(player1)] = game
        games[id(player2)] = game

        await player1.send(json.dumps({
            "type": "start",
            "color": game["colors"][0],
            "opponent": player2_name,
            "message": "Game started! You go first." if game["colors"][0] == "black" else "Game started! Wait for opponent."
        }))
        await player2.send(json.dumps({
            "type": "start",
            "color": game["colors"][1],
            "opponent": player1_name,
            "message": "Game started! You go first." if game["colors"][1] == "black" else "Game started! Wait for opponent."
        }))

        task1 = asyncio.create_task(listen(player1, game))
        task2 = asyncio.create_task(listen(player2, game))
        await asyncio.gather(task1, task2)
        return

    if waiting_player is None:
        waiting_player = (websocket, player_name)

        await websocket.send(json.dumps({
            "type": "waiting",
            "message": "Waiting for opponent..."
        }))

        try:
            await websocket.wait_closed()
        finally:
            if waiting_player and waiting_player[0] == websocket:
                waiting_player = None

    else:
        player1, player1_name = waiting_player
        waiting_player = None

        player2 = websocket
        player2_name = player_name

        game = create_game(player1, player2)
        games[id(player1)] = game
        games[id(player2)] = game

        await player1.send(json.dumps({
            "type": "start",
            "color": game["colors"][0],
            "opponent": player2_name,
            "message": "Game started! You go first." if game["colors"][0] == "black" else "Game started! Wait for opponent."
        }))
        await player2.send(json.dumps({
            "type": "start",
            "color": game["colors"][1],
            "opponent": player1_name,
            "message": "Game started! You go first." if game["colors"][1] == "black" else "Game started! Wait for opponent."
        }))

        task1 = asyncio.create_task(listen(player1, game))
        task2 = asyncio.create_task(listen(player2, game))
        await asyncio.gather(task1, task2)


async def start_ai_game(websocket, player_name):
    game = create_game(websocket, None)
    game["ai"] = True
    game["ai_color"] = "white"
    game["colors"] = ["black", "white"]
    games[id(websocket)] = game

    await websocket.send(json.dumps({
        "type": "start",
        "color": "black",
        "opponent": "AI",
        "message": "Game started! You go first."
    }))

    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "move":
                await handle_move(websocket, game, data["x"], data["y"])
    except websockets.exceptions.ConnectionClosed:
        pass


def create_game(player1, player2):
    # randomly decide who gets black and who gets white
    first = random.randint(0, 1)
    colors = ["black", "white"] if first == 0 else ["white", "black"]

    return {
        "board": [[None]*10 for _ in range(10)],
        "players": [player1, player2],
        "current_turn": 0,
        "colors": colors,
        "over": False,
        "ai": False,
        "ai_color": None
    }


async def listen(websocket, game):
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "move":
                await handle_move(websocket, game, data["x"], data["y"])

    except Exception:
        pass

    finally:
        if not game["over"]:
            game["over"] = True
            for player in game["players"]:
                if player is not None and player != websocket:
                    try:
                        await player.send(json.dumps({
                            "type": "opponent_left",
                            "message": "Opponent disconnected."
                        }))
                    except:
                        pass


async def handle_move(websocket, game, x, y):
    player_index = game["players"].index(websocket)
    color = game["colors"][player_index]

    if game["over"]:
        await websocket.send(json.dumps({
            "type": "invalid",
            "message": "Game is already over."
        }))
        return

    if game["current_turn"] != player_index:
        await websocket.send(json.dumps({
            "type": "invalid",
            "message": "Not your turn!"
        }))
        return

    if game["board"][y][x] is not None:
        await websocket.send(json.dumps({
            "type": "invalid",
            "message": "That spot is already taken."
        }))
        return

    game["board"][y][x] = color

    for player in game["players"]:
        if player is not None:
            await player.send(json.dumps({
                "type": "move",
                "x": x,
                "y": y,
                "color": color
            }))

    if check_win(game["board"], x, y, color):
        game["over"] = True
        for player in game["players"]:
            if player is not None:
                await player.send(json.dumps({
                    "type": "game_over",
                    "winner": color,
                    "message": f"{color} wins!"
                }))
        return

    game["current_turn"] = 1 - game["current_turn"]

    if game["ai"] and not game["over"]:
        await make_ai_move(websocket, game)


async def make_ai_move(websocket, game):
    ai_color = game["ai_color"]
    await asyncio.sleep(0.5)

    ax, ay = get_best_move(game["board"], ai_color)
    game["board"][ay][ax] = ai_color

    await websocket.send(json.dumps({
        "type": "move",
        "x": ax,
        "y": ay,
        "color": ai_color
    }))

    if check_win(game["board"], ax, ay, ai_color):
        game["over"] = True
        await websocket.send(json.dumps({
            "type": "game_over",
            "winner": ai_color,
            "message": f"{ai_color} wins!"
        }))
        return

    game["current_turn"] = 0


def check_win(board, x, y, color):
    directions = [(1,0), (0,1), (1,1), (1,-1)]

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


async def main():
    print("Server started on ws://0.0.0.0:8765")
    print("Waiting for players to connect...")
    async with websockets.serve(handle_player, "0.0.0.0", 8765):
        await asyncio.Future()


ip = get_local_ip()

http = subprocess.Popen(
    [sys.executable, "-m", "http.server", "4321"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

print(f"HTTP server started on port 4321")
print(f"Game available at http://{ip}:4321/client/index.html")
print(f"Share this link with your friends to play together")

asyncio.run(main())

http.terminate()