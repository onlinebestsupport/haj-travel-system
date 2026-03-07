/**
 * Login Handler for Alhudha Haj Travel
 * Handles admin and traveler login forms
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔐 Login page initialized');
    
    // Initialize login form
    initLoginForm();
    
    // Check if already logged in
    checkExistingSession();
});

/**
 * Initialize the login form
 */
function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        console.error('❌ Login form not found!');
        return;
    }
    
    console.log('✅ Login form found, attaching handler');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const username = document.getElementById('username')?.value;
        const password = document.getElementById('password')?.value;
        
        if (!username || !password) {
            showError('Please enter both username and password');
            return;
        }
        
        // Show loading state
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const originalText = submitBtn?.textContent || 'Login';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';
        }
        
        try {
            console.log(`📡 Attempting login for user: ${username}`);
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
                credentials: 'include'
            });
            
            const data = await response.json();
            console.log('📡 Login response:', data);
            
            if (data.success && data.authenticated) {
                // Store user info in sessionStorage
                sessionStorage.setItem('adminLoggedIn', 'true');
                sessionStorage.setItem('adminName', data.user.name || 'Admin');
                sessionStorage.setItem('adminRole', data.user.role || 'admin');
                sessionStorage.setItem('adminUsername', data.user.username || '');
                sessionStorage.setItem('loginTime', Date.now().toString());
                
                showSuccess('Login successful! Redirecting...');
                
                // Redirect to admin dashboard
                setTimeout(() => {
                    window.location.href = '/admin/';
                }, 1000);
            } else {
                showError(data.error || 'Invalid username or password');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }
            }
        } catch (error) {
            console.error('❌ Login error:', error);
            showError('Connection error. Please try again.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    });
}

/**
 * Check if already logged in and redirect if necessary
 */
function checkExistingSession() {
    // Don't redirect if we're already on login page (prevents loops)
    if (sessionStorage.getItem('adminLoggedIn') === 'true') {
        console.log('👤 Already logged in, checking session validity...');
        
        // Verify with server
        fetch('/api/check-session', {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                console.log('✅ Session valid, redirecting to dashboard');
                window.location.href = '/admin/';
            } else {
                console.log('⚠️ Session invalid, clearing storage');
                sessionStorage.clear();
            }
        })
        .catch(() => {
            // If server check fails, still clear to be safe
            sessionStorage.clear();
        });
    }
}

/**
 * Show error message to user
 */
function showError(message) {
    const errorDiv = document.getElementById('loginError');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.className = 'error-message';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        alert(message);
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const successDiv = document.getElementById('loginSuccess');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        successDiv.className = 'success-message';
    }
}

/**
 * Toggle password visibility
 */
function togglePasswordVisibility() {
    const passwordInput = document.getElementById('password');
    const toggleBtn = document.getElementById('togglePassword');
    
    if (!passwordInput || !toggleBtn) return;
    
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
    
    // Toggle icon
    const icon = toggleBtn.querySelector('i');
    if (icon) {
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    }
}

// Export for testing if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initLoginForm, checkExistingSession };
}