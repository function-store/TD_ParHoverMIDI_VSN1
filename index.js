const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");
const { Jimp } = require("jimp");

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

let imageMessageQue = [];
let imageMessageQueTimeoutId = undefined;
let imageMessageQueTimeout = 25; // Faster for image messages
let imageDrawingActive = false;

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

function queImageMessage(message, priority = false) {
  if (priority) {
    imageMessageQue.unshift(message);
  } else {
    imageMessageQue.push(message);
  }
  if (imageMessageQueTimeoutId === undefined) {
    sendNextImageMessage();
  }
}

function sendNextImageMessage() {
  clearTimeout(imageMessageQueTimeoutId);
  imageMessageQueTimeoutId = undefined;
  
  // Check if image drawing was interrupted
  if (!imageDrawingActive) {
    console.log("Image drawing interrupted, clearing queue");
    imageMessageQue = [];
    return;
  }
  
  let message = imageMessageQue.shift();
  if (!message) {
    console.log("Image queue empty, stopping");
    imageDrawingActive = false;
    return;
  }

  console.log(`Sending image message, ${imageMessageQue.length} remaining`);
  controller.sendMessageToEditor(message);
  imageMessageQueTimeoutId = setTimeout(sendNextImageMessage, imageMessageQueTimeout);
}

// Image streaming Lua code for VSN1 display
const imageStreamLuaCode = `
function b64_decode(a,b,c,d)
  local va=b64_to_value(a)
  local vb=b64_to_value(b)
  local vc=b64_to_value(c)
  local vd=b64_to_value(d)
  local b1=(va*4)+math.floor(vb/16)
  local b2=((vb%16)*16)+math.floor(vc/4)
  local b3=((vc%4)*64)+vd;
  return{b1,b2,b3}
end

--SPLIT--

function b64_to_value(b)
  if not b or b==61 then return 0 end;
  if b>=65 and b<=90 then return b-65 end;
  if b>=97 and b<=122 then return b-71 end;
  if b>=48 and b<=57 then return b+4 end;
  if b==43 then return 62 end;
  if b==47 then return 63 end;
  return 0 
end

--SPLIT--
function a(b,c,d,e,f,g)if#g==4 then local a,h,i,g=g:byte(1,4)local j=b64_decode(a,h,i,g)ele[13]:ldrf(b,c,b+d,c+e,j)else local k=1;local l=b;local m=c;while k<#g do local a,h,i,g=g:byte(k,k+3)local j=b64_decode(a,h,i,g)if f==1 then ele[13]:ldpx(l,m,j)else ele[13]:ldrf(l,m,l+f-1,m+f-1,j)end;l=l+f;if l>=b+d then l=b;m=m+f end;k=k+4 end end;ele[13]:ldsw()end
`;

const maxCharacterCount = 365;

async function sendSplashScreen(targetDx, targetDy) {
  console.log("Starting splash screen...");
  
  // Stop any existing image drawing
  imageDrawingActive = false;
  clearTimeout(imageMessageQueTimeoutId);
  imageMessageQue = [];
  
  // Start new image drawing
  imageDrawingActive = true;
  
  const imagePath = path.resolve(__dirname, "resources/TDIconConnected.png");
  const x = 0;
  const y = 0;
  const w = 320;
  const h = 240;
  const scales = [25, 10, 3, 1]; // Progressive loading: very coarse to fine

  try {
    // First, send the Lua helper functions directly
    const scripts = imageStreamLuaCode.split("--SPLIT--").map((e) => e.trim());
    for (const script of scripts) {
      controller.sendMessageToEditor({
        type: "execute-lua-script",
        script: script,
        targetDx: targetDx,
        targetDy: targetDy,
      });
    }

    // Then load and send the image - simplified approach
    const image = await Jimp.read(imagePath);
    
    for (let currScale of scales) {
      // Check if interrupted
      if (!imageDrawingActive) {
        console.log("Image drawing interrupted during scale", currScale);
        return;
      }
      
      let scaledImage = image.clone();
      const imageSizeWidth = w / currScale;
      const imageSizeHeight = h / currScale;
      await scaledImage.resize({ w: imageSizeWidth, h: imageSizeHeight });
      
      let maxSquareSize = Math.floor(Math.sqrt(maxCharacterCount / 4));
      let maxWholePartX = Math.floor(imageSizeWidth / maxSquareSize);
      let maxWholePartY = Math.floor(imageSizeHeight / maxSquareSize);
      let imageString;
      
      for (let partY = 0; partY < maxWholePartY; partY++) {
        for (let partX = 0; partX < maxWholePartX; partX++) {
          // Check if interrupted
          if (!imageDrawingActive) {
            console.log("Image drawing interrupted during processing");
            return;
          }
          
          imageString = "";
          for (let i = partY * maxSquareSize; i < (partY + 1) * maxSquareSize; i++) {
            for (let j = partX * maxSquareSize; j < (partX + 1) * maxSquareSize; j++) {
              let pixel = scaledImage.getPixelColor(j, i);
              const r = (pixel >> 24) & 0xff;
              const g = (pixel >> 16) & 0xff;
              const b = (pixel >> 8) & 0xff;

              const buffer = Buffer.from([r, g, b]);
              imageString += buffer.toString("base64");
            }
          }
          
          // Send immediately with small delay
          controller.sendMessageToEditor({
            type: "execute-lua-script",
            script: `a(${x + partX * currScale * maxSquareSize},${y + partY * currScale * maxSquareSize},${currScale * maxSquareSize},${currScale * maxSquareSize},${currScale},"${imageString}")`,
            targetDx: targetDx,
            targetDy: targetDy,
          });
          
          // Small delay to prevent blocking
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      }
    }
    
    imageDrawingActive = false;
    console.log("Splash screen sent successfully!");
  } catch (error) {
    console.error("Failed to send splash screen:", error);
    imageDrawingActive = false;
  }
}

exports.loadPackage = async function (gridController, persistedData) {
  controller = gridController;
  let actionIconSvg = fs.readFileSync(
    path.resolve(__dirname, "TouchDesigner-icon.svg"),
    { encoding: "utf-8" },
  );

  //console.log({ persistedData });
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

  // Create "Initialize Splash" action for manual VSN1 display setup
  createAction({
    short: "ispl",
    displayName: "Initialize Splash",
    defaultLua: 'gps("package-touchdesigner-parhover", "init-splash", gmx(), gmy())',
    actionComponent: "single-event-static-action",
    toggleable: false,
  });

  wss = new WebSocket.Server({ port: websocketPort });

  console.log(
    `TouchDesigner Hover Control server is listening on ws://localhost:${websocketPort}`,
  );
  wss.on("connection", (ws) => {
    clientWs = ws;

    ws.on("message", handleWebsocketMessage);
    notifyStatusChange();

    // Send splash screen when TouchDesigner connects
    console.log("TouchDesigner connected, sending splash screen...");
    sendSplashScreen(0, 0);

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
  clearTimeout(imageMessageQueTimeoutId);
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
      //console.log({ e });
      if (e.data.type === "set-setting") {
        //console.log({ data: e.data });
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
  //console.log({ args });
  if (Array.isArray(args)) {
    // Handle "init-splash" action - sends Lua functions and splash image
    if (args[0] === "init-splash") {
      if (!clientWs) {
        console.log("Cannot send splash - TouchDesigner client not connected!");
        controller.sendMessageToEditor({
          type: "show-message",
          message:
            "Cannot send splash screen - TouchDesigner not connected!",
          messageType: "fail",
        });
        return;
      }
      console.log("Initialize Splash action triggered");
      sendSplashScreen(args[1], args[2]);
      return;
    }

    // Interrupt image drawing for any other action
    if (imageDrawingActive) {
      console.log("Interrupting image drawing for other action");
      imageDrawingActive = false;
      clearTimeout(imageMessageQueTimeoutId);
      imageMessageQue = [];
    }

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
