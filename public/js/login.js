/**
 * Login Handler - Production Version
 * Secure authentication with proper error handling
 */

// Wait for DOM
document.addEventListener('DOMContentLoaded', function() {
    initLoginForm();
    checkExistingSession();
});

function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    
    if (!loginForm) {
        console.error('Login form element not found');
        return;
    }
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username')?.value?.trim();
        const password = document.getElementById('password')?.value;
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        
        // Validate inputs
        if (!username || !password) {
            showError('Please enter username and password');
            return;
        }
        
        if (password.length < 3) {
            showError('Invalid password');
            return;
        }
        
        // Disable button and show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
        }
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username, password}),
                credentials: 'include' // Include cookies for session
            });
            
            const data = await response.json();
            
            if (data.success && response.ok) {
                showSuccess('Login successful! Redirecting...');
                setTimeout(() => {
                    window.location.href = '/admin/';
                }, 1000);
            } else {
                const errorMsg = data.error || 'Invalid credentials';
                showError('Login failed: ' + errorMsg);
                
                // Reset form
                loginForm.reset();
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Login';
                }
            }
        } catch (error) {
            showError('Network error: ' + error.message);
            console.error('Login error:', error);
            
            // Reset form
            loginForm.reset();
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Login';
            }
        }
    });
}

function checkExistingSession() {
    // Check if user is already logged in
    fetch('/api/check-session', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            // User already logged in, redirect to admin
            window.location.href = '/admin/';
        }
    })
    .catch(error => console.error('Session check error:', error));
}

function showError(message) {
    const alertDiv = document.getElementById('loginAlert') || createAlert();
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Error!</strong> ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertDiv.style.display = 'block';
}

function showSuccess(message) {
    const alertDiv = document.getElementById('loginAlert') || createAlert();
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Success!</strong> ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertDiv.style.display = 'block';
}

function createAlert() {
    const alertDiv = document.createElement('div');
    alertDiv.id = 'loginAlert';
    alertDiv.style.marginBottom = '20px';
    const loginContainer = document.querySelector('.login-container');
    if (loginContainer) {
        loginContainer.insertBefore(alertDiv, loginContainer.firstChild);
    }
    return alertDiv;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
