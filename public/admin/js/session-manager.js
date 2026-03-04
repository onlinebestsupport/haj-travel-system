// ==================== 🔥 ULTIMATE SESSION MANAGER ====================
// Place this file in /public/admin/js/session-manager.js

const SessionManager = {
    // Check session with retry logic
    checkSession: async function(redirect = true) {
        const maxRetries = 2;
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch('/api/check-session', {
                    credentials: 'include',
                    headers: { 
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                });
                
                if (response.status === 401) {
                    if (i === maxRetries-1) {
                        if (redirect) this.redirectToLogin();
                        return false;
                    }
                    continue;
                }
                
                const data = await response.json();
                console.log('🔐 Session check:', data);
                
                if (!data.authenticated) {
                    if (i === maxRetries-1) {
                        if (redirect) this.redirectToLogin();
                        return false;
                    }
                    continue;
                }
                
                // Update role badge
                const roleBadge = document.getElementById('roleBadge');
                if (roleBadge && data.user) {
                    roleBadge.textContent = data.user.role.toUpperCase();
                }
                
                // Store in sessionStorage as backup
                sessionStorage.setItem('adminLoggedIn', 'true');
                sessionStorage.setItem('adminName', data.user?.name || 'Admin');
                sessionStorage.setItem('adminRole', data.user?.role || 'admin');
                
                return true;
            } catch (error) {
                console.log(`⚠️ Session check attempt ${i+1} failed:`, error);
                if (i === maxRetries-1) {
                    if (redirect) this.redirectToLogin();
                    return false;
                }
                await new Promise(r => setTimeout(r, 500));
            }
        }
        return false;
    },

    redirectToLogin: function() {
        console.log('🚪 Redirecting to login...');
        const currentPage = window.location.pathname;
        if (!currentPage.includes('login')) {
            sessionStorage.setItem('redirectAfterLogin', currentPage);
        }
        window.location.href = '/admin.login.html';
    },

    logout: async function() {
        try {
            await fetch('/api/logout', { 
                method: 'POST', 
                credentials: 'include' 
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            sessionStorage.clear();
            window.location.href = '/admin.login.html';
        }
    },

    initPage: async function(loadFunction) {
        console.log('🚀 Initializing page with session check...');
        
        const isValid = await this.checkSession(true);
        if (isValid && typeof loadFunction === 'function') {
            try {
                await loadFunction();
            } catch (error) {
                console.error('❌ Load function error:', error);
            }
        }
    }
};

window.SessionManager = SessionManager;
