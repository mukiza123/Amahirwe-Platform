/**
 * Amahirwe: mentor match display and teacher approve/decline actions.
 * Implemented in Phase 6 (Mentor Matching).
 */

import { api } from "./api.js";
import { talentAreaIcon, talentAreaLabel, formatDate } from "./dashboard.js";

const STATUS_LABELS = { pending: "Awaiting review", approved: "Approved", rejected: "Not approved" };
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
  const statusBadge = `<span class="badge ${STATUS_CLASSES[match.status]}">${STATUS_LABELS[match.status]}</span>`;
  const areaLine = `<p>${talentAreaIcon(match.talent_area)} ${talentAreaLabel(match.talent_area)} match</p>`;

  let contactLine = "";
  if (match.status === "approved") {
    if (perspective === "student" && match.mentor_contact_email) {
      contactLine = `<p class="text-secondary">Mentor: ${match.mentor_name || ""} (${match.mentor_contact_email})</p>`;
    } else if (perspective === "mentor" && match.student_contact_email) {
      contactLine = `<p class="text-secondary">Student: ${match.student_name || ""} (${match.student_contact_email})</p>`;
    } else if (perspective === "reviewer") {
      contactLine = `<p class="text-secondary">${match.student_name || "Student"} &harr; ${match.mentor_name || "Mentor"}</p>`;
    }
  } else if (perspective === "reviewer") {
    contactLine = `<p class="text-secondary">${match.student_name || "A student"} requested this match.</p>`;
  }

  const actions =
    showActions && match.status === "pending"
      ? `<div class="card__actions">
          <button type="button" class="btn btn-secondary btn-sm" data-action="reject-match" data-id="${match.id}">Decline</button>
          <button type="button" class="btn btn-primary btn-sm" data-action="approve-match" data-id="${match.id}">Approve</button>
        </div>`
      : "";

  return `
    <div class="card match-card" data-match-id="${match.id}">
      <div class="match-card__header">${statusBadge}<span class="text-secondary" style="font-size:0.85em">${formatDate(match.created_at)}</span></div>
      ${areaLine}
      ${contactLine}
      ${actions}
    </div>`;
}

export { findAMentor, listMyMatches, listSchoolMatches, approveMatch, rejectMatch, renderMatchCard };
