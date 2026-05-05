/**
 * frontpage.js - Front page editor functions
 * Alhudha Haj Travel Management System
 */

'use strict';

// Module-level state
let frontpageSettings = {};
let packagesList = [];
let featuresList = [];

// ====== LOAD FRONTPAGE SETTINGS ======
/**
 * Fetch current front page settings from the API
 */
async function loadFrontpageSettings() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/frontpage');
        frontpageSettings = data.settings || data || {};
        populateFrontpageForm(frontpageSettings);
        console.log('✅ Front page settings loaded');
    } catch (error) {
        handleApiError(error, 'Load front page settings');
    } finally {
        showLoading(false);
    }
}

/**
 * Populate the front page form with loaded settings
 * @param {Object} settings
 */
function populateFrontpageForm(settings) {
    const fieldMap = {
        'heroTitle':         settings.hero_title         || settings.heroTitle,
        'heroSubtitle':      settings.hero_subtitle      || settings.heroSubtitle,
        'heroButtonText':    settings.hero_button_text   || settings.heroButtonText,
        'heroButtonLink':    settings.hero_button_link   || settings.heroButtonLink,
        'aboutTitle':        settings.about_title        || settings.aboutTitle,
        'aboutText':         settings.about_text         || settings.aboutText,
        'contactEmail':      settings.contact_email      || settings.contactEmail,
        'contactPhone':      settings.contact_phone      || settings.contactPhone,
        'contactAddress':    settings.contact_address    || settings.contactAddress,
        'companyName':       settings.company_name       || settings.companyName,
        'primaryColor':      settings.primary_color      || settings.primaryColor,
        'secondaryColor':    settings.secondary_color    || settings.secondaryColor,
        'fontFamily':        settings.font_family        || settings.fontFamily
    };

    Object.entries(fieldMap).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el && value !== undefined && value !== null) el.value = value;
    });

    // Load packages and features lists
    if (settings.packages) {
        packagesList = Array.isArray(settings.packages) ? settings.packages : [];
        renderPackagesList();
    }
    if (settings.features) {
        featuresList = Array.isArray(settings.features) ? settings.features : [];
        renderFeaturesList();
    }
}

// ====== SAVE FRONTPAGE SETTINGS ======
/**
 * Save front page settings to the API
 */
async function saveFrontpageSettings() {
    const settingsData = collectFrontpageFormData();

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', '/api/frontpage', settingsData);
        if (result.success || result.id || result.message) {
            frontpageSettings = settingsData;
            showNotification('Front page settings saved successfully!', 'success');
        } else {
            showNotification(result.error || 'Failed to save settings', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Save front page settings');
    } finally {
        showLoading(false);
    }
}

/**
 * Collect all form data from the front page editor
 * @returns {Object}
 */
function collectFrontpageFormData() {
    const fields = [
        'heroTitle','heroSubtitle','heroButtonText','heroButtonLink',
        'aboutTitle','aboutText','contactEmail','contactPhone',
        'contactAddress','companyName','primaryColor','secondaryColor','fontFamily'
    ];

    const data = {};
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) data[id] = el.value;
    });

    data.packages = packagesList;
    data.features = featuresList;

    return data;
}

// ====== PUBLISH CHANGES ======
/**
 * Publish front page changes to the live site
 */
async function publishChanges() {
    // Save first, then publish
    const settingsData = collectFrontpageFormData();

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/frontpage/publish', settingsData);
        if (result.success || result.message) {
            showNotification('Website published successfully! Public homepage updated.', 'success');
            updatePreview();
        } else {
            showNotification(result.error || 'Failed to publish changes', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Publish front page changes');
    } finally {
        showLoading(false);
    }
}

// ====== LOAD SAVED SETTINGS ======
/**
 * Load previously saved settings (alias for loadFrontpageSettings with notification)
 */
async function loadSavedSettings() {
    await loadFrontpageSettings();
    showNotification('Saved settings loaded', 'info');
}

// ====== UPDATE PREVIEW ======
/**
 * Update the live preview iframe with current settings
 */
function updatePreview() {
    const iframe = document.getElementById('previewFrame') || document.getElementById('sitePreview');
    if (!iframe) return;

    // Reload the preview iframe
    const src = iframe.src;
    iframe.src = '';
    setTimeout(() => { iframe.src = src || '/'; }, 100);
}

// ====== ADD PACKAGE ======
/**
 * Add a new package item to the packages list
 */
function addPackage() {
    const nameEl  = document.getElementById('newPackageName')  || document.getElementById('packageName');
    const priceEl = document.getElementById('newPackagePrice') || document.getElementById('packagePrice');
    const descEl  = document.getElementById('newPackageDesc')  || document.getElementById('packageDesc');

    const name  = nameEl  ? nameEl.value.trim()  : '';
    const price = priceEl ? priceEl.value.trim()  : '';
    const desc  = descEl  ? descEl.value.trim()   : '';

    if (!name) {
        showNotification('Package name is required', 'error');
        return;
    }

    packagesList.push({ name, price, description: desc });
    renderPackagesList();

    if (nameEl)  nameEl.value  = '';
    if (priceEl) priceEl.value = '';
    if (descEl)  descEl.value  = '';

    showNotification('Package added', 'success');
}

/**
 * Render the packages list in the editor
 */
function renderPackagesList() {
    const container = document.getElementById('packagesList') || document.getElementById('packagesContainer');
    if (!container) return;

    if (packagesList.length === 0) {
        container.innerHTML = '<p style="color:#95a5a6;font-size:0.9rem;">No packages added yet</p>';
        return;
    }

    container.innerHTML = packagesList.map((pkg, index) => `
        <div style="background:#f8f9fa;padding:12px;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong>${escapeHtml(pkg.name)}</strong>
                ${pkg.price ? ` — ${escapeHtml(pkg.price)}` : ''}
                ${pkg.description ? `<div style="font-size:0.85rem;color:#7f8c8d;">${escapeHtml(pkg.description)}</div>` : ''}
            </div>
            <button onclick="removePackage(${index})" style="background:none;border:none;color:#e74c3c;cursor:pointer;font-size:1.1rem;" title="Remove">
                <i class="fas fa-times"></i>
            </button>
        </div>`).join('');
}

// ====== REMOVE PACKAGE ======
/**
 * Remove a package item from the list
 * @param {number} index
 */
function removePackage(index) {
    packagesList.splice(index, 1);
    renderPackagesList();
}

// ====== ADD FEATURE ======
/**
 * Add a new feature item to the features list
 */
function addFeature() {
    const textEl = document.getElementById('newFeatureText') || document.getElementById('featureText');
    const iconEl = document.getElementById('newFeatureIcon') || document.getElementById('featureIcon');

    const text = textEl ? textEl.value.trim() : '';
    const icon = iconEl ? iconEl.value.trim() : 'fa-check';

    if (!text) {
        showNotification('Feature text is required', 'error');
        return;
    }

    featuresList.push({ text, icon });
    renderFeaturesList();

    if (textEl) textEl.value = '';
    if (iconEl) iconEl.value = '';

    showNotification('Feature added', 'success');
}

/**
 * Render the features list in the editor
 */
function renderFeaturesList() {
    const container = document.getElementById('featuresList') || document.getElementById('featuresContainer');
    if (!container) return;

    if (featuresList.length === 0) {
        container.innerHTML = '<p style="color:#95a5a6;font-size:0.9rem;">No features added yet</p>';
        return;
    }

    container.innerHTML = featuresList.map((feat, index) => `
        <div style="background:#f8f9fa;padding:12px;border-radius:8px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
            <div>
                <i class="fas ${escapeHtml(feat.icon || 'fa-check')}" style="color:#3498db;margin-right:8px;"></i>
                ${escapeHtml(feat.text)}
            </div>
            <button onclick="removeFeature(${index})" style="background:none;border:none;color:#e74c3c;cursor:pointer;font-size:1.1rem;" title="Remove">
                <i class="fas fa-times"></i>
            </button>
        </div>`).join('');
}

// ====== REMOVE FEATURE ======
/**
 * Remove a feature item from the list
 * @param {number} index
 */
function removeFeature(index) {
    featuresList.splice(index, 1);
    renderFeaturesList();
}

// ====== UPLOAD LOGO ======
/**
 * Upload the company logo
 * @param {File} file
 */
async function uploadLogo(file) {
    if (!file) {
        const input = document.getElementById('logoUpload') || document.getElementById('logoFile');
        if (input && input.files && input.files[0]) {
            file = input.files[0];
        } else {
            showNotification('No file selected', 'error');
            return;
        }
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('Only JPG, PNG, GIF, SVG, and WebP files are allowed', 'error');
        return;
    }

    if (file.size > 2 * 1024 * 1024) {
        showNotification('Logo file size must be less than 2MB', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('logo', file);

    showLoading(true);
    try {
        const response = await fetch('/api/frontpage/logo', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!response.ok) throw new Error(`Upload failed: HTTP ${response.status}`);

        const result = await response.json();
        if (result.success || result.url) {
            showNotification('Logo uploaded successfully!', 'success');

            // Update preview image
            const preview = document.getElementById('logoPreview') || document.getElementById('currentLogo');
            if (preview && result.url) preview.src = result.url;
        } else {
            showNotification(result.error || 'Logo upload failed', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Upload logo');
    } finally {
        showLoading(false);
    }
}
