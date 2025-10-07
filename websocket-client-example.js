const WebSocket = require("ws");
const readline = require("readline");

// Replace with your server's WebSocket URL
const ws = new WebSocket("ws://localhost:9642");

// Log when connected
ws.on("open", () => {
  console.log("Connected to server.");
});

// Print all incoming messages
ws.on("message", (data) => {
  console.log(`Received: ${data}`);
});

// Handle errors
ws.on("error", (err) => {
  console.error(`Error: ${err.message}`);
});

// Handle close
ws.on("close", () => {
  console.log("Disconnected from server.");
});

// Setup readline for keypress input
readline.emitKeypressEvents(process.stdin);
process.stdin.setRawMode(true);

process.stdin.on("keypress", (str, key) => {
  if (key.sequence === "\u0003") {
    // Ctrl+C
    process.exit();
  } else {
    const command = JSON.stringify({
      type: "execute-code",
      script: `print("Hello from Websocket!")`,
    });
    ws.send(command);
    console.log(`Sent: ${command}`);
  }
});
