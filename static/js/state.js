// Ausgabenplaner State Management

export const state = {
    token: localStorage.getItem("token") || null,
    user: null,
    availablePlans: [],
    activePlan: null,
    activePlanId: null,
    selectedVersionId: null,
    currentVersionDetails: null,
    isDirty: false,
    isPositionsUnlocked: false,
    isContributionsUnlocked: false,
    unlockedVersionIds: new Set(),
    pendingAction: null, // Callback when confirming discard of unsaved changes
};

export function setDirty(isDirty) {
    state.isDirty = isDirty;
    if (typeof state.onDirtyChange === "function") {
        state.onDirtyChange(isDirty);
    }
}
