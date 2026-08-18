// Central Event Listeners Setup
import { state, setDirty } from "./state.js";
import { elements } from "./dom.js";
import { apiFetch } from "./api.js";
import { formatCurrency, formatGermanDate } from "./formatters.js";
import { openModal, closeModal, guardedAction } from "./components/modals.js";
import { recalculateDraftTotals } from "./components/kpi.js";
import { updateLockControls, updatePositionCalculationPreview, renderVersionDetails } from "./components/tables.js";
import { loadHistoryTimeline, loadHistoryComparison, switchHistoryTab } from "./components/history.js";
import { resetUserForm, loadUsersList } from "./components/users.js";
import { executeTestsuite } from "./components/testsuite.js";

export function setupEventListeners({
    login,
    logout,
    loadActivePlan,
    loadVersionDetails,
    discardCurrentDraft,
    showSettings,
    showDashboardView,
    switchSettingsTab,
    showDashboard,
}) {
    // BeforeUnload Warning
    window.addEventListener("beforeunload", (e) => {
        if (state.isDirty) {
            e.preventDefault();
            e.returnValue = "Sie haben ungespeicherte Änderungen.";
        }
    });

    // Login Form
    if (elements.loginForm) {
        elements.loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (elements.loginError) elements.loginError.classList.add("hidden");
            const username = elements.loginForm["login-username"].value.trim();
            const password = elements.loginForm["login-password"].value;
            await login(username, password);
        });
    }

    // Logout Buttons
    if (elements.btnLogout) {
        elements.btnLogout.addEventListener("click", () => {
            guardedAction(() => {
                logout();
            });
        });
    }
    if (elements.btnLogoutSettings) {
        elements.btnLogoutSettings.addEventListener("click", () => {
            logout();
        });
    }

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
    if (elements.selectVersion) {
        elements.selectVersion.addEventListener("change", async (e) => {
            const newVerId = parseInt(e.target.value, 10);
            if (state.isDirty) {
                e.preventDefault();
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
    }

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
    if (elements.posRawAmount && elements.posInterval) {
        elements.posRawAmount.addEventListener("input", updatePositionCalculationPreview);
        elements.posInterval.addEventListener("change", updatePositionCalculationPreview);
    }

    // Positions Form & Modal
    if (elements.btnAddPosition) {
        elements.btnAddPosition.addEventListener("click", () => {
            if (elements.formPosition) elements.formPosition.reset();
            elements.posId.value = "";
            elements.posInterval.value = "monthly";
            elements.posRawAmount.value = "";
            elements.posAmount.value = "";
            elements.posCalculatedMonthlyVal.textContent = "-0,00 € / Monat";
            elements.modalPosTitle.textContent = "Position hinzufügen";
            openModal("modal-position");
        });
    }

    if (elements.formPosition) {
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
                const pos = state.currentVersionDetails.positions.find((p) => String(p.id) === String(id));
                if (pos) {
                    pos.title = title;
                    pos.amount = amount;
                    pos.amount_formatted = formatCurrency(amount);
                    pos.comment = comment;
                }
            } else {
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
    }

    // Contributions Form & Modal
    if (elements.btnAddContribution) {
        elements.btnAddContribution.addEventListener("click", () => {
            if (elements.formContribution) elements.formContribution.reset();
            elements.contribId.value = "";
            elements.modalContribTitle.textContent = "Beitrag hinzufügen";
            openModal("modal-contribution");
        });
    }

    if (elements.formContribution) {
        elements.formContribution.addEventListener("submit", (e) => {
            e.preventDefault();
            const id = elements.contribId.value;
            const person_name = elements.contribPerson.value.trim();
            const amount = parseFloat(elements.contribAmount.value);
            const comment = elements.contribComment.value.trim();

            if (!state.currentVersionDetails) return;

            if (id) {
                const contrib = state.currentVersionDetails.contributions.find((c) => String(c.id) === String(id));
                if (contrib) {
                    contrib.person_name = person_name;
                    contrib.amount = amount;
                    contrib.amount_formatted = formatCurrency(amount);
                    contrib.comment = comment;
                }
            } else {
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
    }

    // Save Version Modal & Submit
    if (elements.btnSaveVersion) {
        elements.btnSaveVersion.addEventListener("click", () => {
            if (!state.currentVersionDetails) return;

            const today = new Date();
            const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);
            const formattedDate = nextMonth.toISOString().split("T")[0];
            const dateDE = nextMonth.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });

            elements.saveVersionTitle.value = `Stand ab ${dateDE}`;
            elements.saveVersionDate.value = formattedDate;

            const totals = state.currentVersionDetails.totals || {};
            elements.saveSummaryPosCount.textContent = state.currentVersionDetails.positions.length;
            elements.saveSummaryExpenses.textContent = totals.total_expenses_formatted || "0,00 €";
            elements.saveSummaryContribCount.textContent = state.currentVersionDetails.contributions.length;
            elements.saveSummaryContributions.textContent = totals.total_contributions_formatted || "0,00 €";
            elements.saveSummaryBalance.textContent = totals.net_balance_formatted || "0,00 €";
            elements.saveSummaryBalance.className = totals.net_balance < 0 ? "text-neg" : "text-pos";

            openModal("modal-save-version");
        });
    }

    if (elements.formSaveVersion) {
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
    }

    // History Modal Open & Tab Switching
    if (elements.btnOpenHistory) {
        elements.btnOpenHistory.addEventListener("click", async () => {
            await loadHistoryTimeline();
            switchHistoryTab("timeline");
            openModal("modal-history");
        });
    }

    if (elements.tabBtnTimeline) {
        elements.tabBtnTimeline.addEventListener("click", () => {
            switchHistoryTab("timeline");
            loadHistoryTimeline();
        });
    }

    if (elements.tabBtnMatrix) {
        elements.tabBtnMatrix.addEventListener("click", () => {
            switchHistoryTab("matrix");
            loadHistoryComparison();
        });
    }

    // Auto-update Stand Title suggestions when Date changes
    if (elements.editVerDate) {
        elements.editVerDate.addEventListener("change", (e) => {
            const d = e.target.value;
            if (!d) return;
            const curVal = elements.editVerTitle.value.trim();
            const formattedDate = formatGermanDate(d);
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
            const formattedDate = formatGermanDate(d);
            if (!curVal || curVal.startsWith("Stand ab ") || curVal.startsWith("Stand ")) {
                elements.saveVersionTitle.value = `Stand ab ${formattedDate}`;
            }
        });
    }

    // Edit Version Metadata Form
    if (elements.formVersionEdit) {
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

                if (state.currentVersionDetails && state.currentVersionDetails.id === verId) {
                    state.currentVersionDetails.title = updatedVer.title;
                    state.currentVersionDetails.effective_date = updatedVer.effective_date;
                }

                const currentSelId = state.selectedVersionId || verId;
                await loadActivePlan();
                state.selectedVersionId = currentSelId;
                elements.selectVersion.value = currentSelId;

                if (!elements.modalHistory.classList.contains("hidden")) {
                    await loadHistoryTimeline();
                }
            } catch (err) {
                alert(err.message || "Fehler beim Aktualisieren der Stand-Informationen");
            }
        });
    }

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
    if (elements.btnDiscardUnsaved) {
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
    }

    if (elements.btnSaveBeforeAction) {
        elements.btnSaveBeforeAction.addEventListener("click", () => {
            closeModal("modal-unsaved-warning");
            elements.btnSaveVersion.click();
        });
    }

    // Settings Navigation Open & Close
    if (elements.btnSettings) {
        elements.btnSettings.addEventListener("click", () => {
            showSettings();
        });
    }

    if (elements.btnBackToDashboard) {
        elements.btnBackToDashboard.addEventListener("click", () => {
            showDashboardView();
        });
    }

    if (elements.btnBackToDashboardTop) {
        elements.btnBackToDashboardTop.addEventListener("click", () => {
            showDashboardView();
        });
    }

    if (elements.btnBrandLogoSettings) {
        elements.btnBrandLogoSettings.addEventListener("click", () => {
            showDashboardView();
        });
    }

    // Settings Tab Switching
    document.querySelectorAll(".settings-tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-tab");
            if (targetId === "tab-settings-new-user" && (!elements.userEditId || !elements.userEditId.value)) {
                resetUserForm();
            }
            switchSettingsTab(targetId);
            if (targetId === "tab-settings-new-user" && elements.userUsername) {
                elements.userUsername.focus();
            }
        });
    });

    if (elements.btnSwitchToNewUser) {
        elements.btnSwitchToNewUser.addEventListener("click", () => {
            resetUserForm();
            switchSettingsTab("tab-settings-new-user");
            if (elements.userUsername) elements.userUsername.focus();
        });
    }

    // Export JSON
    if (elements.btnExportJson) {
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
                a.download = `ausgabenplaner_export_${dateStr}.json`;
                a.href = url;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (err) {
                alert(err.message || "Fehler beim Exportieren der Daten");
            }
        });
    }

    // Export XLSX
    if (elements.btnExportXlsx) {
        elements.btnExportXlsx.addEventListener("click", async () => {
            try {
                const resp = await apiFetch("/api/data/export-xlsx");
                if (!resp.ok) throw new Error("Excel-Export fehlgeschlagen");
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                const dateStr = new Date().toISOString().split("T")[0];
                a.download = `ausgabenplaner_export_${dateStr}.xlsx`;
                a.href = url;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (err) {
                alert(err.message || "Fehler beim Exportieren der Excel-Datei");
            }
        });
    }

    // Import JSON
    if (elements.btnImportJson) {
        elements.btnImportJson.addEventListener("click", () => {
            if (elements.formImportJson) elements.formImportJson.reset();
            if (elements.importError) elements.importError.classList.add("hidden");
            openModal("modal-import");
        });
    }

    if (elements.formImportJson) {
        elements.formImportJson.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (elements.importError) elements.importError.classList.add("hidden");
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
                closeModal("modal-settings");
                setDirty(false);
                await loadActivePlan();
                alert("Daten erfolgreich wiederhergestellt!");
            } catch (err) {
                if (elements.importError) {
                    elements.importError.textContent = err.message || "Fehler beim Importieren der Datei. Bitte prüfen Sie das JSON-Format.";
                    elements.importError.classList.remove("hidden");
                }
            }
        });
    }

    if (elements.btnCancelUserEdit) {
        elements.btnCancelUserEdit.addEventListener("click", () => {
            resetUserForm();
            switchSettingsTab("tab-settings-users");
        });
    }

    // Testsuite Runner (Admin)
    if (elements.btnReRunTests) {
        elements.btnReRunTests.addEventListener("click", executeTestsuite);
    }

    // User Create / Edit Form
    if (elements.formUserCreate) {
        elements.formUserCreate.addEventListener("submit", async (e) => {
            e.preventDefault();
            const editId = elements.userEditId ? elements.userEditId.value : "";
            const username = elements.userUsername.value.trim();
            const name = elements.userName.value.trim();
            const password = elements.userPassword.value;
            const role = elements.userRole.value;
            const can_export = elements.userCanExport ? elements.userCanExport.checked : true;

            if (editId) {
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
                    switchSettingsTab("tab-settings-users");
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
                const resp = await apiFetch("/api/users", {
                    method: "POST",
                    body: { username, name, password, role, can_export },
                });

                if (resp.ok) {
                    resetUserForm();
                    await loadUsersList();
                    switchSettingsTab("tab-settings-users");
                } else {
                    const errData = await resp.json();
                    alert(errData.detail || "Fehler beim Erstellen des Benutzers");
                }
            }
        });
    }
}
