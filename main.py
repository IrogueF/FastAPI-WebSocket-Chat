from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
import uvicorn

app = FastAPI()

class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Sends a message to all connected clients."""
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user has left the chat.")

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Chat</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; }
        #chatbox { width: 50%; height: 300px; border: 1px solid #ccc; overflow-y: auto; margin: 20px auto; padding: 10px; }
        #message { width: 40%; padding: 5px; }
        #send { padding: 5px; }
    </style>
</head>
<body>
    <h2>Real-Time Chat</h2>
    <div id="chatbox"></div>
    <input type="text" id="message" placeholder="Type your message...">
    <button id="send">Send</button>

    <script>
        const ws = new WebSocket("ws://localhost:8000/ws");
        const chatbox = document.getElementById("chatbox");
        const messageInput = document.getElementById("message");
        const sendButton = document.getElementById("send");

        ws.onmessage = function(event) {
            const msg = document.createElement("p");
            msg.textContent = event.data;
            chatbox.appendChild(msg);
            chatbox.scrollTop = chatbox.scrollHeight;
        };

        sendButton.onclick = function() {
            if (messageInput.value.trim() !== "") {
                ws.send(messageInput.value);
                messageInput.value = "";
            }
        };

        messageInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                sendButton.click();
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_page():
    """Serves the HTML page for chat."""
    return HTMLResponse(content=html)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
