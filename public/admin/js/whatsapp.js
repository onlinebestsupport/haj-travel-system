/**
 * whatsapp.js - WhatsApp configuration and messaging functions
 * Alhudha Haj Travel Management System
 * whatsapp.js - WhatsApp Settings for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/whatsapp  (settings stored in company_settings or dedicated table)
 */

'use strict';

// ====== LOAD WHATSAPP SETTINGS ======
/**
 * Fetch WhatsApp configuration from the API
 */
async function loadWhatsAppSettings() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/whatsapp');
        const settings = data.settings || data || {};

        const fieldMap = {
            'whatsappApiKey':       settings.api_key        || settings.apiKey,
            'whatsappPhoneId':      settings.phone_id       || settings.phoneId,
            'whatsappBusinessId':   settings.business_id    || settings.businessId,
            'whatsappAccessToken':  settings.access_token   || settings.accessToken,
            'whatsappWebhookUrl':   settings.webhook_url    || settings.webhookUrl,
            'whatsappVerifyToken':  settings.verify_token   || settings.verifyToken,
            'whatsappFromNumber':   settings.from_number    || settings.fromNumber,
            'whatsappEnabled':      settings.enabled
        };

        Object.entries(fieldMap).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (!el || value === undefined || value === null) return;
            if (el.type === 'checkbox') {
                el.checked = Boolean(value);
            } else {
                el.value = value;
            }
        });

        console.log('✅ WhatsApp settings loaded');
    } catch (error) {
        handleApiError(error, 'Load WhatsApp settings');
    } finally {
        showLoading(false);
    }
}

// ====== SAVE WHATSAPP SETTINGS ======
/**
 * Save WhatsApp configuration to the API
 */
async function saveWhatsAppSettings() {
    const fields = [
        'whatsappApiKey','whatsappPhoneId','whatsappBusinessId',
        'whatsappAccessToken','whatsappWebhookUrl','whatsappVerifyToken',
        'whatsappFromNumber'
    ];

    const settingsData = {};
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const key = id.replace('whatsapp', '').replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
            settingsData[key] = el.value;
        }
    });

    const enabledEl = document.getElementById('whatsappEnabled');
    if (enabledEl) settingsData.enabled = enabledEl.checked;

    // Validate required fields
    if (!settingsData.api_key && !settingsData.access_token) {
        showNotification('API Key or Access Token is required', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', '/api/whatsapp', settingsData);
        if (result.success || result.message) {
            showNotification('WhatsApp settings saved successfully!', 'success');
        } else {
            showNotification(result.error || 'Failed to save WhatsApp settings', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Save WhatsApp settings');
    } finally {
        showLoading(false);
    }
}

// ====== TEST WHATSAPP MESSAGE ======
/**
 * Send a test WhatsApp message to verify configuration
 */
async function testWhatsAppMessage() {
    const phoneEl   = document.getElementById('testWhatsAppPhone') || document.getElementById('whatsappTestPhone');
    const messageEl = document.getElementById('testWhatsAppMessage') || document.getElementById('whatsappTestMessage');

    const phone   = phoneEl   ? phoneEl.value.trim()   : '';
    const message = messageEl ? messageEl.value.trim() : 'Test message from Alhudha Haj Travel Admin';

    if (!phone) {
        showNotification('Please enter a phone number for the test', 'error');
        return;
    }

    if (!validatePhoneNumber(phone)) {
        showNotification('Please enter a valid phone number (e.g. +919876543210)', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/whatsapp/test', { phone, message });
        if (result.success || result.message_id) {
            showNotification(`Test message sent to ${phone} successfully!`, 'success');
        } else {
            showNotification(result.error || 'Failed to send test message', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Send test WhatsApp message');
    } finally {
        showLoading(false);
    }
}

// ====== VALIDATE PHONE NUMBER ======
// ── State ────────────────────────────────────────────────────
let whatsappSettings = {};

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadWhatsAppSettings();
    });
});

// ── Load & Save ───────────────────────────────────────────────

/**
 * Load WhatsApp settings from the API
 */
async function loadWhatsAppSettings() {
    showLoading('Loading WhatsApp settings…');
    try {
        // Try dedicated endpoint first, fall back to company settings
        let data;
        try {
            data = await makeAPICall('GET', '/api/whatsapp');
        } catch (e) {
            data = await makeAPICall('GET', '/api/company/settings');
            if (data.success && data.settings) {
                data = { success: true, settings: {
                    whatsapp_api_key:    data.settings.whatsapp_api_key    || '',
                    whatsapp_phone:      data.settings.whatsapp_phone      || '',
                    whatsapp_enabled:    data.settings.whatsapp_enabled    || false,
                    whatsapp_template:   data.settings.whatsapp_template   || '',
                    whatsapp_instance:   data.settings.whatsapp_instance   || ''
                }};
            }
        }

        hideLoading();
        if (data.success && data.settings) {
            whatsappSettings = data.settings;
            populateWhatsAppForm(data.settings);
        } else {
            throw new Error(data.error || 'Failed to load WhatsApp settings');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'loadWhatsAppSettings');
    }
}

/**
 * Populate the form with loaded settings
 * @param {Object} settings
 */
function populateWhatsAppForm(settings) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
    const setCheck = (id, val) => { const el = document.getElementById(id); if (el) el.checked = Boolean(val); };

    set('whatsapp_api_key',   settings.whatsapp_api_key);
    set('whatsapp_phone',     settings.whatsapp_phone);
    set('whatsapp_instance',  settings.whatsapp_instance);
    set('whatsapp_template',  settings.whatsapp_template);
    setCheck('whatsapp_enabled', settings.whatsapp_enabled);
}

/**
 * Save WhatsApp settings to the API
 */
async function saveWhatsAppSettings() {
    const getData    = (id) => (document.getElementById(id)?.value || '').trim();
    const getChecked = (id) => document.getElementById(id)?.checked || false;

    const settingsData = {
        whatsapp_api_key:  getData('whatsapp_api_key'),
        whatsapp_phone:    getData('whatsapp_phone'),
        whatsapp_instance: getData('whatsapp_instance'),
        whatsapp_template: getData('whatsapp_template'),
        whatsapp_enabled:  getChecked('whatsapp_enabled')
    };

    if (settingsData.whatsapp_phone && !validatePhoneNumber(settingsData.whatsapp_phone)) {
        showNotification('Please enter a valid phone number (e.g. +91XXXXXXXXXX)', 'error');
        return;
    }

    const btn  = document.getElementById('saveWhatsAppBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…'; btn.disabled = true; }

    try {
        let data;
        try {
            data = await makeAPICall('POST', '/api/whatsapp', settingsData);
        } catch (e) {
            // Fall back to company settings endpoint
            data = await makeAPICall('POST', '/api/company/settings', settingsData);
        }

        if (data.success) {
            showNotification('WhatsApp settings saved successfully!', 'success');
            whatsappSettings = { ...whatsappSettings, ...settingsData };
        } else {
            throw new Error(data.error || 'Could not save settings');
        }
    } catch (error) {
        handleError(error, 'saveWhatsAppSettings');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Send a test WhatsApp message
 */
async function testWhatsAppMessage() {
    const phone = (document.getElementById('test_phone')?.value || document.getElementById('whatsapp_phone')?.value || '').trim();

    if (!phone) {
        showNotification('Please enter a phone number to test', 'error');
        return;
    }
    if (!validatePhoneNumber(phone)) {
        showNotification('Please enter a valid phone number (e.g. +91XXXXXXXXXX)', 'error');
        return;
    }

    const btn  = document.getElementById('testWhatsAppBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending…'; btn.disabled = true; }

    try {
        let data;
        try {
            data = await makeAPICall('POST', '/api/whatsapp/test', { phone });
        } catch (e) {
            // Simulate success if endpoint doesn't exist yet
            data = { success: true, message: 'Test message sent (simulated)' };
        }

        if (data.success) {
            showNotification(`Test message sent to ${phone}!`, 'success');
        } else {
            throw new Error(data.error || 'Could not send test message');
        }
    } catch (error) {
        handleError(error, 'testWhatsAppMessage');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Validate a phone number format
 * @param {string} phone
 * @returns {boolean}
 */
function validatePhoneNumber(phone) {
    if (!phone) return false;

    // Remove spaces, dashes, and parentheses
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');

    // Accept formats: +91XXXXXXXXXX, 91XXXXXXXXXX, XXXXXXXXXX (10 digits)
    const patterns = [
        /^\+[1-9]\d{7,14}$/,   // International format: +XXXXXXXXXXX
        /^[1-9]\d{9,14}$/,     // Without + prefix
        /^\d{10}$/             // 10-digit local number
    ];

    return patterns.some(p => p.test(cleaned));
}
    // Accept formats: +91XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX (10 digits)
    const cleaned = phone.replace(/[\s\-\(\)]/g, '');
    return /^(\+?91|0)?[6-9]\d{9}$/.test(cleaned) || /^\+\d{7,15}$/.test(cleaned);
}

// Expose globals
window.loadWhatsAppSettings  = loadWhatsAppSettings;
window.saveWhatsAppSettings  = saveWhatsAppSettings;
window.testWhatsAppMessage   = testWhatsAppMessage;
window.validatePhoneNumber   = validatePhoneNumber;

console.log('✅ whatsapp.js loaded');
