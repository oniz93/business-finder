<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token() }}">

    <title>{{ config('app.name', 'Laravel') }}</title>

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    <!-- Scripts -->
    @vite(['resources/css/app.css', 'resources/js/app.js'])

    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JG4MJ55HBH"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('consent', 'default', {
            'analytics_storage': 'denied'
        });

        gtag('config', 'G-JG4MJ55HBH');
    </script>
</head>
<body class="font-sans antialiased bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="min-h-screen">
        @include('layouts.navigation')

        <!-- Page Heading -->
        @if (isset($header))
            <header class="bg-white dark:bg-gray-800 shadow">
                <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                    {{ $header }}
                </div>
            </header>
        @endif

        <!-- Page Content -->
        <main>
            {{ $slot }}
        </main>
    </div>

    <x-cookie-consent-banner />

    <script>
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
                const banner = document.getElementById('cookie-consent-banner');
                if (banner) banner.style.display = 'block';
            }
        });

        function copyToClipboard(elementId) {
            var copyText = document.getElementById(elementId);
            if(copyText) {
                copyText.select();
                copyText.setSelectionRange(0, 99999); /* For mobile devices */
                document.execCommand("copy");
                alert("Copied the link: " + copyText.value);
            }
        }
    </script>
    @stack('scripts')
</body>
</html>