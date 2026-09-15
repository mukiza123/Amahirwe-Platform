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

function initials(fullName) {
  return fullName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

const ROLE_LABELS = {
  student: "Student",
  teacher: "Teacher",
  mentor: "Mentor",
  provider: "Provider",
  admin: "Administrator",
  parent: "Parent",
};

/** Wires up the parts every dashboard page's sidebar shell shares: user
 * avatar/name/role in the topbar, active nav highlighting, the mobile
 * sidebar drawer, and the notification-bell unread indicator. Call once
 * per page, after requireRole() resolves. `pageKey` matches the
 * data-page attribute on that page's own sidebar link. */
function initDashShell(user, pageKey) {
  const nameEl = document.querySelector("#dash-user-name");
  const roleEl = document.querySelector("#dash-user-role");
  const avatarEl = document.querySelector("#dash-user-avatar");
  if (nameEl) nameEl.textContent = user.full_name;
  if (roleEl) roleEl.textContent = ROLE_LABELS[user.role] || user.role;
  if (avatarEl) avatarEl.textContent = initials(user.full_name);

  const firstName = user.full_name.split(" ").filter(Boolean)[0] || user.full_name;
  document.querySelectorAll("[data-dash-first-name]").forEach((el) => {
    el.textContent = firstName;
  });
  document.querySelectorAll("[data-dash-full-name]").forEach((el) => {
    el.textContent = user.full_name;
  });

  document.querySelectorAll(".dash-sidebar__link[data-page]").forEach((link) => {
    link.classList.toggle("is-active", link.dataset.page === pageKey);
  });

  const sidebar = document.querySelector(".dash-sidebar");
  const toggle = document.querySelector(".dash-sidebar-toggle");
  const closeBtn = document.querySelector(".dash-sidebar__close");
  const backdrop = document.querySelector(".dash-sidebar-backdrop");
  const closeSidebar = () => {
    sidebar?.classList.remove("is-open");
    backdrop?.classList.remove("is-open");
  };
  toggle?.addEventListener("click", () => {
    sidebar?.classList.add("is-open");
    backdrop?.classList.add("is-open");
  });
  closeBtn?.addEventListener("click", closeSidebar);
  backdrop?.addEventListener("click", closeSidebar);

  const bellDot = document.querySelector("#dash-notif-dot");
  if (bellDot) {
    api
      .get("/notifications/me")
      .then((notifications) => {
        bellDot.hidden = !notifications.some((n) => !n.is_read);
      })
      .catch(() => {
        bellDot.hidden = true;
      });
  }
}

function initSettingsNav() {
  const nav = document.querySelector("[data-settings-nav]");
  if (!nav) return;
  nav.querySelectorAll("[data-settings-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.settingsTarget;
      nav.querySelectorAll("[data-settings-target]").forEach((el) => el.classList.toggle("is-active", el === btn));
      document.querySelectorAll("[data-settings-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.settingsPanel !== id;
      });
    });
  });
}

function initInbox() {
  const list = document.querySelector("#inbox-list");
  const thread = document.querySelector("#inbox-thread");
  if (!list || !thread) return;
  list.querySelectorAll(".inbox-item").forEach((item) => {
    item.addEventListener("click", () => {
      list.querySelectorAll(".inbox-item").forEach((el) => el.classList.remove("is-active"));
      item.classList.add("is-active");
      const title = item.querySelector(".inbox-item__title")?.textContent || "Message";
      const body = item.dataset.body || item.querySelector(".inbox-item__preview")?.textContent || "";
      const time = item.querySelector(".inbox-item__time")?.textContent || "";
      thread.innerHTML = `
        <div>
          <h2 style="margin:0 0 4px;font-size:1.05rem">${title}</h2>
          <p class="text-secondary" style="margin:0 0 16px;font-size:0.8rem">${time}</p>
          <div class="thread-bubble">${body}</div>
        </div>
        <form class="thread-composer" onsubmit="return false">
          <input class="form-input" type="text" placeholder="Write a reply..." disabled />
          <button type="button" class="btn btn-primary btn-sm" disabled>Send</button>
        </form>`;
    });
  });
}

export {
  talentAreaLabel,
  talentAreaIcon,
  formatDate,
  greetingWord,
  showContent,
  showError,
  loadNotifications,
  initDashShell,
  initSettingsNav,
  initInbox,
  TALENT_AREA_LABELS,
};
