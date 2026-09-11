/**
 * Amahirwe: browsing, filtering, creating opportunities.
 * Implemented in Phase 7 (Opportunities).
 */

import { api } from "./api.js";
import { talentAreaIcon, talentAreaLabel, formatDate } from "./dashboard.js";

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
  const areaTag = opportunity.talent_area
    ? `<span class="badge badge-mint">${talentAreaIcon(opportunity.talent_area)} ${talentAreaLabel(opportunity.talent_area)}</span>`
    : `<span class="badge badge-neutral">Open to all talents</span>`;
  const statusTag = opportunity.is_active
    ? `<span class="badge badge-success">Active</span>`
    : `<span class="badge badge-neutral">Inactive</span>`;
  const deadline = opportunity.deadline ? `<p class="text-secondary">Deadline: ${formatDate(opportunity.deadline)}</p>` : "";

  return `
    <div class="card opportunity-card" data-id="${opportunity.id}">
      <div class="card__actions" style="justify-content: space-between;">
        ${areaTag}${statusTag}
      </div>
      <h3>${opportunity.title}</h3>
      <p>${opportunity.description}</p>
      <p class="text-secondary">${opportunity.location}</p>
      ${deadline}
      <div class="card__actions">
        <button type="button" class="btn btn-secondary btn-sm" data-action="toggle-opportunity" data-id="${opportunity.id}" data-active="${opportunity.is_active}">
          ${opportunity.is_active ? "Deactivate" : "Reactivate"}
        </button>
        <button type="button" class="btn btn-danger btn-sm" data-action="delete-opportunity" data-id="${opportunity.id}">Delete</button>
      </div>
    </div>`;
}

export { listMyOpportunities, createOpportunity, updateOpportunity, deleteOpportunity, renderOpportunityCard };
