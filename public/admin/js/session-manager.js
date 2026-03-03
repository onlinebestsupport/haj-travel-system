// ==================== MASTER SESSION MANAGER ====================
// This file handles session for ALL admin pages

const SessionManager = {
    // Check if user is authenticated
    checkSession: async function(redirect = true) {
        try {
            const response = await fetch('/api/check-session', {
                credentials: 'include',
                headers: { 'Cache-Control': 'no-cache' }
            });
            
            if (response.status === 401) {
                console.log('🔒 Session expired (401)');
                if (redirect) this.redirectToLogin();
                return false;
            }
            
            const data = await response.json();
            console.log('🔐 Session:', data);
            
            if (!data.authenticated) {
                console.log('⚠️ Not authenticated');
                if (redirect) this.redirectToLogin();
                return false;
            }
            
            // Update role badge
            const roleBadge = document.getElementById('roleBadge');
            if (roleBadge && data.user) {
                roleBadge.textContent = data.user.role.toUpperCase();
            }
            
            // Store in sessionStorage
            sessionStorage.setItem('adminLoggedIn', 'true');
            sessionStorage.setItem('adminName', data.user?.name || 'Admin');
            sessionStorage.setItem('adminRole', data.user?.role || 'admin');
            
            return true;
        } catch (error) {
            console.error('❌ Session check failed:', error);
            
            // Try local storage as fallback
            const localLoggedIn = sessionStorage.getItem('adminLoggedIn');
            if (localLoggedIn === 'true') {
                console.log('⚠️ Using local session fallback');
                return true;
            }
            
            if (redirect) this.redirectToLogin();
            return false;
        }
    },

    redirectToLogin: function() {
        console.log('🚪 Redirecting to login...');
        sessionStorage.clear();
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

    initPage: async function(loadDataFunction) {
        console.log('🚀 Initializing page...');
        
        const isValid = await this.checkSession(true);
        if (isValid && typeof loadDataFunction === 'function') {
            await loadDataFunction();
        }
    }
};

// Make it global
window.SessionManager = SessionManager;