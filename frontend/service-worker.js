/**
 * Amahirwe service worker (Phase 4: Offline Assessment).
 * Caches the app shell (CSS/JS/dashboard pages/locales) so a student who
 * lost connectivity mid-session can still load the assessment screen;
 * actual answer submission while offline is queued by js/offline.js, not
 * this file. Registration happens from js/offline.js.
 */

const CACHE_NAME = "amahirwe-v2";

const PRECACHE_URLS = [
  "css/style.css",
  "css/components.css",
  "css/responsive.css",
  "js/api.js",
  "js/auth.js",
  "js/main.js",
  "js/dashboard.js",
  "js/assessment.js",
  "js/offline.js",
  "js/matching.js",
  "js/opportunities.js",
  "js/notifications.js",
  "locales/en.json",
  "locales/rw.json",
  "locales/fr.json",
  "student/dashboard.html",
  "manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Never cache API calls: assessment answers, auth, etc. must always be
  // live data, and offline queuing for those is handled at the app level.
  if (request.method !== "GET" || request.url.includes("/api/")) {
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
