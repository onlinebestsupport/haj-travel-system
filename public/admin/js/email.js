/**
 * email.js - Email settings and communication functions
 * Alhudha Haj Travel Admin Panel
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

console.log('✅ email.js loaded');
