// User Management Component
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { escapeHtml } from "../formatters.js";

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
    if (elements.userCanExport) elements.userCanExport.checked = true;
    if (elements.userFormHeading) elements.userFormHeading.textContent = "Neuen Benutzer anlegen";
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "Benutzer erstellen";
    if (elements.btnCancelUserEdit) elements.btnCancelUserEdit.textContent = "Abbrechen";
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
    if (elements.userCanExport) elements.userCanExport.checked = !!user.can_export;
    if (elements.userFormHeading) elements.userFormHeading.textContent = `Benutzer „${user.username}“ bearbeiten`;
    if (elements.btnSubmitUser) elements.btnSubmitUser.textContent = "💾 Änderungen speichern";
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
    users.forEach((u) => {
        const card = document.createElement("div");
        card.className = "user-profile-card glass-panel";
        const uJson = JSON.stringify(u).replace(/'/g, "&#39;");
        const isAdmin = u.role === "admin";
        const isSelf = state.user && String(state.user.id) === String(u.id);
        const initials = (u.name || u.username || "??").trim().substring(0, 2).toUpperCase();

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

            <div class="user-card-badges">
                <span class="badge ${isAdmin ? 'badge-admin' : 'badge-user'}">
                    ${isAdmin ? '👑 Administrator' : '👤 Benutzer'}
                </span>
                <span class="badge ${u.can_export ? 'badge-saved' : 'badge-archived'}">
                    ${u.can_export ? '💾 Export erlaubt' : '🔒 Kein Export'}
                </span>
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
