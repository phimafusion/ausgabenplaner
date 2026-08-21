// User Management Component
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { escapeHtml } from "../formatters.js";
import { renderUserPlanAssignmentCheckboxes, getSelectedUserPlanIds } from "./plans.js";

let onSwitchTabCallback = null;

export function setSwitchTabHandler(fn) {
    onSwitchTabCallback = fn;
}

export function resetUserForm() {
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
    if (elements.userPermManagePlans) elements.userPermManagePlans.checked = false;
    if (elements.userPermExport) elements.userPermExport.checked = true;
    if (elements.userPermImport) elements.userPermImport.checked = false;
    if (elements.userPermManageBackups) elements.userPermManageBackups.checked = false;
    if (elements.userPermManageUsers) elements.userPermManageUsers.checked = false;
    if (elements.userPermRunTestsuite) elements.userPermRunTestsuite.checked = false;
    if (elements.userPermViewChangelog) elements.userPermViewChangelog.checked = true;
    if (elements.userCanExport) elements.userCanExport.checked = true;
    if (elements.userFormHeading) elements.userFormHeading.textContent = "Neuen Benutzer anlegen";
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "Benutzer erstellen";
    if (elements.btnCancelUserEdit) elements.btnCancelUserEdit.textContent = "Abbrechen";
    renderUserPlanAssignmentCheckboxes([]);
}

export function startEditUser(user) {
    if (typeof user === "string") {
        try { user = JSON.parse(user); } catch (e) {}
    }
    if (!user) return;
    if (typeof onSwitchTabCallback === "function") {
        onSwitchTabCallback("tab-settings-new-user");
    }
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
    if (elements.userPermManagePlans) elements.userPermManagePlans.checked = !!user.can_manage_plans;
    if (elements.userPermExport) elements.userPermExport.checked = !!user.can_export;
    if (elements.userPermImport) elements.userPermImport.checked = !!user.can_import;
    if (elements.userPermManageBackups) elements.userPermManageBackups.checked = !!user.can_manage_backups;
    if (elements.userPermManageUsers) elements.userPermManageUsers.checked = !!user.can_manage_users;
    if (elements.userPermRunTestsuite) elements.userPermRunTestsuite.checked = !!user.can_run_testsuite;
    if (elements.userPermViewChangelog) elements.userPermViewChangelog.checked = user.can_view_changelog !== undefined ? !!user.can_view_changelog : true;
    if (elements.userCanExport) elements.userCanExport.checked = !!user.can_export;
    if (elements.userFormHeading) elements.userFormHeading.textContent = `Benutzer „${user.username}“ bearbeiten`;
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "💾 Änderungen speichern";

    renderUserPlanAssignmentCheckboxes(user.assigned_plan_ids || []);
    if (elements.userName) elements.userName.focus();
}

export async function deleteUser(userId, username) {
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
}

export async function loadUsersList() {
    const resp = await apiFetch("/api/users");
    if (!resp.ok) return;
    const users = await resp.json();
    if (!elements.usersList) return;
    elements.usersList.innerHTML = "";

    const allPlansMap = new Map((state.availablePlans || []).map((p) => [p.id, p.title]));

    users.forEach((u) => {
        const card = document.createElement("div");
        card.className = "user-profile-card glass-panel";
        const uJson = JSON.stringify(u).replace(/'/g, "&#39;");
        const isAdmin = u.role === "admin";
        const isSelf = state.user && String(state.user.id) === String(u.id);
        const initials = (u.name || u.username || "??").trim().substring(0, 2).toUpperCase();

        let planBadges = "";
        if (isAdmin) {
            planBadges = `<span class="badge badge-admin" style="font-size: 0.75rem;">📋 Alle Pläne (Vollzugriff)</span>`;
        } else if (u.assigned_plan_ids && u.assigned_plan_ids.length > 0) {
            const planNames = u.assigned_plan_ids.map((id) => allPlansMap.get(id) || `Plan #${id}`);
            planBadges = planNames.map((n) => `<span class="badge badge-saved" style="font-size: 0.75rem;">📋 ${escapeHtml(n)}</span>`).join(" ");
        } else {
            planBadges = `<span class="badge badge-saved" style="font-size: 0.75rem;">📋 Alle Pläne (Offen)</span>`;
        }

        let permBadges = [];
        if (isAdmin) {
            permBadges.push(`<span class="badge badge-admin">👑 Vollzugriff</span>`);
        } else {
            if (u.can_manage_plans) permBadges.push(`<span class="badge badge-saved">📋 Pläne verwalten</span>`);
            if (u.can_export) permBadges.push(`<span class="badge badge-saved">💾 Export</span>`);
            if (u.can_import) permBadges.push(`<span class="badge badge-saved">📤 Import</span>`);
            if (u.can_manage_backups) permBadges.push(`<span class="badge badge-saved">🛡️ Backups</span>`);
            if (u.can_manage_users) permBadges.push(`<span class="badge badge-saved">👥 Benutzer</span>`);
            if (u.can_run_testsuite) permBadges.push(`<span class="badge badge-saved">🧪 Testsuite</span>`);
            if (permBadges.length === 0) permBadges.push(`<span class="badge badge-archived">🔒 Nur Lesezugriff</span>`);
        }

        card.innerHTML = `
            <div class="user-card-top">
                <div class="user-avatar ${isAdmin ? 'avatar-admin' : 'avatar-user'}">
                    <span>${isAdmin ? '👑' : initials}</span>
                </div>
                <div class="user-card-identity">
                    <div class="user-card-name-row">
                        <strong class="user-card-name">${escapeHtml(u.name)}</strong>
                        ${isSelf ? '<span class="badge badge-self">Sie</span>' : ''}
                    </div>
                    <span class="user-card-handle">@${escapeHtml(u.username)}</span>
                </div>
            </div>

            <div class="user-card-badges" style="margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 4px;">
                <span class="badge ${isAdmin ? 'badge-admin' : 'badge-user'}">
                    ${isAdmin ? '👑 Administrator' : '👤 Benutzer'}
                </span>
                ${permBadges.join(" ")}
            </div>

            <div class="user-card-plans" style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 4px;">
                ${planBadges}
            </div>

            <div class="user-card-actions">
                <button type="button" class="btn btn-sm btn-secondary user-action-btn" onclick='startEditUser(${uJson})' title="Benutzer bearbeiten">
                    ✏️ Bearbeiten
                </button>
                ${u.username !== "admin" ? `
                <button type="button" class="btn btn-sm btn-danger user-action-btn" onclick="deleteUser(${u.id}, '${escapeHtml(u.username)}')" title="Benutzer löschen">
                    🗑️ Löschen
                </button>` : ''}
            </div>
        `;
        elements.usersList.appendChild(card);
    });
}

// Window attachments for inline HTML onclick handlers
window.startEditUser = startEditUser;
window.deleteUser = deleteUser;

