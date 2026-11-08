const http = require("node:http");
const fs = require("node:fs/promises");
const path = require("node:path");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webmanifest": "application/manifest+json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".glb": "model/gltf-binary",
};
const API_PREFIXES = ["/auth", "/users", "/families", "/imports", "/health"];
const UPSTREAM_TIMEOUT_MS = 180_000;

async function startLocalWebServer(webRoot, backendOrigin, preferredPort = 18765) {
  const root = path.resolve(webRoot);
  await fs.access(path.join(root, "index.html"));
  const server = http.createServer(async (request, response) => {
    const url = new URL(request.url || "/", "http://127.0.0.1");
    let pathname;
    try {
      pathname = decodeURIComponent(url.pathname);
    } catch {
      response.writeHead(400).end();
      return;
    }
    if (request.headers.host !== `127.0.0.1:${server.address().port}`) {
      response.writeHead(403).end();
      return;
    }
    if (API_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) {
      try {
        const chunks = [];
        let received = 0;
        for await (const chunk of request) {
          received += chunk.length;
          if (received > 32 * 1024 * 1024) {
            response.writeHead(413).end();
            return;
          }
          chunks.push(chunk);
        }
        const body = Buffer.concat(chunks);
        const headers = {};
        for (const key of ["content-type", "authorization", "accept"]) {
          if (request.headers[key]) headers[key] = request.headers[key];
        }
        const upstream = await fetch(`${backendOrigin}${url.pathname}${url.search}`, {
          method: request.method,
          headers,
          body: body.length ? body : undefined,
          signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
        });
        const upstreamContentType = upstream.headers.get("content-type") || "";
        if (upstream.status === 503 && upstreamContentType.includes("text/html")) {
          response.writeHead(503, {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "no-store",
            "retry-after": "60",
          });
          response.end(JSON.stringify({ detail: "Máy chủ PharmaMind đang khởi động sau thời gian không hoạt động. Hãy đợi khoảng 1 phút rồi thử lại." }));
          return;
        }
        const responseHeaders = {
          "content-type": upstreamContentType || "application/octet-stream",
          "cache-control": "no-store",
        };
        if (upstream.headers.get("content-disposition")) {
          responseHeaders["content-disposition"] = upstream.headers.get("content-disposition");
        }
        response.writeHead(upstream.status, responseHeaders);
        response.end(Buffer.from(await upstream.arrayBuffer()));
      } catch (error) {
        const timedOut = error?.name === "TimeoutError" || error?.name === "AbortError";
        response.writeHead(timedOut ? 504 : 502, {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "no-store",
          ...(timedOut ? { "retry-after": "60" } : {}),
        });
        response.end(JSON.stringify({
          detail: timedOut
            ? "Kết nối tới máy chủ PharmaMind quá thời gian chờ. Máy chủ miễn phí có thể đang khởi động; hãy đợi 1–2 phút rồi thử lại."
            : "Không kết nối được tới máy chủ PharmaMind. Hãy kiểm tra Wi-Fi hoặc Internet trên Raspberry Pi rồi thử lại.",
        }));
      }
      return;
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      response.writeHead(405).end();
      return;
    }
    const candidate = path.resolve(root, `.${pathname}`);
    if (candidate !== root && !candidate.startsWith(`${root}${path.sep}`)) {
      response.writeHead(403).end();
      return;
    }
    try {
      const isAsset = pathname.includes(".") || pathname.startsWith("/assets/") || pathname.startsWith("/models/");
      const file = isAsset ? candidate : path.join(root, "index.html");
      const content = await fs.readFile(file);
      response.writeHead(200, {
        "content-type": MIME[path.extname(file)] || "application/octet-stream",
        "cache-control": "no-store",
      });
      response.end(request.method === "HEAD" ? undefined : content);
    } catch {
      response.writeHead(404).end();
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(preferredPort, "127.0.0.1", resolve);
  });
  return { server, origin: `http://127.0.0.1:${server.address().port}` };
}

module.exports = { startLocalWebServer };
