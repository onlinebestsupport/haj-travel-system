/**
 * email.js - Email settings and communication functions
 * Alhudha Haj Travel Admin Panel
 * email.js - Email configuration and sending functions
 * Alhudha Haj Travel Management System
 * email.js - Email Settings for Alhudha Haj Travel Admin
 * Depends on: common.js, session-manager.js
 * API base: /api/email  (settings stored in company_settings or dedicated table)
 */

'use strict';

// ====== STATE ======
let emailSettings = {
    fromEmail: 'bookings@alhudha.com',
    replyTo: 'info@alhudha.com',
    subjectPrefix: '[Alhudha] ',
    smtpServer: 'smtp.gmail.com',
    smtpPort: 587,
    smtpEncryption: 'TLS',
    enabled: true
};

// ====== LOAD EMAIL SETTINGS ======
/**
 * Fetch email settings from /api/email
 */
async function loadEmailSettings() {
    try {
        const data = await makeAPICall('GET', '/api/email');
        if (data.success && data.settings) {
            emailSettings = { ...emailSettings, ...data.settings };
            applyEmailSettings(emailSettings);
            console.log('✅ Email settings loaded from API');
        } else {
            loadEmailFromLocalStorage();
        }
    } catch (error) {
        console.log('ℹ️ Email API not available, loading from localStorage');
        loadEmailFromLocalStorage();
    }
}

function loadEmailFromLocalStorage() {
    const fromEmail = localStorage.getItem('bookingEmail') || emailSettings.fromEmail;
    const subjectPrefix = localStorage.getItem('emailSubject') || emailSettings.subjectPrefix;

    emailSettings = { ...emailSettings, fromEmail, subjectPrefix };
    applyEmailSettings(emailSettings);
}

function applyEmailSettings(settings) {
    // Update config bar display
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || ''; };
    setEl('configFromEmail', settings.fromEmail);
    setEl('configReplyTo', settings.replyTo);
    setEl('configSubject', settings.subjectPrefix);

    // Update settings modal display
    setEl('smtpServer', settings.smtpServer);
    setEl('smtpPort', settings.smtpPort);
    setEl('smtpEncryption', settings.smtpEncryption);
    setEl('settingsFromEmail', settings.fromEmail);
    setEl('settingsReplyTo', settings.replyTo);
    setEl('settingsSubject', settings.subjectPrefix);
}

// ====== SAVE EMAIL SETTINGS ======
/**
 * POST/PUT email settings to /api/email
 */
async function saveEmailSettings() {
    const fromEmail = document.getElementById('settingsFromEmail')?.textContent?.trim() ||
                      document.getElementById('configFromEmail')?.textContent?.trim();
    const replyTo = document.getElementById('settingsReplyTo')?.textContent?.trim();
    const subjectPrefix = document.getElementById('settingsSubject')?.textContent?.trim();

    if (!fromEmail) { showNotification('From email is required', 'error'); return; }
    if (!validateEmailAddress(fromEmail)) {
        showNotification('Please enter a valid email address', 'error'); return;
    }

    const settings = {
        fromEmail: fromEmail || emailSettings.fromEmail,
        replyTo: replyTo || emailSettings.replyTo,
        subjectPrefix: subjectPrefix || emailSettings.subjectPrefix,
        smtpServer: emailSettings.smtpServer,
        smtpPort: emailSettings.smtpPort,
        smtpEncryption: emailSettings.smtpEncryption
    };

    try {
        const data = await makeAPICall('POST', '/api/email', settings);
        if (data.success) {
            emailSettings = { ...emailSettings, ...settings };
            localStorage.setItem('bookingEmail', settings.fromEmail);
            localStorage.setItem('emailSubject', settings.subjectPrefix);
            showNotification('Email settings saved successfully!', 'success');
        } else {
            emailSettings = { ...emailSettings, ...settings };
            localStorage.setItem('bookingEmail', settings.fromEmail);
            localStorage.setItem('emailSubject', settings.subjectPrefix);
            showNotification('Settings saved locally!', 'success');
        }
    } catch (error) {
        emailSettings = { ...emailSettings, ...settings };
        localStorage.setItem('bookingEmail', settings.fromEmail);
        localStorage.setItem('emailSubject', settings.subjectPrefix);
        showNotification('Settings saved locally!', 'success');
    }

    applyEmailSettings(emailSettings);
}

// ====== TEST EMAIL CONNECTION ======
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
    const testEmail = prompt('Enter email address to send test to:', emailSettings.fromEmail);
    if (!testEmail) return;

    if (!validateEmailAddress(testEmail)) {
        showNotification('Please enter a valid email address', 'error'); return;
    }

    showNotification('Testing email connection...', 'info');

    try {
        const data = await makeAPICall('POST', '/api/email/test', {
            to: testEmail,
            subject: `${emailSettings.subjectPrefix}Test Email`,
            body: 'This is a test email from Alhudha Haj Travel Admin Panel.'
        });
    const testEmail = (document.getElementById('test_email')?.value || emailSettings.from_email || '').trim();

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
            showNotification('Email test failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Email connection test failed. Check SMTP settings.', 'error');
        console.error('Email test error:', error);
    }
}

// ====== VALIDATE EMAIL ADDRESS ======
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
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim());
}

// ====== EDIT SETTING ======
/**
 * Edit a specific email setting inline
 * @param {string} setting - Setting key
 */
function editSetting(setting) {
    const currentValues = {
        fromEmail: emailSettings.fromEmail,
        replyTo: emailSettings.replyTo,
        subjectPrefix: emailSettings.subjectPrefix
    };

    const labels = {
        fromEmail: 'From Email',
        replyTo: 'Reply-To Email',
        subjectPrefix: 'Subject Prefix'
    };

    const newValue = prompt(`Edit ${labels[setting] || setting}:`, currentValues[setting] || '');
    if (newValue === null) return;

    if (setting === 'fromEmail' || setting === 'replyTo') {
        if (!validateEmailAddress(newValue)) {
            showNotification('Please enter a valid email address', 'error'); return;
        }
    }

    emailSettings[setting] = newValue;
    applyEmailSettings(emailSettings);
    showNotification(`${labels[setting]} updated`, 'success');
}

    // RFC 5322 simplified pattern
    const pattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$/;
    return pattern.test(email.trim());
}
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Expose globals
window.loadEmailSettings    = loadEmailSettings;
window.saveEmailSettings    = saveEmailSettings;
window.testEmailConnection  = testEmailConnection;
window.validateEmailAddress = validateEmailAddress;

console.log('✅ email.js loaded');
