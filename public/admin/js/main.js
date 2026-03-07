// Main JavaScript for Alhudha Haj Travel front page
console.log('Alhudha Haj Travel - Front page loaded');

// Package booking functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to package buttons
    const packageButtons = document.querySelectorAll('.package-btn');
    packageButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const packageName = this.dataset.package || 'selected package';
            alert(`Thank you for your interest in ${packageName}. Please login to proceed.`);
            window.location.href = '/traveler_login.html';
        });
    });
    
    console.log('Front page initialized');
});