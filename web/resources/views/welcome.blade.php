<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Laravel</title>

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=instrument-sans:400,500,600" rel="stylesheet" />

    <!-- Styles -->
    @vite('resources/css/app.css')
</head>
<body class="bg-gray-900 text-white">
    <div class="flex flex-col h-screen">
        <div class="p-4 flex justify-center">
            <a href="{{ route('home') }}" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                Next Idea
            </a>
        </div>
        <div class="flex-grow flex items-center justify-center">
            @if (isset($plan))
                <div class="max-w-2xl mx-auto">
                    <div class="bg-gray-800 shadow-lg rounded-lg p-6">
                        <h2 class="text-2xl font-bold mb-2">{{ $plan['_source']['name'] }}</h2>
                        <p class="text-gray-400">{{ $plan['_source']['description'] }}</p>
                        <div class="mt-4">
                            <h3 class="text-lg font-bold">Problem</h3>
                            <p class="text-gray-400">{{ $plan['_source']['problem'] }}</p>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-bold">Solution</h3>
                            <p class="text-gray-400">{{ $plan['_source']['solution'] }}</p>
                        </div>
                    </div>
                </div>
            @else
                <div class="text-center">
                    <p class="text-lg">Click the "Next Idea" button to get a business plan.</p>
                </div>
            @endif
        </div>
        <div class="p-4 flex justify-center">
            <form action="{{ route('waitlist.store') }}" method="POST" class="flex items-center">
                @csrf
                <input type="email" name="email" placeholder="Enter your email" class="w-1/2 px-4 py-2 border border-gray-300 rounded-lg text-black">
                <button type="submit" class="ml-2 px-4 py-2 bg-green-500 text-white rounded-lg">Join Waitlist</button>
            </form>
        </div>
    </div>
</body>
</html>
