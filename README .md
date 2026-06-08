# GoMoKu — Connect Five

A two-player browser-based GoMoKu game built with Python (WebSockets) and HTML/JS.

---

## Requirements

Install the one dependency before running anything:

```bash
pip install websockets
```

---

## How to Run

### Step 1 — Start the server

Open the terminal in PyCharm and run:

```bash
python server.py
```

This starts everything automatically — the WebSocket server on port 8765 and the HTTP server on port 4321 at the same time. You should see something like:

```
HTTP server started on port 4321
Game available at http://10.250.70.123:4321/client/index.html
Server started on ws://0.0.0.0:8765
Waiting for players to connect...
```

The link in your terminal is the exact link to use. Keep this terminal open the whole time. If you close it both servers stop.

---

### Step 2 — Both players open the link

Copy the link that appeared in your terminal and open it in the browser. Share it with your friend so they can open it too on their device.

Both players must be on the same WiFi network.

---

### Step 3 — Play

- Enter your name and choose a game mode
- **Create Room** ; creates a private room and gives you a code to share with your friend
- **Join Room** ; enter the code your friend gave you to join their room
- **Play Random** ;gets paired with whoever is waiting
- **vs AI** ; play alone against the computer
- color is assigned randomly

---

## Project Structure

```
gomoku/
├── server.py          — WebSocket server, game logic, AI, starts HTTP server
├── ai_player.py       — AI move logic
└── client/
    ├── index.html     — Game UI
    ├── game.js        — Board rendering and WebSocket client
    └── assets/
        ├── background.gif
        ├── blackstone.gif
        └── whitestone.gif
```

---

## Playing vs AI

Open the game, enter your name and click vs AI. No second player needed, the server handles the AI moves automatically.

---

## Common Issues

**Server won't start** — make sure you ran `pip install websockets` and your terminal shows `(.venv)` at the start.

**Players not connecting** — make sure all devices are on the same WiFi network and the server is running before opening the browser.

**Room code not working** — make sure the player who created the room is still connected and the code is exactly 6 letters.

---

## If Port 8765 is Already in Use

```cmd
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8765') do taskkill /PID %a /F
```

Then run `python server.py` again normally.
