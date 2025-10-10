<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Business Finder - Data-Driven Business Ideas</title>

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    @vite('resources/css/app.css')
</head>
<body class="bg-gray-900 text-white font-sans antialiased">
    <div class="min-h-screen flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">

        <!-- Hero Section -->
        <div class="text-center mb-12">
            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500 mb-3">
                Unlock Your Next Venture
            </h1>
            <p class="text-gray-300 text-lg max-w-3xl mx-auto">
                Stop guessing. We analyze millions of Reddit conversations to uncover real-world problems and data-driven business ideas, delivering validated plans to spark your entrepreneurial journey.
            </p>
        </div>

        <!-- Featured Idea Section -->
        @if ($plan && $plan->exists)
            <div class="w-full max-w-3xl bg-gray-800 shadow-2xl rounded-xl p-8 mb-8 border border-gray-700 transform hover:scale-105 transition-transform duration-300">
                <h2 class="text-3xl font-bold mb-3 text-green-400">{{ $plan->title }}</h2>
                <p class="text-gray-400 mb-6">{{ Str::limit($plan->executive_summary, 180) }}</p>
                <div class="flex justify-between items-center">
                    <a href="{{ route('business-plan', ['id' => $plan->id]) }}" class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
                        View Full Plan
                    </a>
                    <a href="{{ route('home') }}" class="text-green-400 hover:text-green-300 font-semibold py-3 px-6 transition duration-300">
                        Show Me Another &rarr;
                    </a>
                </div>
            </div>
        @else
            <div class="max-w-2xl w-full bg-gray-800 shadow-2xl rounded-lg p-8 mb-8 text-center border border-gray-700">
                <p class="text-lg text-gray-400">No business plans found. Our data miners are hard at work. Click below to try again.</p>
                <a href="{{ route('home') }}" class="mt-4 inline-block bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
                    Refresh Ideas
                </a>
            </div>
        @endif

        <!-- Upcoming Features Section -->
        <div class="w-full max-w-6xl mx-auto mt-16 sm:mt-24 px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl sm:text-4xl font-bold mb-2">The Future is Intelligent</h2>
            <p class="text-gray-400 text-lg sm:text-xl mb-12">We're building a suite of AI-powered tools to not just find ideas, but to build upon them.</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <!-- Feature 1: Semantic Search -->
                <div class="bg-gray-800 p-6 sm:p-8 rounded-xl border border-gray-700 transform hover:-translate-y-2 transition-transform duration-300">
                    <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.5 13.5h-1.5V12h1.5v1.5zm-1.5 1.5h1.5v1.5h-1.5v-1.5z" />
                    </svg>
                    <h3 class="text-xl sm:text-2xl font-semibold mb-3 text-blue-400">Semantic Search</h3>
                    <p class="text-gray-400">Go beyond keywords. Search for business plans by concept, industry, or problem. Find what you *really* mean, not just what you type.</p>
                </div>
                <!-- Feature 2: Idea Fusion -->
                <div class="bg-gray-800 p-6 sm:p-8 rounded-xl border border-gray-700 transform hover:-translate-y-2 transition-transform duration-300">
                    <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zM3.75 6H7.5m3 12h9.75m-9.75 0a2.25 2.25 0 01-4.5 0 2.25 2.25 0 014.5 0zM3.75 18H7.5m3-6h9.75m-9.75 0a2.25 2.25 0 00-4.5 0 2.25 2.25 0 004.5 0zM3.75 12H7.5" />
                    </svg>
                    <h3 class="text-xl sm:text-2xl font-semibold mb-3 text-blue-400">Idea Fusion</h3>
                    <p class="text-gray-400">Combine and conquer. Merge multiple business plans into a single, more powerful and unique venture. Your next unicorn could be a hybrid.</p>
                </div>
                <!-- Feature 3: Iterate & Innovate -->
                <div class="bg-gray-800 p-6 sm:p-8 rounded-xl border border-gray-700 transform hover:-translate-y-2 transition-transform duration-300">
                    <svg class="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0011.664 0l3.181-3.183m-4.991-2.695v-2.257a2.25 2.25 0 012.25-2.25h.003a2.25 2.25 0 012.25 2.25v2.257m-4.501 0a2.25 2.25 0 002.25 2.25h.003a2.25 2.25 0 002.25-2.25M6.75 15.75l-3.181-3.182a8.25 8.25 0 0111.664 0l3.181 3.182" />
                    </svg>
                    <h3 class="text-xl sm:text-2xl font-semibold mb-3 text-blue-400">Iterate & Innovate</h3>
                    <p class="text-gray-400">A plan is a starting point. Refine, adjust, and regenerate your business plan with new inputs until it perfectly matches your vision.</p>
                </div>
            </div>
        </div>

        <!-- Pricing Section -->
        <div class="w-full max-w-6xl mx-auto py-16 sm:py-24 px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl sm:text-4xl font-bold mb-2">Choose Your Plan</h2>
            <p class="text-gray-400 text-lg sm:text-xl mb-12">Unlock the right features for your entrepreneurial journey.</p>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">

                <!-- Tier 1: Basic -->
                <div class="bg-gray-800 p-8 rounded-xl border border-gray-700 flex flex-col">
                    <h3 class="text-2xl font-semibold mb-4">Basic</h3>
                    <p class="text-4xl font-bold mb-6">Free</p>
                    <ul class="text-gray-400 space-y-3 text-left mb-8 flex-grow">
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>View plans randomly</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Save plans</li>
                    </ul>
                    <a href="#" class="mt-auto w-full text-center bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300">Get Started</a>
                </div>

                <!-- Tier 2: Startupper (Highlighted) -->
                <div class="bg-gray-800 p-8 rounded-xl border-2 border-blue-500 flex flex-col relative lg:scale-105">
                    <div class="absolute top-0 -translate-y-1/2 left-1/2 -translate-x-1/2">
                        <span class="bg-blue-500 text-white text-sm font-semibold px-4 py-1 rounded-full uppercase">Most Popular</span>
                    </div>
                    <h3 class="text-2xl font-semibold mb-4">Startupper</h3>
                    <p class="text-4xl font-bold mb-2">$20<span class="text-lg font-normal text-gray-400"> / month</span></p>
                    <ul class="text-gray-400 space-y-3 text-left mb-8 flex-grow mt-4">
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Everything in Basic</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Search by subreddit</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Semantic search</li>
                    </ul>
                    <a href="#" class="mt-auto w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">Choose Startupper</a>
                </div>

                <!-- Tier 3: Businessman -->
                <div class="bg-gray-800 p-8 rounded-xl border border-gray-700 flex flex-col">
                    <h3 class="text-2xl font-semibold mb-4">Businessman</h3>
                    <p class="text-4xl font-bold mb-2">$100<span class="text-lg font-normal text-gray-400"> / month</span></p>
                    <ul class="text-gray-400 space-y-3 text-left mb-8 flex-grow mt-4">
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Everything in Startupper</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7
"></path></svg>Request subreddit scan</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Generate new plans</li>
                        <li class="flex items-center"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Customize plans</li>
                    </ul>
                    <a href="#" class="mt-auto w-full text-center bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300">Choose Businessman</a>
                </div>

            </div>
        </div>

        <!-- Waitlist Section -->
        <div class="mt-20 w-full max-w-2xl text-center">
            <h3 class="text-2xl font-semibold mb-3">Get Early Access</h3>
            <p class="text-gray-400 mb-6">Join the waitlist to be the first to use these features and help shape the future of idea generation.</p>
            <form action="{{ route('waitlist.store') }}" method="POST" class="flex justify-center max-w-md mx-auto">
                @csrf
                <input type="email" name="email" placeholder="your.email@company.com" class="w-full px-4 py-3 border border-gray-700 bg-gray-800 rounded-l-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                <button type="submit" class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-r-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">Join Waitlist</button>
            </form>
            @if(session('success'))
                <p class="text-green-400 mt-4">{{ session('success') }}</p>
            @endif
            @error('email')
                <p class="text-red-400 mt-4">{{ $message }}</p>
            @enderror
        </div>

    </div>
</body>
</html>