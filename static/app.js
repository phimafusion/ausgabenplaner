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
import { loadBackupSettings, loadBackupsList, createManualBackup, downloadBackup, deleteBackup, restoreBackup, setOnBackupRestoredHandler } from "./js/components/backups.js";
import {
    loadAllPlans,
    switchPlan,
    setOnPlanSwitchedHandler,
    openCreatePlanModal,
    openEditPlanModal,
    openDuplicatePlanModal,
    openDeletePlanModal,
} from "./js/components/plans.js";
import { setupEventListeners } from "./js/events.js";

// Wire callbacks across modules
setUnauthorizedHandler(() => logout());
setOnPlanChangedHandler(async () => await loadActivePlan());
setOnPlanSwitchedHandler(async () => {
    updatePlanView();
});
setOnBackupRestoredHandler(async () => {
    await loadAllPlans();
    await loadActivePlan();
    showDashboard();
});
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

        const isAdmin = state.user.role === "admin";
        const canManagePlans = isAdmin || !!state.user.can_manage_plans;
        const canExport = isAdmin || !!state.user.can_export;
        const canImport = isAdmin || !!state.user.can_import;
        const canManageBackups = isAdmin || !!state.user.can_manage_backups;
        const canManageUsers = isAdmin || !!state.user.can_manage_users;
        const canRunTestsuite = isAdmin || !!state.user.can_run_testsuite;
        const canViewChangelog = isAdmin || (state.user.can_view_changelog !== undefined ? !!state.user.can_view_changelog : true);

        const hasAnySettingsAccess = canManagePlans || canExport || canImport || canManageBackups || canManageUsers || canRunTestsuite || canViewChangelog;

        if (elements.btnSettings) {
            elements.btnSettings.classList.toggle("hidden", !hasAnySettingsAccess);
        }

        if (elements.tabBtnPlans) elements.tabBtnPlans.classList.toggle("hidden", !canManagePlans);
        if (elements.tabBtnUsers) elements.tabBtnUsers.classList.toggle("hidden", !canManageUsers);
        if (elements.tabBtnNewUser) elements.tabBtnNewUser.classList.toggle("hidden", !canManageUsers);
        const canViewDataTab = canExport || canImport || canManageBackups;
        if (elements.tabBtnData) elements.tabBtnData.classList.toggle("hidden", !canViewDataTab);
        if (elements.tabBtnTestsuite) elements.tabBtnTestsuite.classList.toggle("hidden", !canRunTestsuite);
        if (elements.tabBtnChangelog) elements.tabBtnChangelog.classList.toggle("hidden", !canViewChangelog);

        if (elements.cardAutomatedBackups) elements.cardAutomatedBackups.classList.toggle("hidden", !canManageBackups);
        if (elements.btnExportJson) elements.btnExportJson.classList.toggle("hidden", !canExport);
        if (elements.btnExportXlsx) elements.btnExportXlsx.classList.toggle("hidden", !canExport);
        if (elements.btnImportJson) elements.btnImportJson.classList.toggle("hidden", !canImport);

        // Toggle admin-only / plan-manage action buttons in the UI
        document.querySelectorAll(".admin-only").forEach((el) => {
            el.classList.toggle("hidden", !canManagePlans && !isAdmin);
        });

        if (elements.btnDeletePlan) elements.btnDeletePlan.classList.toggle("hidden", !canManagePlans);
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
    if (tabId === "tab-settings-plans") {
        loadAllPlans();
    }
    if (tabId === "tab-settings-users") {
        loadUsersList();
    }
    if (tabId === "tab-settings-data" && state.user && (state.user.role === "admin" || state.user.can_manage_backups)) {
        loadBackupSettings();
        loadBackupsList();
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

    const isAdmin = state.user && state.user.role === "admin";
    const canManagePlans = isAdmin || !!(state.user && state.user.can_manage_plans);
    const canExport = isAdmin || !!(state.user && state.user.can_export);
    const canImport = isAdmin || !!(state.user && state.user.can_import);
    const canManageBackups = isAdmin || !!(state.user && state.user.can_manage_backups);
    const canManageUsers = isAdmin || !!(state.user && state.user.can_manage_users);
    const canRunTestsuite = isAdmin || !!(state.user && state.user.can_run_testsuite);
    const canViewChangelog = isAdmin || (state.user && state.user.can_view_changelog !== undefined ? !!state.user.can_view_changelog : true);

    if (targetTab) {
        switchSettingsTab(targetTab);
    } else {
        // Choose default visible tab for this user
        if (canManagePlans) {
            switchSettingsTab("tab-settings-plans");
        } else if (canExport || canImport || canManageBackups) {
            switchSettingsTab("tab-settings-data");
        } else if (canManageUsers) {
            switchSettingsTab("tab-settings-users");
        } else if (canRunTestsuite) {
            switchSettingsTab("tab-settings-testsuite");
        } else if (canViewChangelog) {
            switchSettingsTab("tab-settings-changelog");
        } else {
            switchSettingsTab("tab-settings-data");
        }
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
        await loadAllPlans();
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
    const targetUrl = state.activePlanId ? `/api/plans/${state.activePlanId}` : "/api/plans/active";
    const resp = await apiFetch(targetUrl);
    if (!resp.ok) return;

    state.activePlan = await resp.json();
    state.activePlanId = state.activePlan.id;
    updatePlanView();
}

function updatePlanView() {
    if (!state.activePlan) return;

    if (elements.selectPlan) {
        elements.selectPlan.value = state.activePlan.id;
    }
    if (elements.planTitle) elements.planTitle.textContent = state.activePlan.title;
    if (elements.planArchivedBadge) {
        elements.planArchivedBadge.classList.toggle("hidden", !state.activePlan.is_archived);
    }

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
            await loadAllPlans();
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
window.openCreatePlanModal = openCreatePlanModal;
window.openEditPlanModal = openEditPlanModal;
window.openDuplicatePlanModal = openDuplicatePlanModal;
window.openDeletePlanModal = openDeletePlanModal;
window.switchPlan = switchPlan;

// Boot application
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}
