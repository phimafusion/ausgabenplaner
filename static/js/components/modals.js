// Modals & Dialog Handling
import { state } from "../state.js";

export function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove("hidden");
}

export function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add("hidden");
}

export function guardedAction(callback) {
    if (state.isDirty) {
        state.pendingAction = callback;
        openModal("modal-unsaved-warning");
    } else {
        callback();
    }
}
