// Tables Rendering & In-Memory Draft Actions
import { state, setDirty } from "../state.js";
import { elements } from "../dom.js";
import { formatCurrency, escapeHtml } from "../formatters.js";
import { openModal } from "./modals.js";
import { renderKPIs, recalculateDraftTotals, updateDraftStatusBadge } from "./kpi.js";
import { getCategoryBadgeHtml } from "./categories.js";

export function updateLockControls() {
    // Positions
    if (elements.btnToggleUnlockPositions) {
        if (state.isPositionsUnlocked) {
            elements.btnToggleUnlockPositions.className = "btn-lock-toggle is-unlocked";
            elements.btnToggleUnlockPositions.innerHTML = "🔓 Entsperrt";
            elements.btnToggleUnlockPositions.title = "Wieder sperren (Schreibschutz aktivieren)";
            if (elements.btnAddPosition) elements.btnAddPosition.classList.remove("hidden");
        } else {
            elements.btnToggleUnlockPositions.className = "btn-lock-toggle";
            elements.btnToggleUnlockPositions.innerHTML = "🔒 Entsperren";
            elements.btnToggleUnlockPositions.title = "Bearbeitung entsperren";
            if (elements.btnAddPosition) elements.btnAddPosition.classList.add("hidden");
        }
    }
    const thPosActions = document.querySelector("#table-positions .th-actions");
    if (thPosActions) {
        thPosActions.classList.toggle("hidden", !state.isPositionsUnlocked);
    }
    if (elements.sumPositionsColspan) {
        elements.sumPositionsColspan.colSpan = state.isPositionsUnlocked ? 2 : 1;
    }

    // Contributions
    if (elements.btnToggleUnlockContributions) {
        if (state.isContributionsUnlocked) {
            elements.btnToggleUnlockContributions.className = "btn-lock-toggle is-unlocked";
            elements.btnToggleUnlockContributions.innerHTML = "🔓 Entsperrt";
            elements.btnToggleUnlockContributions.title = "Wieder sperren (Schreibschutz aktivieren)";
            if (elements.btnAddContribution) elements.btnAddContribution.classList.remove("hidden");
        } else {
            elements.btnToggleUnlockContributions.className = "btn-lock-toggle";
            elements.btnToggleUnlockContributions.innerHTML = "🔒 Entsperren";
            elements.btnToggleUnlockContributions.title = "Bearbeitung entsperren";
            if (elements.btnAddContribution) elements.btnAddContribution.classList.add("hidden");
        }
    }
    const thContribActions = document.querySelector("#table-contributions .th-actions");
    if (thContribActions) {
        thContribActions.classList.toggle("hidden", !state.isContributionsUnlocked);
    }
    if (elements.sumContributionsColspan) {
        elements.sumContributionsColspan.colSpan = state.isContributionsUnlocked ? 2 : 1;
    }
}

export function updatePositionCalculationPreview() {
    if (!elements.posRawAmount || !elements.posInterval || !elements.posCalculatedMonthlyVal) return;
    const rawVal = parseFloat(elements.posRawAmount.value);
    if (isNaN(rawVal)) {
        elements.posCalculatedMonthlyVal.textContent = "-0,00 € / Monat";
        elements.posAmount.value = "";
        return;
    }

    const interval = elements.posInterval.value;
    let divisor = 1;
    if (interval === "quarterly") divisor = 3;
    else if (interval === "yearly") divisor = 12;

    const absAmount = Math.abs(rawVal);
    const monthlyAbs = Math.round((absAmount / divisor) * 100) / 100;
    const finalMonthlyVal = -monthlyAbs; // Negative for expense

    elements.posAmount.value = finalMonthlyVal;
    elements.posCalculatedMonthlyVal.textContent = `${formatCurrency(finalMonthlyVal)} / Monat`;
}

export function renderVersionDetails(verData) {
    state.currentVersionDetails = JSON.parse(JSON.stringify(verData)); // deep clone for safe drafting
    const totals = verData.totals || {};

    renderKPIs(totals);

    const allPositions = verData.positions || [];
    const query = (state.posSearchQuery || "").toLowerCase().trim();
    const catFilter = (state.posCategoryFilter || "").toLowerCase().trim();
    const typeFilter = state.posTypeFilter || "all";

    const isFilterActive = Boolean(query || catFilter || (typeFilter && typeFilter !== "all"));

    const filteredPositions = allPositions.filter((p) => {
        // 1. Text Search (title and comment)
        if (query) {
            const titleMatch = (p.title || "").toLowerCase().includes(query);
            const commentMatch = (p.comment || "").toLowerCase().includes(query);
            if (!titleMatch && !commentMatch) return false;
        }
        // 2. Category Filter
        if (catFilter) {
            const pCat = (p.category || "Allgemein").toLowerCase();
            if (pCat !== catFilter) return false;
        }
        // 3. Type Filter
        if (typeFilter === "expense" && p.amount >= 0) return false;
        if (typeFilter === "income" && p.amount < 0) return false;

        return true;
    });

    // Update Filter Count Badge & Reset Button
    if (elements.posFilterCountBadge) {
        if (isFilterActive) {
            elements.posFilterCountBadge.style.display = "inline-flex";
            elements.posFilterCountBadge.textContent = `${filteredPositions.length} von ${allPositions.length} Positionen`;
        } else {
            elements.posFilterCountBadge.style.display = "none";
        }
    }
    if (elements.btnResetFilters) {
        elements.btnResetFilters.classList.toggle("hidden", !isFilterActive);
    }

    // Render Positions Table
    if (elements.tablePositionsBody) {
        elements.tablePositionsBody.innerHTML = "";

        if (filteredPositions.length === 0) {
            const emptyTr = document.createElement("tr");
            const colCount = state.isPositionsUnlocked ? 5 : 4;
            emptyTr.innerHTML = `
                <td colspan="${colCount}" class="text-center text-muted" style="padding: 24px;">
                    ${isFilterActive ? '🔍 Keine passenden Positionen für diesen Filter gefunden.' : 'Keine Positionen vorhanden.'}
                </td>
            `;
            elements.tablePositionsBody.appendChild(emptyTr);
        } else {
            filteredPositions.forEach((p) => {
                const tr = document.createElement("tr");
                const amountClass = p.amount < 0 ? "text-neg" : "text-pos";
                tr.innerHTML = `
                    <td data-label="Position"><strong>${escapeHtml(p.title)}</strong></td>
                    <td data-label="Kategorie">${getCategoryBadgeHtml(p.category)}</td>
                    <td data-label="Kosten" class="${amountClass}">${escapeHtml(p.amount_formatted || formatCurrency(p.amount))}</td>
                    <td data-label="Bemerkung" class="text-muted">${escapeHtml(p.comment || "")}</td>
                    ${state.isPositionsUnlocked ? `
                    <td data-label="Aktionen" class="actions-cell">
                        <button class="btn btn-sm btn-outline btn-icon" onclick="editPosition('${p.id}')" title="Bearbeiten" aria-label="Bearbeiten">✏️</button>
                        <button class="btn btn-sm btn-danger btn-icon" onclick="deletePosition('${p.id}')" title="Löschen" aria-label="Löschen">🗑️</button>
                    </td>` : ''}
                `;
                elements.tablePositionsBody.appendChild(tr);
            });
        }
    }

    if (elements.sumPositionsVal) {
        elements.sumPositionsVal.textContent = totals.total_expenses_formatted || "0,00 €";
        elements.sumPositionsVal.className = totals.total_expenses < 0 ? "text-neg" : "text-pos";
    }

    // Render Contributions Table
    if (elements.tableContributionsBody) {
        elements.tableContributionsBody.innerHTML = "";
        (verData.contributions || []).forEach((c) => {
            const tr = document.createElement("tr");
            const amountClass = c.amount < 0 ? "text-neg" : "text-pos";
            tr.innerHTML = `
                <td data-label="Person"><strong>Zahlung ${escapeHtml(c.person_name)}</strong></td>
                <td data-label="Betrag" class="${amountClass}">${escapeHtml(c.amount_formatted || formatCurrency(c.amount))}</td>
                <td data-label="Bemerkung" class="text-muted">${escapeHtml(c.comment || "")}</td>
                ${state.isContributionsUnlocked ? `
                <td data-label="Aktionen" class="actions-cell">
                    <button class="btn btn-sm btn-outline btn-icon" onclick="editContribution('${c.id}')" title="Bearbeiten" aria-label="Bearbeiten">✏️</button>
                    <button class="btn btn-sm btn-danger btn-icon" onclick="deleteContribution('${c.id}')" title="Löschen" aria-label="Löschen">🗑️</button>
                </td>` : ''}
            `;
            elements.tableContributionsBody.appendChild(tr);
        });
    }

    if (elements.sumContributionsVal) {
        elements.sumContributionsVal.textContent = totals.total_contributions_formatted || "0,00 €";
        elements.sumContributionsVal.className = totals.total_contributions < 0 ? "text-neg" : "text-pos";
    }

    updateLockControls();
    updateDraftStatusBadge();
}

export function editPosition(posId) {
    if (!state.currentVersionDetails) return;
    const pos = state.currentVersionDetails.positions.find((p) => String(p.id) === String(posId));
    if (!pos) return;
    elements.posId.value = pos.id;
    elements.posTitle.value = pos.title;
    elements.posInterval.value = "monthly";
    elements.posRawAmount.value = Math.abs(pos.amount);
    elements.posAmount.value = pos.amount;
    if (elements.posCategory) {
        elements.posCategory.value = pos.category || "Allgemein";
    }
    elements.posComment.value = pos.comment || "";
    elements.posCalculatedMonthlyVal.textContent = `${formatCurrency(pos.amount)} / Monat`;
    elements.modalPosTitle.textContent = "Position bearbeiten";
    openModal("modal-position");
}

export function deletePosition(posId) {
    if (!state.currentVersionDetails) return;
    state.currentVersionDetails.positions = state.currentVersionDetails.positions.filter(
        (p) => String(p.id) !== String(posId)
    );
    recalculateDraftTotals();
    renderVersionDetails(state.currentVersionDetails);
    setDirty(true);
}

export function editContribution(contribId) {
    if (!state.currentVersionDetails) return;
    const c = state.currentVersionDetails.contributions.find((item) => String(item.id) === String(contribId));
    if (!c) return;
    elements.contribId.value = c.id;
    elements.contribPerson.value = c.person_name;
    elements.contribAmount.value = c.amount;
    elements.contribComment.value = c.comment || "";
    elements.modalContribTitle.textContent = "Beitrag bearbeiten";
    openModal("modal-contribution");
}

export function deleteContribution(contribId) {
    if (!state.currentVersionDetails) return;
    state.currentVersionDetails.contributions = state.currentVersionDetails.contributions.filter(
        (c) => String(c.id) !== String(contribId)
    );
    recalculateDraftTotals();
    renderVersionDetails(state.currentVersionDetails);
    setDirty(true);
}

// Window attachments for inline HTML onclick handlers
window.editPosition = editPosition;
window.deletePosition = deletePosition;
window.editContribution = editContribution;
window.deleteContribution = deleteContribution;
