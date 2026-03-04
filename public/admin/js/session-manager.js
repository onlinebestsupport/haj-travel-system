// ==================== 🔥 ULTIMATE SESSION MANAGER ====================
// Place this file in /public/admin/js/session-manager.js
// Version: 2.0.0
// Last Updated: 2026

const SessionManager = {
    // Session timeout in milliseconds (30 minutes)
    SESSION_TIMEOUT: 30 * 60 * 1000,
    WARNING_BEFORE: 2 * 60 * 1000, // Show warning 2 minutes before expiry
    
    // Session timers
    warningTimer: null,
    logoutTimer: null,
    
    // Check session with retry logic and timeout
    checkSession: async function(redirect = true) {
        const maxRetries = 2;
        const timeout = 5000; // 5 seconds timeout
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                // Create abort controller for timeout
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                
                const response = await fetch('/api/check-session', {
                    credentials: 'include',
                    signal: controller.signal,
                    headers: { 
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                clearTimeout(timeoutId);
                
                if (response.status === 401) {
                    console.log(`⚠️ Unauthorized (attempt ${i+1}/${maxRetries})`);
                    if (i === maxRetries-1) {
                        if (redirect) this.redirectToLogin();
                        return false;
                    }
                    continue;
                }
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('🔐 Session check successful:', data);
                
                if (!data.authenticated) {
                    console.log('⚠️ Session not authenticated');
                    if (i === maxRetries-1) {
                        if (redirect) this.redirectToLogin();
                        return false;
                    }
                    continue;
                }
                
                // Store session data
                this.updateSessionData(data);
                
                // Reset session timers
                this.resetTimers();
                
                return true;
                
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log(`⏱️ Session check timeout (attempt ${i+1}/${maxRetries})`);
                } else {
                    console.log(`⚠️ Session check error (attempt ${i+1}/${maxRetries}):`, error.message);
                }
                
                if (i === maxRetries-1) {
                    if (redirect) this.redirectToLogin();
                    return false;
                }
                await new Promise(r => setTimeout(r, 1000));
            }
        }
        return false;
    },

    // Update session data in sessionStorage and UI
    updateSessionData: function(data) {
        if (!data.user) return;
        
        const user = data.user;
        
        // Store in sessionStorage
        sessionStorage.setItem('adminLoggedIn', 'true');
        sessionStorage.setItem('adminName', user.name || 'Admin');
        sessionStorage.setItem('adminRole', user.role || 'admin');
        sessionStorage.setItem('adminUsername', user.username || '');
        sessionStorage.setItem('loginTime', Date.now().toString());
        
        // Update UI elements
        this.updateUI(user);
    },

    // Update UI with user info
    updateUI: function(user) {
        // Update role badge
        const roleBadge = document.getElementById('roleBadge');
        if (roleBadge) {
            roleBadge.textContent = user.role ? user.role.toUpperCase() : 'ADMIN';
        }
        
        // Update user name in header
        const userNameEl = document.getElementById('userDisplayName');
        if (userNameEl) {
            userNameEl.textContent = user.name || 'Admin User';
        }
        
        // Update user role display
        const userRoleEl = document.getElementById('userRoleDisplay');
        if (userRoleEl) {
            userRoleEl.textContent = this.formatRole(user.role || 'admin');
        }
        
        // Update greeting name
        const greetingEl = document.getElementById('greetingName');
        if (greetingEl) {
            greetingEl.textContent = user.name || 'Admin';
        }
        
        // Update avatar initials
        const avatarEl = document.getElementById('userAvatar');
        if (avatarEl && user.name) {
            const nameParts = user.name.split(' ');
            let initials = '';
            for (let i = 0; i < Math.min(2, nameParts.length); i++) {
                if (nameParts[i] && nameParts[i].length > 0) {
                    initials += nameParts[i][0].toUpperCase();
                }
            }
            avatarEl.textContent = initials || 'AD';
        }
    },

    // Format role string
    formatRole: function(role) {
        if (!role) return 'Administrator';
        return role.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    },

    // Redirect to login page
    redirectToLogin: function() {
        console.log('🚪 Redirecting to login...');
        
        // Store current page for redirect after login
        const currentPage = window.location.pathname;
        if (!currentPage.includes('login') && !currentPage.includes('admin.login')) {
            sessionStorage.setItem('redirectAfterLogin', currentPage);
        }
        
        // Clear session storage
        sessionStorage.clear();
        
        // Redirect to login
        window.location.href = '/admin.login.html';
    },

    // Logout function
    logout: async function() {
        console.log('🚪 Logging out...');
        
        try {
            // Call logout API with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            await fetch('/api/logout', { 
                method: 'POST', 
                credentials: 'include',
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            clearTimeout(timeoutId);
            
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('⏱️ Logout timeout');
            } else {
                console.error('Logout error:', error);
            }
        } finally {
            // Always clear session and redirect
            sessionStorage.clear();
            localStorage.removeItem('rememberedUser');
            window.location.href = '/admin.login.html';
        }
    },

    // Initialize page with session check
    initPage: async function(loadFunction) {
        console.log('🚀 Initializing page with session check...');
        
        try {
            // Check session
            const isValid = await this.checkSession(true);
            
            if (isValid) {
                // Start session timers
                this.startTimers();
                
                // Load page data if function provided
                if (typeof loadFunction === 'function') {
                    try {
                        await loadFunction();
                        console.log('✅ Page loaded successfully');
                    } catch (error) {
                        console.error('❌ Load function error:', error);
                        this.showNotification('Error loading page data', 'error');
                    }
                }
                
                // Setup activity monitoring
                this.setupActivityMonitoring();
            }
        } catch (error) {
            console.error('❌ Session initialization error:', error);
            this.redirectToLogin();
        }
    },

    // Start session timers
    startTimers: function() {
        this.clearTimers();
        
        // Warning timer (show warning 2 minutes before expiry)
        this.warningTimer = setTimeout(() => {
            this.showSessionWarning();
        }, this.SESSION_TIMEOUT - this.WARNING_BEFORE);
        
        // Logout timer (force logout at expiry)
        this.logoutTimer = setTimeout(() => {
            this.forceLogout();
        }, this.SESSION_TIMEOUT);
    },

    // Reset session timers on activity
    resetTimers: function() {
        this.clearTimers();
        this.startTimers();
        this.hideSessionWarning();
    },

    // Clear all timers
    clearTimers: function() {
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
            this.warningTimer = null;
        }
        if (this.logoutTimer) {
            clearTimeout(this.logoutTimer);
            this.logoutTimer = null;
        }
    },

    // Show session warning
    showSessionWarning: function() {
        const warningEl = document.getElementById('sessionWarning');
        if (!warningEl) return;
        
        const messageEl = document.getElementById('sessionWarningMessage');
        if (messageEl) {
            messageEl.textContent = 'Your session will expire in 2 minutes. Click to extend.';
        }
        
        warningEl.style.display = 'block';
        
        // Auto-hide after 1.5 minutes if no interaction
        setTimeout(() => {
            if (warningEl.style.display === 'block') {
                warningEl.style.opacity = '0.5';
            }
        }, 90000); // 1.5 minutes
    },

    // Hide session warning
    hideSessionWarning: function() {
        const warningEl = document.getElementById('sessionWarning');
        if (warningEl) {
            warningEl.style.display = 'none';
            warningEl.style.opacity = '1';
        }
    },

    // Force logout due to session expiry
    forceLogout: function() {
        console.log('⏰ Session expired');
        this.hideSessionWarning();
        this.showNotification('Your session has expired. Redirecting to login...', 'warning');
        
        setTimeout(() => {
            this.redirectToLogin();
        }, 3000);
    },

    // Extend session
    extendSession: async function() {
        console.log('🔄 Extending session...');
        
        try {
            const isValid = await this.checkSession(false);
            if (isValid) {
                this.resetTimers();
                this.showNotification('Session extended successfully', 'success');
            } else {
                this.forceLogout();
            }
        } catch (error) {
            console.error('Failed to extend session:', error);
            this.forceLogout();
        }
    },

    // Setup activity monitoring
    setupActivityMonitoring: function() {
        const events = ['click', 'mousemove', 'keypress', 'scroll', 'touchstart', 'touchmove'];
        
        const resetHandler = () => {
            this.resetTimers();
        };
        
        // Remove existing listeners and add new ones
        events.forEach(event => {
            document.removeEventListener(event, resetHandler);
            document.addEventListener(event, resetHandler, { passive: true });
        });
        
        // Handle visibility change
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    },

    // Handle page visibility change
    handleVisibilityChange: function() {
        if (!document.hidden) {
            // Page became visible, check session
            this.checkSession(false).then(isValid => {
                if (!isValid) {
                    this.redirectToLogin();
                }
            });
        }
    },

    // Show notification
    showNotification: function(message, type = 'success') {
        const notification = document.getElementById('notification');
        if (!notification) return;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'exclamation-circle' : 
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
        notification.style.display = 'block';
        
        // Clear existing timeout
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
        }
        
        // Auto hide after 3 seconds
        this.notificationTimeout = setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    },

    // Get current user from sessionStorage
    getCurrentUser: function() {
        return {
            name: sessionStorage.getItem('adminName') || 'Admin',
            role: sessionStorage.getItem('adminRole') || 'admin',
            username: sessionStorage.getItem('adminUsername') || ''
        };
    },

    // Check if user is authenticated (client-side)
    isAuthenticated: function() {
        return sessionStorage.getItem('adminLoggedIn') === 'true';
    },

    // Get session expiry time
    getSessionExpiry: function() {
        const loginTime = sessionStorage.getItem('loginTime');
        if (!loginTime) return null;
        
        const expiryTime = parseInt(loginTime) + this.SESSION_TIMEOUT;
        const remaining = expiryTime - Date.now();
        
        if (remaining <= 0) return 'Expired';
        
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        
        return `${minutes}m ${seconds}s`;
    }
};

// Make SessionManager globally available
window.SessionManager = SessionManager;

// Auto-initialize if page has session check
document.addEventListener('DOMContentLoaded', function() {
    // Check if page needs session management
    const needsAuth = document.querySelector('[data-requires-auth="true"]') || 
                     window.location.pathname.includes('/admin/');
    
    if (needsAuth && !window.location.pathname.includes('login')) {
        console.log('🛡️ Page requires authentication');
        SessionManager.initPage();
    }
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}
