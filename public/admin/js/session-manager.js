// ====== 🔥 ULTIMATE SESSION MANAGER ======
// File: /public/admin/js/session-manager.js
// Version: 2.0.1 - Fixed session timeout

startTimers: function() {
    // Clear any existing timers first
    this.clearTimers();
    
    console.log('⏱️ Session timers started', {
        timeout: this.SESSION_TIMEOUT / 60000 + ' minutes',
        warning: this.WARNING_BEFORE / 60000 + ' minutes'
    });
    
    this.warningTimer = setTimeout(() => {
        this.showSessionWarning();
    }, this.SESSION_TIMEOUT - this.WARNING_BEFORE);
    
    this.logoutTimer = setTimeout(() => {
        this.forceLogout();
    }, this.SESSION_TIMEOUT);
},
    
    warningTimer: null,
    logoutTimer: null,
    notificationTimeout: null,
    timerStarted: false,  // Flag to prevent multiple timer starts

    // Check session with retry logic
    checkSession: async function(redirect = true) {
        console.log('🔍 Checking session...');
        const maxRetries = 2;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                
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
                
                console.log(`📡 Session response status: ${response.status}`);
                
                if (response.status === 401) {
                    console.log('⚠️ Session expired or not authenticated');
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
                console.log('🔐 Session data:', data);
                
                if (!data.authenticated) {
                    console.log('⚠️ Not authenticated in response');
                    if (i === maxRetries-1) {
                        if (redirect) this.redirectToLogin();
                        return false;
                    }
                    continue;
                }
                
                // Store session data
                this.updateSessionData(data);
                this.resetTimers();
                
                return true;
                
            } catch (error) {
                console.error(`❌ Session check error (attempt ${i+1}):`, error);
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
        
        console.log('✅ Session data stored:', {
            name: user.name,
            role: user.role,
            username: user.username
        });
        
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
        
        // Don't redirect if already on login page
        const currentPage = window.location.pathname;
        if (currentPage.includes('login') || currentPage.includes('admin.login')) {
            console.log('📍 Already on login page, skipping redirect');
            return;
        }
        
        // Store current page for redirect after login
        sessionStorage.setItem('redirectAfterLogin', currentPage);
        
        // Clear session storage
        sessionStorage.clear();
        
        // Redirect to login
        window.location.href = '/admin.login.html';
    },

    // Logout function
    logout: async function() {
        console.log('🚪 Logging out...');
        
        try {
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
            console.error('Logout error:', error);
        } finally {
            sessionStorage.clear();
            localStorage.removeItem('rememberedUser');
            window.location.href = '/admin.login.html';
        }
    },

    // Initialize page with session check
    initPage: async function(loadFunction) {
        console.log('🚀 Initializing page with session check...');
        console.log('📍 Current path:', window.location.pathname);
        
        // Don't check session on login page
        if (window.location.pathname.includes('login') || 
            window.location.pathname.includes('admin.login')) {
            console.log('📍 On login page, skipping session check');
            return;
        }
        
        try {
            const isValid = await this.checkSession(true);
            
            if (isValid) {
                console.log('✅ Session valid, starting timers');
                this.startTimers();
                this.setupActivityMonitoring();
                
                if (typeof loadFunction === 'function') {
                    try {
                        await loadFunction();
                        console.log('✅ Page loaded successfully');
                    } catch (error) {
                        console.error('❌ Load function error:', error);
                    }
                }
            } else {
                console.log('❌ Session invalid, redirecting...');
            }
        } catch (error) {
            console.error('❌ Session initialization error:', error);
        }
    },

startTimers: function() {
    // Clear any existing timers first
    this.clearTimers();
    
    console.log('⏱️ Session timers started', {
        timeout: this.SESSION_TIMEOUT / 60000 + ' minutes',
        warning: this.WARNING_BEFORE / 60000 + ' minutes'
    });
    
    this.warningTimer = setTimeout(() => {
        this.showSessionWarning();
    }, this.SESSION_TIMEOUT - this.WARNING_BEFORE);
    
    this.logoutTimer = setTimeout(() => {
        this.forceLogout();
    }, this.SESSION_TIMEOUT);
},
    
    this.warningTimer = setTimeout(() => {
        this.showSessionWarning();
    }, this.SESSION_TIMEOUT - this.WARNING_BEFORE);
    
    this.logoutTimer = setTimeout(() => {
        this.forceLogout();
    }, this.SESSION_TIMEOUT);
},
        
        this.warningTimer = setTimeout(() => {
            this.showSessionWarning();
        }, this.SESSION_TIMEOUT - this.WARNING_BEFORE);
        
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
        
        setTimeout(() => {
            if (warningEl.style.display === 'block') {
                warningEl.style.opacity = '0.5';
            }
        }, 90000);
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
        const events = ['click', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        const resetHandler = () => {
            this.resetTimers();
        };
        
        events.forEach(event => {
            document.removeEventListener(event, resetHandler);
            document.addEventListener(event, resetHandler, { passive: true });
        });
        
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    },

    // Handle page visibility change
    handleVisibilityChange: function() {
        if (!document.hidden) {
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
        
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
        }
        
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
    }
};

// Make SessionManager globally available
window.SessionManager = SessionManager;

// Auto-initialize for admin pages
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, checking if page needs auth');
    
    // Check if page needs authentication
    const needsAuth = window.location.pathname.includes('/admin/') && 
                     !window.location.pathname.includes('login');
    
    if (needsAuth) {
        console.log('🛡️ Page requires authentication');
        SessionManager.initPage();
    }

    checkAuth: function() {
        const isLoggedIn = sessionStorage.getItem('adminLoggedIn');
        if (!isLoggedIn) {
            window.location.href = '/admin.login.html';
            return false;
        }
        return true;
    },

    closeAllModals: function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.style.display = 'none');
        const overlay = document.getElementById('modalOverlay');
        if (overlay) overlay.style.display = 'none';
    },

    previousPage: function(currentPage, callback) {
        if (currentPage > 1) {
            callback(currentPage - 1);
        }
    },

    nextPage: function(currentPage, totalPages, callback) {
        if (currentPage < totalPages) {
            callback(currentPage + 1);
        }
    },

    resetFilters: function(searchId, roleId, statusId, displayCallback) {
        if (searchId) document.getElementById(searchId).value = '';
        if (roleId) document.getElementById(roleId).value = 'all';
        if (statusId) document.getElementById(statusId).value = 'all';
        if (displayCallback) displayCallback();
    },

    checkAdminSession: async function() {
        try {
            const response = await fetch('/api/check-session', {
                credentials: 'include',
                headers: { 'Cache-Control': 'no-cache' }
            });
            const data = await response.json();
            return data.authenticated || false;
        } catch (error) {
            console.error('Session check failed:', error);
            return false;
        }
    },

    showError: function(message) {
        this.showNotification(message, 'error');
    },

    showSuccess: function(message) {
        this.showNotification(message, 'success');
    },

    validateForm: function(fields) {
        for (let field of fields) {
            const value = document.getElementById(field.id)?.value;
            if (!value || value.trim() === '') {
                this.showError(field.name + ' is required');
                return false;
            }
        }
        return true;
    },

    formatDate: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('en-IN');
    },

    formatCurrency: function(amount) {
        return '₹' + Number(amount).toLocaleString('en-IN');
    },

    getUrlParameter: function(name) {
        const url = window.location.search;
        const regex = new RegExp('[?&]' + name + '=([^&#]*)');
        const results = regex.exec(url);
        return results ? decodeURIComponent(results[1].replace(/\+/g, ' ')) : null;
    }

    adjustColor: function(color, percent) {
        // Simple color adjustment function
        return color;
    },

    renderFeatures: function(features) {
        if (!features || !features.length) return '';
        return features.map(f => `<li><i class="fas fa-check"></i> ${f}</li>`).join('');
    },

    renderPackages: function(packages) {
        if (!packages || !packages.length) return '';
        return packages.map(p => `
            <div class="package-card">
                <h3>${p.name}</h3>
                <div class="price">${p.price}</div>
            </div>
        `).join('');
    },

    allowNumbersOnly: function(e) {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
    },

    loadBatches: async function() {
        try {
            const response = await fetch('/api/batches', {
                credentials: 'include'
            });
            const data = await response.json();
            return data.batches || [];
        } catch (error) {
            console.error('Error loading batches:', error);
            return [];
        }
    },

    useDemoBatches: function() {
        return [
            { id: 1, name: 'Demo Batch 1' },
            { id: 2, name: 'Demo Batch 2' }
        ];
    },

    updatePaginationInfo: function(currentPage, totalItems, itemsPerPage) {
        const start = (currentPage - 1) * itemsPerPage + 1;
        const end = Math.min(currentPage * itemsPerPage, totalItems);
        return { start, end, total: totalItems };
    },

    updateBatchDropdowns: function(batches) {
        const selects = document.querySelectorAll('.batch-select');
        selects.forEach(select => {
            select.innerHTML = '<option value="">Select Batch</option>';
            batches.forEach(batch => {
                select.innerHTML += `<option value="${batch.id}">${batch.name}</option>`;
            });
        });
    },

    clearSearch: function(searchId) {
        const search = document.getElementById(searchId);
        if (search) search.value = '';
    },

    resetSessionTimer: function() {
        if (this.resetTimers) this.resetTimers();
    },

    showSessionExpiredWarning: function(message) {
        alert(message || 'Session expired');
        window.location.href = '/admin.login.html';
    },

    authenticatedFetch: async function(url, options = {}) {
        options.credentials = 'include';
        try {
            const response = await fetch(url, options);
            if (response.status === 401) {
                window.location.href = '/admin.login.html';
                return null;
            }
            return response;
        } catch (error) {
            console.error('Fetch error:', error);
            return null;
        }
    },

    useTemplate: function(templateId, data) {
        const template = document.getElementById(templateId);
        if (!template) return '';
        let html = template.innerHTML;
        for (let key in data) {
            html = html.replace(new RegExp(`{{${key}}}`, 'g'), data[key]);
        }
        return html;
    },

    toggleSelectAll: function(checkboxId, itemClass) {
        const selectAll = document.getElementById(checkboxId);
        const checkboxes = document.querySelectorAll(itemClass);
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
    },

    loadAddressTemplate: function() {
        const saved = localStorage.getItem('companyAddress');
        return saved ? JSON.parse(saved) : null;
    },

    saveAddressTemplate: function(address) {
        localStorage.setItem('companyAddress', JSON.stringify(address));
    },

    closeModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
        const overlay = document.getElementById('modalOverlay');
        if (overlay) overlay.style.display = 'none';
    },

    applyFilters: function(filterData) {
        console.log('Applying filters:', filterData);
    },

    loadTravelers: async function() {
        try {
            const response = await fetch('/api/travelers', {
                credentials: 'include'
            });
            const data = await response.json();
            return data.travelers || [];
        } catch (error) {
            console.error('Error loading travelers:', error);
            return [];
        }
    },

    showSaveReportModal: function() {
        const modal = document.getElementById('saveReportModal');
        if (modal) modal.style.display = 'block';
    },

    closeSaveReportModal: function() {
        const modal = document.getElementById('saveReportModal');
        if (modal) modal.style.display = 'none';
    },

    saveReportConfig: function(config) {
        localStorage.setItem('reportConfig', JSON.stringify(config));
    },

    refreshSavedReports: function() {
        const saved = localStorage.getItem('savedReports');
        return saved ? JSON.parse(saved) : [];
    },

    loadSavedReport: function(reportId) {
        const reports = JSON.parse(localStorage.getItem('savedReports') || '[]');
        return reports.find(r => r.id === reportId);
    },

    deleteSavedReport: function(reportId) {
        let reports = JSON.parse(localStorage.getItem('savedReports') || '[]');
        reports = reports.filter(r => r.id !== reportId);
        localStorage.setItem('savedReports', JSON.stringify(reports));
    },

    emailReport: function(reportData) {
        console.log('Emailing report:', reportData);
    },

    changeChartType: function(type) {
        console.log('Changing chart type to:', type);
    },

    showReportLoading: function() {
        const loader = document.getElementById('reportLoader');
        if (loader) loader.style.display = 'block';
    },

    hideReportLoading: function() {
        const loader = document.getElementById('reportLoader');
        if (loader) loader.style.display = 'none';
    }
});
