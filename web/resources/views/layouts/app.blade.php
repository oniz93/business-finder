<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">

        <title>{{ config('app.name', 'Laravel') }}</title>

        <!-- Fonts -->
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=figtree:400,500,600&display=swap" rel="stylesheet" />

        @livewireStyles

        <!-- Scripts -->
        @vite(['resources/css/app.css', 'resources/js/app.js'])
    </head>
    <body class="font-sans antialiased">
        <div class="min-h-screen bg-gray-100 dark:bg-gray-900">
            @include('layouts.navigation')

            <!-- Page Heading -->
            @isset($header)
                <header class="bg-white dark:bg-gray-800 shadow">
                    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                        {{ $header }}
                    </div>
                </header>
            @endisset

            <!-- Page Content -->
            <main>
                {{ $slot }}
            </main>
        </div>
        <script>
            function copyToClipboard(elementId) {
                var copyText = document.getElementById(elementId);
                copyText.select();
                copyText.setSelectionRange(0, 99999); /* For mobile devices */
                document.execCommand("copy");
                alert("Copied the link: " + copyText.value);
            }

            function enterPresentationMode() {
                const element = document.documentElement; // Get the root HTML element
                if (element.requestFullscreen) {
                    element.requestFullscreen();
                } else if (element.mozRequestFullScreen) { /* Firefox */
                    element.mozRequestFullScreen();
                } else if (element.webkitRequestFullscreen) { /* Chrome, Safari and Opera */
                    element.webkitRequestFullscreen();
                } else if (element.msRequestFullscreen) { /* IE/Edge */
                    element.msRequestFullscreen();
                }

                // Optionally, hide navigation or other UI elements in presentation mode
                document.body.classList.add('presentation-mode');
            }

            function exitPresentationMode() {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.mozCancelFullScreen) { /* Firefox */
                    document.mozCancelFullScreen();
                } else if (document.webkitExitFullscreen) { /* Chrome, Safari and Opera */
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) { /* IE/Edge */
                    document.msExitFullscreen();
                }

                document.body.classList.remove('presentation-mode');
            }

            // Listen for fullscreen change events to adjust UI
            document.addEventListener('fullscreenchange', () => {
                if (!document.fullscreenElement) {
                    exitPresentationMode();
                }
            });
            document.addEventListener('mozfullscreenchange', () => {
                if (!document.mozFullScreenElement) {
                    exitPresentationMode();
                }
            });
            document.addEventListener('webkitfullscreenchange', () => {
                if (!document.webkitFullscreenElement) {
                    exitPresentationMode();
                }
            });
            document.addEventListener('msfullscreenchange', () => {
                if (!document.msFullscreenElement) {
                    exitPresentationMode();
                }
            });
        </script>
        @livewireScripts
    </body>
</html>
