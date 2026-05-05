/**
 * whatsapp.js - WhatsApp configuration and messaging functions
 * Alhudha Haj Travel Management System
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
