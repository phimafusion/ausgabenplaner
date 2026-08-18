// Ausgabenplaner Frontend Application Logic

const state = {
    token: localStorage.getItem("token") || null,
    user: null,
    activePlan: null,
    selectedVersionId: null,
    currentVersionDetails: null,
    isDirty: false,
    isPositionsUnlocked: false,
    isContributionsUnlocked: false,
    unlockedVersionIds: new Set(),
    pendingAction: null, // Callback when confirming discard of unsaved changes
};

// DOM Elements
const elements = {
    loginView: document.getElementById("login-view"),
    dashboardView: document.getElementById("dashboard-view"),
    loginForm: document.getElementById("login-form"),
    loginError: document.getElementById("login-error"),
    btnMobileMenu: document.getElementById("btn-mobile-menu"),
    navbarActions: document.getElementById("navbar-actions"),
    userDisplayName: document.getElementById("user-display-name"),
    userRoleBadge: document.getElementById("user-role-badge"),
    btnRunTests: document.getElementById("btn-run-tests"),
    btnUserMgmt: document.getElementById("btn-user-mgmt"),
    btnLogout: document.getElementById("btn-logout"),

    planTitle: document.getElementById("plan-title"),
    selectVersion: document.getElementById("select-version"),
    draftStatusBadge: document.getElementById("draft-status-badge"),
    btnDiscardDraft: document.getElementById("btn-discard-draft"),
    btnSaveVersion: document.getElementById("btn-save-version"),
    btnOpenHistory: document.getElementById("btn-open-history"),

    kpiExpensesVal: document.getElementById("kpi-expenses-val"),
    kpiContributionsVal: document.getElementById("kpi-contributions-val"),
    kpiBalanceVal: document.getElementById("kpi-balance-val"),
    kpiBalanceCard: document.getElementById("kpi-balance-card"),

    btnToggleUnlockPositions: document.getElementById("btn-toggle-unlock-positions"),
    tablePositionsBody: document.querySelector("#table-positions tbody"),
    sumPositionsVal: document.getElementById("sum-positions-val"),
    sumPositionsColspan: document.getElementById("sum-positions-colspan"),
    btnAddPosition: document.getElementById("btn-add-position"),

    btnToggleUnlockContributions: document.getElementById("btn-toggle-unlock-contributions"),
    tableContributionsBody: document.querySelector("#table-contributions tbody"),
    sumContributionsVal: document.getElementById("sum-contributions-val"),
    sumContributionsColspan: document.getElementById("sum-contributions-colspan"),
    btnAddContribution: document.getElementById("btn-add-contribution"),

    // Modals
    modalPosition: document.getElementById("modal-position"),
    formPosition: document.getElementById("form-position"),
    posId: document.getElementById("pos-id"),
    posTitle: document.getElementById("pos-title"),
    posInterval: document.getElementById("pos-interval"),
    posRawAmount: document.getElementById("pos-raw-amount"),
    posCalculatedMonthlyVal: document.getElementById("pos-calculated-monthly-val"),
    posAmount: document.getElementById("pos-amount"),
    posComment: document.getElementById("pos-comment"),
    modalPosTitle: document.getElementById("modal-position-title"),

    modalContribution: document.getElementById("modal-contribution"),
    formContribution: document.getElementById("form-contribution"),
    contribId: document.getElementById("contrib-id"),
    contribPerson: document.getElementById("contrib-person"),
    contribAmount: document.getElementById("contrib-amount"),
    contribComment: document.getElementById("contrib-comment"),
    modalContribTitle: document.getElementById("modal-contrib-title"),

    // Save Version Modal
    modalSaveVersion: document.getElementById("modal-save-version"),
    formSaveVersion: document.getElementById("form-save-version"),
    saveVersionTitle: document.getElementById("save-version-title"),
    saveVersionDate: document.getElementById("save-version-date"),
    saveSummaryPosCount: document.getElementById("save-summary-pos-count"),
    saveSummaryExpenses: document.getElementById("save-summary-expenses"),
    saveSummaryContribCount: document.getElementById("save-summary-contrib-count"),
    saveSummaryContributions: document.getElementById("save-summary-contributions"),
    saveSummaryBalance: document.getElementById("save-summary-balance"),

    // History Modal
    modalHistory: document.getElementById("modal-history"),
    tabBtnTimeline: document.getElementById("tab-btn-timeline"),
    tabBtnMatrix: document.getElementById("tab-btn-matrix"),
    historyTabTimeline: document.getElementById("history-tab-timeline"),
    historyTabMatrix: document.getElementById("history-tab-matrix"),
    historyTimelineList: document.getElementById("history-timeline-list"),
    historyContainer: document.getElementById("history-comparison-container"),

    // Version Edit Modal (Unlocked)
    modalVersionEdit: document.getElementById("modal-version-edit"),
    formVersionEdit: document.getElementById("form-version-edit"),
    editVerId: document.getElementById("edit-ver-id"),
    editVerTitle: document.getElementById("edit-ver-title"),
    editVerDate: document.getElementById("edit-ver-date"),

    // Confirm Delete Version Modal
    modalConfirmDeleteVersion: document.getElementById("modal-confirm-delete-version"),
    deleteVersionId: document.getElementById("delete-version-id"),
    deleteVersionTitleDisplay: document.getElementById("delete-version-title-display"),
    deleteVersionActiveWarning: document.getElementById("delete-version-active-warning"),
    btnExecuteDeleteVersion: document.getElementById("btn-execute-delete-version"),

    // Confirm Discard Draft Modal
    modalConfirmDiscardDraft: document.getElementById("modal-confirm-discard-draft"),
    btnExecuteDiscardDraft: document.getElementById("btn-execute-discard-draft"),

    // Unsaved Warning Modal
    modalUnsavedWarning: document.getElementById("modal-unsaved-warning"),
    btnDiscardUnsaved: document.getElementById("btn-discard-unsaved"),
    btnSaveBeforeAction: document.getElementById("btn-save-before-action"),

    modalUsers: document.getElementById("modal-users"),
    formUserCreate: document.getElementById("form-user-create"),
    userEditId: document.getElementById("user-edit-id"),
    userUsername: document.getElementById("user-username"),
    userName: document.getElementById("user-name"),
    userPassword: document.getElementById("user-password"),
    userPasswordLabel: document.getElementById("user-password-label"),
    userPasswordHelp: document.getElementById("user-password-help"),
    userRole: document.getElementById("user-role"),
    userCanExport: document.getElementById("user-can-export"),
    userFormHeading: document.getElementById("user-form-heading"),
    btnSubmitUser: document.getElementById("btn-submit-user"),
    btnCancelUserEdit: document.getElementById("btn-cancel-user-edit"),
    usersList: document.getElementById("users-list"),

    btnExportJson: document.getElementById("btn-export-json"),
    btnImportJson: document.getElementById("btn-import-json"),

    modalImport: document.getElementById("modal-import"),
    formImportJson: document.getElementById("form-import-json"),
    importFileInput: document.getElementById("import-file-input"),
    importError: document.getElementById("import-error"),

    modalTestsuite: document.getElementById("modal-testsuite"),
    testsuiteStatusBox: document.getElementById("testsuite-status-box"),
    testsuiteOutput: document.getElementById("testsuite-output"),
    btnReRunTests: document.getElementById("btn-re-run-tests"),
};

// API Helper
async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        logout();
        throw new Error("Sitzung abgelaufen. Bitte erneut anmelden.");
    }
    return response;
}

// Format Currency DE
function formatCurrency(val) {
    if (val === undefined || val === null || isNaN(val)) return "0,00 €";
    const isNeg = val < 0;
    const absVal = Math.abs(val);
    const parts = absVal.toFixed(2).split(".");
    const intPart = parseInt(parts[0], 10).toLocaleString("de-DE");
    const decPart = parts[1];
    let res = `${intPart},${decPart} €`;
    if (isNeg) res = `-${res}`;
    return res;
}

// Format German Date Helper
function formatGermanDate(isoStr) {
    if (!isoStr) return "";
    const parts = isoStr.split("-");
    if (parts.length === 3) {
        return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return isoStr;
}

// Format German Date-Time Helper for Audit Metadata
function formatDateTimeDE(dtStr) {
    if (!dtStr) return "";
    try {
        const d = new Date(dtStr.replace(" ", "T"));
        if (isNaN(d.getTime())) return dtStr;
        const datePart = d.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
        const timePart = d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
        return `${datePart}, ${timePart} Uhr`;
    } catch {
        return dtStr;
    }
}

function formatVersionDropdownLabel(v) {
    if (!v.effective_date) return v.title;
    const deDate = formatGermanDate(v.effective_date);
    if (v.title.includes(deDate)) {
        return v.title;
    }
    return `${v.title} (ab ${deDate})`;
}

// Status Badge Tracking (Active vs Archived vs Dirty Draft)
function updateDraftStatusBadge() {
    if (!elements.draftStatusBadge) return;

    if (state.isDirty) {
        elements.draftStatusBadge.textContent = "● Ungespeichert";
        elements.draftStatusBadge.className = "badge badge-dirty";
        elements.btnSaveVersion.classList.add("is-dirty");
        if (elements.btnDiscardDraft) elements.btnDiscardDraft.classList.remove("hidden");
        return;
    }

    elements.btnSaveVersion.classList.remove("is-dirty");
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

// Dirty Tracking
function setDirty(isDirty) {
    state.isDirty = isDirty;
    updateDraftStatusBadge();
}

// Lock State Controls for Positions & Contributions
function updateLockControls() {
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

// App Init
async function initApp() {
    setupEventListeners();
    if (state.token) {
        try {
            await fetchCurrentUser();
            showDashboard();
            await loadActivePlan();
        } catch (err) {
            logout();
        }
    } else {
        showLogin();
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // BeforeUnload Warning
    window.addEventListener("beforeunload", (e) => {
        if (state.isDirty) {
            e.preventDefault();
            e.returnValue = "Sie haben ungespeicherte Änderungen.";
        }
    });

    // Login
    elements.loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        elements.loginError.classList.add("hidden");
        const username = elements.loginForm["login-username"].value.trim();
        const password = elements.loginForm["login-password"].value;

        try {
            const resp = await apiFetch("/api/auth/login", {
                method: "POST",
                body: { username, password },
            });
            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || "Anmeldung fehlgeschlagen");
            }
            const data = await resp.json();
            state.token = data.access_token;
            state.user = data.user;
            localStorage.setItem("token", state.token);
            showDashboard();
            await loadActivePlan();
        } catch (err) {
            elements.loginError.textContent = err.message;
            elements.loginError.classList.remove("hidden");
        }
    });

    // Logout
    elements.btnLogout.addEventListener("click", () => {
        guardedAction(() => {
            logout();
        });
    });

    // Mobile Navigation Menu Toggle
    if (elements.btnMobileMenu && elements.navbarActions) {
        elements.btnMobileMenu.addEventListener("click", (e) => {
            e.stopPropagation();
            elements.navbarActions.classList.toggle("is-open");
            elements.btnMobileMenu.classList.toggle("is-active");
        });

        document.addEventListener("click", (e) => {
            if (!elements.navbarActions.contains(e.target) && !elements.btnMobileMenu.contains(e.target)) {
                elements.navbarActions.classList.remove("is-open");
                elements.btnMobileMenu.classList.remove("is-active");
            }
        });

        elements.navbarActions.querySelectorAll("button").forEach((btn) => {
            btn.addEventListener("click", () => {
                elements.navbarActions.classList.remove("is-open");
                elements.btnMobileMenu.classList.remove("is-active");
            });
        });
    }

    // Version dropdown change with dirty check
    elements.selectVersion.addEventListener("change", async (e) => {
        const newVerId = parseInt(e.target.value, 10);
        if (state.isDirty) {
            e.preventDefault();
            // Revert selector visually until confirmed
            elements.selectVersion.value = state.selectedVersionId;
            guardedAction(async () => {
                elements.selectVersion.value = newVerId;
                state.selectedVersionId = newVerId;
                await loadVersionDetails(newVerId);
                setDirty(false);
            });
        } else {
            state.selectedVersionId = newVerId;
            await loadVersionDetails(state.selectedVersionId);
        }
    });

    // Modal Close buttons
    document.querySelectorAll("[data-close]").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            const targetId = e.target.getAttribute("data-close");
            closeModal(targetId);
        });
    });

    // Lock Toggle Handlers for Positions & Contributions
    if (elements.btnToggleUnlockPositions) {
        elements.btnToggleUnlockPositions.addEventListener("click", () => {
            state.isPositionsUnlocked = !state.isPositionsUnlocked;
            updateLockControls();
            if (state.currentVersionDetails) {
                renderVersionDetails(state.currentVersionDetails);
            }
        });
    }

    if (elements.btnToggleUnlockContributions) {
        elements.btnToggleUnlockContributions.addEventListener("click", () => {
            state.isContributionsUnlocked = !state.isContributionsUnlocked;
            updateLockControls();
            if (state.currentVersionDetails) {
                renderVersionDetails(state.currentVersionDetails);
            }
        });
    }

    // Live Calculation of Monthly Expense from Payment Interval
    function updatePositionCalculationPreview() {
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

    if (elements.posRawAmount && elements.posInterval) {
        elements.posRawAmount.addEventListener("input", updatePositionCalculationPreview);
        elements.posInterval.addEventListener("change", updatePositionCalculationPreview);
    }

    // Positions Modals & Forms (Draft in memory)
    elements.btnAddPosition.addEventListener("click", () => {
        elements.formPosition.reset();
        elements.posId.value = "";
        elements.posInterval.value = "monthly";
        elements.posRawAmount.value = "";
        elements.posAmount.value = "";
        elements.posCalculatedMonthlyVal.textContent = "-0,00 € / Monat";
        elements.modalPosTitle.textContent = "Position hinzufügen";
        openModal("modal-position");
    });

    elements.formPosition.addEventListener("submit", (e) => {
        e.preventDefault();
        const id = elements.posId.value;
        const title = elements.posTitle.value.trim();
        updatePositionCalculationPreview();
        const amount = parseFloat(elements.posAmount.value);
        if (isNaN(amount)) {
            alert("Bitte einen gültigen Zahlungsbetrag eingeben.");
            return;
        }
        const comment = elements.posComment.value.trim();

        if (!state.currentVersionDetails) return;

        if (id) {
            // Edit existing
            const pos = state.currentVersionDetails.positions.find((p) => String(p.id) === String(id));
            if (pos) {
                pos.title = title;
                pos.amount = amount;
                pos.amount_formatted = formatCurrency(amount);
                pos.comment = comment;
            }
        } else {
            // New position in draft
            const newPos = {
                id: "temp_" + Date.now(),
                title: title,
                amount: amount,
                amount_formatted: formatCurrency(amount),
                comment: comment,
                category: "Allgemein",
                sort_order: state.currentVersionDetails.positions.length,
            };
            state.currentVersionDetails.positions.push(newPos);
        }

        recalculateDraftTotals();
        renderVersionDetails(state.currentVersionDetails);
        setDirty(true);
        closeModal("modal-position");
    });

    // Contributions Modals & Forms (Draft in memory)
    elements.btnAddContribution.addEventListener("click", () => {
        elements.formContribution.reset();
        elements.contribId.value = "";
        elements.modalContribTitle.textContent = "Beitrag hinzufügen";
        openModal("modal-contribution");
    });

    elements.formContribution.addEventListener("submit", (e) => {
        e.preventDefault();
        const id = elements.contribId.value;
        const person_name = elements.contribPerson.value.trim();
        const amount = parseFloat(elements.contribAmount.value);
        const comment = elements.contribComment.value.trim();

        if (!state.currentVersionDetails) return;

        if (id) {
            // Edit existing
            const contrib = state.currentVersionDetails.contributions.find((c) => String(c.id) === String(id));
            if (contrib) {
                contrib.person_name = person_name;
                contrib.amount = amount;
                contrib.amount_formatted = formatCurrency(amount);
                contrib.comment = comment;
            }
        } else {
            // New contribution in draft
            const newContrib = {
                id: "temp_c_" + Date.now(),
                person_name: person_name,
                amount: amount,
                amount_formatted: formatCurrency(amount),
                comment: comment,
                sort_order: state.currentVersionDetails.contributions.length,
            };
            state.currentVersionDetails.contributions.push(newContrib);
        }

        recalculateDraftTotals();
        renderVersionDetails(state.currentVersionDetails);
        setDirty(true);
        closeModal("modal-contribution");
    });

    // Open Save Version Modal
    elements.btnSaveVersion.addEventListener("click", () => {
        if (!state.currentVersionDetails) return;

        // Populate default values
        const today = new Date();
        const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
        const formattedDate = nextMonth.toISOString().split("T")[0];
        const dateDE = nextMonth.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });

        elements.saveVersionTitle.value = `Stand ab ${dateDE}`;
        elements.saveVersionDate.value = formattedDate;

        // Preview sums
        const totals = state.currentVersionDetails.totals || {};
        elements.saveSummaryPosCount.textContent = state.currentVersionDetails.positions.length;
        elements.saveSummaryExpenses.textContent = totals.total_expenses_formatted || "0,00 €";
        elements.saveSummaryContribCount.textContent = state.currentVersionDetails.contributions.length;
        elements.saveSummaryContributions.textContent = totals.total_contributions_formatted || "0,00 €";
        elements.saveSummaryBalance.textContent = totals.net_balance_formatted || "0,00 €";
        elements.saveSummaryBalance.className = totals.net_balance < 0 ? "text-neg" : "text-pos";

        openModal("modal-save-version");
    });

    // Submit Save Version
    elements.formSaveVersion.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!state.activePlan || !state.currentVersionDetails) return;

        const payload = {
            title: elements.saveVersionTitle.value.trim(),
            effective_date: elements.saveVersionDate.value || null,
            positions: state.currentVersionDetails.positions.map((p, idx) => ({
                title: p.title,
                amount: p.amount,
                comment: p.comment || null,
                category: p.category || "Allgemein",
                sort_order: idx,
            })),
            contributions: state.currentVersionDetails.contributions.map((c, idx) => ({
                person_name: c.person_name,
                amount: c.amount,
                comment: c.comment || null,
                sort_order: idx,
            })),
        };

        try {
            const resp = await apiFetch(`/api/plans/${state.activePlan.id}/save-version`, {
                method: "POST",
                body: payload,
            });
            if (!resp.ok) throw new Error("Fehler beim Speichern des Stands");
            const newVer = await resp.json();

            closeModal("modal-save-version");
            setDirty(false);
            await loadActivePlan();
            state.selectedVersionId = newVer.id;
            elements.selectVersion.value = newVer.id;
            renderVersionDetails(newVer);
        } catch (err) {
            alert(err.message || "Fehler beim Speichern des neuen Stands");
        }
    });

    // History Modal Open & Tab Switching
    elements.btnOpenHistory.addEventListener("click", async () => {
        await loadHistoryTimeline();
        switchHistoryTab("timeline");
        openModal("modal-history");
    });

    elements.tabBtnTimeline.addEventListener("click", () => {
        switchHistoryTab("timeline");
        loadHistoryTimeline();
    });

    elements.tabBtnMatrix.addEventListener("click", () => {
        switchHistoryTab("matrix");
        loadHistoryComparison();
    });

    // Auto-update Stand Title suggestions when Date changes
    if (elements.editVerDate) {
        elements.editVerDate.addEventListener("change", (e) => {
            const d = e.target.value;
            if (!d) return;
            const curVal = elements.editVerTitle.value.trim();
            const formattedDate = formatDateDE(d);
            if (!curVal || curVal.startsWith("Stand ab ") || curVal.startsWith("Stand ")) {
                elements.editVerTitle.value = `Stand ab ${formattedDate}`;
            }
        });
    }

    if (elements.saveVersionDate) {
        elements.saveVersionDate.addEventListener("change", (e) => {
            const d = e.target.value;
            if (!d) return;
            const curVal = elements.saveVersionTitle.value.trim();
            const formattedDate = formatDateDE(d);
            if (!curVal || curVal.startsWith("Stand ab ") || curVal.startsWith("Stand ")) {
                elements.saveVersionTitle.value = `Stand ab ${formattedDate}`;
            }
        });
    }

    // Edit Version Metadata Form (Unlocked or Header Edit)
    elements.formVersionEdit.addEventListener("submit", async (e) => {
        e.preventDefault();
        const verId = parseInt(elements.editVerId.value, 10);
        if (!verId) return;
        const payload = {
            title: elements.editVerTitle.value.trim(),
            effective_date: elements.editVerDate.value || null,
        };

        try {
            const resp = await apiFetch(`/api/versions/${verId}`, {
                method: "PATCH",
                body: payload,
            });
            if (!resp.ok) throw new Error("Fehler beim Aktualisieren des Stands");
            const updatedVer = await resp.json();
            closeModal("modal-version-edit");

            // Update in-memory state
            if (state.currentVersionDetails && state.currentVersionDetails.id === verId) {
                state.currentVersionDetails.title = updatedVer.title;
                state.currentVersionDetails.effective_date = updatedVer.effective_date;
            }

            const currentSelId = state.selectedVersionId || verId;
            await loadActivePlan();
            state.selectedVersionId = currentSelId;
            elements.selectVersion.value = currentSelId;

            // Also reload timeline if history modal was open
            if (!elements.modalHistory.classList.contains("hidden")) {
                await loadHistoryTimeline();
            }
        } catch (err) {
            alert(err.message || "Fehler beim Aktualisieren der Stand-Informationen");
        }
    });

    // Discard Draft Button & Modal Actions
    if (elements.btnDiscardDraft) {
        elements.btnDiscardDraft.addEventListener("click", () => {
            openModal("modal-confirm-discard-draft");
        });
    }

    if (elements.btnExecuteDiscardDraft) {
        elements.btnExecuteDiscardDraft.addEventListener("click", async () => {
            closeModal("modal-confirm-discard-draft");
            await discardCurrentDraft();
        });
    }

    // Execute Delete Version from Modal
    if (elements.btnExecuteDeleteVersion) {
        elements.btnExecuteDeleteVersion.addEventListener("click", async () => {
            const versionId = parseInt(elements.deleteVersionId.value, 10);
            if (!versionId) return;

            try {
                const resp = await apiFetch(`/api/versions/${versionId}`, { method: "DELETE" });
                if (!resp.ok) {
                    const errData = await resp.json();
                    throw new Error(errData.detail || "Fehler beim Löschen des Stands");
                }
                closeModal("modal-confirm-delete-version");
                state.unlockedVersionIds.delete(versionId);
                await loadActivePlan();
                await loadHistoryTimeline();
                if (state.isDirty) {
                    setDirty(false);
                }
            } catch (err) {
                alert(err.message || "Fehler beim Löschen des Stands");
            }
        });
    }

    // Unsaved Warning Modal Actions
    elements.btnDiscardUnsaved.addEventListener("click", () => {
        closeModal("modal-unsaved-warning");
        setDirty(false);
        if (typeof state.pendingAction === "function") {
            const action = state.pendingAction;
            state.pendingAction = null;
            action();
        } else {
            discardCurrentDraft();
        }
    });

    elements.btnSaveBeforeAction.addEventListener("click", () => {
        closeModal("modal-unsaved-warning");
        elements.btnSaveVersion.click();
    });

    // Export JSON
    elements.btnExportJson.addEventListener("click", async () => {
        try {
            const resp = await apiFetch("/api/data/export");
            if (!resp.ok) throw new Error("Export fehlgeschlagen");
            const data = await resp.json();
            const jsonStr = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonStr], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            const dateStr = new Date().toISOString().split("T")[0];
            a.href = url;
            a.download = `ausgabenplaner_export_${dateStr}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            alert(err.message || "Fehler beim Exportieren der Daten");
        }
    });

    // Import JSON
    elements.btnImportJson.addEventListener("click", () => {
        elements.formImportJson.reset();
        elements.importError.classList.add("hidden");
        openModal("modal-import");
    });

    elements.formImportJson.addEventListener("submit", async (e) => {
        e.preventDefault();
        elements.importError.classList.add("hidden");
        const file = elements.importFileInput.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const payload = JSON.parse(text);

            const resp = await apiFetch("/api/data/import", {
                method: "POST",
                body: payload,
            });

            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || "Import fehlgeschlagen");
            }

            closeModal("modal-import");
            setDirty(false);
            await loadActivePlan();
            alert("Daten erfolgreich wiederhergestellt!");
        } catch (err) {
            elements.importError.textContent = err.message || "Fehler beim Importieren der Datei. Bitte prüfen Sie das JSON-Format.";
            elements.importError.classList.remove("hidden");
        }
    });

    // User Management (Admin)
    elements.btnUserMgmt.addEventListener("click", async () => {
        resetUserForm();
        await loadUsersList();
        openModal("modal-users");
    });

    if (elements.btnCancelUserEdit) {
        elements.btnCancelUserEdit.addEventListener("click", () => {
            resetUserForm();
        });
    }

    // Testsuite Runner (Admin)
    elements.btnRunTests.addEventListener("click", executeTestsuite);
    elements.btnReRunTests.addEventListener("click", executeTestsuite);

    elements.formUserCreate.addEventListener("submit", async (e) => {
        e.preventDefault();
        const editId = elements.userEditId ? elements.userEditId.value : "";
        const username = elements.userUsername.value.trim();
        const name = elements.userName.value.trim();
        const password = elements.userPassword.value;
        const role = elements.userRole.value;
        const can_export = elements.userCanExport ? elements.userCanExport.checked : true;

        if (editId) {
            // Update existing user
            const payload = { name, role, can_export };
            if (password && password.trim()) {
                payload.password = password.trim();
            }
            const resp = await apiFetch(`/api/users/${editId}`, {
                method: "PATCH",
                body: payload,
            });
            if (resp.ok) {
                resetUserForm();
                await loadUsersList();
                // If editing self, update state
                if (state.user && String(state.user.id) === String(editId)) {
                    state.user.name = name;
                    state.user.role = role;
                    state.user.can_export = can_export;
                    showDashboard();
                }
            } else {
                const errData = await resp.json();
                alert(errData.detail || "Fehler beim Aktualisieren des Benutzers");
            }
        } else {
            // Create new user
            const resp = await apiFetch("/api/users", {
                method: "POST",
                body: { username, name, password, role, can_export },
            });

            if (resp.ok) {
                resetUserForm();
                await loadUsersList();
            } else {
                const errData = await resp.json();
                alert(errData.detail || "Fehler beim Erstellen des Benutzers");
            }
        }
    });
}

// Guarded Action Helper: Prompts warning if dirty before continuing
function guardedAction(callback) {
    if (state.isDirty) {
        state.pendingAction = callback;
        openModal("modal-unsaved-warning");
    } else {
        callback();
    }
}

// History Tab Switching
function switchHistoryTab(tabName) {
    if (tabName === "timeline") {
        elements.tabBtnTimeline.classList.add("active");
        elements.tabBtnMatrix.classList.remove("active");
        elements.historyTabTimeline.classList.remove("hidden");
        elements.historyTabMatrix.classList.add("hidden");
    } else {
        elements.tabBtnTimeline.classList.remove("active");
        elements.tabBtnMatrix.classList.add("active");
        elements.historyTabTimeline.classList.add("hidden");
        elements.historyTabMatrix.classList.remove("hidden");
    }
}

// Recalculate Draft Totals in Memory
function recalculateDraftTotals() {
    if (!state.currentVersionDetails) return;

    let totalExpenses = 0.0;
    state.currentVersionDetails.positions.forEach((p) => {
        totalExpenses += parseFloat(p.amount) || 0;
    });

    let totalContrib = 0.0;
    state.currentVersionDetails.contributions.forEach((c) => {
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

// User Actions
async function fetchCurrentUser() {
    const resp = await apiFetch("/api/auth/me");
    state.user = await resp.json();
}

function logout() {
    state.token = null;
    state.user = null;
    state.isDirty = false;
    localStorage.removeItem("token");
    showLogin();
}

function showLogin() {
    elements.loginView.classList.remove("hidden");
    elements.dashboardView.classList.add("hidden");
}

function showDashboard() {
    elements.loginView.classList.add("hidden");
    elements.dashboardView.classList.remove("hidden");

    if (state.user) {
        elements.userDisplayName.textContent = state.user.name || state.user.username;
        elements.userRoleBadge.textContent = state.user.role === "admin" ? "Admin" : "Benutzer";
        if (state.user.role === "admin") {
            elements.btnUserMgmt.classList.remove("hidden");
            elements.btnRunTests.classList.remove("hidden");
            elements.btnExportJson.classList.remove("hidden");
            elements.btnImportJson.classList.remove("hidden");
        } else {
            elements.btnUserMgmt.classList.add("hidden");
            elements.btnRunTests.classList.add("hidden");
            if (state.user.can_export) {
                elements.btnExportJson.classList.remove("hidden");
                elements.btnImportJson.classList.remove("hidden");
            } else {
                elements.btnExportJson.classList.add("hidden");
                elements.btnImportJson.classList.add("hidden");
            }
        }
    }
}

let activeEventSource = null;

async function executeTestsuite() {
    openModal("modal-testsuite");

    if (activeEventSource) {
        activeEventSource.close();
    }

    const progressBar = document.getElementById("testsuite-progress-bar");
    const progressPercent = document.getElementById("testsuite-progress-percent");

    progressBar.style.width = "0%";
    progressPercent.textContent = "0%";
    elements.testsuiteStatusBox.className = "alert alert-info";
    elements.testsuiteStatusBox.textContent = "⏳ Verbinde zur Testsuite...";
    elements.testsuiteOutput.textContent = "";

    const url = `/api/admin/run-tests-stream?token=${encodeURIComponent(state.token)}`;
    const evtSource = new EventSource(url);
    activeEventSource = evtSource;

    evtSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "start") {
                elements.testsuiteStatusBox.textContent = `🚀 ${data.message}`;
            } else if (data.type === "log") {
                if (data.progress !== undefined) {
                    progressBar.style.width = `${data.progress}%`;
                    progressPercent.textContent = `${data.progress}%`;
                }
                elements.testsuiteOutput.textContent += data.line;
                const logBox = document.querySelector(".testsuite-log-box");
                if (logBox) logBox.scrollTop = logBox.scrollHeight;
            } else if (data.type === "complete") {
                evtSource.close();
                progressBar.style.width = "100%";
                progressPercent.textContent = "100%";
                if (data.passed) {
                    elements.testsuiteStatusBox.className = "alert alert-success";
                    elements.testsuiteStatusBox.textContent = "✅ Alle automatisierte Tests erfolgreich bestanden (100% Green)!";
                } else {
                    elements.testsuiteStatusBox.className = "alert alert-danger";
                    elements.testsuiteStatusBox.textContent = "❌ Einige Tests sind fehlgeschlagen.";
                }
            }
        } catch (e) {
            console.error("Event parse error", e);
        }
    };

    evtSource.onerror = () => {
        evtSource.close();
        if (progressBar.style.width !== "100%") {
            elements.testsuiteStatusBox.className = "alert alert-danger";
            elements.testsuiteStatusBox.textContent = "❌ Verbindung zur Testsuite unterbrochen.";
        }
    };
}

// Discard Current Draft & Revert to Saved
async function discardCurrentDraft() {
    if (!state.selectedVersionId) {
        if (state.activePlan && state.activePlan.active_version) {
            state.selectedVersionId = state.activePlan.active_version.id;
        }
    }
    if (state.selectedVersionId) {
        await loadVersionDetails(state.selectedVersionId);
        elements.selectVersion.value = state.selectedVersionId;
    }
    setDirty(false);
}

// Load Active Plan
async function loadActivePlan() {
    const resp = await apiFetch("/api/plans/active");
    if (!resp.ok) return;

    state.activePlan = await resp.json();
    elements.planTitle.textContent = state.activePlan.title;

    // Populate version selector with clean German date format
    elements.selectVersion.innerHTML = "";
    state.activePlan.versions.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = formatVersionDropdownLabel(v);
        elements.selectVersion.appendChild(opt);
    });

    if (state.activePlan.active_version) {
        state.selectedVersionId = state.activePlan.active_version.id;
        elements.selectVersion.value = state.selectedVersionId;
        renderVersionDetails(state.activePlan.active_version);
    }
}

// Load Version Details
async function loadVersionDetails(versionId) {
    const resp = await apiFetch(`/api/versions/${versionId}`);
    if (!resp.ok) return;
    const data = await resp.json();
    renderVersionDetails(data);
}

// Render Version Details
function renderVersionDetails(verData) {
    state.currentVersionDetails = JSON.parse(JSON.stringify(verData)); // deep clone for safe drafting
    const totals = verData.totals || {};

    // Render KPIs
    elements.kpiExpensesVal.textContent = totals.total_expenses_formatted || "0,00 €";
    elements.kpiExpensesVal.className = `kpi-value ${totals.total_expenses < 0 ? "text-neg" : "text-pos"}`;

    elements.kpiContributionsVal.textContent = totals.total_contributions_formatted || "0,00 €";
    elements.kpiContributionsVal.className = `kpi-value ${totals.total_contributions < 0 ? "text-neg" : "text-pos"}`;

    elements.kpiBalanceVal.textContent = totals.net_balance_formatted || "0,00 €";
    elements.kpiBalanceVal.className = `kpi-value ${totals.net_balance < 0 ? "text-neg" : "text-pos"}`;

    elements.kpiBalanceCard.classList.remove("balance-positive", "balance-negative");
    if ((totals.net_balance || 0) >= 0) {
        elements.kpiBalanceCard.classList.add("balance-positive");
    } else {
        elements.kpiBalanceCard.classList.add("balance-negative");
    }

    // Render Positions Table
    elements.tablePositionsBody.innerHTML = "";
    (verData.positions || []).forEach((p) => {
        const tr = document.createElement("tr");
        const amountClass = p.amount < 0 ? "text-neg" : "text-pos";
        tr.innerHTML = `
            <td data-label="Position"><strong>${escapeHtml(p.title)}</strong></td>
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
    elements.sumPositionsVal.textContent = totals.total_expenses_formatted || "0,00 €";
    elements.sumPositionsVal.className = totals.total_expenses < 0 ? "text-neg" : "text-pos";

    // Render Contributions Table
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
    elements.sumContributionsVal.textContent = totals.total_contributions_formatted || "0,00 €";
    elements.sumContributionsVal.className = totals.total_contributions < 0 ? "text-neg" : "text-pos";

    updateLockControls();
    updateDraftStatusBadge();
}

// Edit/Delete handlers in Draft
window.editPosition = (posId) => {
    const pos = state.currentVersionDetails.positions.find((p) => String(p.id) === String(posId));
    if (!pos) return;
    elements.posId.value = pos.id;
    elements.posTitle.value = pos.title;
    elements.posInterval.value = "monthly";
    elements.posRawAmount.value = Math.abs(pos.amount);
    elements.posAmount.value = pos.amount;
    elements.posComment.value = pos.comment || "";
    elements.posCalculatedMonthlyVal.textContent = `${formatCurrency(pos.amount)} / Monat`;
    elements.modalPosTitle.textContent = "Position bearbeiten";
    openModal("modal-position");
};

window.deletePosition = (posId) => {
    if (!state.currentVersionDetails) return;
    state.currentVersionDetails.positions = state.currentVersionDetails.positions.filter(
        (p) => String(p.id) !== String(posId)
    );
    recalculateDraftTotals();
    renderVersionDetails(state.currentVersionDetails);
    setDirty(true);
};

window.editContribution = (contribId) => {
    const c = state.currentVersionDetails.contributions.find((item) => String(item.id) === String(contribId));
    if (!c) return;
    elements.contribId.value = c.id;
    elements.contribPerson.value = c.person_name;
    elements.contribAmount.value = c.amount;
    elements.contribComment.value = c.comment || "";
    elements.modalContribTitle.textContent = "Beitrag bearbeiten";
    openModal("modal-contribution");
};

window.deleteContribution = (contribId) => {
    if (!state.currentVersionDetails) return;
    state.currentVersionDetails.contributions = state.currentVersionDetails.contributions.filter(
        (c) => String(c.id) !== String(contribId)
    );
    recalculateDraftTotals();
    renderVersionDetails(state.currentVersionDetails);
    setDirty(true);
};

// History Timeline List Loader & Renderer
async function loadHistoryTimeline() {
    if (!state.activePlan) return;
    const resp = await apiFetch(`/api/plans/${state.activePlan.id}/history`);
    if (!resp.ok) return;
    const history = await resp.json();

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

// Lock Toggle
window.toggleVersionLock = (versionId) => {
    if (state.unlockedVersionIds.has(versionId)) {
        state.unlockedVersionIds.delete(versionId);
    } else {
        state.unlockedVersionIds.add(versionId);
    }
    loadHistoryTimeline();
};

// Option C: Load as Draft
window.loadVersionAsDraft = async (versionId) => {
    guardedAction(async () => {
        closeModal("modal-history");
        const resp = await apiFetch(`/api/versions/${versionId}`);
        if (!resp.ok) return;
        const verData = await resp.json();
        renderVersionDetails(verData);
        setDirty(true);
    });
};

// Option C: Activate Historical Version
window.activateHistoricalVersion = async (versionId) => {
    guardedAction(async () => {
        try {
            const resp = await apiFetch(`/api/versions/${versionId}/activate`, { method: "POST" });
            if (!resp.ok) throw new Error("Fehler beim Aktivieren des Stands");
            closeModal("modal-history");
            setDirty(false);
            await loadActivePlan();
        } catch (err) {
            alert(err.message || "Fehler beim Aktivieren der Version");
        }
    });
};

// Edit Historical Version Metadata (Unlocked)
window.openVersionEditModal = async (versionId, title, date) => {
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
};

// Delete Historical Version (Safety Modal Confirmation)
window.confirmDeleteHistoricalVersion = async (versionId, title, isActive) => {
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
};

window.deleteHistoricalVersion = (versionId, title) => {
    confirmDeleteHistoricalVersion(versionId, title);
};

// Historical Side-by-Side Matrix
async function loadHistoryComparison() {
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

    elements.historyContainer.innerHTML = html;
}

// User Management Form & List Handlers
function resetUserForm() {
    if (elements.formUserCreate) elements.formUserCreate.reset();
    if (elements.userEditId) elements.userEditId.value = "";
    if (elements.userUsername) {
        elements.userUsername.disabled = false;
        elements.userUsername.value = "";
    }
    if (elements.userName) elements.userName.value = "";
    if (elements.userPassword) {
        elements.userPassword.value = "";
        elements.userPassword.required = true;
    }
    if (elements.userPasswordHelp) elements.userPasswordHelp.classList.add("hidden");
    if (elements.userRole) elements.userRole.value = "user";
    if (elements.userCanExport) elements.userCanExport.checked = true;
    if (elements.userFormHeading) elements.userFormHeading.textContent = "Neuen Benutzer anlegen";
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "Benutzer erstellen";
    if (elements.btnCancelUserEdit) elements.btnCancelUserEdit.classList.add("hidden");
}

window.startEditUser = (user) => {
    if (typeof user === "string") {
        try { user = JSON.parse(user); } catch (e) {}
    }
    if (!user) return;
    if (elements.userEditId) elements.userEditId.value = user.id;
    if (elements.userUsername) {
        elements.userUsername.value = user.username;
        elements.userUsername.disabled = true;
    }
    if (elements.userName) elements.userName.value = user.name;
    if (elements.userPassword) {
        elements.userPassword.value = "";
        elements.userPassword.required = false;
    }
    if (elements.userPasswordHelp) elements.userPasswordHelp.classList.remove("hidden");
    if (elements.userRole) elements.userRole.value = user.role;
    if (elements.userCanExport) elements.userCanExport.checked = !!user.can_export;
    if (elements.userFormHeading) elements.userFormHeading.textContent = `Benutzer „${user.username}“ bearbeiten`;
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "💾 Änderungen speichern";
    if (elements.btnCancelUserEdit) elements.btnCancelUserEdit.classList.remove("hidden");
};

window.deleteUser = async (userId, username) => {
    if (!confirm(`Möchten Sie den Benutzer „${username}“ wirklich löschen?`)) {
        return;
    }
    try {
        const resp = await apiFetch(`/api/users/${userId}`, { method: "DELETE" });
        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || "Fehler beim Löschen des Benutzers");
        }
        await loadUsersList();
    } catch (err) {
        alert(err.message || "Fehler beim Löschen des Benutzers");
    }
};

// Users List Loader
async function loadUsersList() {
    const resp = await apiFetch("/api/users");
    if (!resp.ok) return;
    const users = await resp.json();
    elements.usersList.innerHTML = "";
    users.forEach((u) => {
        const li = document.createElement("li");
        li.className = "user-list-item";
        const uJson = JSON.stringify(u).replace(/'/g, "&#39;");
        li.innerHTML = `
            <div class="user-info">
                <div class="user-name-line">
                    <strong>${escapeHtml(u.name)}</strong>
                    <span class="text-muted" style="font-size: 0.85rem;">(@${escapeHtml(u.username)})</span>
                </div>
                <div class="user-badges-line">
                    <span class="badge ${u.role === "admin" ? "badge-admin" : "badge-user"}">${u.role === "admin" ? "👑 Administrator" : "👤 Benutzer"}</span>
                    <span class="badge ${u.can_export ? "badge-saved" : "badge-archived"}">${u.can_export ? "💾 Export erlaubt" : "🔒 Kein Export"}</span>
                </div>
            </div>
            <div class="user-item-actions">
                <button type="button" class="btn btn-sm btn-outline btn-icon" onclick='startEditUser(${uJson})' title="Benutzer bearbeiten">✏️</button>
                ${u.username !== "admin" ? `<button type="button" class="btn btn-sm btn-danger btn-icon" onclick="deleteUser(${u.id}, '${escapeHtml(u.username)}')" title="Benutzer löschen">🗑️</button>` : ''}
            </div>
        `;
        elements.usersList.appendChild(li);
    });
}

// Modal Helpers
function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove("hidden");
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add("hidden");
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

// Boot app
document.addEventListener("DOMContentLoaded", initApp);

