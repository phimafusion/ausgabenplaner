// Formatters and String Helpers

export function formatCurrency(val) {
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

export function formatGermanDate(isoStr) {
    if (!isoStr) return "";
    const parts = isoStr.split("-");
    if (parts.length === 3) {
        return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
    return isoStr;
}

export function formatDateTimeDE(dtStr) {
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

export function formatVersionDropdownLabel(v) {
    if (!v.effective_date) return v.title;
    const deDate = formatGermanDate(v.effective_date);
    if (v.title.includes(deDate)) {
        return v.title;
    }
    return `${v.title} (ab ${deDate})`;
}

export function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export function showToast(message, type = "success", duration = 3500) {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast-item toast-${type}`;

    let icon = "✓";
    if (type === "error") icon = "⚠️";
    if (type === "info") icon = "ℹ️";

    toast.innerHTML = `<span style="font-size: 1.1rem; line-height: 1;">${icon}</span><span>${escapeHtml(message)}</span>`;

    const removeToast = () => {
        toast.classList.add("toast-hide");
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 250);
    };

    toast.addEventListener("click", removeToast);
    container.appendChild(toast);

    setTimeout(removeToast, duration);
}

