/**
 * Amahirwe: IndexedDB sync queue and connectivity detection for the
 * offline-first talent assessment. Implemented in Phase 4 (Offline).
 *
 * Rural connectivity is unreliable (SRS FR-1.3), so a student taking the
 * assessment must be able to finish and "submit" it with no network at
 * all. The answers are saved locally and pushed to the server the next
 * time the app detects a connection.
 */

const DB_NAME = "amahirwe-offline";
const DB_VERSION = 1;
const QUEUE_STORE = "pending_assessments";

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        db.createObjectStore(QUEUE_STORE, { keyPath: "queuedAt" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function queueAssessment(payload) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(QUEUE_STORE, "readwrite");
    tx.objectStore(QUEUE_STORE).add({ ...payload, queuedAt: Date.now() });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function listQueuedAssessments() {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(QUEUE_STORE, "readonly");
    const request = tx.objectStore(QUEUE_STORE).getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function removeQueuedAssessment(queuedAt) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(QUEUE_STORE, "readwrite");
    tx.objectStore(QUEUE_STORE).delete(queuedAt);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

/** Tries to push every queued assessment to the server. Stops at the
 * first failure (the network is probably still down) rather than
 * reordering or dropping anything. */
async function syncQueuedAssessments(submitFn, onEach) {
  const queued = await listQueuedAssessments();
  let synced = 0;
  for (const item of queued) {
    const { queuedAt, ...payload } = item;
    try {
      await submitFn(payload);
      await removeQueuedAssessment(queuedAt);
      synced += 1;
      if (onEach) onEach(payload, synced, queued.length);
    } catch {
      break;
    }
  }
  return synced;
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  const scope = window.location.pathname.includes("/frontend/") ? "/frontend/" : "/";
  navigator.serviceWorker.register(`${scope}service-worker.js`, { scope }).catch(() => {
    // Offline caching is a progressive enhancement; a failed registration
    // shouldn't block the rest of the app.
  });
}

export { queueAssessment, listQueuedAssessments, removeQueuedAssessment, syncQueuedAssessments, registerServiceWorker };
