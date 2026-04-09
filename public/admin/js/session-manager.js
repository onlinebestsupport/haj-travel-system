// Session Manager - Fixed Version
const SessionManager = {
    initPage: async function(callback) {
        console.log('🔍 SessionManager.initPage called');
        
        try {
            // Check if we're already on login page
            if (window.location.pathname.includes('/admin.login.html')) {
                console.log('📋 On login page - skipping session check');
                if (callback && typeof callback === 'function') {
                    await callback();
                }
                return true;
            }
            
            const session = await this.checkSession();
            console.log('📡 Session data:', session);
            
            if (!session.authenticated) {
                console.log('❌ Not authenticated, redirecting to login...');
                window.location.href = '/admin.login.html';
                return false;
            }
            
            console.log('✅ Authenticated as:', session.username || session.user?.username);
            
            if (callback && typeof callback === 'function') {
                await callback();
            }
            
            this.startTimers();
            return true;
            
        } catch (error) {
            console.error('❌ Session initialization failed:', error);
            window.location.href = '/admin.login.html';
            return false;
        }
    },

    checkSession: async function() {
        try {
            console.log('🔍 Checking session...');
            const response = await fetch('/api/check-session', {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                console.log('❌ Session check HTTP error:', response.status);
                return { authenticated: false };
            }
            
            const data = await response.json();
            console.log('📡 Session check response:', data);
            return data;
            
        } catch (error) {
            console.error('❌ Session check error:', error);
            return { authenticated: false };
        }
    },

    logout: async function() {
        console.log('🚪 Logging out...');
        try {
            await fetch('/api/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        window.location.href = '/admin.login.html';
    },

    startTimers: function() {
        console.log('⏰ Starting session timers');
        let timeout;
        
        const resetTimer = () => {
            clearTimeout(timeout);
            timeout = setTimeout(async () => {
                console.log('⏰ Session timeout check...');
                const session = await this.checkSession();
                if (!session.authenticated) {
                    console.log('❌ Session expired, redirecting...');
                    window.location.href = '/admin.login.html';
                }
            }, 30 * 60 * 1000); // 30 minutes
        };
        
        document.addEventListener('click', resetTimer);
        document.addEventListener('keypress', resetTimer);
        resetTimer();
    }
};

// Global logout function
function logout() {
    SessionManager.logout();
}

console.log('✅ Session Manager loaded');