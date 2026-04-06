// Session Manager for Admin Pages
const SessionManager = {
    initPage: async function(callback) {
        try {
            const session = await this.checkSession();
            if (!session.authenticated) {
                window.location.href = '/admin.login.html';
                return false;
            }
            if (callback && typeof callback === 'function') {
                await callback();
            }
            return true;
        } catch (error) {
            console.error('Session init failed:', error);
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
            console.log('❌ Session check failed with status:', response.status);
            return { authenticated: false };
        }
        
        const data = await response.json();
        console.log('📡 Session check response:', data);
        return data;
    } catch (error) {
        console.error('❌ Session check error:', error);
        return { authenticated: false };
    }
}
// Start timers function
function startTimers() {
    console.log('Session timers started');
    // Reset session on activity
    let timeout;
    function resetTimer() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (window.location.pathname !== '/admin.login.html') {
                SessionManager.checkSession().then(session => {
                    if (!session.authenticated) {
                        window.location.href = '/admin.login.html';
                    }
                });
            }
        }, 30 * 60 * 1000);
    }
    document.addEventListener('click', resetTimer);
    document.addEventListener('keypress', resetTimer);
    resetTimer();
}