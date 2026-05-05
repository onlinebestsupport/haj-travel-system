/**
 * whatsapp.js - WhatsApp settings and communication functions
 * Alhudha Haj Travel Admin Panel
 */

'use strict';

// ====== STATE ======
let whatsappSettings = {
    number: '919876543210',
    message: "Hi, I'm interested in your Haj/Umrah packages. Can you please share more details?",
    enabled: true
};

// ====== LOAD WHATSAPP SETTINGS ======
/**
 * Fetch WhatsApp settings from /api/whatsapp
 */
async function loadWhatsAppSettings() {
    try {
        const data = await makeAPICall('GET', '/api/whatsapp');
        if (data.success && data.settings) {
            whatsappSettings = { ...whatsappSettings, ...data.settings };
            applyWhatsAppSettings(whatsappSettings);
            console.log('✅ WhatsApp settings loaded from API');
        } else {
            loadWhatsAppFromLocalStorage();
        }
    } catch (error) {
        console.log('ℹ️ WhatsApp API not available, loading from localStorage');
        loadWhatsAppFromLocalStorage();
    }
}

function loadWhatsAppFromLocalStorage() {
    const number = localStorage.getItem('whatsappNumber') || '919876543210';
    const message = localStorage.getItem('whatsappMessage') || whatsappSettings.message;
    const enabled = localStorage.getItem('whatsappEnabled') !== 'false';

    whatsappSettings = { number, message, enabled };
    applyWhatsAppSettings(whatsappSettings);
}

function applyWhatsAppSettings(settings) {
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
    const setCheck = (id, val) => { const el = document.getElementById(id); if (el) el.checked = val; };

    setEl('whatsappNumber', settings.number || '');
    setEl('whatsappMessage', settings.message || '');
    setCheck('whatsappEnabled', settings.enabled !== false);

    // Update display
    const displayEl = document.getElementById('whatsappNumberDisplay');
    if (displayEl) displayEl.textContent = formatWhatsAppNumber(settings.number);
}

// ====== SAVE WHATSAPP SETTINGS ======
/**
 * POST/PUT WhatsApp settings to /api/whatsapp
 */
async function saveWhatsAppSettings() {
    const number = document.getElementById('whatsappNumber')?.value?.trim();
    const message = document.getElementById('whatsappMessage')?.value?.trim();
    const enabled = document.getElementById('whatsappEnabled')?.checked !== false;

    if (!number) { showNotification('WhatsApp number is required', 'error'); return; }
    if (!validatePhoneNumber(number)) {
        showNotification('Please enter a valid phone number (10-13 digits)', 'error'); return;
    }

    const settings = { number, message, enabled };

    try {
        const data = await makeAPICall('POST', '/api/whatsapp', settings);
        if (data.success) {
            whatsappSettings = settings;
            localStorage.setItem('whatsappNumber', number);
            localStorage.setItem('whatsappMessage', message);
            localStorage.setItem('whatsappEnabled', String(enabled));
            showNotification('WhatsApp settings saved successfully!', 'success');
        } else {
            // Save to localStorage as fallback
            whatsappSettings = settings;
            localStorage.setItem('whatsappNumber', number);
            localStorage.setItem('whatsappMessage', message);
            localStorage.setItem('whatsappEnabled', String(enabled));
            showNotification('Settings saved locally!', 'success');
        }
    } catch (error) {
        // Save to localStorage
        whatsappSettings = settings;
        localStorage.setItem('whatsappNumber', number);
        localStorage.setItem('whatsappMessage', message);
        localStorage.setItem('whatsappEnabled', String(enabled));
        showNotification('Settings saved locally!', 'success');
    }

    // Update display
    const displayEl = document.getElementById('whatsappNumberDisplay');
    if (displayEl) displayEl.textContent = formatWhatsAppNumber(number);
}

// ====== TEST WHATSAPP MESSAGE ======
/**
 * Send a test WhatsApp message
 */
async function testWhatsAppMessage() {
    const number = document.getElementById('whatsappNumber')?.value?.trim() || whatsappSettings.number;
    const message = document.getElementById('whatsappMessage')?.value?.trim() || whatsappSettings.message;

    if (!number) { showNotification('Please enter a WhatsApp number first', 'error'); return; }
    if (!validatePhoneNumber(number)) {
        showNotification('Invalid phone number format', 'error'); return;
    }

    // Try API first
    try {
        const data = await makeAPICall('POST', '/api/whatsapp/test', { number, message });
        if (data.success) {
            showNotification('Test message sent successfully!', 'success');
            return;
        }
    } catch (error) {
        // Fallback to WhatsApp web link
    }

    // Open WhatsApp web as fallback
    const cleanNumber = number.replace(/\D/g, '');
    const encodedMessage = encodeURIComponent(message || 'Test message from Alhudha Haj Admin');
    const whatsappUrl = `https://wa.me/${cleanNumber}?text=${encodedMessage}`;
    window.open(whatsappUrl, '_blank');
    showNotification('Opening WhatsApp Web for test message', 'info');
}

// ====== VALIDATE PHONE NUMBER ======
/**
 * Validate a phone number format
 * @param {string} phone
 * @returns {boolean}
 */
function validatePhoneNumber(phone) {
    if (!phone) return false;
    const cleaned = String(phone).replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 13;
}

// ====== FORMAT WHATSAPP NUMBER ======
function formatWhatsAppNumber(number) {
    if (!number) return 'Not configured';
    const cleaned = String(number).replace(/\D/g, '');
    if (cleaned.length === 12 && cleaned.startsWith('91')) {
        return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 7)} ${cleaned.slice(7)}`;
    }
    if (cleaned.length === 10) {
        return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
    }
    return '+' + cleaned;
}

console.log('✅ whatsapp.js loaded');
