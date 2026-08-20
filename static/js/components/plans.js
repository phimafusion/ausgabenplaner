// Ausgabenplaner Multi-Plan Management Component
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { formatCurrency } from "../formatters.js";
import { openModal, closeModal, guardedAction } from "./modals.js";

let onPlanSwitchedCallback = null;

export function setOnPlanSwitchedHandler(fn) {
    onPlanSwitchedCallback = fn;
}

export async function loadAllPlans() {
    try {
        const resp = await apiFetch("/api/plans?include_archived=true");
        if (!resp.ok) return [];
        state.availablePlans = await resp.json();
        renderPlanDropdown();
        renderPlansManagementGrid();
        return state.availablePlans;
    } catch (err) {
        console.error("Fehler beim Laden der Pläne:", err);
        return [];
    }
}

export function renderPlanDropdown() {
    if (!elements.selectPlan) return;
    elements.selectPlan.innerHTML = "";

    if (!state.availablePlans || state.availablePlans.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Keine Pläne verfügbar";
        elements.selectPlan.appendChild(opt);
        return;
    }

    state.availablePlans.forEach((plan) => {
        const opt = document.createElement("option");
        opt.value = plan.id;
        const statusPrefix = plan.is_archived ? "📦 [Archiviert] " : "📋 ";
        opt.textContent = `${statusPrefix}${plan.title}`;
        elements.selectPlan.appendChild(opt);
    });

    if (state.activePlanId) {
        elements.selectPlan.value = state.activePlanId;
    } else if (state.activePlan) {
        elements.selectPlan.value = state.activePlan.id;
    }
}

export async function switchPlan(planId) {
    const targetId = parseInt(planId, 10);
    if (!targetId || (state.activePlan && state.activePlan.id === targetId && !state.isDirty)) {
        return;
    }

    guardedAction(async () => {
        try {
            const resp = await apiFetch(`/api/plans/${targetId}`);
            if (!resp.ok) {
                const err = await resp.json();
                alert(err.detail || "Fehler beim Wechseln des Plans");
                return;
            }
            state.activePlan = await resp.json();
            state.activePlanId = state.activePlan.id;
            localStorage.setItem("lastSelectedPlanId", state.activePlanId.toString());

            if (elements.selectPlan) elements.selectPlan.value = state.activePlanId;
            if (elements.planTitle) elements.planTitle.textContent = state.activePlan.title;
            if (elements.planArchivedBadge) {
                elements.planArchivedBadge.classList.toggle("hidden", !state.activePlan.is_archived);
            }

            if (typeof onPlanSwitchedCallback === "function") {
                await onPlanSwitchedCallback(state.activePlan);
            }
        } catch (err) {
            console.error("Fehler beim Planwechsel:", err);
        }
    });
}

export function renderPlansManagementGrid() {
    if (!elements.plansGrid) return;
    elements.plansGrid.innerHTML = "";

    if (!state.availablePlans || state.availablePlans.length === 0) {
        elements.plansGrid.innerHTML = `
            <div class="empty-state glass-card" style="padding: 24px; text-align: center; grid-column: 1 / -1;">
                <p class="text-muted">Keine Pläne gefunden.</p>
            </div>
        `;
        return;
    }

    state.availablePlans.forEach((plan) => {
        const isCurrentActive = state.activePlan && state.activePlan.id === plan.id;
        const card = document.createElement("div");
        card.className = `plan-card glass-card ${isCurrentActive ? 'plan-card-active' : ''}`;
        card.style.cssText = "display: flex; flex-direction: column; justify-content: space-between; padding: 20px; border-radius: 12px; position: relative;";

        const statusBadge = plan.is_archived
            ? `<span class="badge badge-warning">📦 Archiviert</span>`
            : `<span class="badge badge-success">✓ Aktiv</span>`;

        const activeTag = isCurrentActive
            ? `<span class="badge badge-admin" style="margin-left: 6px;">Aktuell ausgewählt</span>`
            : '';

        const expFormatted = formatCurrency(plan.total_expenses || 0);
        const conFormatted = formatCurrency(plan.total_contributions || 0);
        const balFormatted = formatCurrency(plan.total_balance || 0);
        const balClass = (plan.total_balance || 0) >= 0 ? "text-pos" : "text-neg";

        card.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; font-size: 1.15rem; color: var(--text-main); font-weight: 600;">${escapeHtml(plan.title)}</h4>
                        <p class="text-muted" style="margin: 4px 0 0 0; font-size: 0.85rem;">${escapeHtml(plan.description || "Keine Beschreibung")}</p>
                    </div>
                    <div style="display: flex; align-items: center;">
                        ${statusBadge}
                        ${activeTag}
                    </div>
                </div>

                <div class="plan-card-metrics" style="background: rgba(15, 23, 42, 0.4); border-radius: 8px; padding: 12px; margin: 14px 0; font-size: 0.88rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span class="text-muted">Stände / Versionen:</span>
                        <strong>${plan.versions_count || 1}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span class="text-muted">Aktiver Stand:</span>
                        <span>${escapeHtml(plan.active_version_title || "Aktueller Stand")}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span class="text-muted">Ausgaben:</span>
                        <span class="text-neg">${expFormatted}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span class="text-muted">Beiträge:</span>
                        <span class="text-pos">${conFormatted}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-weight: 700; border-top: 1px solid var(--border-color); padding-top: 6px; margin-top: 6px;">
                        <span>Saldo:</span>
                        <span class="${balClass}">${balFormatted}</span>
                    </div>
                </div>
            </div>

            <div class="plan-card-actions" style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;">
                <button type="button" class="btn btn-sm ${isCurrentActive ? 'btn-secondary' : 'btn-primary'} btn-plan-select" data-id="${plan.id}" title="Zu diesem Plan wechseln">
                    👁️ Auswählen
                </button>
                <button type="button" class="btn btn-sm btn-outline btn-plan-edit admin-only" data-id="${plan.id}" title="Plan umbenennen / bearbeiten">
                    ✏️ Bearbeiten
                </button>
                <button type="button" class="btn btn-sm btn-outline btn-plan-duplicate admin-only" data-id="${plan.id}" title="Diesen Plan duplizieren (Vorlage)">
                    📋 Duplizieren
                </button>
                <button type="button" class="btn btn-sm btn-outline btn-plan-toggle-archive admin-only" data-id="${plan.id}" data-archived="${plan.is_archived ? '1' : '0'}" title="${plan.is_archived ? 'Plan reaktivieren' : 'Plan archivieren'}">
                    ${plan.is_archived ? '🔄 Reaktivieren' : '📦 Archivieren'}
                </button>
                <button type="button" class="btn btn-sm btn-danger btn-plan-delete admin-only" data-id="${plan.id}" data-title="${escapeHtml(plan.title)}" title="Plan löschen">
                    🗑️
                </button>
            </div>
        `;

        elements.plansGrid.appendChild(card);
    });

    // Wire action buttons
    elements.plansGrid.querySelectorAll(".btn-plan-select").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = parseInt(btn.getAttribute("data-id"), 10);
            switchPlan(id);
            if (typeof window.showDashboardView === "function") {
                window.showDashboardView();
            }
        });
    });

    elements.plansGrid.querySelectorAll(".btn-plan-edit").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = parseInt(btn.getAttribute("data-id"), 10);
            openEditPlanModal(id);
        });
    });

    elements.plansGrid.querySelectorAll(".btn-plan-duplicate").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = parseInt(btn.getAttribute("data-id"), 10);
            openDuplicatePlanModal(id);
        });
    });

    elements.plansGrid.querySelectorAll(".btn-plan-toggle-archive").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const id = parseInt(btn.getAttribute("data-id"), 10);
            const isCurrentlyArchived = btn.getAttribute("data-archived") === "1";
            await toggleArchivePlan(id, !isCurrentlyArchived);
        });
    });

    elements.plansGrid.querySelectorAll(".btn-plan-delete").forEach((btn) => {
        btn.addEventListener("click", () => {
            const id = parseInt(btn.getAttribute("data-id"), 10);
            const title = btn.getAttribute("data-title");
            openDeletePlanModal(id, title);
        });
    });
}

export function openCreatePlanModal() {
    if (elements.formCreatePlan) elements.formCreatePlan.reset();
    openModal("modal-create-plan");
    if (elements.createPlanTitle) elements.createPlanTitle.focus();
}

export async function submitCreatePlan(e) {
    if (e) e.preventDefault();
    const title = elements.createPlanTitle ? elements.createPlanTitle.value.trim() : "";
    const description = elements.createPlanDesc ? elements.createPlanDesc.value.trim() : "";

    if (!title) {
        alert("Bitte geben Sie einen Plan-Namen ein.");
        return;
    }

    try {
        const resp = await apiFetch("/api/plans", {
            method: "POST",
            body: { title, description },
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || "Fehler beim Erstellen des Plans");
            return;
        }

        const newPlan = await resp.json();
        closeModal("modal-create-plan");
        await loadAllPlans();
        await switchPlan(newPlan.id);
        if (typeof window.showDashboardView === "function") {
            window.showDashboardView();
        }
    } catch (err) {
        console.error("Fehler beim Erstellen des Plans:", err);
    }
}

export function openEditPlanModal(planId) {
    const plan = (state.availablePlans || []).find((p) => p.id === planId) || state.activePlan;
    if (!plan) return;

    if (elements.editPlanId) elements.editPlanId.value = plan.id;
    if (elements.editPlanTitle) elements.editPlanTitle.value = plan.title;
    if (elements.editPlanDesc) elements.editPlanDesc.value = plan.description || "";
    if (elements.editPlanArchived) elements.editPlanArchived.checked = !!plan.is_archived;

    openModal("modal-edit-plan");
    if (elements.editPlanTitle) elements.editPlanTitle.focus();
}

export async function submitEditPlan(e) {
    if (e) e.preventDefault();
    const planId = parseInt(elements.editPlanId ? elements.editPlanId.value : "0", 10);
    const title = elements.editPlanTitle ? elements.editPlanTitle.value.trim() : "";
    const description = elements.editPlanDesc ? elements.editPlanDesc.value.trim() : "";
    const isArchived = elements.editPlanArchived ? elements.editPlanArchived.checked : false;

    if (!planId || !title) {
        alert("Bitte einen gültigen Plan-Namen angeben.");
        return;
    }

    try {
        const resp = await apiFetch(`/api/plans/${planId}`, {
            method: "PATCH",
            body: { title, description, is_archived: isArchived },
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || "Fehler beim Speichern des Plans");
            return;
        }

        closeModal("modal-edit-plan");
        await loadAllPlans();
        if (state.activePlan && state.activePlan.id === planId) {
            await switchPlan(planId);
        }
    } catch (err) {
        console.error("Fehler beim Bearbeiten des Plans:", err);
    }
}

export function openDuplicatePlanModal(planId) {
    const plan = (state.availablePlans || []).find((p) => p.id === planId) || state.activePlan;
    if (!plan) return;

    if (elements.duplicatePlanId) elements.duplicatePlanId.value = plan.id;
    if (elements.duplicateSourceName) elements.duplicateSourceName.textContent = plan.title;
    if (elements.duplicatePlanTitle) elements.duplicatePlanTitle.value = `${plan.title} (Kopie)`;

    openModal("modal-duplicate-plan");
    if (elements.duplicatePlanTitle) {
        elements.duplicatePlanTitle.focus();
        elements.duplicatePlanTitle.select();
    }
}

export async function submitDuplicatePlan(e) {
    if (e) e.preventDefault();
    const planId = parseInt(elements.duplicatePlanId ? elements.duplicatePlanId.value : "0", 10);
    const title = elements.duplicatePlanTitle ? elements.duplicatePlanTitle.value.trim() : "";

    if (!planId) return;

    try {
        const resp = await apiFetch(`/api/plans/${planId}/duplicate`, {
            method: "POST",
            body: { title: title || undefined },
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || "Fehler beim Duplizieren des Plans");
            return;
        }

        const newPlan = await resp.json();
        closeModal("modal-duplicate-plan");
        await loadAllPlans();
        await switchPlan(newPlan.id);
        if (typeof window.showDashboardView === "function") {
            window.showDashboardView();
        }
    } catch (err) {
        console.error("Fehler beim Duplizieren des Plans:", err);
    }
}

export async function toggleArchivePlan(planId, newArchivedState) {
    try {
        const resp = await apiFetch(`/api/plans/${planId}`, {
            method: "PATCH",
            body: { is_archived: newArchivedState },
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || "Fehler beim Aktualisieren des Status");
            return;
        }
        await loadAllPlans();
        if (state.activePlan && state.activePlan.id === planId) {
            await switchPlan(planId);
        }
    } catch (err) {
        console.error("Fehler beim Archivieren/Reaktivieren:", err);
    }
}

export function openDeletePlanModal(planId, planTitle) {
    if (elements.deletePlanId) elements.deletePlanId.value = planId;
    if (elements.deletePlanTitleDisplay) elements.deletePlanTitleDisplay.textContent = planTitle || "Plan";
    openModal("modal-confirm-delete-plan");
}

export async function executeDeletePlan() {
    const planId = parseInt(elements.deletePlanId ? elements.deletePlanId.value : "0", 10);
    if (!planId) return;

    try {
        const resp = await apiFetch(`/api/plans/${planId}`, {
            method: "DELETE",
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || "Fehler beim Löschen des Plans");
            return;
        }

        closeModal("modal-confirm-delete-plan");
        await loadAllPlans();

        // If we deleted currently active plan, switch to first remaining plan
        if (state.activePlan && state.activePlan.id === planId) {
            const remaining = state.availablePlans.find((p) => !p.is_archived) || state.availablePlans[0];
            if (remaining) {
                await switchPlan(remaining.id);
            }
        }
    } catch (err) {
        console.error("Fehler beim Löschen des Plans:", err);
    }
}

export function renderUserPlanAssignmentCheckboxes(assignedPlanIds = []) {
    if (!elements.userPlansAssignmentContainer) return;
    elements.userPlansAssignmentContainer.innerHTML = "";

    const assignedSet = new Set(assignedPlanIds || []);
    const plansToDisplay = state.availablePlans || [];

    if (plansToDisplay.length === 0) {
        elements.userPlansAssignmentContainer.innerHTML = `<span class="text-muted" style="font-size: 0.85rem;">Keine Pläne vorhanden.</span>`;
        return;
    }

    plansToDisplay.forEach((plan) => {
        const row = document.createElement("label");
        row.className = "checkbox-label";
        row.style.cssText = "display: flex; align-items: center; gap: 8px; margin-bottom: 6px; cursor: pointer; font-size: 0.88rem;";

        const isChecked = assignedSet.has(plan.id);
        const statusText = plan.is_archived ? " (Archiviert)" : "";

        row.innerHTML = `
            <input type="checkbox" class="user-plan-checkbox" value="${plan.id}" ${isChecked ? 'checked' : ''} style="width: 16px; height: 16px; cursor: pointer;">
            <span>📋 <strong>${escapeHtml(plan.title)}</strong>${statusText}</span>
        `;
        elements.userPlansAssignmentContainer.appendChild(row);
    });
}

export function getSelectedUserPlanIds() {
    if (!elements.userPlansAssignmentContainer) return [];
    const checkboxes = elements.userPlansAssignmentContainer.querySelectorAll(".user-plan-checkbox:checked");
    return Array.from(checkboxes).map((cb) => parseInt(cb.value, 10));
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
