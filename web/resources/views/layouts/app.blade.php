<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Laravel</title>

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

        <script>
            if (document.cookie.includes('theme=dark')) {
                document.documentElement.classList.add('dark');
            } else if (!document.cookie.includes('theme=') && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        </script>

        @livewireStyles

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
    <body class="font-sans antialiased">
        <div class="min-h-screen bg-gray-100 dark:bg-gray-900">
            @include('layouts.navigation')

    <script>
        if (document.cookie.includes('theme=dark')) {
            document.documentElement.classList.add('dark');
        } else if (!document.cookie.includes('theme=') && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    </script>
</head>
<body class="bg-gray-900 text-white">
    <nav class="p-6 bg-gray-800 flex justify-between mb-6">
        <ul class="flex items-center">
            <li>
                <a href="/" class="p-3">Home</a>
            </li>
            <li>
                <a href="/dashboard" class="p-3">Dashboard</a>
            </li>
            <li>
                <a href="/business-plans" class="p-3">Business Plans</a>
            </li>
        </ul>

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
                    document.getElementById('cookie-consent-banner').style.display = 'block';
                }
            });
        </script>

        <script>
            function copyToClipboard(elementId) {
                var copyText = document.getElementById(elementId);
                copyText.select();
                copyText.setSelectionRange(0, 99999); /* For mobile devices */
                document.execCommand("copy");
                alert("Copied the link: " + copyText.value);
            }

            @guest
                <li>
                    <a href="{{ route('login') }}" class="p-3">Login</a>
                </li>
                <li>
                    <a href="{{ route('register') }}" class="p-3">Register</a>
                </li>
            @endguest
        </ul>
    </nav>
    @yield('content')
</body>
</html>
