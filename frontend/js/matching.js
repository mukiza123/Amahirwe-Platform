/**
 * Amahirwe: mentor match display and teacher approve/decline actions.
 * Implemented in Phase 6 (Mentor Matching).
 */

import { api } from "./api.js";
import { talentAreaIcon, talentAreaLabel, formatDate } from "./dashboard.js";
import { t } from "./main.js";

function statusLabel(status) {
  if (status === "approved") return t("dash_status_approved", "Approved");
  if (status === "rejected") return t("dash_status_rejected", "Not approved");
  return t("dash_awaiting_review", "Awaiting review");
}

const STATUS_CLASSES = { pending: "badge-mint", approved: "badge-success", rejected: "badge-error" };

function findAMentor() {
  return api.post("/matches/find", {});
}

function listMyMatches() {
  return api.get("/matches/me");
}

function listSchoolMatches(status) {
  const query = status ? `?match_status=${status}` : "";
  return api.get(`/teachers/me/matches${query}`);
}

function approveMatch(id) {
  return api.patch(`/matches/${id}/approve`);
}

function rejectMatch(id) {
  return api.patch(`/matches/${id}/reject`);
}

/** A match card. `perspective` controls which name/contact is shown:
 * "student" (viewer is the student, so show mentor), "mentor" (viewer is
 * the mentor, so show student), or "reviewer" (teacher/admin, show both). */
function renderMatchCard(match, perspective, { showActions = false } = {}) {
  const statusBadge = `<span class="badge ${STATUS_CLASSES[match.status]}">${statusLabel(match.status)}</span>`;
  const areaLine = `<p>${talentAreaIcon(match.talent_area)} ${talentAreaLabel(match.talent_area)} ${t("dash_match_suffix", "match")}</p>`;

  let contactLine = "";
  if (match.status === "approved") {
    if (perspective === "student" && match.mentor_contact_email) {
      contactLine = `<p class="text-secondary">${t("dash_mentor_colon", "Mentor:")} ${match.mentor_name || ""} (${match.mentor_contact_email})</p>`;
    } else if (perspective === "mentor" && match.student_contact_email) {
      contactLine = `<p class="text-secondary">${t("dash_student_colon", "Student:")} ${match.student_name || ""} (${match.student_contact_email})</p>`;
    } else if (perspective === "reviewer") {
      contactLine = `<p class="text-secondary">${match.student_name || t("role_student", "Student")} &harr; ${match.mentor_name || t("role_mentor", "Mentor")}</p>`;
    }
  } else if (perspective === "reviewer") {
    contactLine = `<p class="text-secondary">${match.student_name || t("dash_a_student", "A student")} ${t("dash_requested_this_match", "requested this match.")}</p>`;
  }

  const actions =
    showActions && match.status === "pending"
      ? `<div class="card__actions">
          <button type="button" class="btn btn-secondary btn-sm" data-action="reject-match" data-id="${match.id}">${t("dash_decline", "Decline")}</button>
          <button type="button" class="btn btn-primary btn-sm" data-action="approve-match" data-id="${match.id}">${t("dash_approve", "Approve")}</button>
        </div>`
      : "";

  const name =
    perspective === "student"
      ? match.mentor_name || t("role_mentor", "Mentor")
      : perspective === "mentor"
        ? match.student_name || t("role_student", "Student")
        : `${match.student_name || t("role_student", "Student")} · ${match.mentor_name || t("role_mentor", "Mentor")}`;
  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");

  return `
    <article class="page-card match-card people-row" data-match-id="${match.id}" style="grid-template-columns:40px 1fr auto;align-items:start">
      <span class="home-avatar">${initials || "AM"}</span>
      <div>
        <div class="match-card__header">${statusBadge}<span class="text-secondary" style="font-size:0.8rem">${formatDate(match.created_at)}</span></div>
        <p class="assess-item__title">${name}</p>
        ${areaLine}
        ${contactLine}
      </div>
      <div class="people-row__actions">${actions}</div>
    </article>`;
}

export { findAMentor, listMyMatches, listSchoolMatches, approveMatch, rejectMatch, renderMatchCard };
