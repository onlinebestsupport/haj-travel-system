/**
 * Alhudha Haj Travel - Front Page JavaScript
 * Handles interactive elements on the main landing page
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Alhudha Haj Travel - Front page initialized');
    
    // Initialize all components
    initPackageCards();
    initMobileMenu();
    initNewsletterForm();
    initSmoothScroll();
    updateDynamicContent();
});

/**
 * Package card interactions
 * Makes package cards clickable and adds hover effects
 */
function initPackageCards() {
    const packageCards = document.querySelectorAll('.package-card, [class*="package"]');
    
    packageCards.forEach((card, index) => {
        // Add click handler
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button inside the card
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') return;
            
            const packageName = this.querySelector('h3')?.textContent || 
                               this.querySelector('h2')?.textContent || 
                               `Package ${index + 1}`;
            
            console.log(`📦 Package selected: ${packageName}`);
            
            // Show a subtle notification
            showNotification(`Viewing ${packageName}`, 'info');
        });
        
        // Add hover animation class
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });
    
    console.log(`✅ Initialized ${packageCards.length} package cards`);
}

/**
 * Mobile menu toggle for responsive design
 */
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (!menuToggle || !navMenu) {
        // Create mobile menu if it doesn't exist
        createMobileMenu();
        return;
    }
    
    menuToggle.addEventListener('click', function() {
        const expanded = this.getAttribute('aria-expanded') === 'true' ? false : true;
        this.setAttribute('aria-expanded', expanded);
        navMenu.classList.toggle('active');
        
        // Toggle icon if it exists
        const icon = this.querySelector('i');
        if (icon) {
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!menuToggle.contains(e.target) && !navMenu.contains(e.target)) {
            navMenu.classList.remove('active');
            menuToggle.setAttribute('aria-expanded', 'false');
            
            const icon = menuToggle.querySelector('i');
            if (icon) {
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-times');
            }
        }
    });
}

/**
 * Create mobile menu if not present in HTML
 */
function createMobileMenu() {
    const header = document.querySelector('header') || document.body;
    
    const menuToggle = document.createElement('button');
    menuToggle.className = 'menu-toggle';
    menuToggle.setAttribute('aria-label', 'Toggle menu');
    menuToggle.innerHTML = '<i class="fas fa-bars"></i> Menu';
    
    const navMenu = document.createElement('nav');
    navMenu.className = 'nav-menu';
    navMenu.innerHTML = `
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="#packages">Packages</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#contact">Contact</a></li>
            <li><a href="/traveler_login.html">Traveler Login</a></li>
            <li><a href="/admin.login.html">Admin Login</a></li>
        </ul>
    `;
    
    header.appendChild(menuToggle);
    header.appendChild(navMenu);
    
    // Re-initialize with new elements
    initMobileMenu();
}

/**
 * Newsletter/contact form handling
 */
function initNewsletterForm() {
    const forms = document.querySelectorAll('.newsletter-form, .contact-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            const formData = new FormData(form);
            
            try {
                // Disable button and show loading
                submitBtn.disabled = true;
                submitBtn.textContent = 'Sending...';
                
                // Get form data
                const data = Object.fromEntries(formData.entries());
                
                // Send to API (if you have one)
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                }).catch(() => ({ ok: false })); // Handle network errors gracefully
                
                if (response.ok) {
                    showNotification('Thank you! We\'ll contact you soon.', 'success');
                    form.reset();
                } else {
                    // Fallback for demo/if API doesn't exist
                    showNotification('Thank you for your interest!', 'success');
                    form.reset();
                }
                
            } catch (error) {
                console.error('Form error:', error);
                showNotification('Thank you for your interest!', 'success');
                form.reset();
                
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href === '#') return;
            
            e.preventDefault();
            
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update URL without jumping
                history.pushState(null, null, href);
            }
        });
    });
}

/**
 * Update dynamic content from API
 */
async function updateDynamicContent() {
    try {
        // Fetch latest packages from API
        const response = await fetch('/api/batches').catch(() => null);
        
        if (response && response.ok) {
            const batches = await response.json();
            
            // Update package prices if needed
            if (batches && batches.length) {
                console.log(`📊 Found ${batches.length} packages from API`);
                // You can update DOM with real-time data here
            }
        }
    } catch (error) {
        console.log('Using static package data');
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.front-page-notification');
    if (existing) existing.remove();
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `front-page-notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
        cursor: pointer;
    `;
    
    // Add icon based on type
    const icon = type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️';
    notification.innerHTML = `${icon} ${message}`;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
    
    // Remove on click
    notification.addEventListener('click', () => notification.remove());
}

// Add slide animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);