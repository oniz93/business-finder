<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Business Finder</title>

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    @vite('resources/css/app.css')
</head>
<body class="bg-gray-900 text-white font-sans antialiased">
    <div class="min-h-screen flex flex-col items-center justify-center">
        
        <div class="text-center mb-8">
            <h1 class="text-5xl font-bold mb-2">Find Your Next Big Idea</h1>
            <p class="text-gray-400 text-lg">Randomly generated business plans to spark your entrepreneurial spirit.</p>
        </div>

        @if ($plan && $plan->exists)
            <div class="max-w-2xl w-full bg-gray-800 shadow-2xl rounded-lg p-8 mb-8">
                <h2 class="text-3xl font-bold mb-3">{{ $plan->title }}</h2>
                <p class="text-gray-400 mb-4">{{ Str::limit($plan->executive_summary, 150) }}</p>
                <a href="{{ route('business-plan', ['id' => $plan->id]) }}" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition duration-300">View Full Plan</a>
            </div>
        @else
            <div class="max-w-2xl w-full bg-gray-800 shadow-2xl rounded-lg p-8 mb-8 text-center">
                <p class="text-lg text-gray-400">No business plans found in the index. Click below to try again.</p>
            </div>
        @endif

        <div class="flex space-x-4">
            <a href="{{ route('home') }}" class="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300">Next Idea</a>
        </div>

        <div class="mt-12 text-center">
            <h3 class="text-xl font-semibold mb-3">Join the Waitlist</h3>
            <p class="text-gray-400 mb-4">Be the first to know when we launch new features.</p>
            <form action="{{ route('waitlist.store') }}" method="POST" class="flex justify-center max-w-md mx-auto">
                @csrf
                <input type="email" name="email" placeholder="Enter your email" class="w-full px-4 py-2 border border-gray-700 rounded-l-lg text-black focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                <button type="submit" class="px-6 py-2 bg-blue-500 text-white font-semibold rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500">Join</button>
            </form>
            @if(session('success'))
                <p class="text-green-400 mt-3">{{ session('success') }}</p>
            @endif
            @error('email')
                <p class="text-red-400 mt-3">{{ $message }}</p>
            @enderror
        </div>

    </div>
</body>
</html>