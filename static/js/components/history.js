// History Timeline & Matrix Comparison
import { state, setDirty } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { formatGermanDate, formatDateTimeDE, escapeHtml } from "../formatters.js";
import { openModal, closeModal, guardedAction } from "./modals.js";
import { renderVersionDetails } from "./tables.js";

let onPlanChangedCallback = null;

export function setOnPlanChangedHandler(fn) {
    onPlanChangedCallback = fn;
}

export function switchHistoryTab(tabName) {
    if (tabName === "timeline") {
        if (elements.tabBtnTimeline) elements.tabBtnTimeline.classList.add("active");
        if (elements.tabBtnMatrix) elements.tabBtnMatrix.classList.remove("active");
        if (elements.historyTabTimeline) elements.historyTabTimeline.classList.remove("hidden");
        if (elements.historyTabMatrix) elements.historyTabMatrix.classList.add("hidden");
    } else {
        if (elements.tabBtnTimeline) elements.tabBtnTimeline.classList.remove("active");
        if (elements.tabBtnMatrix) elements.tabBtnMatrix.classList.add("active");
        if (elements.historyTabTimeline) elements.historyTabTimeline.classList.add("hidden");
        if (elements.historyTabMatrix) elements.historyTabMatrix.classList.remove("hidden");
    }
}

export async function loadHistoryTimeline() {
    if (!state.activePlan) return;
    const resp = await apiFetch(`/api/plans/${state.activePlan.id}/history`);
    if (!resp.ok) return;
    const history = await resp.json();

    if (!elements.historyTimelineList) return;
    elements.historyTimelineList.innerHTML = "";

    history.forEach((v) => {
        const isUnlocked = state.unlockedVersionIds.has(v.id);
        const isActive = v.is_active === 1;
        const totals = v.totals || {};

        const card = document.createElement("div");
        card.className = `history-card ${isActive ? "is-active" : ""} ${isUnlocked ? "is-unlocked" : ""}`;
        card.id = `history-card-${v.id}`;

        card.innerHTML = `
            <div class="history-card-header">
                <div class="history-card-title-box">
                    <span class="history-card-title">${escapeHtml(v.title)}</span>
                    ${isActive ? '<span class="badge badge-admin">🟢 Aktuell aktiv</span>' : '<span class="badge" style="background: rgba(255,255,255,0.08); color: var(--text-muted);">Archiviert</span>'}
                    ${isUnlocked ? '<span class="badge badge-dirty">🔓 Entsperrt</span>' : ''}
                </div>
                <div class="history-card-meta">
                    <span>📅 Gültig ab: <strong>${escapeHtml(v.effective_date ? formatGermanDate(v.effective_date) : "ohne Datum")}</strong></span>
                    <span>📑 ${v.positions_count} Positionen</span>
                    <span>👥 ${v.contributions_count} Beitragszahler</span>
                </div>
                <div class="history-card-audit">
                    <span>👤 Angelegt von: <strong>${escapeHtml(v.created_by || "Administrator")}</strong> (${formatDateTimeDE(v.created_at)})</span>
                    ${v.updated_at ? `<span>✏️ Zuletzt geändert von: <strong>${escapeHtml(v.updated_by || "Administrator")}</strong> (${formatDateTimeDE(v.updated_at)})</span>` : ''}
                </div>
            </div>

            <div class="history-card-kpi-grid">
                <div class="history-kpi-item">
                    <span class="history-kpi-label">Ausgaben</span>
                    <span class="history-kpi-val text-neg">${totals.total_expenses_formatted || "0,00 €"}</span>
                </div>
                <div class="history-kpi-item">
                    <span class="history-kpi-label">Beiträge</span>
                    <span class="history-kpi-val text-pos">${totals.total_contributions_formatted || "0,00 €"}</span>
                </div>
                <div class="history-kpi-item">
                    <span class="history-kpi-label">Saldo (Rest)</span>
                    <span class="history-kpi-val ${(totals.net_balance || 0) < 0 ? "text-neg" : "text-pos"}">${totals.net_balance_formatted || "0,00 €"}</span>
                </div>
            </div>

            <div class="history-card-actions">
                <div class="history-actions-left">
                    <button class="btn btn-sm btn-outline" onclick="loadVersionAsDraft(${v.id})" title="Lädt diesen Stand als Vorlage in die Hauptmaske">
                        📝 Als Entwurf laden
                    </button>
                    ${!isActive ? `
                    <button class="btn btn-sm btn-primary" onclick="activateHistoricalVersion(${v.id})" title="Setzt diesen Stand sofort als aktiven Standard-Stand">
                        🚀 Als aktiv setzen
                    </button>` : ''}
                </div>

                <div class="history-actions-right">
                    <button class="btn-lock-toggle ${isUnlocked ? 'is-unlocked' : ''}" onclick="toggleVersionLock(${v.id})" title="${isUnlocked ? 'Wieder sperren' : 'Entsperren zur Bearbeitung'}">
                        ${isUnlocked ? '🔓 Entsperrt' : '🔒 Schreibgeschützt'}
                    </button>
                    ${isUnlocked ? `
                    <div class="unlocked-actions">
                        <button class="btn btn-sm btn-secondary" onclick="openVersionEditModal(${v.id})" title="Stand umbenennen / Datum anpassen">
                            ✏️ Umbenennen
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="confirmDeleteHistoricalVersion(${v.id})" title="Stand unwiderruflich löschen">
                            🗑️ Löschen
                        </button>
                    </div>` : ''}
                </div>
            </div>
        `;

        elements.historyTimelineList.appendChild(card);
    });
}

export function toggleVersionLock(versionId) {
    if (state.unlockedVersionIds.has(versionId)) {
        state.unlockedVersionIds.delete(versionId);
    } else {
        state.unlockedVersionIds.add(versionId);
    }
    loadHistoryTimeline();
}

export async function loadVersionAsDraft(versionId) {
    guardedAction(async () => {
        closeModal("modal-history");
        const resp = await apiFetch(`/api/versions/${versionId}`);
        if (!resp.ok) return;
        const verData = await resp.json();
        renderVersionDetails(verData);
        setDirty(true);
    });
}

export async function activateHistoricalVersion(versionId) {
    guardedAction(async () => {
        try {
            const resp = await apiFetch(`/api/versions/${versionId}/activate`, { method: "POST" });
            if (!resp.ok) throw new Error("Fehler beim Aktivieren des Stands");
            closeModal("modal-history");
            setDirty(false);
            if (typeof onPlanChangedCallback === "function") {
                await onPlanChangedCallback();
            }
        } catch (err) {
            alert(err.message || "Fehler beim Aktivieren der Version");
        }
    });
}

export async function openVersionEditModal(versionId, title, date) {
    if (title !== undefined && date !== undefined) {
        elements.editVerId.value = versionId;
        elements.editVerTitle.value = title;
        elements.editVerDate.value = date;
        openModal("modal-version-edit");
        return;
    }

    let v = state.activePlan && state.activePlan.versions ? state.activePlan.versions.find(x => x.id === versionId) : null;
    if (!v) {
        const resp = await apiFetch(`/api/versions/${versionId}`);
        if (resp.ok) v = await resp.json();
    }
    if (!v) return;
    elements.editVerId.value = v.id;
    elements.editVerTitle.value = v.title || "";
    elements.editVerDate.value = v.effective_date || "";
    openModal("modal-version-edit");
}

export async function confirmDeleteHistoricalVersion(versionId, title, isActive) {
    if (state.activePlan && state.activePlan.versions && state.activePlan.versions.length <= 1) {
        alert("Der letzte verbleibende Stand eines Plans kann nicht gelöscht werden. Ein Plan muss mindestens einen Stand behalten.");
        return;
    }

    let verTitle = title;
    let isAct = isActive;

    if (verTitle === undefined) {
        let v = state.activePlan && state.activePlan.versions ? state.activePlan.versions.find(x => x.id === versionId) : null;
        if (!v) {
            const resp = await apiFetch(`/api/versions/${versionId}`);
            if (resp.ok) v = await resp.json();
        }
        if (!v) return;
        verTitle = v.title;
        isAct = (state.activePlan && state.activePlan.active_version && state.activePlan.active_version.id === versionId) || v.is_active === 1;
    }

    elements.deleteVersionId.value = versionId;
    elements.deleteVersionTitleDisplay.textContent = `„${verTitle}“`;
    if (isAct) {
        elements.deleteVersionActiveWarning.classList.remove("hidden");
    } else {
        elements.deleteVersionActiveWarning.classList.add("hidden");
    }
    openModal("modal-confirm-delete-version");
}

export function deleteHistoricalVersion(versionId, title) {
    confirmDeleteHistoricalVersion(versionId, title);
}

export async function loadHistoryComparison() {
    if (!state.activePlan) return;
    const resp = await apiFetch(`/api/plans/${state.activePlan.id}/history-comparison`);
    if (!resp.ok) return;
    const compData = await resp.json();

    const versions = compData.versions;
    let html = `<table class="matrix-table">
        <thead>
            <tr>
                <th>Position / Person</th>
                <th>Bemerkung</th>`;
    versions.forEach((v) => {
        html += `<th>${escapeHtml(v.title)}</th>`;
    });
    html += `</tr></thead><tbody>`;

    // Positions header
    html += `<tr class="matrix-section-header"><td colspan="${versions.length + 2}">Positionen (Kosten)</td></tr>`;
    compData.rows.forEach((r) => {
        html += `<tr>
            <td><strong>${escapeHtml(r.title)}</strong></td>
            <td class="text-muted">${escapeHtml(r.comment || "")}</td>`;
        versions.forEach((v) => {
            const formatted = r.formatted_values[v.id.toString()] || "-";
            const valClass = formatted && formatted.trim().startsWith("-") ? "text-neg" : (formatted !== "-" ? "text-pos" : "");
            html += `<td class="${valClass}">${formatted}</td>`;
        });
        html += `</tr>`;
    });

    // Contributions header
    html += `<tr class="matrix-section-header"><td colspan="${versions.length + 2}">Personen-Beiträge</td></tr>`;
    compData.contributions_rows.forEach((r) => {
        html += `<tr>
            <td><strong>${escapeHtml(r.title)}</strong></td>
            <td class="text-muted">${escapeHtml(r.comment || "")}</td>`;
        versions.forEach((v) => {
            const formatted = r.formatted_values[v.id.toString()] || "-";
            const valClass = formatted && formatted.trim().startsWith("-") ? "text-neg" : (formatted !== "-" ? "text-pos" : "");
            html += `<td class="${valClass}">${formatted}</td>`;
        });
        html += `</tr>`;
    });

    // Totals SUMME Row
    html += `<tr class="matrix-total-row">
        <td><strong>SUMME (Rest)</strong></td>
        <td></td>`;
    versions.forEach((v) => {
        const tot = compData.totals[v.id.toString()];
        const formatted = tot ? tot.net_balance_formatted : "-";
        const valClass = formatted && formatted.trim().startsWith("-") ? "text-neg" : (formatted !== "-" ? "text-pos" : "");
        html += `<td class="${valClass}"><strong>${formatted}</strong></td>`;
    });
    html += `</tr>`;

    // Audit Info Row
    html += `<tr>
        <td class="text-muted" style="font-size: 0.78rem;"><em>👤 Zuletzt bearbeitet</em></td>
        <td></td>`;
    versions.forEach((v) => {
        const author = v.updated_by || v.created_by || "Administrator";
        const dt = v.updated_at || v.created_at;
        html += `<td class="text-muted" style="font-size: 0.78rem;">${escapeHtml(author)}<br><span style="opacity:0.8;">${formatDateTimeDE(dt)}</span></td>`;
    });
    html += `</tr></tbody></table>`;

    if (elements.historyContainer) {
        elements.historyContainer.innerHTML = html;
    }
}

// Window attachments for inline HTML onclick handlers
window.toggleVersionLock = toggleVersionLock;
window.loadVersionAsDraft = loadVersionAsDraft;
window.activateHistoricalVersion = activateHistoricalVersion;
window.openVersionEditModal = openVersionEditModal;
window.confirmDeleteHistoricalVersion = confirmDeleteHistoricalVersion;
window.deleteHistoricalVersion = deleteHistoricalVersion;
