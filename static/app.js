// Ausgabenplaner Frontend Application Logic

const state = {
    token: localStorage.getItem("token") || null,
    user: null,
    activePlan: null,
    selectedVersionId: null,
    currentVersionDetails: null,
};

// DOM Elements
const elements = {
    loginView: document.getElementById("login-view"),
    dashboardView: document.getElementById("dashboard-view"),
    loginForm: document.getElementById("login-form"),
    loginError: document.getElementById("login-error"),
    userDisplayName: document.getElementById("user-display-name"),
    userRoleBadge: document.getElementById("user-role-badge"),
    btnRunTests: document.getElementById("btn-run-tests"),
    btnUserMgmt: document.getElementById("btn-user-mgmt"),
    btnLogout: document.getElementById("btn-logout"),

    planTitle: document.getElementById("plan-title"),
    selectVersion: document.getElementById("select-version"),
    btnNewSnapshot: document.getElementById("btn-new-snapshot"),
    btnHistoryComparison: document.getElementById("btn-history-comparison"),

    kpiExpensesVal: document.getElementById("kpi-expenses-val"),
    kpiContributionsVal: document.getElementById("kpi-contributions-val"),
    kpiBalanceVal: document.getElementById("kpi-balance-val"),
    kpiBalanceCard: document.getElementById("kpi-balance-card"),

    tablePositionsBody: document.querySelector("#table-positions tbody"),
    sumPositionsVal: document.getElementById("sum-positions-val"),
    btnAddPosition: document.getElementById("btn-add-position"),

    tableContributionsBody: document.querySelector("#table-contributions tbody"),
    sumContributionsVal: document.getElementById("sum-contributions-val"),
    btnAddContribution: document.getElementById("btn-add-contribution"),

    // Modals
    modalPosition: document.getElementById("modal-position"),
    formPosition: document.getElementById("form-position"),
    posId: document.getElementById("pos-id"),
    posTitle: document.getElementById("pos-title"),
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

    modalSnapshot: document.getElementById("modal-snapshot"),
    formSnapshot: document.getElementById("form-snapshot"),
    snapTitle: document.getElementById("snap-title"),
    snapDate: document.getElementById("snap-date"),
    snapCopy: document.getElementById("snap-copy"),

    modalHistory: document.getElementById("modal-history"),
    historyContainer: document.getElementById("history-comparison-container"),

    modalUsers: document.getElementById("modal-users"),
    formUserCreate: document.getElementById("form-user-create"),
    usersList: document.getElementById("users-list"),

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

// Format Currency
function formatCurrency(val) {
    if (val === undefined || val === null) return "0,00 €";
    const isNeg = val < 0;
    const absVal = Math.abs(val);
    const parts = absVal.toFixed(2).split(".");
    const intPart = parseInt(parts[0], 10).toLocaleString("de-DE");
    const decPart = parts[1];
    let res = `${intPart},${decPart} €`;
    if (isNeg) res = `-${res}`;
    return res;
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
    elements.btnLogout.addEventListener("click", logout);

    // Version dropdown change
    elements.selectVersion.addEventListener("change", async (e) => {
        state.selectedVersionId = parseInt(e.target.value, 10);
        await loadVersionDetails(state.selectedVersionId);
    });

    // Modal Close buttons
    document.querySelectorAll("[data-close]").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            const targetId = e.target.getAttribute("data-close");
            closeModal(targetId);
        });
    });

    // Positions Modals & Forms
    elements.btnAddPosition.addEventListener("click", () => {
        elements.formPosition.reset();
        elements.posId.value = "";
        elements.modalPosTitle.textContent = "Position hinzufügen";
        openModal("modal-position");
    });

    elements.formPosition.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = elements.posId.value;
        const payload = {
            title: elements.posTitle.value.trim(),
            amount: parseFloat(elements.posAmount.value),
            comment: elements.posComment.value.trim(),
        };

        if (id) {
            // Update
            await apiFetch(`/api/positions/${id}`, { method: "PUT", body: payload });
        } else {
            // Create
            await apiFetch(`/api/versions/${state.selectedVersionId}/positions`, {
                method: "POST",
                body: payload,
            });
        }
        closeModal("modal-position");
        await loadVersionDetails(state.selectedVersionId);
    });

    // Contributions Modals & Forms
    elements.btnAddContribution.addEventListener("click", () => {
        elements.formContribution.reset();
        elements.contribId.value = "";
        elements.modalContribTitle.textContent = "Beitrag hinzufügen";
        openModal("modal-contribution");
    });

    elements.formContribution.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = elements.contribId.value;
        const payload = {
            person_name: elements.contribPerson.value.trim(),
            amount: parseFloat(elements.contribAmount.value),
            comment: elements.contribComment.value.trim(),
        };

        if (id) {
            await apiFetch(`/api/contributions/${id}`, { method: "PUT", body: payload });
        } else {
            await apiFetch(`/api/versions/${state.selectedVersionId}/contributions`, {
                method: "POST",
                body: payload,
            });
        }
        closeModal("modal-contribution");
        await loadVersionDetails(state.selectedVersionId);
    });

    // Snapshot Creation
    elements.btnNewSnapshot.addEventListener("click", () => {
        elements.formSnapshot.reset();
        elements.snapDate.value = new Date().toISOString().split("T")[0];
        openModal("modal-snapshot");
    });

    elements.formSnapshot.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            title: elements.snapTitle.value.trim(),
            effective_date: elements.snapDate.value || null,
            copy_from_version_id: elements.snapCopy.checked ? state.selectedVersionId : null,
        };

        const resp = await apiFetch(`/api/plans/${state.activePlan.id}/snapshots`, {
            method: "POST",
            body: payload,
        });
        const newVer = await resp.json();
        closeModal("modal-snapshot");
        await loadActivePlan();
        elements.selectVersion.value = newVer.id;
        state.selectedVersionId = newVer.id;
        await loadVersionDetails(newVer.id);
    });

    // Historical Side-by-Side Comparison
    elements.btnHistoryComparison.addEventListener("click", async () => {
        await loadHistoryComparison();
        openModal("modal-history");
    });

    // User Management (Admin)
    elements.btnUserMgmt.addEventListener("click", async () => {
        await loadUsersList();
        openModal("modal-users");
    });

    // Testsuite Runner (Admin)
    elements.btnRunTests.addEventListener("click", executeTestsuite);
    elements.btnReRunTests.addEventListener("click", executeTestsuite);

    elements.formUserCreate.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("user-username").value.trim();
        const name = document.getElementById("user-name").value.trim();
        const password = document.getElementById("user-password").value;
        const role = document.getElementById("user-role").value;

        const resp = await apiFetch("/api/users", {
            method: "POST",
            body: { username, name, password, role },
        });

        if (resp.ok) {
            elements.formUserCreate.reset();
            await loadUsersList();
        } else {
            const errData = await resp.json();
            alert(errData.detail || "Fehler beim Erstellen des Benutzers");
        }
    });
}

// User Actions
async function fetchCurrentUser() {
    const resp = await apiFetch("/api/auth/me");
    state.user = await resp.json();
}

function logout() {
    state.token = null;
    state.user = null;
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
        elements.userRoleBadge.textContent = state.user.role === "admin" ? "Admin" : "User";
        if (state.user.role === "admin") {
            elements.btnUserMgmt.classList.remove("hidden");
            elements.btnRunTests.classList.remove("hidden");
        } else {
            elements.btnUserMgmt.classList.add("hidden");
            elements.btnRunTests.classList.add("hidden");
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

    evtSource.onerror = (err) => {
        evtSource.close();
        if (progressBar.style.width !== "100%") {
            elements.testsuiteStatusBox.className = "alert alert-danger";
            elements.testsuiteStatusBox.textContent = "❌ Verbindung zur Testsuite unterbrochen.";
        }
    };
}

// Load Active Plan
async function loadActivePlan() {
    const resp = await apiFetch("/api/plans/active");
    if (!resp.ok) return;

    state.activePlan = await resp.json();
    elements.planTitle.textContent = state.activePlan.title;

    // Populate version selector
    elements.selectVersion.innerHTML = "";
    state.activePlan.versions.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = `${v.title} (${v.effective_date || "ohne Datum"})`;
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

// Render Version
function renderVersionDetails(verData) {
    state.currentVersionDetails = verData;
    const totals = verData.totals;

    // Render KPIs
    elements.kpiExpensesVal.textContent = totals.total_expenses_formatted;
    elements.kpiContributionsVal.textContent = totals.total_contributions_formatted;
    elements.kpiBalanceVal.textContent = totals.net_balance_formatted;

    elements.kpiBalanceCard.classList.remove("balance-positive", "balance-negative");
    if (totals.net_balance >= 0) {
        elements.kpiBalanceCard.classList.add("balance-positive");
    } else {
        elements.kpiBalanceCard.classList.add("balance-negative");
    }

    // Render Positions Table
    elements.tablePositionsBody.innerHTML = "";
    verData.positions.forEach((p) => {
        const tr = document.createElement("tr");
        const amountClass = p.amount < 0 ? "text-neg" : "text-pos";
        tr.innerHTML = `
            <td><strong>${escapeHtml(p.title)}</strong></td>
            <td class="${amountClass}">${escapeHtml(p.amount_formatted)}</td>
            <td class="text-muted">${escapeHtml(p.comment || "")}</td>
            <td class="actions-cell">
                <button class="btn btn-sm btn-outline btn-icon" onclick="editPosition(${p.id})">✏️</button>
                <button class="btn btn-sm btn-danger btn-icon" onclick="deletePosition(${p.id})">🗑️</button>
            </td>
        `;
        elements.tablePositionsBody.appendChild(tr);
    });
    elements.sumPositionsVal.textContent = totals.total_expenses_formatted;

    // Render Contributions Table
    elements.tableContributionsBody.innerHTML = "";
    verData.contributions.forEach((c) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>Zahlung ${escapeHtml(c.person_name)}</strong></td>
            <td class="text-pos">${escapeHtml(c.amount_formatted)}</td>
            <td class="text-muted">${escapeHtml(c.comment || "")}</td>
            <td class="actions-cell">
                <button class="btn btn-sm btn-outline btn-icon" onclick="editContribution(${c.id})">✏️</button>
                <button class="btn btn-sm btn-danger btn-icon" onclick="deleteContribution(${c.id})">🗑️</button>
            </td>
        `;
        elements.tableContributionsBody.appendChild(tr);
    });
    elements.sumContributionsVal.textContent = totals.total_contributions_formatted;
}

// Edit/Delete handlers
window.editPosition = (posId) => {
    const pos = state.currentVersionDetails.positions.find((p) => p.id === posId);
    if (!pos) return;
    elements.posId.value = pos.id;
    elements.posTitle.value = pos.title;
    elements.posAmount.value = pos.amount;
    elements.posComment.value = pos.comment || "";
    elements.modalPosTitle.textContent = "Position bearbeiten";
    openModal("modal-position");
};

window.deletePosition = async (posId) => {
    if (!confirm("Möchten Sie diese Position wirklich löschen?")) return;
    await apiFetch(`/api/positions/${posId}`, { method: "DELETE" });
    await loadVersionDetails(state.selectedVersionId);
};

window.editContribution = (contribId) => {
    const c = state.currentVersionDetails.contributions.find((item) => item.id === contribId);
    if (!c) return;
    elements.contribId.value = c.id;
    elements.contribPerson.value = c.person_name;
    elements.contribAmount.value = c.amount;
    elements.contribComment.value = c.comment || "";
    elements.modalContribTitle.textContent = "Beitrag bearbeiten";
    openModal("modal-contribution");
};

window.deleteContribution = async (contribId) => {
    if (!confirm("Möchten Sie diesen Beitrag wirklich löschen?")) return;
    await apiFetch(`/api/contributions/${contribId}`, { method: "DELETE" });
    await loadVersionDetails(state.selectedVersionId);
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
            html += `<td>${formatted}</td>`;
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
            html += `<td>${formatted}</td>`;
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
        html += `<td><strong>${formatted}</strong></td>`;
    });
    html += `</tr></tbody></table>`;

    elements.historyContainer.innerHTML = html;
}

// Users List
async function loadUsersList() {
    const resp = await apiFetch("/api/users");
    if (!resp.ok) return;
    const users = await resp.json();
    elements.usersList.innerHTML = "";
    users.forEach((u) => {
        const li = document.createElement("li");
        li.innerHTML = `
            <div>
                <strong>${escapeHtml(u.name)}</strong> (${escapeHtml(u.username)})
            </div>
            <span class="badge ${u.role === "admin" ? "badge-admin" : "badge-user"}">${escapeHtml(u.role)}</span>
        `;
        elements.usersList.appendChild(li);
    });
}

// Modal Helpers
function openModal(modalId) {
    document.getElementById(modalId).classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
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
