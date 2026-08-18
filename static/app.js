// Ausgabenplaner Modular Main Entry Point
import { state, setDirty } from "./js/state.js";
import { elements } from "./js/dom.js";
import { apiFetch, setUnauthorizedHandler } from "./js/api.js";
import { formatVersionDropdownLabel } from "./js/formatters.js";
import { openModal, closeModal, guardedAction } from "./js/components/modals.js";
import { updateDraftStatusBadge, recalculateDraftTotals, renderKPIs } from "./js/components/kpi.js";
import { renderVersionDetails, updateLockControls, editPosition, deletePosition, editContribution, deleteContribution } from "./js/components/tables.js";
import { loadHistoryTimeline, loadHistoryComparison, switchHistoryTab, setOnPlanChangedHandler } from "./js/components/history.js";
import { loadUsersList, resetUserForm, startEditUser, deleteUser, setSwitchTabHandler as setUsersSwitchTab } from "./js/components/users.js";
import { executeTestsuite, setSwitchTabHandler as setTestsuiteSwitchTab } from "./js/components/testsuite.js";
import { setupEventListeners } from "./js/events.js";

// Wire callbacks across modules
setUnauthorizedHandler(() => logout());
setOnPlanChangedHandler(async () => await loadActivePlan());
setUsersSwitchTab((tabId) => switchSettingsTab(tabId));
setTestsuiteSwitchTab((tabId) => switchSettingsTab(tabId));
state.onDirtyChange = () => updateDraftStatusBadge();

// Navigation & View Switching
export function showLogin() {
    if (elements.loginView) elements.loginView.classList.remove("hidden");
    if (elements.dashboardView) elements.dashboardView.classList.add("hidden");
    if (elements.settingsView) elements.settingsView.classList.add("hidden");
}

export function showDashboard() {
    if (elements.loginView) elements.loginView.classList.add("hidden");
    if (elements.settingsView) elements.settingsView.classList.add("hidden");
    if (elements.dashboardView) elements.dashboardView.classList.remove("hidden");

    if (state.user) {
        if (elements.userDisplayName) elements.userDisplayName.textContent = state.user.name || state.user.username;
        if (elements.userRoleBadge) elements.userRoleBadge.textContent = state.user.role === "admin" ? "Admin" : "Benutzer";
        if (elements.settingsUserDisplayName) elements.settingsUserDisplayName.textContent = state.user.name || state.user.username;
        if (elements.settingsUserRoleBadge) elements.settingsUserRoleBadge.textContent = state.user.role === "admin" ? "Admin" : "Benutzer";

        const canExportOrAdmin = state.user.role === "admin" || !!state.user.can_export;

        if (state.user.role === "admin") {
            if (elements.btnSettings) elements.btnSettings.classList.remove("hidden");
            if (elements.tabBtnUsers) elements.tabBtnUsers.classList.remove("hidden");
            if (elements.tabBtnNewUser) elements.tabBtnNewUser.classList.remove("hidden");
            if (elements.tabBtnTestsuite) elements.tabBtnTestsuite.classList.remove("hidden");
        } else {
            if (elements.tabBtnUsers) elements.tabBtnUsers.classList.add("hidden");
            if (elements.tabBtnNewUser) elements.tabBtnNewUser.classList.add("hidden");
            if (elements.tabBtnTestsuite) elements.tabBtnTestsuite.classList.add("hidden");
            if (elements.btnSettings) {
                elements.btnSettings.classList.toggle("hidden", !canExportOrAdmin);
            }
        }

        if (elements.btnExportJson) elements.btnExportJson.classList.toggle("hidden", !canExportOrAdmin);
        if (elements.btnExportXlsx) elements.btnExportXlsx.classList.toggle("hidden", !canExportOrAdmin);
        if (elements.btnImportJson) elements.btnImportJson.classList.toggle("hidden", !canExportOrAdmin);
    }
}

export function showDashboardView() {
    if (elements.settingsView) elements.settingsView.classList.add("hidden");
    if (elements.loginView) elements.loginView.classList.add("hidden");
    if (elements.dashboardView) elements.dashboardView.classList.remove("hidden");
}

export function switchSettingsTab(tabId) {
    document.querySelectorAll(".settings-tab-btn").forEach((b) => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".settings-tab-content").forEach((c) => {
        c.classList.toggle("hidden", c.id !== tabId);
    });
    if (tabId === "tab-settings-users") {
        loadUsersList();
    }
}

export function showSettings(targetTab) {
    if (elements.dashboardView) elements.dashboardView.classList.add("hidden");
    if (elements.loginView) elements.loginView.classList.add("hidden");
    if (elements.settingsView) elements.settingsView.classList.remove("hidden");

    if (state.user) {
        if (elements.settingsUserDisplayName) {
            elements.settingsUserDisplayName.textContent = state.user.name || state.user.username;
        }
        if (elements.settingsUserRoleBadge) {
            elements.settingsUserRoleBadge.textContent = state.user.role === "admin" ? "Admin" : "Benutzer";
        }
    }

    if (state.user && state.user.role !== "admin") {
        switchSettingsTab("tab-settings-data");
    } else if (targetTab) {
        switchSettingsTab(targetTab);
    } else {
        const activeTab = document.querySelector('.settings-tab-btn.active');
        const defaultTab = activeTab ? activeTab.getAttribute("data-tab") : "tab-settings-data";
        switchSettingsTab(defaultTab);
    }
}

// User Actions
export async function fetchCurrentUser() {
    const resp = await apiFetch("/api/auth/me");
    state.user = await resp.json();
}

export async function login(username, password) {
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
        if (elements.loginError) {
            elements.loginError.textContent = err.message;
            elements.loginError.classList.remove("hidden");
        }
    }
}

export function logout() {
    state.token = null;
    state.user = null;
    state.isDirty = false;
    localStorage.removeItem("token");
    showLogin();
}

// Plans & Version Data Loaders
export async function loadActivePlan() {
    const resp = await apiFetch("/api/plans/active");
    if (!resp.ok) return;

    state.activePlan = await resp.json();
    if (elements.planTitle) elements.planTitle.textContent = state.activePlan.title;

    if (elements.selectVersion) {
        elements.selectVersion.innerHTML = "";
        (state.activePlan.versions || []).forEach((v) => {
            const opt = document.createElement("option");
            opt.value = v.id;
            opt.textContent = formatVersionDropdownLabel(v);
            elements.selectVersion.appendChild(opt);
        });
    }

    if (state.activePlan.active_version) {
        state.selectedVersionId = state.activePlan.active_version.id;
        if (elements.selectVersion) elements.selectVersion.value = state.selectedVersionId;
        renderVersionDetails(state.activePlan.active_version);
    }
}

export async function loadVersionDetails(versionId) {
    const resp = await apiFetch(`/api/versions/${versionId}`);
    if (!resp.ok) return;
    const data = await resp.json();
    renderVersionDetails(data);
}

export async function discardCurrentDraft() {
    if (!state.selectedVersionId) {
        if (state.activePlan && state.activePlan.active_version) {
            state.selectedVersionId = state.activePlan.active_version.id;
        }
    }
    if (state.selectedVersionId) {
        await loadVersionDetails(state.selectedVersionId);
        if (elements.selectVersion) elements.selectVersion.value = state.selectedVersionId;
    }
    setDirty(false);
}

// App Init Bootstrapping
export async function initApp() {
    setupEventListeners({
        login,
        logout,
        loadActivePlan,
        loadVersionDetails,
        discardCurrentDraft,
        showSettings,
        showDashboardView,
        switchSettingsTab,
        showDashboard,
    });

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

// Window Globals for backwards compatibility & inline handlers
window.switchSettingsTab = switchSettingsTab;
window.showSettings = showSettings;
window.showDashboardView = showDashboardView;
window.executeTestsuite = executeTestsuite;
window.editPosition = editPosition;
window.deletePosition = deletePosition;
window.editContribution = editContribution;
window.deleteContribution = deleteContribution;
window.startEditUser = startEditUser;
window.deleteUser = deleteUser;
window.openModal = openModal;
window.closeModal = closeModal;

// Boot application
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}
