import { PluginOption } from "vite";
import { WebSocket } from "ws";
import path from "path";

export function notifyEditorAfterBuildPlugin(): PluginOption {
  return {
    name: "postbuild-notify-editor",
    closeBundle: () =>
      new Promise<void>((resolve) => {
        let timeout = setTimeout(() => {
          console.log("No connection to Editor, closing websocket connection");
          ws.close();
          resolve();
        }, 3000);
        let ws = new WebSocket("ws://localhost:9000");
        let packageId = require("../package.json").name;
        ws.on("open", () => {
          ws.send(
            JSON.stringify({
              type: "developer-package",
              event: "components-build-complete",
              id: packageId,
              rootPath: path.resolve(__dirname, ".."),
            }),
          );
          ws.close();
          clearTimeout(timeout);
          resolve();
        });
        ws.on("error", (err) => {
          console.error(err);
          clearTimeout(timeout);
          resolve();
        });
      }),
  };
}
