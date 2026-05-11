/**
 * frontpage.js - Front page editor functions
 * Alhudha Haj Travel Admin Panel
 * Alhudha Haj Travel Management System
 * frontpage.js - Front Page Editor for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/company/settings  (frontpage settings stored in company_settings)
 */

'use strict';

// ====== STATE ======
let frontpagePackages = [];
let frontpageFeatures = [];
let frontpageCompanyDetails = {};

// ====== LOAD FRONTPAGE SETTINGS ======
/**
 * Fetch frontpage settings from /api/frontpage
 */
async function loadFrontpageSettings() {
    try {
        const data = await makeAPICall('GET', '/api/frontpage');
        if (data.success && data.settings) {
            applyFrontpageSettings(data.settings);
            console.log('✅ Frontpage settings loaded from API');
        } else {
            loadSavedSettings();
        }
    } catch (error) {
        console.log('ℹ️ Frontpage API not available, loading from localStorage');
        loadSavedSettings();
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
 * POST/PUT frontpage settings to /api/frontpage
 */
async function saveFrontpageSettings() {
    const settings = collectFrontpageSettings();

    try {
        const data = await makeAPICall('POST', '/api/frontpage', settings);
        if (data.success) {
            showNotification('Settings saved to database!', 'success');
        } else {
            // Fallback to localStorage
            saveToLocalStorage(settings);
            showNotification('Settings saved locally!', 'success');
        }
    } catch (error) {
        saveToLocalStorage(settings);
        showNotification('Settings saved locally!', 'success');
    }
}

// Alias for inline HTML
function saveChanges() { saveFrontpageSettings(); }

// ====== PUBLISH CHANGES ======
/**
 * Publish frontpage changes to the live site
 */
async function publishChanges() {
    await saveFrontpageSettings();

    try {
        const data = await makeAPICall('POST', '/api/frontpage/publish', {});
        if (data.success) {
            showNotification('Changes published to live site!', 'success');
        } else {
            showNotification('Settings saved. Live site will update shortly.', 'info');
        }
    } catch (error) {
        showNotification('Settings saved. Live site will update on next reload.', 'info');
    }

    updatePreview();
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
 * Load settings from localStorage
 */
function loadSavedSettings() {
    const set = (id, key, def) => {
        const el = document.getElementById(id);
        if (el) el.value = localStorage.getItem(key) || def || '';
    };

    set('heroHeading', 'heroHeading', 'Your Journey to the Holy Land');
    set('heroSubheading', 'heroSubheading', 'Experience the spiritual journey of a lifetime with our premium Haj and Umrah packages.');
    set('heroButton', 'heroButton', 'View Packages');
    set('heroButtonLink', 'heroButtonLink', '#packages');
    set('packagesTitle', 'packagesTitle', 'Our Haj & Umrah Packages');
    set('footerText', 'footerText', '© 2026 Alhudha Haj Travel. All rights reserved.');
    set('footerPhone', 'footerPhone', '+91 98765 43210');
    set('footerEmail', 'footerEmail', 'info@alhudha.com');
    set('whatsappNumber', 'whatsappNumber', '919876543210');
    set('bookingEmail', 'bookingEmail', 'bookings@alhudha.com');

    // Load company details
    const savedCompany = localStorage.getItem('companyDetails');
    if (savedCompany) {
        try {
            frontpageCompanyDetails = JSON.parse(savedCompany);
        } catch (e) {
            frontpageCompanyDetails = {};
        }
    }

    // Load packages and features
    const savedPackages = localStorage.getItem('packages');
    if (savedPackages) {
        try {
            frontpagePackages = JSON.parse(savedPackages);
            if (typeof renderPackages === 'function') renderPackages();
        } catch (e) {
            frontpagePackages = [];
        }
    }

    const savedFeatures = localStorage.getItem('features');
    if (savedFeatures) {
        try {
            frontpageFeatures = JSON.parse(savedFeatures);
            if (typeof renderFeatures === 'function') renderFeatures();
        } catch (e) {
            frontpageFeatures = [];
        }
    }

    updatePreview();
    console.log('✅ Settings loaded from localStorage');
}

// ====== UPDATE PREVIEW ======
/**
 * Update the iframe preview with current settings
 */
function updatePreview() {
    const previewFrame = document.getElementById('previewFrame');
    if (!previewFrame) return;

    const heading = document.getElementById('heroHeading')?.value || 'Your Journey to the Holy Land';
    const subheading = document.getElementById('heroSubheading')?.value || '';
    const buttonText = document.getElementById('heroButton')?.value || 'View Packages';
    const heroColor1 = document.getElementById('heroColor1')?.value || '#1e3c72';
    const heroColor2 = document.getElementById('heroColor2')?.value || '#3498db';
    const footerText = document.getElementById('footerText')?.value || '© 2026 Alhudha Haj Travel';
    const primaryColor = document.getElementById('primaryColor')?.value || '#3498db';
    const fontFamily = document.getElementById('fontFamily')?.value || "'Segoe UI', sans-serif";

    const alertEnabled = document.getElementById('urgentAlertEnabled')?.checked;
    const alertMessage = document.getElementById('urgentAlertMessage')?.value || '';
    const alertColor = document.getElementById('urgentAlertColor')?.value || '#f39c12';

    const packagesHtml = frontpagePackages.map(pkg => `
        <div style="background:white;padding:20px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1);text-align:center;">
            <i class="fas ${pkg.icon || 'fa-mosque'}" style="font-size:2rem;color:${primaryColor};margin-bottom:10px;"></i>
            <h3>${escapeHtml(pkg.name)}</h3>
            <p style="color:#7f8c8d;">${escapeHtml(pkg.description || '')}</p>
            ${pkg.price ? `<div style="font-size:1.3rem;font-weight:bold;color:#27ae60;">₹${Number(pkg.price).toLocaleString('en-IN')}</div>` : ''}
        </div>`).join('');

    const previewHtml = `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: ${fontFamily}; }
    .hero { background: linear-gradient(135deg, ${heroColor1}, ${heroColor2}); color: white; padding: 60px 20px; text-align: center; }
    .hero h1 { font-size: 2rem; margin-bottom: 15px; }
    .hero p { font-size: 1rem; opacity: 0.9; margin-bottom: 25px; }
    .hero-btn { background: white; color: ${heroColor1}; padding: 12px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; display: inline-block; }
    .packages { padding: 40px 20px; background: #f5f7fa; }
    .packages h2 { text-align: center; margin-bottom: 30px; color: #2c3e50; }
    .packages-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
    .alert-bar { background: ${alertColor}; color: white; padding: 10px 20px; text-align: center; font-weight: bold; }
    footer { background: #2c3e50; color: white; padding: 20px; text-align: center; }
</style>
</head><body>
    ${alertEnabled && alertMessage ? `<div class="alert-bar"><i class="fas fa-exclamation-triangle"></i> ${escapeHtml(alertMessage)}</div>` : ''}
    <div class="hero">
        <h1>${escapeHtml(heading)}</h1>
        <p>${escapeHtml(subheading)}</p>
        <a href="#" class="hero-btn">${escapeHtml(buttonText)}</a>
    </div>
    ${frontpagePackages.length > 0 ? `
    <div class="packages">
        <h2>${escapeHtml(document.getElementById('packagesTitle')?.value || 'Our Packages')}</h2>
        <div class="packages-grid">${packagesHtml}</div>
    </div>` : ''}
    <footer><p>${escapeHtml(footerText)}</p></footer>
</body></html>`;

    try {
        const blob = new Blob([previewHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        previewFrame.src = url;
    } catch (e) {
        previewFrame.srcdoc = previewHtml;
    }
}

// ====== ADD PACKAGE ======
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
// ── State ────────────────────────────────────────────────────
let frontpageSettings = {};
let packages = [];
let features = [];

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadFrontpageSettings();
        initPreviewListeners();
    });
});

function initPreviewListeners() {
    // Auto-update preview on input changes
    const inputs = document.querySelectorAll('.frontpage-input, .preview-trigger');
    inputs.forEach((el) => {
        el.addEventListener('input', debounce(updatePreview, 500));
        el.addEventListener('change', debounce(updatePreview, 500));
    });
}

// ── Load & Save ───────────────────────────────────────────────

/**
 * Load frontpage settings from the API
 */
async function loadFrontpageSettings() {
    showLoading('Loading settings…');
    try {
        const data = await makeAPICall('GET', '/api/company/settings');
        hideLoading();
        if (data.success && data.settings) {
            frontpageSettings = data.settings;
            populateFrontpageForm(data.settings);
            updatePreview();
        } else {
            throw new Error(data.error || 'Failed to load settings');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'loadFrontpageSettings');
    }
}

/**
 * Populate the form fields with loaded settings
 * @param {Object} settings
 */
function populateFrontpageForm(settings) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };

    set('company_name',    settings.company_name);
    set('company_address', settings.address);
    set('company_phone',   settings.phone);
    set('company_email',   settings.email);
    set('company_website', settings.website);
    set('footer_text',     settings.footer_text);
    set('terms_conditions', settings.terms_conditions);

    // Parse packages/features if stored as JSON
    try {
        packages = JSON.parse(settings.packages || '[]');
    } catch (e) { packages = []; }
    try {
        features = JSON.parse(settings.features || '[]');
    } catch (e) { features = []; }

    renderPackagesList();
    renderFeaturesList();
}

/**
 * Save frontpage settings to the API
 */
async function saveFrontpageSettings() {
    const getData = (id) => (document.getElementById(id)?.value || '').trim();

    const settingsData = {
        company_name:      getData('company_name'),
        address:           getData('company_address'),
        phone:             getData('company_phone'),
        email:             getData('company_email'),
        website:           getData('company_website'),
        footer_text:       getData('footer_text'),
        terms_conditions:  getData('terms_conditions'),
        packages:          JSON.stringify(packages),
        features:          JSON.stringify(features)
    };

    const btn  = document.getElementById('saveSettingsBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…'; btn.disabled = true; }

    try {
        const data = await makeAPICall('POST', '/api/company/settings', settingsData);
        if (data.success) {
            showNotification('Settings saved successfully!', 'success');
            frontpageSettings = { ...frontpageSettings, ...settingsData };
        } else {
            throw new Error(data.error || 'Could not save settings');
        }
    } catch (error) {
        handleError(error, 'saveFrontpageSettings');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Publish changes to the live site
 */
async function publishChanges() {
    if (!confirmAction('Publish these changes to the live site?')) return;

    const btn  = document.getElementById('publishBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Publishing…'; btn.disabled = true; }

    try {
        // Save first, then mark as published
        await saveFrontpageSettings();
        showNotification('Changes published to live site!', 'success');
    } catch (error) {
        handleError(error, 'publishChanges');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Reload settings from the database (discard unsaved changes)
 */
async function loadSavedSettings() {
    if (!confirmAction('Reload saved settings? Any unsaved changes will be lost.')) return;
    await loadFrontpageSettings();
    showNotification('Settings reloaded from database', 'info');
}

// ── Preview ───────────────────────────────────────────────────

/**
 * Update the preview iframe or preview panel
 */
function updatePreview() {
    const previewFrame = document.getElementById('previewFrame');
    if (previewFrame) {
        // Reload the iframe to show latest saved state
        try {
            previewFrame.src = previewFrame.src;
        } catch (e) { /* cross-origin */ }
        return;
    }

    // Inline preview panel
    const previewPanel = document.getElementById('previewPanel');
    if (!previewPanel) return;

    const name    = document.getElementById('company_name')?.value || 'Alhudha Haj Travel';
    const address = document.getElementById('company_address')?.value || '';
    const phone   = document.getElementById('company_phone')?.value || '';
    const email   = document.getElementById('company_email')?.value || '';
    const footer  = document.getElementById('footer_text')?.value || '';

    previewPanel.innerHTML = `
        <div style="font-family:'Segoe UI',sans-serif; padding:20px; background:#f5f7fa; border-radius:8px;">
            <div style="background:linear-gradient(135deg,#2c3e50,#34495e); color:white; padding:20px; border-radius:8px; margin-bottom:15px;">
                <h2 style="margin:0;">${escapeHtml(name)}</h2>
                ${address ? `<p style="margin:5px 0; opacity:0.8;">${escapeHtml(address)}</p>` : ''}
                <div style="display:flex; gap:20px; margin-top:10px; font-size:0.9rem;">
                    ${phone ? `<span><i class="fas fa-phone"></i> ${escapeHtml(phone)}</span>` : ''}
                    ${email ? `<span><i class="fas fa-envelope"></i> ${escapeHtml(email)}</span>` : ''}
                </div>
            </div>
            ${packages.length > 0 ? `
                <h3 style="color:#2c3e50; margin-bottom:10px;">Packages</h3>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:15px;">
                    ${packages.map((p) => `<div style="background:white; padding:15px; border-radius:8px; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                        <strong>${escapeHtml(p.name || '')}</strong>
                        ${p.price ? `<p style="color:#27ae60; font-weight:bold;">${formatCurrency(p.price)}</p>` : ''}
                    </div>`).join('')}
                </div>` : ''}
            ${footer ? `<div style="text-align:center; color:#7f8c8d; font-size:0.9rem; margin-top:15px;">${escapeHtml(footer)}</div>` : ''}
        </div>`;
}

// ── Packages ──────────────────────────────────────────────────

/**
 * Add a new package item
 */
function addPackage() {
    if (typeof showAddPackageModal === 'function') {
        showAddPackageModal();
    } else {
        const name = prompt('Package name:');
        if (!name) return;
        frontpagePackages.push({ id: Date.now(), name, description: '', price: '', icon: 'fa-mosque' });
        if (typeof renderPackages === 'function') renderPackages();
        updatePreview();
        showNotification('Package added', 'success');
    }
}

// ====== REMOVE PACKAGE ======
    packages.push({ name: '', price: '', description: '', duration: '' });
    renderPackagesList();
}

/**
 * Remove a package by index
 * @param {number} index
 */
function removePackage(index) {
    if (index >= 0 && index < frontpagePackages.length) {
        frontpagePackages.splice(index, 1);
        if (typeof renderPackages === 'function') renderPackages();
        updatePreview();
        showNotification('Package removed', 'success');
    }
}

// ====== ADD FEATURE ======
    packages.splice(index, 1);
    renderPackagesList();
    updatePreview();
}

function renderPackagesList() {
    const container = document.getElementById('packagesList');
    if (!container) return;

    if (packages.length === 0) {
        container.innerHTML = '<p style="color:#7f8c8d; text-align:center; padding:20px;">No packages added yet. Click "Add Package" to start.</p>';
        return;
    }

    container.innerHTML = packages.map((pkg, i) => `
        <div style="background:white; padding:20px; border-radius:8px; margin-bottom:15px; border:1px solid #ecf0f1; position:relative;">
            <button onclick="removePackage(${i})" style="position:absolute; top:10px; right:10px; background:#e74c3c; color:white; border:none; border-radius:50%; width:28px; height:28px; cursor:pointer; font-size:1rem;" title="Remove">×</button>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px;">
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Package Name</label>
                    <input type="text" value="${escapeHtml(pkg.name || '')}" onchange="packages[${i}].name=this.value; updatePreview();"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="e.g. Haj Gold">
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Price (₹)</label>
                    <input type="number" value="${pkg.price || ''}" onchange="packages[${i}].price=this.value; updatePreview();"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="e.g. 250000">
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Duration</label>
                    <input type="text" value="${escapeHtml(pkg.duration || '')}" onchange="packages[${i}].duration=this.value;"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="e.g. 30 days">
                </div>
                <div>
                    <label style="display:block; margin-bottom:5px; font-weight:600;">Description</label>
                    <input type="text" value="${escapeHtml(pkg.description || '')}" onchange="packages[${i}].description=this.value;"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="Short description">
                </div>
            </div>
        </div>`).join('');
}

// ── Features ──────────────────────────────────────────────────

/**
 * Add a new feature item
 */
function addFeature() {
    frontpageFeatures.push({ id: Date.now(), text: 'New Feature', icon: 'fa-check-circle' });
    if (typeof renderFeatures === 'function') renderFeatures();
    updatePreview();
    showNotification('Feature added', 'success');
}

// ====== REMOVE FEATURE ======
    features.push({ title: '', description: '', icon: 'fa-star' });
    renderFeaturesList();
}

/**
 * Remove a feature by index
 * @param {number} index
 */
function removeFeature(index) {
    if (index >= 0 && index < frontpageFeatures.length) {
        frontpageFeatures.splice(index, 1);
        if (typeof renderFeatures === 'function') renderFeatures();
        updatePreview();
        showNotification('Feature removed', 'success');
    }
    features.splice(index, 1);
    renderFeaturesList();
}

function renderFeaturesList() {
    const container = document.getElementById('featuresList');
    if (!container) return;

    if (features.length === 0) {
        container.innerHTML = '<p style="color:#7f8c8d; text-align:center; padding:20px;">No features added yet. Click "Add Feature" to start.</p>';
        return;
    }

    container.innerHTML = features.map((feat, i) => `
        <div style="background:white; padding:15px; border-radius:8px; margin-bottom:10px; border:1px solid #ecf0f1; display:flex; gap:15px; align-items:flex-start;">
            <div style="flex:1; display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div>
                    <label style="display:block; margin-bottom:4px; font-weight:600; font-size:0.9rem;">Title</label>
                    <input type="text" value="${escapeHtml(feat.title || '')}" onchange="features[${i}].title=this.value;"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="Feature title">
                </div>
                <div>
                    <label style="display:block; margin-bottom:4px; font-weight:600; font-size:0.9rem;">Icon (FA class)</label>
                    <input type="text" value="${escapeHtml(feat.icon || 'fa-star')}" onchange="features[${i}].icon=this.value;"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="fa-star">
                </div>
                <div style="grid-column:1/-1;">
                    <label style="display:block; margin-bottom:4px; font-weight:600; font-size:0.9rem;">Description</label>
                    <input type="text" value="${escapeHtml(feat.description || '')}" onchange="features[${i}].description=this.value;"
                        style="width:100%; padding:8px; border:2px solid #ecf0f1; border-radius:5px;" placeholder="Short description">
                </div>
            </div>
            <button onclick="removeFeature(${i})" style="background:#e74c3c; color:white; border:none; border-radius:5px; padding:8px 12px; cursor:pointer;" title="Remove">
                <i class="fas fa-trash"></i>
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
 * Handle logo file upload
 * @param {HTMLInputElement} input
 */
function uploadLogo(input) {
    if (!input?.files?.[0]) return;

    const file = input.files[0];
    if (!file.type.startsWith('image/')) {
        showNotification('Please select an image file', 'error'); return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('logoPreview');
        if (preview) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Logo" style="max-width:200px;max-height:80px;margin-top:10px;">`;
        }
        localStorage.setItem('companyLogo', e.target.result);
        showNotification('Logo uploaded successfully!', 'success');
        updatePreview();
    };
    reader.readAsDataURL(file);
}

// Alias for inline HTML
function handleLogoUpload(input) { uploadLogo(input); }

// ====== HELPERS ======
function collectFrontpageSettings() {
    return {
        heroHeading: document.getElementById('heroHeading')?.value,
        heroSubheading: document.getElementById('heroSubheading')?.value,
        heroButton: document.getElementById('heroButton')?.value,
        heroButtonLink: document.getElementById('heroButtonLink')?.value,
        heroColor1: document.getElementById('heroColor1')?.value,
        heroColor2: document.getElementById('heroColor2')?.value,
        packagesTitle: document.getElementById('packagesTitle')?.value,
        footerText: document.getElementById('footerText')?.value,
        footerPhone: document.getElementById('footerPhone')?.value,
        footerEmail: document.getElementById('footerEmail')?.value,
        whatsappNumber: document.getElementById('whatsappNumber')?.value,
        bookingEmail: document.getElementById('bookingEmail')?.value,
        primaryColor: document.getElementById('primaryColor')?.value,
        fontFamily: document.getElementById('fontFamily')?.value,
        urgentAlertEnabled: document.getElementById('urgentAlertEnabled')?.checked,
        urgentAlertMessage: document.getElementById('urgentAlertMessage')?.value,
        urgentAlertColor: document.getElementById('urgentAlertColor')?.value,
        packages: frontpagePackages,
        features: frontpageFeatures
    };
}

function saveToLocalStorage(settings) {
    Object.entries(settings).forEach(([key, val]) => {
        if (typeof val === 'object') {
            localStorage.setItem(key, JSON.stringify(val));
        } else if (val !== null && val !== undefined) {
            localStorage.setItem(key, String(val));
        }
    });
}

function applyFrontpageSettings(settings) {
    const set = (id, val) => { const el = document.getElementById(id); if (el && val !== undefined) el.value = val; };
    set('heroHeading', settings.heroHeading);
    set('heroSubheading', settings.heroSubheading);
    set('heroButton', settings.heroButton);
    set('heroButtonLink', settings.heroButtonLink);
    set('packagesTitle', settings.packagesTitle);
    set('footerText', settings.footerText);
    set('footerPhone', settings.footerPhone);
    set('footerEmail', settings.footerEmail);
    set('whatsappNumber', settings.whatsappNumber);
    set('bookingEmail', settings.bookingEmail);

    if (settings.packages) {
        frontpagePackages = settings.packages;
        if (typeof renderPackages === 'function') renderPackages();
    }
    if (settings.features) {
        frontpageFeatures = settings.features;
        if (typeof renderFeatures === 'function') renderFeatures();
    }

    updatePreview();
}

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
// ── Logo Upload ───────────────────────────────────────────────

/**
 * Handle logo file upload
 */
async function uploadLogo() {
    const fileInput = document.getElementById('logoFile') || document.getElementById('logo_upload');
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
        showNotification('Please select a logo file first', 'error');
        return;
    }

    const file = fileInput.files[0];
    const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/gif'];
    if (!allowed.includes(file.type)) {
        showNotification('Invalid file type. Allowed: PNG, JPG, SVG, GIF', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('logo', file);

    showLoading(true);
    try {
        const response = await fetch('/api/frontpage/logo', {
    const btn  = document.getElementById('uploadLogoBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading…'; btn.disabled = true; }

    try {
        const response = await fetch('/api/company/logo', {
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
        const data = await response.json();
        if (data.success) {
            showNotification('Logo uploaded successfully!', 'success');
            const preview = document.getElementById('logoPreview');
            if (preview) { preview.src = data.logo_url; preview.style.display = 'block'; }
        } else {
            throw new Error(data.error || 'Could not upload logo');
        }
    } catch (error) {
        handleError(error, 'uploadLogo');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

// Expose globals
window.loadFrontpageSettings = loadFrontpageSettings;
window.saveFrontpageSettings = saveFrontpageSettings;
window.publishChanges        = publishChanges;
window.loadSavedSettings     = loadSavedSettings;
window.updatePreview         = updatePreview;
window.addPackage            = addPackage;
window.removePackage         = removePackage;
window.addFeature            = addFeature;
window.removeFeature         = removeFeature;
window.uploadLogo            = uploadLogo;

console.log('✅ frontpage.js loaded');
