let socket = null
let myColor = null
let myName = ""
let isMyTurn = false
let gameMode = "random"

let blackStone = new Image()
let whiteStone = new Image()
blackStone.src = "assets/blackstone.gif"
whiteStone.src = "assets/whitestone.gif"

let canvas = document.getElementById("canvas")
let ctx = canvas.getContext("2d")
let statusBox = document.getElementById("status")


function setStatus(text, type) {
    statusBox.textContent = text
    statusBox.className = ""
    if (type) statusBox.classList.add(type)
}


function drawGrid() {
    let squareSize = canvas.width / 10
    ctx.strokeStyle = "#000000"
    ctx.lineWidth = 1

    for (let i = 0; i <= 10; i++) {
        ctx.beginPath()
        ctx.moveTo(i * squareSize, 0)
        ctx.lineTo(i * squareSize, canvas.height)
        ctx.stroke()
    }

    for (let i = 0; i <= 10; i++) {
        ctx.beginPath()
        ctx.moveTo(0, i * squareSize)
        ctx.lineTo(canvas.width, i * squareSize)
        ctx.stroke()
    }
}


function showJoinInput() {
    let nameInput = document.getElementById("name-input").value.trim()
    if (nameInput === "") {
        alert("Please enter your name first!")
        return
    }
    document.getElementById("join-input-row").classList.add("visible")
    document.getElementById("code-input").focus()
}


function confirmJoin() {
    let code = document.getElementById("code-input").value.trim().toUpperCase()
    if (code.length !== 6) {
        alert("Please enter a valid 6 letter room code!")
        return
    }
    joinGame("join_room", code)
}


function joinGame(mode, roomCode = null) {
    let nameInput = document.getElementById("name-input").value.trim()

    if (nameInput === "") {
        alert("Please enter your name first!")
        return
    }

    myName = nameInput
    gameMode = mode

    document.getElementById("name-screen").style.display = "none"
    document.getElementById("game-screen").style.display = "flex"

    connectToServer(roomCode)
}


function connectToServer(roomCode = null) {
    socket = new WebSocket("ws://" + window.location.hostname + ":8765")
    socket.onopen = function() {
        let msg = {
            type: "join",
            name: myName,
            mode: gameMode
        }
        if (roomCode) msg.room_code = roomCode
        socket.send(JSON.stringify(msg))
    }

    socket.onmessage = function(event) {
        let msg = JSON.parse(event.data)
        handleMessage(msg)
    }

    socket.onclose = function() {
        setStatus("Disconnected from server.", "error")
    }
}


function setActivePlayer(color) {
    document.getElementById("p1-cell").classList.remove("active")
    document.getElementById("p2-cell").classList.remove("active")

    if (color === "black") {
        document.getElementById("p1-cell").classList.add("active")
    } else {
        document.getElementById("p2-cell").classList.add("active")
    }
}


function backToMenu() {
    if (socket) socket.close()
    socket = null
    myColor = null
    myName = ""
    isMyTurn = false
    gameMode = "random"
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    document.getElementById("room-code-bar").innerHTML = ""
    document.getElementById("p1-name").textContent = "—"
    document.getElementById("p2-name").textContent = "—"
    document.getElementById("back-btn").style.display = "none"
    document.getElementById("join-input-row").classList.remove("visible")
    document.getElementById("code-input").value = ""
    document.getElementById("name-input").value = ""
    setStatus("Connecting...", "")
    document.getElementById("game-screen").style.display = "none"
    document.getElementById("name-screen").style.display = "flex"
}


function handleMessage(msg) {

    // draw grid while waiting for opponent in random mode
    if (msg.type === "waiting") {
        setStatus("Waiting for opponent...", "")
        drawGrid()
    }

    // draw grid and show room code while waiting for friend to join
    if (msg.type === "room_created") {
        let bar = document.getElementById("room-code-bar")
        bar.innerHTML = "Room Code: <span>" + msg.code + "</span>"
        setStatus("Share your code with a friend", "")
        drawGrid()
    }

    if (msg.type === "invalid_room") {
        document.getElementById("game-screen").style.display = "none"
        document.getElementById("name-screen").style.display = "flex"
        alert("Room not found. Check the code and try again.")
    }

    if (msg.type === "start") {
        myColor = msg.color
        isMyTurn = (myColor === "black")

        if (myColor === "black") {
            document.getElementById("p1-name").textContent = myName
            document.getElementById("p2-name").textContent = msg.opponent
        } else {
            document.getElementById("p1-name").textContent = msg.opponent
            document.getElementById("p2-name").textContent = myName
        }

        setActivePlayer("black")
        drawGrid()

        if (isMyTurn) {
            setStatus("Your turn!", "active")
        } else {
            setStatus(msg.opponent + "'s turn", "")
        }
    }

    if (msg.type === "move") {
        drawStone(msg.x, msg.y, msg.color)
        drawGrid()

        isMyTurn = (msg.color !== myColor)

        let nextColor = (msg.color === "black") ? "white" : "black"
        setActivePlayer(nextColor)

        if (isMyTurn) {
            setStatus("Your turn!", "active")
        } else {
            let opponentName = document.getElementById(
                myColor === "black" ? "p2-name" : "p1-name"
            ).textContent
            if (gameMode === "ai") {
                setStatus("AI is thinking...", "")
            } else {
                setStatus(opponentName + "'s turn", "")
            }
        }
    }

    if (msg.type === "invalid") {
        setStatus("Invalid move — try again", "error")
        isMyTurn = true
        setTimeout(() => setStatus("Your turn!", "active"), 2000)
    }

    if (msg.type === "game_over") {
        if (msg.winner === myColor) {
            setStatus("You win!", "win")
        } else {
            setStatus("You lose!", "error")
        }
        document.getElementById("p1-cell").classList.remove("active")
        document.getElementById("p2-cell").classList.remove("active")
        isMyTurn = false
    }

    if (msg.type === "opponent_left") {
        let opponentName = document.getElementById(
            myColor === "black" ? "p2-name" : "p1-name"
        ).textContent
        setStatus(opponentName + " disconnected — please go back to main page", "error")
        document.getElementById("p1-cell").classList.remove("active")
        document.getElementById("p2-cell").classList.remove("active")
        document.getElementById("back-btn").style.display = "inline-block"
        isMyTurn = false
    }
}


canvas.addEventListener("click", function(event) {
    if (!isMyTurn) return

    let squareSize = canvas.width / 10
    let x = Math.floor(event.offsetX / squareSize)
    let y = Math.floor(event.offsetY / squareSize)

    socket.send(JSON.stringify({ type: "move", x: x, y: y }))

    isMyTurn = false
})


function drawStone(x, y, color) {
    let squareSize = canvas.width / 10
    let img = (color === "black") ? blackStone : whiteStone

    let drawX = x * squareSize + squareSize * 0.1
    let drawY = y * squareSize + squareSize * 0.1
    let size = squareSize * 0.8

    ctx.drawImage(img, drawX, drawY, size, size)
}