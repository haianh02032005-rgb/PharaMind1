const path = require("node:path");
const { app, BrowserWindow, Menu, shell, session } = require("electron");

const SYSTEM_URL = "https://pharmamind-ai-demo.onrender.com";
const SYSTEM_ORIGIN = new URL(SYSTEM_URL).origin;

app.setAppUserModelId("ai.pharmamind.desktop");

function isAllowedPharmaMindUrl(value) {
  try {
    return new URL(value).origin === SYSTEM_ORIGIN;
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
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    show: false,
    backgroundColor: "#f7fafa",
    autoHideMenuBar: true,
    title: "PharmaMind AI",
    icon: path.join(__dirname, "assets", "icon.png"),
    webPreferences: {
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

  void mainWindow.loadURL(SYSTEM_URL, {
    extraHeaders: "Accept-Language: vi-VN,vi;q=0.9,en;q=0.8\n",
  });
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);

  session.fromPartition("persist:pharmamind").setPermissionRequestHandler(
    (_webContents, permission, callback, details) => {
      const trustedOrigin = isAllowedPharmaMindUrl(details.requestingUrl);
      callback(trustedOrigin && (permission === "media" || permission === "notifications"));
    },
  );

  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
