// Mobile Compatibility Fix
window.startTimers = function() {
    console.log('Timers started');
};

window.toggleMobileMenu = function() {
    var nav = document.querySelector('nav');
    if (nav) {
        nav.style.display = nav.style.display === 'none' ? 'block' : 'none';
    }
};

// Add mobile menu button
document.addEventListener('DOMContentLoaded', function() {
    var header = document.querySelector('.header-content');
    if (header && !document.getElementById('mobile-menu-btn')) {
        var menuBtn = document.createElement('button');
        menuBtn.id = 'mobile-menu-btn';
        menuBtn.innerHTML = '☰';
        menuBtn.style.cssText = 'display:none;background:transparent;border:none;color:white;font-size:24px;';
        menuBtn.onclick = window.toggleMobileMenu;
        header.appendChild(menuBtn);
        
        if (window.innerWidth <= 768) {
            menuBtn.style.display = 'block';
        }
    }
});

// Fix for arrow functions
window.safeForEach = function(arr, callback) {
    for (var i = 0; i < arr.length; i++) {
        callback(arr[i], i, arr);
    }
};
