/**
 * Amahirwe: fetching and rendering in-app notifications.
 * Implemented in Phase 6 (Mentor Matching) and used across later phases.
 */

import { api } from "./api.js";
import { loadNotifications } from "./dashboard.js";

function markNotificationRead(id) {
  return api.patch(`/notifications/${id}/read`);
}

export { loadNotifications, markNotificationRead };
