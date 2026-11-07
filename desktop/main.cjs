const path = require("node:path");
const { app, BrowserWindow, Menu, ipcMain, shell, session } = require("electron");
const { startLocalWebServer } = require("./local-web.cjs");

const SYSTEM_URL = "https://pharmamind-ai-demo.onrender.com";
const SYSTEM_ORIGIN = new URL(SYSTEM_URL).origin;
const IS_LINUX_ARM64 = process.platform === "linux" && process.arch === "arm64";
let appOrigin = SYSTEM_ORIGIN;
let localWebServer = null;

// Raspberry Pi OS can run either Wayland or X11. Let Chromium select the
// available display backend instead of forcing one that may not exist.
if (IS_LINUX_ARM64) {
  app.commandLine.appendSwitch("ozone-platform-hint", "auto");
}

let hardwareSocket = null;
let hardwareConnected = false;
let hardwareBoxes = null;
let reconnectTimer = null;
let reconnectDelay = 1000;
let nextUnlockAt = 0;

function publishHardwareState() {
  for (const win of BrowserWindow.getAllWindows()) {
    if (isAllowedPharmaMindUrl(win.webContents.getURL())) {
      win.webContents.send("hardware:state", {
        connected: hardwareConnected,
        boxes: hardwareBoxes,
      });
    }
  }
}

function isValidBoxId(id) {
  return Number.isInteger(id) && id >= 1 && id <= 6;
}

function normalizeBox(value) {
  if (!value || !["OPEN", "CLOSED"].includes(value.status) ||
      !["ON", "OFF"].includes(value.led_state)) return null;
  return { status: value.status, led_state: value.led_state };
}

function connectHardware() {
  if (!IS_LINUX_ARM64 || app.isQuitting || hardwareSocket) return;
  const socket = new WebSocket("ws://127.0.0.1:8000/ws");
  hardwareSocket = socket;
  socket.addEventListener("open", () => {
    if (hardwareSocket !== socket) return;
    hardwareConnected = true;
    reconnectDelay = 1000;
    publishHardwareState();
  });
  socket.addEventListener("message", ({ data }) => {
    if (hardwareSocket !== socket || typeof data !== "string") return;
    try {
      const message = JSON.parse(data);
      if (message.type === "INIT_SYSTEM" && message.boxes && typeof message.boxes === "object") {
        const boxes = {};
        for (let id = 1; id <= 6; id++) {
          const box = normalizeBox(message.boxes[String(id)]);
          if (!box) return;
          boxes[String(id)] = box;
        }
        hardwareBoxes = boxes;
        publishHardwareState();
      } else if (message.type === "SENSOR_TRIGGER" && isValidBoxId(message.box_id)) {
        const box = normalizeBox(message);
        if (!box) return;
        hardwareBoxes = { ...hardwareBoxes, [String(message.box_id)]: box };
        publishHardwareState();
      }
    } catch {
      // Ignore malformed data from the local service.
    }
  });
  const onDisconnect = () => {
    if (hardwareSocket !== socket) return;
    hardwareSocket = null;
    hardwareConnected = false;
    hardwareBoxes = null;
    publishHardwareState();
    if (!app.isQuitting && !reconnectTimer) {
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectHardware();
      }, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 10000);
    }
  };
  socket.addEventListener("close", onDisconnect);
  socket.addEventListener("error", () => {
    try { socket.close(); } catch { onDisconnect(); }
  });
}

function trustedHardwareSender(event) {
  try {
    return IS_LINUX_ARM64 && new URL(event.sender.getURL()).origin === appOrigin;
  } catch {
    return false;
  }
}

ipcMain.handle("hardware:get-state", (event) => {
  if (!trustedHardwareSender(event)) throw new Error("Trang không được phép truy cập phần cứng");
  return { connected: hardwareConnected, boxes: hardwareBoxes };
});

ipcMain.handle("hardware:command", (event, command) => {
  if (!trustedHardwareSender(event)) throw new Error("Trang không được phép điều khiển phần cứng");
  if (!hardwareConnected || !hardwareSocket || hardwareSocket.readyState !== WebSocket.OPEN) {
    throw new Error("Chưa kết nối dịch vụ phần cứng trên Raspberry Pi");
  }
  if (!command || !isValidBoxId(command.box_id)) throw new Error("Số hộp không hợp lệ");
  if (command.action === "UNLOCK_BOX") {
    if (Date.now() < nextUnlockAt) throw new Error("Vui lòng đợi chốt ngăn trước nhả hoàn toàn");
    nextUnlockAt = Date.now() + 2500;
    hardwareSocket.send(JSON.stringify({ action: "UNLOCK_BOX", box_id: command.box_id }));
  } else if (command.action === "SET_LED" && ["ON", "OFF"].includes(command.state)) {
    hardwareSocket.send(JSON.stringify({ action: "SET_LED", box_id: command.box_id, state: command.state }));
  } else {
    throw new Error("Lệnh phần cứng không hợp lệ");
  }
  return { sent: true };
});

app.setAppUserModelId("ai.pharmamind.desktop");

function isAllowedPharmaMindUrl(value) {
  try {
    return new URL(value).origin === appOrigin;
  } catch {
    return false;
  }
}

function openExternalUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol === "https:" || url.protocol === "mailto:") {
      void shell.openExternal(url.toString());
    }
  } catch {
    // Ignore malformed URLs instead of passing them to the operating system.
  }
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: IS_LINUX_ARM64 ? 1180 : 1280,
    height: IS_LINUX_ARM64 ? 720 : 820,
    minWidth: IS_LINUX_ARM64 ? 720 : 960,
    minHeight: IS_LINUX_ARM64 ? 480 : 640,
    show: false,
    backgroundColor: "#f7fafa",
    autoHideMenuBar: true,
    title: "PharmaMind AI",
    icon: path.join(__dirname, "assets", "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webviewTag: false,
      spellcheck: true,
      partition: "persist:pharmamind",
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isAllowedPharmaMindUrl(url)) {
      void mainWindow.loadURL(url);
    } else {
      openExternalUrl(url);
    }
    return { action: "deny" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    if (isAllowedPharmaMindUrl(url) || url.startsWith("file://")) return;
    event.preventDefault();
    openExternalUrl(url);
  });

  mainWindow.webContents.on(
    "did-fail-load",
    (_event, errorCode, _errorDescription, validatedUrl, isMainFrame) => {
      if (!isMainFrame || errorCode === -3 || !isAllowedPharmaMindUrl(validatedUrl)) {
        return;
      }
      void mainWindow.loadFile(path.join(__dirname, "renderer", "offline.html"));
    },
  );

  mainWindow.webContents.on("before-input-event", (event, input) => {
    if (input.key === "F12" || (input.control && input.shift && input.key === "I")) {
      event.preventDefault();
    }
  });

  void mainWindow.loadURL(appOrigin, {
    extraHeaders: "Accept-Language: vi-VN,vi;q=0.9,en;q=0.8\n",
  });
}

app.whenReady().then(async () => {
  Menu.setApplicationMenu(null);

  if (IS_LINUX_ARM64) {
    const local = await startLocalWebServer(path.join(__dirname, "web"), SYSTEM_ORIGIN);
    localWebServer = local.server;
    appOrigin = local.origin;
  }

  session.fromPartition("persist:pharmamind").setPermissionRequestHandler(
    (_webContents, permission, callback, details) => {
      const trustedOrigin = isAllowedPharmaMindUrl(details.requestingUrl);
      callback(trustedOrigin && (permission === "media" || permission === "notifications"));
    },
  );

  createWindow();
  connectHardware();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("before-quit", () => {
  app.isQuitting = true;
  if (reconnectTimer) clearTimeout(reconnectTimer);
  hardwareSocket?.close();
  localWebServer?.close();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
