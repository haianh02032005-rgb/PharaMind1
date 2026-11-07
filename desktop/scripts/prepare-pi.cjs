const fs = require("node:fs");
const path = require("node:path");

const frontendDist = path.resolve(__dirname, "../../frontend/dist");
const bundledWeb = path.resolve(__dirname, "../web");
if (!fs.existsSync(path.join(frontendDist, "index.html"))) {
  throw new Error("Build frontend before packaging Raspberry Pi app");
}
fs.cpSync(frontendDist, bundledWeb, { recursive: true, force: true });
process.stdout.write(`Bundled frontend: ${bundledWeb}\n`);
