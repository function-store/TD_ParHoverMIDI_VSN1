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

let actionId = 0;

let latestUpdateParameMessage = undefined;
let messageQueTimeoutId = undefined;
let messageQueTimeout = 50;

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

exports.loadPackage = async function (gridController, persistedData) {
  controller = gridController;
  let actionIconSvg = fs.readFileSync(
    path.resolve(__dirname, "TouchDesigner-icon.svg"),
    { encoding: "utf-8" },
  );

  console.log({ persistedData });
  watchForActiveWindow = persistedData?.watchForActiveWindow ?? false;

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

  console.log(
    `TouchDesigner Hover Control server is listening on ws://localhost:${websocketPort}`,
  );
  wss.on("connection", (ws) => {
    clientWs = ws;

    ws.on("message", handleWebsocketMessage);
    notifyStatusChange();

    ws.on("close", () => {
      clientWs = undefined;
      notifyStatusChange();
    });
  });

  if (watchForActiveWindow) {
    setTimeout(tryActivateActiveWindow, 50);
  }
};

exports.unloadPackage = async function () {
  clearTimeout(messageQueTimeoutId);
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
      console.log({ e });
      if (e.data.type === "set-setting") {
        console.log({ data: e.data });
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
        controller.sendMessageToEditor({
          type: "persist-data",
          data: {
            watchForActiveWindow,
          },
        });
      }
    });
    port.start();
    notifyStatusChange();
  }
};

exports.sendMessage = async function (args) {
  console.log({ args });
  if (Array.isArray(args)) {
    if (watchForActiveWindow && !isWindowActive) {
      console.log("Window is not active, ignoring message!");
      return;
    }
    if (!clientWs) {
      console.log("Websocket Client not connected!");
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
  console.log({ data });
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

function notifyStatusChange() {
  preferenceMessagePort?.postMessage({
    type: "clientStatus",
    clientConnected: clientWs !== undefined,
    watchForActiveWindow,
  });
}
