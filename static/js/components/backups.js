// Automated SQLite Backups & Snapshot Component
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { escapeHtml, formatDateTimeDE, showToast } from "../formatters.js";

export async function loadBackupSettings() {
    if (!state.user || state.user.role !== "admin") return;
    try {
        const resp = await apiFetch("/api/admin/backups/settings");
        if (!resp.ok) return;
        const data = await resp.json();

        const retentionInput = document.getElementById("backup-retention-count");
        const timeInput = document.getElementById("backup-auto-time");
        const folderInput = document.getElementById("backup-folder-path");
        const enabledToggle = document.getElementById("backup-enabled-toggle");
        const freqSelect = document.getElementById("backup-frequency-select");

        if (retentionInput) retentionInput.value = data.retention_count || 14;
        if (timeInput) timeInput.value = data.auto_backup_time || "03:00";
        if (folderInput) folderInput.value = data.backup_folder || "data/backups";
        if (enabledToggle) enabledToggle.checked = !!data.backup_enabled;
        if (freqSelect && data.backup_frequency) freqSelect.value = data.backup_frequency;
    } catch (err) {
        console.error("Error loading backup settings:", err);
    }
}

export async function saveBackupSettings(e) {
    if (e) e.preventDefault();
    const retentionInput = document.getElementById("backup-retention-count");
    const timeInput = document.getElementById("backup-auto-time");
    const folderInput = document.getElementById("backup-folder-path");
    const enabledToggle = document.getElementById("backup-enabled-toggle");
    const freqSelect = document.getElementById("backup-frequency-select");

    const payload = {
        retention_count: parseInt(retentionInput.value, 10) || 14,
        auto_backup_time: timeInput.value || "03:00",
        backup_folder: folderInput.value.trim() || "data/backups",
        backup_enabled: enabledToggle.checked,
        backup_frequency: freqSelect ? freqSelect.value : "daily",
    };

    try {
        const resp = await apiFetch("/api/admin/backups/settings", {
            method: "PATCH",
            body: payload,
        });
        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || "Fehler beim Speichern der Einstellungen");
        }
        showToast("Backup-Einstellungen erfolgreich gespeichert!", "success");
        await loadBackupsList();
    } catch (err) {
        showToast(err.message || "Fehler beim Speichern der Backup-Einstellungen", "error");
    }
}

export async function loadBackupsList() {
    if (!state.user || state.user.role !== "admin") return;
    const listBody = document.getElementById("backups-list-body");
    if (!listBody) return;

    try {
        const resp = await apiFetch("/api/admin/backups");
        if (!resp.ok) {
            listBody.innerHTML = `<tr><td colspan="4" class="text-muted text-center" style="padding: 16px;">Fehler beim Laden der Snapshots</td></tr>`;
            return;
        }
        const backups = await resp.json();

        if (backups.length === 0) {
            listBody.innerHTML = `<tr><td colspan="4" class="text-muted text-center" style="padding: 16px;">Noch keine Datenbank-Snapshots vorhanden. Klicken Sie auf „Jetzt Snapshot erstellen“.</td></tr>`;
            return;
        }

        listBody.innerHTML = "";
        backups.forEach((b) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><code>${escapeHtml(b.filename)}</code></td>
                <td>${formatDateTimeDE(b.created_at)}</td>
                <td><strong>${escapeHtml(b.file_size_formatted)}</strong></td>
                <td class="text-right actions-cell">
                    <button type="button" class="btn btn-sm btn-outline btn-icon" onclick="downloadBackup('${escapeHtml(b.filename)}')" title="Snapshot herunterladen" aria-label="Snapshot herunterladen">
                        📥
                    </button>
                    <button type="button" class="btn btn-sm btn-outline btn-icon" onclick="restoreBackup('${escapeHtml(b.filename)}')" title="Diesen Snapshot wiederherstellen" aria-label="Snapshot wiederherstellen" style="color: #f59e0b; border-color: rgba(245, 158, 11, 0.4);">
                        🔄
                    </button>
                    <button type="button" class="btn btn-sm btn-danger btn-icon" onclick="deleteBackup('${escapeHtml(b.filename)}')" title="Snapshot löschen" aria-label="Snapshot löschen">
                        🗑️
                    </button>
                </td>
            `;
            listBody.appendChild(tr);
        });
    } catch (err) {
        listBody.innerHTML = `<tr><td colspan="4" class="text-muted text-center" style="padding: 16px;">Fehler beim Laden der Snapshots</td></tr>`;
    }
}

export async function createManualBackup() {
    const btn = document.getElementById("btn-create-manual-backup");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "⏳ Erstelle Snapshot...";
    }
    try {
        const resp = await apiFetch("/api/admin/backups/create", { method: "POST" });
        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || "Fehler beim Erstellen des Snapshots");
        }
        const result = await resp.json();
        await loadBackupsList();
        showToast(`Snapshot „${result.filename}“ (${result.file_size_formatted}) erfolgreich erstellt!`, "success");
    } catch (err) {
        showToast(err.message || "Fehler beim Erstellen des Snapshots", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "⚡ Jetzt Snapshot erstellen";
        }
    }
}

export async function downloadBackup(filename) {
    try {
        const resp = await apiFetch(`/api/admin/backups/download/${encodeURIComponent(filename)}`);
        if (!resp.ok) {
            throw new Error("Fehler beim Herunterladen des Snapshots");
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Download von „${filename}“ gestartet`, "info");
    } catch (err) {
        showToast(err.message || "Fehler beim Herunterladen des Snapshots", "error");
    }
}

let onBackupRestored = null;
export function setOnBackupRestoredHandler(handler) {
    onBackupRestored = handler;
}

export async function restoreBackup(filename) {
    const confirmMsg = `ACHTUNG: Möchten Sie die gesamte Datenbank wirklich auf den Snapshot „${filename}“ zurücksetzen?\n\nAlle aktuellen Änderungen werden mit dem Stand dieses Backups überschrieben!`;
    if (!confirm(confirmMsg)) {
        return;
    }

    try {
        const resp = await apiFetch(`/api/admin/backups/restore/${encodeURIComponent(filename)}`, {
            method: "POST",
        });
        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || "Fehler bei der Wiederherstellung des Snapshots");
        }
        const data = await resp.json();
        showToast(data.message || "Datenbank erfolgreich wiederhergestellt!", "success");
        if (typeof onBackupRestored === "function") {
            await onBackupRestored();
        }
        await loadBackupsList();
    } catch (err) {
        showToast(err.message || "Fehler bei der Wiederherstellung des Snapshots", "error");
    }
}

export async function deleteBackup(filename) {
    if (!confirm(`Möchten Sie den Snapshot „${filename}“ wirklich löschen?`)) {
        return;
    }
    try {
        const resp = await apiFetch(`/api/admin/backups/${encodeURIComponent(filename)}`, { method: "DELETE" });
        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || "Fehler beim Löschen des Snapshots");
        }
        showToast(`Snapshot „${filename}“ gelöscht`, "info");
        await loadBackupsList();
    } catch (err) {
        showToast(err.message || "Fehler beim Löschen des Snapshots", "error");
    }
}

// Window attachments for inline HTML onclick handlers
window.downloadBackup = downloadBackup;
window.restoreBackup = restoreBackup;
window.deleteBackup = deleteBackup;
window.createManualBackup = createManualBackup;
