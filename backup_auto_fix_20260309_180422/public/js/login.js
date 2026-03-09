/**
 * Login Handler - DEBUG VERSION
 * Console logs will confirm execution
 */

console.log('🔥🔥🔥 LOGIN.JS IS EXECUTING! 🔥🔥🔥');

// Immediate execution test
window.loginJSLoaded = true;

// Wait for DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM loaded - login.js running');
    
    // Make function globally available
    window.testLoginFunction = function() {
        console.log('✅ testLoginFunction called');
        return true;
    };
    
    initLoginForm();
    checkExistingSession();
});

function initLoginForm() {
    console.log('🔧 initLoginForm called');
    
    const loginForm = document.getElementById('loginForm');
    console.log('📋 Login form element:', loginForm);
    
    if (!loginForm) {
        console.error('❌ Login form not found!');
        return;
    }
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('📤 Form submitted');
        
        const username = document.getElementById('username')?.value;
        const password = document.getElementById('password')?.value;
        
        console.log('👤 Username:', username);
        console.log('🔑 Password length:', password?.length);
        
        if (!username || !password) {
            alert('Please enter username and password');
            return;
        }
        
        try {
            console.log('📡 Sending login request...');
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            console.log('📡 Response status:', response.status);
            const data = await response.json();
            console.log('📡 Response data:', data);
            
            if (data.success) {
                alert('Login successful! Redirecting...');
                window.location.href = '/admin/';
            } else {
                alert('Login failed: ' + (data.error || 'Invalid credentials'));
            }
        } catch (error) {
            console.error('❌ Error:', error);
            alert('Error: ' + error.message);
        }
    });
}

function checkExistingSession() {
    console.log('🔍 checkExistingSession called');
    // Simplified for debugging
}