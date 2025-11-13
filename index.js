const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");

const websocketPort = 9642;
let activeWindowTitle = "TouchDesigner";

let wss = undefined;
let clientWs = undefined;
let controller;
let preferenceMessagePort = undefined;

let watchForActiveWindow = false;
let isWindowActive = false;
let controlScreenOnConnection = false;
let controlLedOnConnection = true;
let inactivityTimeoutMinutes = 0; // Default disabled
let screenDimLevel = 0; // 0-100%, 0 = fully off
let screenActiveLevel = 100; // 0-100%, 100 = full brightness

let actionId = 0;

let latestUpdateParameMessage = undefined;
let messageQueTimeoutId = undefined;
let messageQueTimeout = 50;

let ledState = "auto"; // "auto" or "red"

let inactivityTimeoutId = undefined;
let isScreenActive = true;

function queUpdateMessage(message) {
  latestUpdateParameMessage = message;
  if (messageQueTimeoutId === undefined) {
    sendNextMessage();
  }
}

function sendNextMessage() {
  clearTimeout(messageQueTimeoutId);
  messageQueTimeoutId = undefined;
  if (!latestUpdateParameMessage) return;

  controller.sendMessageToEditor(latestUpdateParameMessage);
  latestUpdateParameMessage = undefined;
  messageQueTimeoutId = setTimeout(sendNextMessage, messageQueTimeout);
}

function startInactivityTimeout() {
  clearTimeout(inactivityTimeoutId);
  
  // Don't start timeout if disabled (0 minutes)
  if (inactivityTimeoutMinutes <= 0) {
    return;
  }
  
  // Convert minutes to milliseconds
  const timeoutMs = inactivityTimeoutMinutes * 60 * 1000;
  
  inactivityTimeoutId = setTimeout(() => {
    // Dim screen after inactivity
    if (isScreenActive) {
      isScreenActive = false;
      // Convert 0-100% to 0-255 brightness value
      const brightness = Math.round((screenDimLevel / 100) * 255);
      setBlackLight(brightness);
    }
  }, timeoutMs);
}

function clearInactivityTimeout() {
  clearTimeout(inactivityTimeoutId);
  inactivityTimeoutId = undefined;
}

exports.loadPackage = async function (gridController, persistedData) {
  controller = gridController;
  let actionIconSvg = fs.readFileSync(
    path.resolve(__dirname, "TouchDesigner-icon.svg"),
    { encoding: "utf-8" },
  );

  watchForActiveWindow = persistedData?.watchForActiveWindow ?? false;
  // Use explicit undefined checks for booleans to ensure false values are preserved
  controlScreenOnConnection = persistedData?.controlScreenOnConnection !== undefined ? persistedData.controlScreenOnConnection : false;
  controlLedOnConnection = persistedData?.controlLedOnConnection !== undefined ? persistedData.controlLedOnConnection : true;
  inactivityTimeoutMinutes = persistedData?.inactivityTimeoutMinutes ?? 0;
  screenDimLevel = persistedData?.screenDimLevel ?? 0;
  screenActiveLevel = persistedData?.screenActiveLevel ?? 100;
  
  // Ensure initial settings are persisted if they were using defaults
  if (!persistedData || persistedData.controlScreenOnConnection === undefined) {
    setTimeout(() => {
      gridController.sendMessageToEditor({
        type: "persist-data",
        data: {
          watchForActiveWindow,
          controlScreenOnConnection,
          controlLedOnConnection,
          inactivityTimeoutMinutes,
          screenDimLevel,
          screenActiveLevel,
        },
      });
    }, 50);
  }

  function createAction(overrides) {
    gridController.sendMessageToEditor({
      type: "add-action",
      info: {
        actionId: actionId++,
        rendering: "standard",
        category: "websocket",
        color: "#00a827",
        icon: actionIconSvg,
        blockIcon: actionIconSvg,
        selectable: true,
        movable: true,
        hideIcon: false,
        type: "single",
        toggleable: true,
        ...overrides,
      },
    });
  }

  wss = new WebSocket.Server({ port: websocketPort });

  wss.on("connection", (ws) => {
    clientWs = ws;

    ws.on("message", handleWebsocketMessage);
    notifyStatusChange();
    
    // Start inactivity timeout when client connects
    isScreenActive = true;
    startInactivityTimeout();

    ws.on("close", () => {
      clientWs = undefined;
      // Clear inactivity timeout when client disconnects
      clearInactivityTimeout();
      isScreenActive = true;
      notifyStatusChange();
    });
  });

  if (watchForActiveWindow) {
    setTimeout(tryActivateActiveWindow, 50);
  }
  
  // Check initial connection status
  setTimeout(notifyStatusChange, 100);
};

exports.unloadPackage = async function () {
  clearTimeout(messageQueTimeoutId);
  clearInactivityTimeout();
  while (--actionId >= 0) {
    controller.sendMessageToEditor({
      type: "remove-action",
      actionId,
    });
  }
  clientWs?.close();
  wss?.close();
  preferenceMessagePort?.close();
  if (watchForActiveWindow) {
    clearTimeout(activeWindowSubscribeTimeoutId);
    controller.sendMessageToEditor({
      type: "send-package-message",
      targetPackageId: "package-active-win",
      message: {
        type: "unsubscribe",
      },
    });
  }
};

exports.addMessagePort = async function (port, senderId) {
  if (senderId == "preferences") {
    preferenceMessagePort?.close();
    preferenceMessagePort = port;
    port.on("close", () => {
      preferenceMessagePort = undefined;
    });
    port.on("message", (e) => {
      if (e.data.type === "set-setting") {
        if (watchForActiveWindow !== e.data.watchForActiveWindow) {
          watchForActiveWindow = e.data.watchForActiveWindow;
          if (watchForActiveWindow) {
            tryActivateActiveWindow();
          } else {
            clearTimeout(activeWindowSubscribeTimeoutId);
            controller.sendMessageToEditor({
              type: "send-package-message",
              targetPackageId: "package-active-win",
              message: {
                type: "unsubscribe",
              },
            });
          }
        }
        if (controlScreenOnConnection !== e.data.controlScreenOnConnection) {
          controlScreenOnConnection = e.data.controlScreenOnConnection;
          // Apply immediately based on current connection state
          notifyStatusChange();
        }
        if (controlLedOnConnection !== e.data.controlLedOnConnection) {
          controlLedOnConnection = e.data.controlLedOnConnection;
          // Apply immediately based on current connection state
          notifyStatusChange();
        }
        if (inactivityTimeoutMinutes !== e.data.inactivityTimeoutMinutes) {
          inactivityTimeoutMinutes = e.data.inactivityTimeoutMinutes;
          // Restart timeout with new duration if client is connected
          if (clientWs && isScreenActive) {
            startInactivityTimeout();
          }
        }
        if (screenDimLevel !== e.data.screenDimLevel) {
          screenDimLevel = e.data.screenDimLevel;
        }
        if (screenActiveLevel !== e.data.screenActiveLevel) {
          screenActiveLevel = e.data.screenActiveLevel;
          // Apply immediately if screen is active
          if (clientWs && isScreenActive) {
            const brightness = Math.round((screenActiveLevel / 100) * 255);
            setBlackLight(brightness);
          }
        }
        const dataToPerist = {
          watchForActiveWindow,
          controlScreenOnConnection,
          controlLedOnConnection,
          inactivityTimeoutMinutes,
          screenDimLevel,
          screenActiveLevel,
        };
        controller.sendMessageToEditor({
          type: "persist-data",
          data: dataToPerist,
        });
      }
    });
    port.start();
    notifyStatusChange();
  }
};

exports.sendMessage = async function (args) {
  if (Array.isArray(args)) {
    if (watchForActiveWindow && !isWindowActive) {
      return;
    }
    if (!clientWs) {
      controller.sendMessageToEditor({
        type: "show-message",
        message:
          "Websocket is not connected! Check if Websocket client connected to server!",
        messageType: "fail",
      });
      return;
    }
    clientWs?.send(
      JSON.stringify({
        event: "set",
        id: args[0],
        value: args[1],
      }),
    );
  } else {
    if (args.type === "active-window-status") {
      clearTimeout(activeWindowSubscribeTimeoutId);
      isWindowActive = args.status;
    }
  }
};

let activeWindowSubscribeTimeoutId = undefined;
function tryActivateActiveWindow() {
  activeWindowSubscribeTimeoutId = setTimeout(
    activeWindowRequestNoResponse,
    50,
  );
  controller.sendMessageToEditor({
    type: "send-package-message",
    targetPackageId: "package-active-win",
    message: {
      type: "subscribe",
      filter: activeWindowTitle,
      target: "application",
    },
  });
}

function activeWindowRequestNoResponse() {
  activeWindowSubscribeTimeoutId = undefined;
  controller.sendMessageToEditor({
    type: "show-message",
    message:
      "Couldn't connect to Active Window package! Make sure it is enabled!",
    messageType: "fail",
  });
  watchForActiveWindow = false;
  notifyStatusChange();
}

function handleWebsocketMessage(message) {
  let data = JSON.parse(message);
  
  // Re-enable screen if it was turned off due to inactivity
  if (!isScreenActive) {
    isScreenActive = true;
    const brightness = Math.round((screenActiveLevel / 100) * 255);
    setBlackLight(brightness);
  }
  
  // Restart inactivity timeout on every message
  startInactivityTimeout();
  
  // If we receive any WebSocket message and we're not in auto mode, reset to auto
  if (ledState !== "auto") {
    resetLedColorMinOnConnect();
  }
  
  if (data.type === "execute-code") {
    controller.sendMessageToEditor({
      type: "execute-lua-script",
      script: data.script,
      targetDx: data.targetDx,
      targetDy: data.targetDy,
    });
  }
  else if (data.type === "queue-code") {
    queUpdateMessage({
      type: "execute-lua-script",
      script: data.script,
      targetDx: data.targetDx,
      targetDy: data.targetDy,
    });
  }
}

function executeSetLedForIndices10to17() {
  const luaScript = `
for i = 10, 17 do
  set_ledcolmin(i-10,33,0,0,1);
  set_led(i, 1, 0);
end
lcd:ldaf(0,0,319,239,c[1]);
lcd:ldrr(3,3,317,237,10,c[2]);
lcd:ldsw();
`;
  
  controller.sendMessageToEditor({
    type: "execute-lua-script",
    script: luaScript
  });
  ledState = "red";
}

function ldsw() {
  const luaScript = `
lcd:ldsw();
`;
  controller.sendMessageToEditor({
    type: "execute-lua-script",
    script: luaScript
  });
}

function resetLedColorMinOnConnect() {
  const luaScript = `
for i = 10, 17 do
  set_ledcolmin(i-10,-1,-1,-1,0.05);
end
`;
  
  controller.sendMessageToEditor({
    type: "execute-lua-script",
    script: luaScript
  });
  ledState = "auto";
}

function setBlackLight(brightness) {
  // Accept brightness as 0-255 value, or true/false for backwards compatibility
  let brightnessValue;
  brightnessValue = Math.max(0, Math.min(255, brightness)); // Clamp to 0-255
  
  const luaScript = `set_l(${brightnessValue});`;
  
  controller.sendMessageToEditor({
    type: "execute-lua-script",
    script: luaScript
  });
}

function notifyStatusChange() {
  preferenceMessagePort?.postMessage({
    type: "clientStatus",
    clientConnected: clientWs !== undefined,
    watchForActiveWindow,
    controlScreenOnConnection,
    controlLedOnConnection,
    inactivityTimeoutMinutes,
    screenDimLevel,
    screenActiveLevel,
  });
  
  if (!clientWs) {
    // Disconnected state
    if (controlLedOnConnection) {
      executeSetLedForIndices10to17();
    }
    if (controlScreenOnConnection) {
      setBlackLight(0);
    }
  } else {
    // Connected state
    const brightness = Math.round((screenActiveLevel / 100) * 255);
    setBlackLight(brightness);
    resetLedColorMinOnConnect();
  }
}
