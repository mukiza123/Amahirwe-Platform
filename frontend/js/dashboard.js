/**
 * Amahirwe: dashboard widgets shared across student/teacher/mentor/
 * provider/admin dashboards. Implemented starting Phase 3 (Student).
 */

import { api } from "./api.js";

const TALENT_AREA_LABELS = {
  technology: "Technology",
  leadership: "Leadership",
  creativity: "Creativity",
  sport: "Sport",
  art: "Art",
  public_speaking: "Public Speaking",
  agriculture: "Agriculture",
};

const TALENT_AREA_ICONS = {
  technology: "💻",
  leadership: "🧭",
  creativity: "🎨",
  sport: "⚽",
  art: "🖌️",
  public_speaking: "🎤",
  agriculture: "🌾",
};

function talentAreaLabel(area) {
  return TALENT_AREA_LABELS[area] || area;
}

function talentAreaIcon(area) {
  return TALENT_AREA_ICONS[area] || "⭐";
}

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return iso;
  }
}

const GREETINGS = { rw: "Muraho", en: "Hello", fr: "Bonjour" };

/** The dashboard welcome heading is built in JS (it needs the user's
 * first name), so it can't pick up a static data-i18n translation. */
function greetingWord() {
  const lang = document.documentElement.getAttribute("lang");
  return GREETINGS[lang] || GREETINGS.rw;
}

/** Swap between a loading/empty/error state block and the real content
 * block, matching the #state-loading / #dashboard-content pattern used
 * on every dashboard page. */
function showContent(loadingEl, contentEl) {
  if (loadingEl) loadingEl.hidden = true;
  if (contentEl) contentEl.hidden = false;
}

function showError(loadingEl, message) {
  if (!loadingEl) return;
  loadingEl.innerHTML = `<p class="text-secondary">${message}</p>`;
}

async function loadNotifications(container) {
  if (!container) return;
  try {
    const notifications = await api.get("/notifications/me");
    if (notifications.length === 0) {
      container.hidden = true;
      return;
    }
    container.hidden = false;
    container.innerHTML = notifications
      .map(
        (n) => `
        <div class="card notification-card${n.is_read ? "" : " notification-card--unread"}" data-id="${n.id}">
          <p>${n.message}</p>
          <span class="text-secondary" style="font-size:0.85em">${formatDate(n.created_at)}</span>
        </div>`
      )
      .join("");
  } catch {
    container.hidden = true;
  }
}

export {
  talentAreaLabel,
  talentAreaIcon,
  formatDate,
  greetingWord,
  showContent,
  showError,
  loadNotifications,
  TALENT_AREA_LABELS,
};
