window.SessionManager = {
    SESSION_TIMEOUT: 30 * 60 * 1000,
    WARNING_BEFORE: 2 * 60 * 1000,
    checkSession() {
        // Call to check session status
        fetch('/api/admin/check-session').catch(() => {
            return fetch('/api/check-session');
        });
    },
    initPage(loadFn) {
        // Initialize page functionality
        loadFn();
    },
    logout() {
        // Perform logout
        fetch('/api/admin/logout', { method: 'POST' }).catch(() => {
            return fetch('/api/logout', { method: 'POST' });
        });
    },
    showNotification(message) {
        // Show user notification
        alert(message);
    },
    closeAllModals() {
        // Logic to close all modals
    },
    authenticatedFetch(url) {
        // Authenticated fetch logic
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Ensure no stray properties are defined here
    startTimers();  // Ensure valid usage of startTimers
});
