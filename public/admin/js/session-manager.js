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
        const response = await fetch('/api/check-session', {
            credentials: 'include'
        });
        return await response.json();
    },

    logout: async function() {
        await fetch('/api/logout', { method: 'POST', credentials: 'include' });
        window.location.href = '/admin.login.html';
    }
};

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