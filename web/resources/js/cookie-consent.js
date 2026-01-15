
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function setCookie(name, value, days) {
    const d = new Date();
    d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + d.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function acceptCookies() {
    setCookie('cookie_consent', 'accepted', 365);
    const banner = document.getElementById('cookie-consent-banner');
    if (banner) banner.style.display = 'none';

    // Update GA consent
    if (typeof gtag === 'function') {
        gtag('consent', 'update', {
            'analytics_storage': 'granted'
        });
    }
}

function rejectCookies() {
    setCookie('cookie_consent', 'rejected', 365);
    const banner = document.getElementById('cookie-consent-banner');
    if (banner) banner.style.display = 'none';
}

// Expose functions to window so they can be called from inline onclick handlers in Blade
window.acceptCookies = acceptCookies;
window.rejectCookies = rejectCookies;

document.addEventListener('DOMContentLoaded', function () {
    if (getCookie('cookie_consent') === 'accepted') {
        if (typeof gtag === 'function') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }
    } else if (!getCookie('cookie_consent')) {
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) banner.style.display = 'block';
    }
});
