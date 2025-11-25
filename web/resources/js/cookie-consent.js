
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
    document.getElementById('cookie-consent-banner').style.display = 'none';
    gtag('consent', 'update', {
        'analytics_storage': 'granted'
    });
}

function rejectCookies() {
    setCookie('cookie_consent', 'rejected', 365);
    document.getElementById('cookie-consent-banner').style.display = 'none';
}

window.acceptCookies = acceptCookies;
window.rejectCookies = rejectCookies;

document.addEventListener('DOMContentLoaded', function() {
    if (getCookie('cookie_consent') === 'accepted') {
        gtag('consent', 'update', {
            'analytics_storage': 'granted'
        });
    } else if (!getCookie('cookie_consent')) {
        document.getElementById('cookie-consent-banner').style.display = 'block';
    }
});
