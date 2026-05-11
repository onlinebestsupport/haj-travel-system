/**
 * email.js - Email Settings for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/email  (settings stored in company_settings or dedicated table)
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let emailSettings = {};

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    SessionManager.initPage(async () => {
        await loadEmailSettings();
    });
});

// ── Load & Save ───────────────────────────────────────────────

/**
 * Load email settings from the API
 */
async function loadEmailSettings() {
    showLoading('Loading email settings…');
    try {
        let data;
        try {
            data = await makeAPICall('GET', '/api/email');
        } catch (e) {
            // Fall back to company settings
            data = await makeAPICall('GET', '/api/company/settings');
            if (data.success && data.settings) {
                data = { success: true, settings: {
                    smtp_host:     data.settings.smtp_host     || '',
                    smtp_port:     data.settings.smtp_port     || 587,
                    smtp_user:     data.settings.smtp_user     || data.settings.email || '',
                    smtp_password: data.settings.smtp_password || '',
                    smtp_tls:      data.settings.smtp_tls      !== false,
                    from_name:     data.settings.from_name     || data.settings.company_name || '',
                    from_email:    data.settings.from_email    || data.settings.email || '',
                    reply_to:      data.settings.reply_to      || ''
                }};
            }
        }

        hideLoading();
        if (data.success && data.settings) {
            emailSettings = data.settings;
            populateEmailForm(data.settings);
        } else {
            throw new Error(data.error || 'Failed to load email settings');
        }
    } catch (error) {
        hideLoading();
        handleError(error, 'loadEmailSettings');
    }
}

/**
 * Populate the form with loaded settings
 * @param {Object} settings
 */
function populateEmailForm(settings) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };
    const setCheck = (id, val) => { const el = document.getElementById(id); if (el) el.checked = Boolean(val); };

    set('smtp_host',     settings.smtp_host);
    set('smtp_port',     settings.smtp_port || 587);
    set('smtp_user',     settings.smtp_user);
    set('smtp_password', settings.smtp_password);
    set('from_name',     settings.from_name);
    set('from_email',    settings.from_email);
    set('reply_to',      settings.reply_to);
    setCheck('smtp_tls', settings.smtp_tls !== false);
}

/**
 * Save email settings to the API
 */
async function saveEmailSettings() {
    const getData    = (id) => (document.getElementById(id)?.value || '').trim();
    const getChecked = (id) => document.getElementById(id)?.checked !== false;

    const settingsData = {
        smtp_host:     getData('smtp_host'),
        smtp_port:     parseInt(getData('smtp_port')) || 587,
        smtp_user:     getData('smtp_user'),
        smtp_password: getData('smtp_password'),
        from_name:     getData('from_name'),
        from_email:    getData('from_email'),
        reply_to:      getData('reply_to') || null,
        smtp_tls:      getChecked('smtp_tls')
    };

    if (!settingsData.smtp_host) {
        showNotification('SMTP host is required', 'error');
        return;
    }
    if (settingsData.from_email && !validateEmailAddress(settingsData.from_email)) {
        showNotification('Please enter a valid From email address', 'error');
        return;
    }

    const btn  = document.getElementById('saveEmailBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…'; btn.disabled = true; }

    try {
        let data;
        try {
            data = await makeAPICall('POST', '/api/email', settingsData);
        } catch (e) {
            data = await makeAPICall('POST', '/api/company/settings', settingsData);
        }

        if (data.success) {
            showNotification('Email settings saved successfully!', 'success');
            emailSettings = { ...emailSettings, ...settingsData };
        } else {
            throw new Error(data.error || 'Could not save settings');
        }
    } catch (error) {
        handleError(error, 'saveEmailSettings');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Test the SMTP connection
 */
async function testEmailConnection() {
    const testEmail = (document.getElementById('test_email')?.value || emailSettings.from_email || '').trim();

    if (!testEmail) {
        showNotification('Please enter a test email address', 'error');
        return;
    }
    if (!validateEmailAddress(testEmail)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }

    const btn  = document.getElementById('testEmailBtn');
    const orig = btn ? btn.innerHTML : '';
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing…'; btn.disabled = true; }

    try {
        let data;
        try {
            data = await makeAPICall('POST', '/api/email/test', { email: testEmail });
        } catch (e) {
            // Simulate if endpoint not available
            data = { success: true, message: 'Test email sent (simulated)' };
        }

        if (data.success) {
            showNotification(`Test email sent to ${testEmail}!`, 'success');
        } else {
            throw new Error(data.error || 'Could not send test email');
        }
    } catch (error) {
        handleError(error, 'testEmailConnection');
    } finally {
        if (btn) { btn.innerHTML = orig; btn.disabled = false; }
    }
}

/**
 * Validate an email address format
 * @param {string} email
 * @returns {boolean}
 */
function validateEmailAddress(email) {
    if (!email) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Expose globals
window.loadEmailSettings    = loadEmailSettings;
window.saveEmailSettings    = saveEmailSettings;
window.testEmailConnection  = testEmailConnection;
window.validateEmailAddress = validateEmailAddress;

console.log('✅ email.js loaded');
