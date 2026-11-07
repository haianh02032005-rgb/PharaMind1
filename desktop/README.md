# PharmaMind AI Desktop

Desktop application for PharmaMind AI. Windows and Linux x64 open the public
service in a locked-down Electron browser:

`https://pharmamind-ai-demo.onrender.com`

## Development

```powershell
npm install
npm start
```

## Windows installer

```powershell
npm run dist:win
```

The NSIS installer creates Start Menu and optional Desktop shortcuts. The app
keeps the web session in an isolated persistent Electron partition. Node.js is
disabled in page content, context isolation and sandboxing are enabled, and
navigation outside the PharmaMind origin opens in the user's default browser.

The generated installer is unsigned. Windows SmartScreen can therefore show
an Unknown Publisher warning until a trusted Authenticode code-signing
certificate is configured.

## Linux / Ubuntu packages

Build on Ubuntu or another Debian-based Linux distribution:

```bash
npm ci
npm run dist:linux
```

Two x64 packages are produced in `dist/`:

- `*.AppImage`: portable package; mark it executable and run it directly.
- `*.deb`: native package for Ubuntu/Debian; install it with the App Center or
  `sudo apt install ./<package>.deb`.

The installed application is available from the desktop application menu as
**PharmaMind AI**. Both packages use the same locked-down Electron settings and
connect to the public PharmaMind service over HTTPS.

## Raspberry Pi 5

Raspberry Pi 5 requires a 64-bit operating system with a graphical desktop.
Build the native ARM64 packages on an ARM64 Linux host after building the
frontend:

```bash
npm ci
npm ci --prefix ../frontend
npm run build --prefix ../frontend
npm run prepare:pi
npm run dist:linux:arm64
```

The ARM64 DEB package is recommended for Raspberry Pi OS 64-bit. Install it
with the desktop package manager or:

```bash
sudo apt install ./PharmaMind-AI-Desktop-*-linux-arm64.deb
```

The ARM64 AppImage is the portable alternative. Raspberry Pi OS Lite is not
supported because the application requires a graphical session. On ARM64,
Electron automatically selects Wayland or X11 and allows a smaller minimum
window size for Raspberry Pi displays.

The Raspberry Pi build bundles the six-box web interface into the installer.
It serves that interface on `127.0.0.1:18765` and proxies authenticated API
requests to the public Render backend. The Electron main process alone opens
`ws://127.0.0.1:8000/ws` and forwards validated `INIT_SYSTEM` and
`SENSOR_TRIGGER` states to the interface. `UNLOCK_BOX` has a global 2.5-second
cooldown; `SET_LED` is limited to boxes 1–6. No app code accesses GPIO directly.

The Pi service must already be installed and listening on port 8000. If it is
unavailable, the app displays a disconnected state and reconnects automatically.
