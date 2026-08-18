// KPI Calculation & Status Badges
import { state } from "../state.js";
import { elements } from "../dom.js";
import { formatCurrency } from "../formatters.js";

export function updateDraftStatusBadge() {
    if (!elements.draftStatusBadge) return;

    if (state.isDirty) {
        elements.draftStatusBadge.textContent = "● Ungespeichert";
        elements.draftStatusBadge.className = "badge badge-dirty";
        if (elements.btnSaveVersion) elements.btnSaveVersion.classList.add("is-dirty");
        if (elements.btnDiscardDraft) elements.btnDiscardDraft.classList.remove("hidden");
        return;
    }

    if (elements.btnSaveVersion) elements.btnSaveVersion.classList.remove("is-dirty");
    if (elements.btnDiscardDraft) elements.btnDiscardDraft.classList.add("hidden");

    const curVerId = state.selectedVersionId || (state.currentVersionDetails ? state.currentVersionDetails.id : null);
    const activeVerId = state.activePlan && state.activePlan.active_version ? state.activePlan.active_version.id : null;
    const isCurActive = curVerId && activeVerId && curVerId === activeVerId;

    if (isCurActive) {
        elements.draftStatusBadge.textContent = "✓ Stand aktuell";
        elements.draftStatusBadge.className = "badge badge-saved";
    } else {
        elements.draftStatusBadge.textContent = "📁 Archiviert";
        elements.draftStatusBadge.className = "badge badge-archived";
    }
}

export function recalculateDraftTotals() {
    if (!state.currentVersionDetails) return;

    let totalExpenses = 0.0;
    (state.currentVersionDetails.positions || []).forEach((p) => {
        totalExpenses += parseFloat(p.amount) || 0;
    });

    let totalContrib = 0.0;
    (state.currentVersionDetails.contributions || []).forEach((c) => {
        totalContrib += parseFloat(c.amount) || 0;
    });

    const netBalance = totalContrib + totalExpenses;

    state.currentVersionDetails.totals = {
        total_expenses: totalExpenses,
        total_expenses_formatted: formatCurrency(totalExpenses),
        total_contributions: totalContrib,
        total_contributions_formatted: formatCurrency(totalContrib),
        net_balance: netBalance,
        net_balance_formatted: formatCurrency(netBalance),
    };
}

export function renderKPIs(totals = {}) {
    if (elements.kpiExpensesVal) {
        elements.kpiExpensesVal.textContent = totals.total_expenses_formatted || "0,00 €";
        elements.kpiExpensesVal.className = `kpi-value ${totals.total_expenses < 0 ? "text-neg" : "text-pos"}`;
    }

    if (elements.kpiContributionsVal) {
        elements.kpiContributionsVal.textContent = totals.total_contributions_formatted || "0,00 €";
        elements.kpiContributionsVal.className = `kpi-value ${totals.total_contributions < 0 ? "text-neg" : "text-pos"}`;
    }

    if (elements.kpiBalanceVal) {
        elements.kpiBalanceVal.textContent = totals.net_balance_formatted || "0,00 €";
        elements.kpiBalanceVal.className = `kpi-value ${totals.net_balance < 0 ? "text-neg" : "text-pos"}`;
    }

    if (elements.kpiBalanceCard) {
        elements.kpiBalanceCard.classList.remove("balance-positive", "balance-negative");
        if ((totals.net_balance || 0) >= 0) {
            elements.kpiBalanceCard.classList.add("balance-positive");
        } else {
            elements.kpiBalanceCard.classList.add("balance-negative");
        }
    }
}
