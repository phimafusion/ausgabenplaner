// Central API Client
import { state } from "./state.js";

let onUnauthorizedCallback = null;

export function setUnauthorizedHandler(fn) {
    onUnauthorizedCallback = fn;
}

export async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (state.token) {
        headers["Authorization"] = `Bearer ${state.token}`;
    }
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }

    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            if (typeof onUnauthorizedCallback === "function") {
                onUnauthorizedCallback();
            }
            throw new Error("Sitzung abgelaufen. Bitte erneut anmelden.");
        }
        return response;
    } catch (err) {
        if (err.name === "TypeError" || (err.message && (err.message.includes("fetch") || err.message.includes("NetworkError")))) {
            throw new Error("Verbindung zum Server fehlgeschlagen. Der Server ist nicht erreichbar. Bitte starten Sie den Server in der Konsole.");
        }
        throw err;
    }
}
