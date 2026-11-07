const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { startLocalWebServer } = require("../local-web.cjs");

test("Pi bundle serves its own UI and proxies API to the fixed cloud origin", async () => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "pharmamind-pi-web-"));
  const cloud = http.createServer((req, res) => {
    assert.equal(req.url, "/families/1/cabinets");
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ items: [{ id: 1 }] }));
  });
  await new Promise((resolve) => cloud.listen(0, "127.0.0.1", resolve));
  let local;
  try {
    await fs.writeFile(path.join(root, "index.html"), "<h1>Six physical boxes</h1>");
    local = await startLocalWebServer(root, `http://127.0.0.1:${cloud.address().port}`, 0);
    const page = await fetch(`${local.origin}/cabinet`);
    assert.match(await page.text(), /Six physical boxes/);
    const api = await fetch(`${local.origin}/families/1/cabinets`);
    assert.deepEqual(await api.json(), { items: [{ id: 1 }] });
    const invalid = await fetch(`${local.origin}/assets/missing.js`);
    assert.equal(invalid.status, 404);
  } finally {
    await new Promise((resolve) => local?.server.close(resolve) || resolve());
    await new Promise((resolve) => cloud.close(resolve));
    await fs.rm(root, { recursive: true, force: true });
  }
});
