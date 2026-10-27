const CACHE_NAME = "hoshi-shell-v29";
const APP_SHELL = ["./", "./index.html", "./trading.css", "./speech-pipeline.js", "./profile-store.js", "./profile-memory.html", "./profile-memory.js", "./hoshi-core.css", "./hoshi-core.mjs", "./hoshi-core-ui.mjs", "./manifest.json", "./reminder-parser.js", "./assistant-commands.js", "./memory-privacy.js", "./hoshi-diagnostics.js", "./hoshi-product-ads.js", "./assets/hoshi-expressions.webp", "./assets/hoshi-hero-background.svg", "./assets/hoshi-app-icon.svg", "./assets/hoshi-nightroom.webp"];

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
    // Always prefer the current online document. Use the cache only if offline.
    event.respondWith(
      fetch(request, { cache: "no-store" })
        .then(response => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, copy);
              cache.put(new URL("./index.html", self.registration.scope).href, response.clone());
            });
          }
          return response;
        })
        .catch(async () => {
          const cache = await caches.open(CACHE_NAME);
          return (await cache.match(request)) ||
            (await cache.match(new URL("./index.html", self.registration.scope).href)) ||
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


