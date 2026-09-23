/**
 * Amahirwe: browsing, filtering, creating opportunities.
 * Implemented in Phase 7 (Opportunities).
 */

import { api } from "./api.js";
import { talentAreaIcon, talentAreaLabel, formatDate } from "./dashboard.js";
import { t } from "./main.js";

function listOpportunities(talentArea) {
  const query = talentArea ? `?talent_area=${talentArea}` : "";
  return api.get(`/opportunities${query}`);
}

function listMyOpportunities() {
  return api.get("/opportunities/mine");
}

function createOpportunity(payload) {
  return api.post("/opportunities", payload);
}

function updateOpportunity(id, payload) {
  return api.patch(`/opportunities/${id}`, payload);
}

function deleteOpportunity(id) {
  return api.delete(`/opportunities/${id}`);
}

/** Opportunity title/description/location are provider-entered free
 * text, so this escapes them before interpolating into innerHTML. */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function renderOpportunityCard(opportunity) {
  const area = opportunity.talent_area || "";
  const areaTag = opportunity.talent_area
    ? `<span class="chip">${talentAreaIcon(opportunity.talent_area)} ${talentAreaLabel(opportunity.talent_area)}</span>`
    : `<span class="chip chip--muted">${t("dash_open_to_all", "Open to all talents")}</span>`;
  const statusTag = opportunity.is_active
    ? `<span class="badge badge-success">${t("dash_active", "Active")}</span>`
    : `<span class="badge badge-neutral">${t("dash_inactive", "Inactive")}</span>`;
  const deadline = opportunity.deadline
    ? `<span class="text-secondary">${t("dash_due_date", "Due {date}").replace("{date}", formatDate(opportunity.deadline))}</span>`
    : "";

  return `
    <article class="opp-card" data-id="${opportunity.id}">
      <div class="opp-card__cover" data-area="${area}"></div>
      <div class="opp-card__body">
        <div class="opp-card__meta">${areaTag}${statusTag}</div>
        <h3>${escapeHtml(opportunity.title)}</h3>
        <p>${escapeHtml(opportunity.description)}</p>
        <p>${escapeHtml(opportunity.location || "")}</p>
        <div class="opp-card__meta">
          ${deadline}
          <div class="card__actions">
            <button type="button" class="btn btn-secondary btn-sm" data-action="toggle-opportunity" data-id="${opportunity.id}" data-active="${opportunity.is_active}">
              ${opportunity.is_active ? t("dash_deactivate", "Deactivate") : t("dash_reactivate", "Reactivate")}
            </button>
            <button type="button" class="btn btn-danger btn-sm" data-action="delete-opportunity" data-id="${opportunity.id}">${t("dash_delete", "Delete")}</button>
          </div>
        </div>
      </div>
    </article>`;
}

/** A read-only opportunity card for students/teachers/parents/mentors
 * browsing what's available, no management actions. */
function renderPublicOpportunityCard(opportunity) {
  const area = opportunity.talent_area || "";
  const kind = opportunity.talent_area ? talentAreaLabel(opportunity.talent_area) : t("dash_opportunity_fallback", "Opportunity");
  const deadline = opportunity.deadline
    ? t("dash_deadline_date", "Deadline {date}").replace("{date}", formatDate(opportunity.deadline))
    : opportunity.location || "";

  return `
    <article class="opp-card" data-id="${opportunity.id}">
      <div class="opp-card__cover" data-area="${area}"></div>
      <div class="opp-card__body">
        <h3>${escapeHtml(opportunity.title)}</h3>
        <p>${escapeHtml(opportunity.description)}</p>
        <div class="opp-card__meta">
          <span class="chip">${kind}</span>
          <span class="text-secondary">${escapeHtml(deadline)}</span>
        </div>
      </div>
    </article>`;
}

export {
  listOpportunities,
  listMyOpportunities,
  createOpportunity,
  updateOpportunity,
  deleteOpportunity,
  renderOpportunityCard,
  renderPublicOpportunityCard,
};
