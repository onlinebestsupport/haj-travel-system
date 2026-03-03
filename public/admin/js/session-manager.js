// ==================== FIXED SESSION MANAGER - NO AUTO REDIRECT ====================

const SessionManager = {
    checkSession: async function() {
        try {
            const response = await fetch('/api/check-session', {
                credentials: 'include'
            });
            const data = await response.json();
            console.log('🔐 Session:', data);
            
            if (data.authenticated && data.user) {
                const roleBadge = document.getElementById('roleBadge');
                if (roleBadge) roleBadge.textContent = data.user.role.toUpperCase();
            }
            return data;
        } catch (error) {
            console.error('Session check failed:', error);
            return { authenticated: false };
        }
    },

    initPage: async function(loadFunction) {
        console.log('Loading page...');
        const session = await this.checkSession();
        
        if (session.authenticated && loadFunction) {
            await loadFunction();
        } else {
            this.showLoginMessage();
            if (loadFunction) setTimeout(loadFunction, 1000);
        }
    },

    showLoginMessage: function() {
        const msg = document.createElement('div');
        msg.style.cssText = `
            position: fixed; top: 20px; right: 20px; 
            background: #f39c12; color: white; padding: 15px 25px;
            border-radius: 5px; z-index: 9999; cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        msg.innerHTML = '⚠️ Not logged in. <a href="/admin.login.html" style="color:white;">Login</a>';
        msg.onclick = () => window.location.href = '/admin.login.html';
        document.body.appendChild(msg);
        setTimeout(() => msg.remove(), 8000);
    },

    logout: async function() {
        await fetch('/api/logout', { method: 'POST', credentials: 'include' });
        sessionStorage.clear();
        window.location.href = '/admin.login.html';
    }
};

window.SessionManager = SessionManager;