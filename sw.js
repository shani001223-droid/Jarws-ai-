const CACHE_NAME = "hoshi-shell-v37";
const APP_SHELL = ["./trading.html", "./hoshi-trading-desk.js", "./hoshi-trading-desk.css", "./", "./index.html", "./trading.css", "./hoshi-focus.css", "./manifest.json", "./reminder-parser.js", "./assistant-commands.js", "./memory-privacy.js", "./hoshi-memory-store.js", "./hoshi-product-ads.js", "./hoshi-task-router.js", "./hoshi-trading-research.js", "./hoshi-annotated-chart.js", "./hoshi-source-research.js", "./hoshi-speech-input.js", "./hoshi-local-ui-actions.js", "./assets/hoshi-expressions.webp", "./assets/hoshi-hero-background.svg", "./assets/hoshi-app-icon.svg", "./assets/hoshi-nightroom.webp", "./speech-pipeline.js", "./profile-store.js", "./profile-memory.html", "./profile-memory.js", "./hoshi-core.css", "./hoshi-core.mjs", "./hoshi-core-ui.mjs", "./hoshi-diagnostics.js", "./hoshi-anime-avatar.css", "./hoshi-anime-avatar.js"];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const isDocument =
    request.mode === "navigate" ||
    url.pathname.endsWith("/") ||
    url.pathname.endsWith("/index.html");

  if (isDocument) {
    const shellURL = new URL("./index.html", self.registration.scope).href;
    const isMainDocument = url.href.split("?")[0] === shellURL ||
      url.pathname === new URL(self.registration.scope).pathname;
    // Always prefer the current online document. Use the cache only if offline.
    event.respondWith(
      fetch(request, { cache: "no-store" })
        .then(response => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, copy);
              // Trading/other documents must never overwrite the main shell.
              if (isMainDocument) cache.put(shellURL, response.clone());
            });
          }
          return response;
        })
        .catch(async () => {
          const cache = await caches.open(CACHE_NAME);
          return (await cache.match(request)) ||
            (isMainDocument && (await cache.match(shellURL))) ||
            Response.error();
        })
    );
    return;
  }

  // Cache static assets first; cache fresh same-origin responses for offline use.
  event.respondWith(
    caches.match(request).then(cached => cached || fetch(request).then(response => {
      if (response && response.ok) {
        caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
      }
      return response;
    }))
  );
});


