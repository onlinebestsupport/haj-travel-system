/**
 * frontpage.js - Front page editor functions
 * Alhudha Haj Travel Admin Panel
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

console.log('✅ frontpage.js loaded');
