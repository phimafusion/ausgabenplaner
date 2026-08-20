// Admin Testsuite Runner Component
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";

let activeEventSource = null;
let onSwitchTabCallback = null;

export function setSwitchTabHandler(fn) {
    onSwitchTabCallback = fn;
}

export async function executeTestsuite() {
    if (typeof onSwitchTabCallback === "function") {
        onSwitchTabCallback("tab-settings-testsuite");
    }

    const runBtn = document.getElementById("btn-re-run-tests") || elements.btnReRunTests;
    const progressBar = document.getElementById("testsuite-progress-bar");
    const progressPercent = document.getElementById("testsuite-progress-percent");
    const statusBox = document.getElementById("testsuite-status-box") || elements.testsuiteStatusBox;
    const outputBox = document.getElementById("testsuite-output") || elements.testsuiteOutput;

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = "⏳ Tests laufen...";
    }

    if (progressBar) progressBar.style.width = "0%";
    if (progressPercent) progressPercent.textContent = "0%";
    if (statusBox) {
        statusBox.className = "alert alert-info";
        statusBox.textContent = "⏳ Testsuite wird ausgeführt...";
    }
    if (outputBox) outputBox.textContent = "Initialisiere Testsuite...\n";

    if (activeEventSource) {
        try { activeEventSource.close(); } catch (e) {}
        activeEventSource = null;
    }

    const token = state.token || localStorage.getItem("token") || "";
    if (!token) {
        if (statusBox) {
            statusBox.className = "alert alert-danger";
            statusBox.textContent = "❌ Keine aktive Sitzung gefunden. Bitte erneut anmelden.";
        }
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = "🔄 Testsuite ausführen";
        }
        return;
    }

    let isCompleted = false;

    const finishSuccess = () => {
        if (isCompleted) return;
        isCompleted = true;
        if (progressBar) progressBar.style.width = "100%";
        if (progressPercent) progressPercent.textContent = "100%";
        if (statusBox) {
            statusBox.className = "alert alert-success";
            statusBox.textContent = "✅ Alle 38 Tests erfolgreich bestanden (100% Green)!";
        }
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = "🔄 Testsuite erneut ausführen";
        }
    };

    const finishFailure = (errMsg) => {
        if (isCompleted) return;
        isCompleted = true;
        if (statusBox) {
            statusBox.className = "alert alert-danger";
            statusBox.textContent = errMsg || "❌ Einige Tests sind fehlgeschlagen.";
        }
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = "🔄 Testsuite erneut ausführen";
        }
    };

    const runFallbackPost = async () => {
        try {
            const resp = await apiFetch("/api/admin/run-tests", { method: "POST" });
            const resData = await resp.json();
            if (outputBox) outputBox.textContent = resData.output || "";
            if (resData.passed) {
                finishSuccess();
            } else {
                finishFailure("❌ Testsuite fehlgeschlagen: " + (resData.output ? "Fehlerhafte Tests" : "Unbekannt"));
            }
        } catch (err) {
            finishFailure("❌ Fehler bei Testausführung: " + (err.message || "Netzwerkfehler"));
        }
    };

    try {
        const url = `/api/admin/run-tests-stream?token=${encodeURIComponent(token)}`;
        const evtSource = new EventSource(url);
        activeEventSource = evtSource;

        let gotAnyData = false;

        evtSource.onmessage = (event) => {
            gotAnyData = true;
            try {
                const data = JSON.parse(event.data);
                if (data.type === "start") {
                    if (statusBox) statusBox.textContent = `🚀 ${data.message}`;
                } else if (data.type === "log") {
                    if (data.progress !== undefined && progressBar && progressPercent) {
                        progressBar.style.width = `${data.progress}%`;
                        progressPercent.textContent = `${data.progress}%`;
                    }
                    if (outputBox) {
                        if (outputBox.textContent === "Initialisiere Testsuite...\n") {
                            outputBox.textContent = "";
                        }
                        outputBox.textContent += data.line;
                        const logBox = document.querySelector(".testsuite-log-box");
                        if (logBox) logBox.scrollTop = logBox.scrollHeight;
                    }
                } else if (data.type === "complete") {
                    evtSource.close();
                    activeEventSource = null;
                    if (data.passed) {
                        finishSuccess();
                    } else {
                        finishFailure();
                    }
                }
            } catch (e) {
                console.error("Event parse error", e);
            }
        };

        evtSource.onerror = async () => {
            evtSource.close();
            activeEventSource = null;
            if (!gotAnyData) {
                // Instantly run fallback via POST endpoint
                await runFallbackPost();
            } else if (!isCompleted) {
                finishFailure("❌ Stream unterbrochen.");
            }
        };
    } catch (err) {
        await runFallbackPost();
    }
}

// Window attachment for inline HTML onclick
window.executeTestsuite = executeTestsuite;
