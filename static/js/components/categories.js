// Categories Management & Dropdowns
import { state } from "../state.js";
import { elements } from "../dom.js";
import { apiFetch } from "../api.js";
import { openModal, closeModal } from "./modals.js";
import { escapeHtml } from "../formatters.js";

export async function loadCategories() {
    try {
        const resp = await apiFetch("/api/categories");
        if (!resp.ok) return;
        const categories = await resp.json();
        state.availableCategories = categories || [];
        populateCategoryDropdowns();
        renderCategoriesList();
    } catch (err) {
        console.error("Fehler beim Laden der Kategorien:", err);
    }
}

export function populateCategoryDropdowns() {
    // 1. Dashboard Filter Dropdown
    if (elements.posCategoryFilter) {
        const currentSelected = elements.posCategoryFilter.value;
        let html = '<option value="">🏷️ Alle Kategorien</option>';
        state.availableCategories.forEach((cat) => {
            html += `<option value="${escapeHtml(cat.name)}">${escapeHtml(cat.icon || "📦")} ${escapeHtml(cat.name)}</option>`;
        });
        elements.posCategoryFilter.innerHTML = html;
        elements.posCategoryFilter.value = currentSelected || "";
    }

    // 2. Position Modal Dropdown
    if (elements.posCategory) {
        let html = "";
        state.availableCategories.forEach((cat) => {
            html += `<option value="${escapeHtml(cat.name)}">${escapeHtml(cat.icon || "📦")} ${escapeHtml(cat.name)}</option>`;
        });
        elements.posCategory.innerHTML = html;
    }
}

export function renderCategoriesList() {
    if (!elements.categoriesListBody) return;
    elements.categoriesListBody.innerHTML = "";

    const userCanManage = state.user && (state.user.role === "admin" || state.user.can_manage_categories);

    state.availableCategories.forEach((cat) => {
        const tr = document.createElement("tr");
        const isDefault = Boolean(cat.is_default);

        tr.innerHTML = `
            <td style="font-size: 1.3rem; text-align: center;">${escapeHtml(cat.icon || "📦")}</td>
            <td><strong>${escapeHtml(cat.name)}</strong></td>
            <td>
                <span class="category-pill" style="background: ${hexToRgba(cat.color, 0.18)}; color: ${cat.color}; border-color: ${hexToRgba(cat.color, 0.4)};">
                    <span>${escapeHtml(cat.icon || "📦")}</span>
                    <span>${escapeHtml(cat.name)}</span>
                </span>
            </td>
            <td>
                <span class="badge ${isDefault ? 'badge-admin' : 'badge-user'}">${isDefault ? 'Standard' : 'Benutzerdefiniert'}</span>
            </td>
            <td class="text-right actions-cell">
                ${userCanManage ? `
                    <button class="btn btn-sm btn-outline btn-icon" onclick="openEditCategoryModal(${cat.id})" title="Bearbeiten">✏️</button>
                    ${!isDefault ? `<button class="btn btn-sm btn-danger btn-icon" onclick="openDeleteCategoryModal(${cat.id})" title="Löschen">🗑️</button>` : ''}
                ` : '<span class="text-muted" style="font-size: 0.8rem;">Nur Leserechte</span>'}
            </td>
        `;
        elements.categoriesListBody.appendChild(tr);
    });
}

export function openCreateCategoryModal() {
    if (!elements.modalCategory) return;
    if (elements.modalCategoryTitle) elements.modalCategoryTitle.textContent = "➕ Neue Kategorie anlegen";
    if (elements.categoryEditId) elements.categoryEditId.value = "";
    if (elements.categoryName) elements.categoryName.value = "";
    if (elements.categoryIcon) elements.categoryIcon.value = "📦";
    if (elements.categoryColor) elements.categoryColor.value = "#3b82f6";
    updateCategoryPreview();
    openModal("modal-category");
}

export function openEditCategoryModal(catId) {
    const cat = state.availableCategories.find((c) => c.id === catId);
    if (!cat) return;

    if (elements.modalCategoryTitle) elements.modalCategoryTitle.textContent = "✏️ Kategorie bearbeiten";
    if (elements.categoryEditId) elements.categoryEditId.value = cat.id;
    if (elements.categoryName) elements.categoryName.value = cat.name;
    if (elements.categoryIcon) elements.categoryIcon.value = cat.icon || "📦";
    if (elements.categoryColor) elements.categoryColor.value = cat.color || "#3b82f6";
    updateCategoryPreview();
    openModal("modal-category");
}

export function openDeleteCategoryModal(catId) {
    const cat = state.availableCategories.find((c) => c.id === catId);
    if (!cat) return;

    if (elements.deleteCategoryId) elements.deleteCategoryId.value = cat.id;
    if (elements.deleteCategoryNameDisplay) elements.deleteCategoryNameDisplay.textContent = `„${cat.name}“`;
    openModal("modal-confirm-delete-category");
}

export function updateCategoryPreview() {
    const name = elements.categoryName?.value?.trim() || "Kategoriename";
    const icon = elements.categoryIcon?.value?.trim() || "📦";
    const color = elements.categoryColor?.value || "#3b82f6";

    if (elements.previewIcon) elements.previewIcon.textContent = icon;
    if (elements.previewName) elements.previewName.textContent = name;
    if (elements.categoryPreviewBadge) {
        elements.categoryPreviewBadge.style.background = hexToRgba(color, 0.18);
        elements.categoryPreviewBadge.style.color = color;
        elements.categoryPreviewBadge.style.borderColor = hexToRgba(color, 0.4);
    }
}

export function getCategoryBadgeHtml(catName) {
    if (!catName) catName = "Allgemein";
    const cat = state.availableCategories.find((c) => c.name.toLowerCase() === catName.toLowerCase()) || {
        name: catName,
        icon: "📦",
        color: "#64748b",
    };

    const bg = hexToRgba(cat.color, 0.18);
    const border = hexToRgba(cat.color, 0.4);
    return `<span class="category-pill" style="background: ${bg}; color: ${cat.color}; border-color: ${border};"><span style="font-size: 0.95em;">${escapeHtml(cat.icon || "📦")}</span> <span>${escapeHtml(cat.name)}</span></span>`;
}

function hexToRgba(hex, alpha) {
    if (!hex || !hex.startsWith("#")) return `rgba(100, 116, 139, ${alpha})`;
    let c = hex.substring(1);
    if (c.length === 3) {
        c = c[0] + c[0] + c[1] + c[1] + c[2] + c[2];
    }
    const num = parseInt(c, 16);
    if (isNaN(num)) return `rgba(100, 116, 139, ${alpha})`;
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Global window mappings for onclick handlers
window.openEditCategoryModal = openEditCategoryModal;
window.openDeleteCategoryModal = openDeleteCategoryModal;
