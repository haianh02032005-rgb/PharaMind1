# PharmaMind AI Desktop

Windows desktop shell for the public PharmaMind AI service. It packages a
locked-down Electron browser and opens:

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
