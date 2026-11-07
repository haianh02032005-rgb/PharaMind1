const { contextBridge, ipcRenderer } = require("electron");

if (process.platform === "linux" && process.arch === "arm64") {
  contextBridge.exposeInMainWorld("pharmamindHardware", {
    getState: () => ipcRenderer.invoke("hardware:get-state"),
    sendCommand: (command) => ipcRenderer.invoke("hardware:command", command),
    subscribe: (callback) => {
      const listener = (_event, state) => callback(state);
      ipcRenderer.on("hardware:state", listener);
      return () => ipcRenderer.removeListener("hardware:state", listener);
    },
  });
}
