/**
 * Amahirwe: browsing, filtering, creating opportunities.
 * Implemented in Phase 7 (Opportunities).
 */

import { api } from "./api.js";
import { talentAreaIcon, talentAreaLabel, formatDate } from "./dashboard.js";

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

function renderOpportunityCard(opportunity) {
  const area = opportunity.talent_area || "";
  const areaTag = opportunity.talent_area
    ? `<span class="chip">${talentAreaIcon(opportunity.talent_area)} ${talentAreaLabel(opportunity.talent_area)}</span>`
    : `<span class="chip chip--muted">Open to all</span>`;
  const statusTag = opportunity.is_active
    ? `<span class="badge badge-success">Active</span>`
    : `<span class="badge badge-neutral">Inactive</span>`;
  const deadline = opportunity.deadline ? `<span class="text-secondary">Due ${formatDate(opportunity.deadline)}</span>` : "";

  return `
    <article class="opp-card" data-id="${opportunity.id}">
      <div class="opp-card__cover" data-area="${area}"></div>
      <div class="opp-card__body">
        <div class="opp-card__meta">${areaTag}${statusTag}</div>
        <h3>${opportunity.title}</h3>
        <p>${opportunity.description}</p>
        <p>${opportunity.location || ""}</p>
        <div class="opp-card__meta">
          ${deadline}
          <div class="card__actions">
            <button type="button" class="btn btn-secondary btn-sm" data-action="toggle-opportunity" data-id="${opportunity.id}" data-active="${opportunity.is_active}">
              ${opportunity.is_active ? "Deactivate" : "Reactivate"}
            </button>
            <button type="button" class="btn btn-danger btn-sm" data-action="delete-opportunity" data-id="${opportunity.id}">Delete</button>
          </div>
        </div>
      </div>
    </article>`;
}

/** A read-only opportunity card for students/teachers/parents/mentors
 * browsing what's available, no management actions. */
function renderPublicOpportunityCard(opportunity) {
  const area = opportunity.talent_area || "";
  const kind = opportunity.talent_area === "leadership" ? "Leadership" : opportunity.talent_area ? talentAreaLabel(opportunity.talent_area) : "Opportunity";
  const deadline = opportunity.deadline ? `Deadline ${formatDate(opportunity.deadline)}` : opportunity.location || "";

  return `
    <article class="opp-card" data-id="${opportunity.id}">
      <div class="opp-card__cover" data-area="${area}"></div>
      <div class="opp-card__body">
        <h3>${opportunity.title}</h3>
        <p>${opportunity.description}</p>
        <div class="opp-card__meta">
          <span class="chip">${kind}</span>
          <span class="text-secondary">${deadline}</span>
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
