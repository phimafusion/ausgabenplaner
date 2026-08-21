// DOM Elements Cache

export const elements = {
    loginView: document.getElementById("login-view"),
    dashboardView: document.getElementById("dashboard-view"),
    loginForm: document.getElementById("login-form"),
    loginError: document.getElementById("login-error"),
    btnMobileMenu: document.getElementById("btn-mobile-menu"),
    navbarActions: document.getElementById("navbar-actions"),
    userDisplayName: document.getElementById("user-display-name"),
    userRoleBadge: document.getElementById("user-role-badge"),
    btnRunTests: document.getElementById("btn-run-tests"),
    btnSettings: document.getElementById("btn-settings"),
    btnLogout: document.getElementById("btn-logout"),

    planTitle: document.getElementById("plan-title"),
    selectVersion: document.getElementById("select-version"),
    draftStatusBadge: document.getElementById("draft-status-badge"),
    btnDiscardDraft: document.getElementById("btn-discard-draft"),
    btnSaveVersion: document.getElementById("btn-save-version"),
    btnOpenHistory: document.getElementById("btn-open-history"),

    kpiExpensesVal: document.getElementById("kpi-expenses-val"),
    kpiContributionsVal: document.getElementById("kpi-contributions-val"),
    kpiBalanceVal: document.getElementById("kpi-balance-val"),
    kpiBalanceCard: document.getElementById("kpi-balance-card"),

    btnToggleUnlockPositions: document.getElementById("btn-toggle-unlock-positions"),
    tablePositionsBody: document.querySelector("#table-positions tbody"),
    sumPositionsVal: document.getElementById("sum-positions-val"),
    sumPositionsColspan: document.getElementById("sum-positions-colspan"),
    btnAddPosition: document.getElementById("btn-add-position"),

    btnToggleUnlockContributions: document.getElementById("btn-toggle-unlock-contributions"),
    tableContributionsBody: document.querySelector("#table-contributions tbody"),
    sumContributionsVal: document.getElementById("sum-contributions-val"),
    sumContributionsColspan: document.getElementById("sum-contributions-colspan"),
    btnAddContribution: document.getElementById("btn-add-contribution"),

    // Position Modal
    modalPosition: document.getElementById("modal-position"),
    modalPosTitle: document.getElementById("modal-position-title"),
    formPosition: document.getElementById("form-position"),
    posId: document.getElementById("pos-id"),
    posTitle: document.getElementById("pos-title"),
    posInterval: document.getElementById("pos-interval"),
    posRawAmount: document.getElementById("pos-raw-amount"),
    posCalculatedMonthlyVal: document.getElementById("pos-calculated-monthly-val"),
    posAmount: document.getElementById("pos-amount"),
    posComment: document.getElementById("pos-comment"),

    // Contribution Modal
    modalContribution: document.getElementById("modal-contribution"),
    modalContribTitle: document.getElementById("modal-contribution-title"),
    formContribution: document.getElementById("form-contribution"),
    contribId: document.getElementById("contrib-id"),
    contribPerson: document.getElementById("contrib-person"),
    contribAmount: document.getElementById("contrib-amount"),
    contribComment: document.getElementById("contrib-comment"),

    // Save Version Modal
    modalSaveVersion: document.getElementById("modal-save-version"),
    formSaveVersion: document.getElementById("form-save-version"),
    saveVersionTitle: document.getElementById("save-version-title"),
    saveVersionDate: document.getElementById("save-version-date"),
    saveSummaryPosCount: document.getElementById("save-summary-pos-count"),
    saveSummaryExpenses: document.getElementById("save-summary-expenses"),
    saveSummaryContribCount: document.getElementById("save-summary-contrib-count"),
    saveSummaryContributions: document.getElementById("save-summary-contributions"),
    saveSummaryBalance: document.getElementById("save-summary-balance"),

    // Edit Version Modal
    modalVersionEdit: document.getElementById("modal-version-edit"),
    formVersionEdit: document.getElementById("form-version-edit"),
    editVerId: document.getElementById("edit-ver-id"),
    editVerTitle: document.getElementById("edit-ver-title"),
    editVerDate: document.getElementById("edit-ver-date"),

    // History Modal
    modalHistory: document.getElementById("modal-history"),
    tabBtnTimeline: document.getElementById("tab-btn-timeline"),
    tabBtnMatrix: document.getElementById("tab-btn-matrix"),
    historyTabTimeline: document.getElementById("history-tab-timeline"),
    historyTabMatrix: document.getElementById("history-tab-matrix"),
    historyTimelineList: document.getElementById("history-timeline-list"),
    historyContainer: document.getElementById("history-comparison-container") || document.getElementById("history-container"),

    // Confirm Delete Version Modal
    modalConfirmDeleteVersion: document.getElementById("modal-confirm-delete-version"),
    deleteVersionId: document.getElementById("delete-version-id"),
    deleteVersionTitleDisplay: document.getElementById("delete-version-title-display"),
    deleteVersionActiveWarning: document.getElementById("delete-version-active-warning"),
    btnExecuteDeleteVersion: document.getElementById("btn-execute-delete-version"),

    // Confirm Discard Draft Modal
    modalConfirmDiscardDraft: document.getElementById("modal-confirm-discard-draft"),
    btnExecuteDiscardDraft: document.getElementById("btn-execute-discard-draft"),

    // Unsaved Warning Modal
    modalUnsavedWarning: document.getElementById("modal-unsaved-warning"),
    btnDiscardUnsaved: document.getElementById("btn-discard-unsaved"),
    btnSaveBeforeAction: document.getElementById("btn-save-before-action"),

    settingsView: document.getElementById("settings-view"),
    settingsUserDisplayName: document.getElementById("settings-user-display-name"),
    settingsUserRoleBadge: document.getElementById("settings-user-role-badge"),
    btnBackToDashboard: document.getElementById("btn-back-to-dashboard"),
    btnBackToDashboardTop: document.getElementById("btn-back-to-dashboard-top"),
    btnBrandLogoSettings: document.getElementById("btn-brand-logo-settings"),
    btnLogoutSettings: document.getElementById("btn-logout-settings"),

    tabBtnUsers: document.getElementById("tab-btn-users"),
    tabBtnNewUser: document.getElementById("tab-btn-new-user"),
    tabBtnTestsuite: document.getElementById("tab-btn-testsuite"),
    btnSwitchToNewUser: document.getElementById("btn-switch-to-new-user"),
    formUserCreate: document.getElementById("form-user-create"),
    userEditId: document.getElementById("user-edit-id"),
    userUsername: document.getElementById("user-username"),
    userName: document.getElementById("user-name"),
    userPassword: document.getElementById("user-password"),
    userPasswordLabel: document.getElementById("user-password-label"),
    userPasswordHelp: document.getElementById("user-password-help"),
    userRole: document.getElementById("user-role"),
    userCanExport: document.getElementById("user-can-export"),
    userPermManagePlans: document.getElementById("user-perm-manage-plans"),
    userPermExport: document.getElementById("user-perm-export"),
    userPermImport: document.getElementById("user-perm-import"),
    userPermManageBackups: document.getElementById("user-perm-manage-backups"),
    userPermManageUsers: document.getElementById("user-perm-manage-users"),
    userPermRunTestsuite: document.getElementById("user-perm-run-testsuite"),
    userPermViewChangelog: document.getElementById("user-perm-view-changelog"),
    userPermissionsGroup: document.getElementById("user-permissions-group"),
    userPermissionsAdminHelp: document.getElementById("user-permissions-admin-help"),
    userFormHeading: document.getElementById("user-form-heading"),
    btnSubmitUser: document.getElementById("btn-submit-user"),
    btnCancelUserEdit: document.getElementById("btn-cancel-user-edit"),
    usersList: document.getElementById("users-list"),

    btnExportJson: document.getElementById("btn-export-json"),
    btnExportXlsx: document.getElementById("btn-export-xlsx"),
    btnImportJson: document.getElementById("btn-import-json"),

    modalImport: document.getElementById("modal-import"),
    formImportJson: document.getElementById("form-import-json"),
    importFileInput: document.getElementById("import-file-input"),
    importError: document.getElementById("import-error"),

    testsuiteStatusBox: document.getElementById("testsuite-status-box"),
    testsuiteOutput: document.getElementById("testsuite-output"),
    btnReRunTests: document.getElementById("btn-re-run-tests"),

    btnDeletePlan: document.getElementById("btn-delete-plan"),
    modalConfirmDeletePlan: document.getElementById("modal-confirm-delete-plan"),
    deletePlanId: document.getElementById("delete-plan-id"),
    deletePlanTitleDisplay: document.getElementById("delete-plan-title-display"),
    btnExecuteDeletePlan: document.getElementById("btn-execute-delete-plan"),
    tabBtnChangelog: document.getElementById("tab-btn-changelog"),
    tabBtnData: document.getElementById("tab-btn-data"),

    cardAutomatedBackups: document.getElementById("card-automated-backups"),
    formBackupSettings: document.getElementById("form-backup-settings"),
    btnSaveBackupSettings: document.getElementById("btn-save-backup-settings"),
    btnCreateManualBackup: document.getElementById("btn-create-manual-backup"),
    backupSettingsMsg: document.getElementById("backup-settings-msg"),
    backupsListBody: document.getElementById("backups-list-body"),

    // Multi-Plan Management Elements
    selectPlan: document.getElementById("select-plan"),
    planArchivedBadge: document.getElementById("plan-archived-badge"),
    btnQuickNewPlan: document.getElementById("btn-quick-new-plan"),
    btnQuickEditPlan: document.getElementById("btn-quick-edit-plan"),
    btnQuickDuplicatePlan: document.getElementById("btn-quick-duplicate-plan"),
    tabBtnPlans: document.getElementById("tab-btn-plans"),
    btnOpenCreatePlan: document.getElementById("btn-open-create-plan"),
    plansGrid: document.getElementById("plans-grid"),
    userPlansAssignmentContainer: document.getElementById("user-plans-assignment-container"),
    userPlansAssignmentGroup: document.getElementById("user-plans-assignment-group"),

    // Create Plan Modal
    modalCreatePlan: document.getElementById("modal-create-plan"),
    formCreatePlan: document.getElementById("form-create-plan"),
    createPlanTitle: document.getElementById("create-plan-title"),
    createPlanDesc: document.getElementById("create-plan-desc"),

    // Edit Plan Modal
    modalEditPlan: document.getElementById("modal-edit-plan"),
    formEditPlan: document.getElementById("form-edit-plan"),
    editPlanId: document.getElementById("edit-plan-id"),
    editPlanTitle: document.getElementById("edit-plan-title"),
    editPlanDesc: document.getElementById("edit-plan-desc"),
    editPlanArchived: document.getElementById("edit-plan-archived"),

    // Duplicate Plan Modal
    modalDuplicatePlan: document.getElementById("modal-duplicate-plan"),
    formDuplicatePlan: document.getElementById("form-duplicate-plan"),
    duplicatePlanId: document.getElementById("duplicate-plan-id"),
    duplicateSourceName: document.getElementById("duplicate-source-name"),
    duplicatePlanTitle: document.getElementById("duplicate-plan-title"),
};
