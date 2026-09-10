/**
 * Amahirwe service worker.
 * Caching and offline-assessment support are implemented in Phase 4
 * (Offline Assessment). Registration happens from js/offline.js once
 * that phase is built; this file is scaffolding for now.
 */

const CACHE_NAME = "amahirwe-v1";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});
