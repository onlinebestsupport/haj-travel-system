/*
  travelers.js - appended overrides and helpers for mailing address, file_reference, expected_return_date,
  and client-side passport expiry validation (6 months after expected return date).
  This file appends new function definitions that override earlier createTraveler/updateTraveler functions
  so the minimal existing code is preserved and new behavior is added.
*/

// Provide compatibility wrappers so HTML that calls handleCreateTraveler/handleUpdateTraveler keeps working
function handleCreateTraveler(event) {
    return createTraveler(event);
}

function handleUpdateTraveler(event) {
    return updateTraveler(event);
}

// Helper: copy passport address to mailing address when checkbox is checked
function toggleMailingAddress(prefix) {
    try {
        // support two checkbox id naming patterns used in different versions of the HTML
        const sameCb = document.getElementById(prefix + '_same_mailing') || document.getElementById(prefix + '_same_as_passport');
        const passportAddr = document.getElementById(prefix + '_passport_address');
        const mailingEl = document.getElementById(prefix + '_mailing_address');
        if (!sameCb || !mailingEl || !passportAddr) return;
        if (sameCb.checked) {
            mailingEl.value = passportAddr.value || '';
            mailingEl.readOnly = true;
        } else {
            mailingEl.readOnly = false;
        }
    } catch (e) {
        console.warn('toggleMailingAddress error', e);
    }
}

// Helper: parse YYYY-MM-DD to Date
function parseDateYMD(s) {
    if (!s) return null;
    const parts = s.split('-');
    if (parts.length !== 3) return null;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10) - 1;
    const d = parseInt(parts[2], 10);
    return new Date(Date.UTC(y, m, d));
}

// Helper: add months to date
function addMonths(date, months) {
    if (!date) return null;
    const d = new Date(date.getTime());
    const day = d.getUTCDate();
    d.setUTCMonth(d.getUTCMonth() + months);
    // handle month overflow
    if (d.getUTCDate() !== day) {
        d.setUTCDate(0); // last day of previous month
    }
    return d;
}

// Validate passport expiry: passport_expiry_date must be at least expected_return_date + 6 months
function validatePassportValidityClient(passportExpiryStr, expectedReturnStr) {
    const expiry = parseDateYMD(passportExpiryStr);
    const ret = parseDateYMD(expectedReturnStr);
    if (!ret) return { valid: false, message: 'Expected return date is required' };
    if (!expiry) return { valid: false, message: 'Passport expiry date is required' };
    const minValid = addMonths(ret, 6);
    if (expiry.getTime() < minValid.getTime()) {
        return { valid: false, message: `Passport expiry must be at least 6 months after expected return date (${minValid.toISOString().slice(0,10)})` };
    }
    return { valid: true, message: '' };
}

// Calculate days left until passport expiry
function daysUntil(dateStr) {
    const d = parseDateYMD(dateStr);
    if (!d) return null;
    const now = new Date();
    const diff = d.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

// Override createTraveler to include mailing_address, file_reference, expected_return_date and client-side validation
async function createTraveler(event) {
    if (event && event.preventDefault) event.preventDefault();
    const formEl = document.getElementById('travelerAddForm') || document.getElementById('addTravelerForm');
    if (!formEl) return;

    // gather base fields from existing form if present
    const get = (id) => document.getElementById(id) ? document.getElementById(id).value.trim() : '';

    const first_name = get('add_first_name');
    const last_name = get('add_last_name');
    const passport_no = get('add_passport_no');
    const mobile = get('add_mobile');
    const batch_id = get('add_batch_id');
    const passport_expiry_date = get('add_passport_expiry_date');
    const expected_return_date = get('add_expected_return_date');
    const file_reference = get('add_file_reference');

    if (!first_name || !last_name || !passport_no || !mobile || !batch_id) {
        showNotification('First name, last name, passport number, mobile and batch are required', 'error');
        return;
    }

    // Validate passport vs expected return date
    const valid = validatePassportValidityClient(passport_expiry_date, expected_return_date);
    if (!valid.valid) {
        showNotification(valid.message, 'error');
        return;
    }

    // Build FormData from form to support file uploads
    const fd = new FormData(formEl.querySelector('form') || formEl);
    // Ensure new fields are appended (in case form doesn't have them)
    if (document.getElementById('add_mailing_address')) fd.set('mailing_address', get('add_mailing_address'));
    if (document.getElementById('add_file_reference')) fd.set('file_reference', file_reference);
    if (document.getElementById('add_expected_return_date')) fd.set('expected_return_date', expected_return_date);

    const submitBtn = formEl.querySelector('button[type="submit"]');
    showLoading(submitBtn, 'Saving...');

    try {
        const resp = await fetch('/api/travelers', { method: 'POST', body: fd, credentials: 'include' });
        const data = await resp.json();
        if (data.success) {
            // show days left notification
            const days = daysUntil(passport_expiry_date);
            if (days !== null) {
                showNotification(`Traveler created. Passport expires in ${days} day(s).`, 'success');
            } else {
                showNotification('Traveler created successfully!', 'success');
            }
            if (typeof hideAddTravelerForm === 'function') hideAddTravelerForm();
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Could not create traveler'), 'error');
        }
    } catch (err) {
        handleAPIError(err, 'createTraveler');
    } finally {
        hideLoading(submitBtn);
    }
}

// Override updateTraveler to include new fields and validation
async function updateTraveler(event) {
    if (event && event.preventDefault) event.preventDefault();

    const idEl = document.getElementById('edit_traveler_id') || document.getElementById('editTravelerId');
    if (!idEl || !idEl.value) { showNotification('No traveler selected for update', 'error'); return; }
    const travelerId = idEl.value;
    const formEl = document.getElementById('editTravelerForm') || document.getElementById('editFormContainer');
    if (!formEl) { showNotification('Edit form not found', 'error'); return; }

    const get = (id) => document.getElementById(id) ? document.getElementById(id).value.trim() : '';
    const passport_expiry_date = get('edit_passport_expiry_date');
    const expected_return_date = get('edit_expected_return_date');

    // Validate if expected_return_date or passport_expiry_date present
    if (expected_return_date || passport_expiry_date) {
        const valid = validatePassportValidityClient(passport_expiry_date, expected_return_date);
        if (!valid.valid) { showNotification(valid.message, 'error'); return; }
    }

    const fd = new FormData(formEl.querySelector('form') || formEl);
    if (document.getElementById('edit_mailing_address')) fd.set('mailing_address', get('edit_mailing_address'));
    if (document.getElementById('edit_file_reference')) fd.set('file_reference', get('edit_file_reference'));
    if (document.getElementById('edit_expected_return_date')) fd.set('expected_return_date', get('edit_expected_return_date'));

    const submitBtn = formEl.querySelector('button[type="submit"]');
    showLoading(submitBtn, 'Updating...');

    try {
        const resp = await fetch(`/api/travelers/${travelerId}`, { method: 'PUT', body: fd, credentials: 'include' });
        const data = await resp.json();
        if (data.success) {
            const days = daysUntil(passport_expiry_date);
            if (days !== null) showNotification(`Traveler updated. Passport expires in ${days} day(s).`, 'success');
            else showNotification('Traveler updated successfully!', 'success');
            if (typeof hideEditTravelerForm === 'function') hideEditTravelerForm();
            await loadTravelers();
        } else {
            showNotification('Error: ' + (data.error || 'Update failed'), 'error');
        }
    } catch (err) {
        handleAPIError(err, 'updateTraveler');
    } finally {
        hideLoading(submitBtn);
    }
}

// Wire checkbox auto-copy behavior for add/edit forms
document.addEventListener('DOMContentLoaded', () => {
    // support both id variants: *_same_mailing and *_same_as_passport
    const addCb = document.getElementById('add_same_mailing') || document.getElementById('add_same_as_passport');
    if (addCb) addCb.addEventListener('change', () => toggleMailingAddress('add'));
    const editCb = document.getElementById('edit_same_mailing') || document.getElementById('edit_same_as_passport');
    if (editCb) editCb.addEventListener('change', () => toggleMailingAddress('edit'));
});
