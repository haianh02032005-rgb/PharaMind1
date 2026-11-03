const CACHE_NAME = "pharmamind-shell-v1";
const SHELL_FILES = [
  "/",
  "/manifest.webmanifest",
  "/pharmamind-icon.svg",
  "/pharmamind-icon-192.png",
  "/pharmamind-icon-512.png",
];
const API_PREFIXES = [
  "/auth",
  "/users",
  "/families",
  "/imports",
  "/health",
  "/ws",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (API_PREFIXES.some((prefix) => url.pathname.startsWith(prefix))) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          void caches.open(CACHE_NAME).then((cache) => cache.put("/", copy));
          return response;
        })
        .catch(() => caches.match("/")),
    );
    return;
  }

  if (
    url.pathname.startsWith("/assets/") ||
    url.pathname.startsWith("/models/")
  ) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ??
          fetch(request).then((response) => {
            const copy = response.clone();
            void caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(request, copy));
            return response;
          }),
      ),
    );
  }
});
