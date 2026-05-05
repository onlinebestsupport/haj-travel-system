/**
 * email.js - Email configuration and sending functions
 * Alhudha Haj Travel Management System
 */

'use strict';

// ====== LOAD EMAIL SETTINGS ======
/**
 * Fetch email configuration from the API
 */
async function loadEmailSettings() {
    showLoading(true);
    try {
        const data = await makeApiCall('GET', '/api/email');
        const settings = data.settings || data || {};

        const fieldMap = {
            'smtpHost':       settings.smtp_host     || settings.smtpHost,
            'smtpPort':       settings.smtp_port     || settings.smtpPort,
            'smtpUser':       settings.smtp_user     || settings.smtpUser     || settings.username,
            'smtpPassword':   settings.smtp_password || settings.smtpPassword || settings.password,
            'smtpFromEmail':  settings.from_email    || settings.fromEmail    || settings.sender_email,
            'smtpFromName':   settings.from_name     || settings.fromName     || settings.sender_name,
            'smtpEncryption': settings.encryption    || settings.smtpEncryption || 'tls',
            'emailEnabled':   settings.enabled
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

        console.log('✅ Email settings loaded');
    } catch (error) {
        handleApiError(error, 'Load email settings');
    } finally {
        showLoading(false);
    }
}

// ====== SAVE EMAIL SETTINGS ======
/**
 * Save email configuration to the API
 */
async function saveEmailSettings() {
    const fields = [
        'smtpHost','smtpPort','smtpUser','smtpPassword',
        'smtpFromEmail','smtpFromName','smtpEncryption'
    ];

    const settingsData = {};
    fields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            // Convert camelCase to snake_case
            const key = id.replace(/([A-Z])/g, '_$1').toLowerCase();
            settingsData[key] = el.value;
        }
    });

    const enabledEl = document.getElementById('emailEnabled');
    if (enabledEl) settingsData.enabled = enabledEl.checked;

    // Validate required fields
    if (!settingsData.smtp_host) {
        showNotification('SMTP host is required', 'error');
        return;
    }
    if (!settingsData.smtp_from_email) {
        showNotification('From email address is required', 'error');
        return;
    }
    if (!validateEmailAddress(settingsData.smtp_from_email)) {
        showNotification('Please enter a valid from email address', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('PUT', '/api/email', settingsData);
        if (result.success || result.message) {
            showNotification('Email settings saved successfully!', 'success');
        } else {
            showNotification(result.error || 'Failed to save email settings', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Save email settings');
    } finally {
        showLoading(false);
    }
}

// ====== TEST EMAIL CONNECTION ======
/**
 * Test the SMTP connection and send a test email
 */
async function testEmailConnection() {
    const testEmailEl = document.getElementById('testEmailAddress') || document.getElementById('emailTestAddress');
    const testEmail   = testEmailEl ? testEmailEl.value.trim() : '';

    if (!testEmail) {
        showNotification('Please enter a test email address', 'error');
        return;
    }

    if (!validateEmailAddress(testEmail)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await makeApiCall('POST', '/api/email/test', { email: testEmail });
        if (result.success || result.message_id) {
            showNotification(`Test email sent to ${testEmail} successfully!`, 'success');
        } else {
            showNotification(result.error || 'Failed to send test email', 'error');
        }
    } catch (error) {
        handleApiError(error, 'Test email connection');
    } finally {
        showLoading(false);
    }
}

// ====== VALIDATE EMAIL ADDRESS ======
/**
 * Validate an email address format
 * @param {string} email
 * @returns {boolean}
 */
function validateEmailAddress(email) {
    if (!email) return false;
    // RFC 5322 simplified pattern
    const pattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/;
    return pattern.test(email.trim());
}
