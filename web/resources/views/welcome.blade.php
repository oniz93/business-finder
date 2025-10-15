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
    @include('layouts.navigation')
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
                    <a href="{{ route('business-plan', ['businessPlan' => $plan->id]) }}" class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
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

        <!-- Feature Wall Section -->
        <div class="w-full max-w-7xl mx-auto mt-16 sm:mt-24 px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-4xl sm:text-5xl font-bold mb-4">Your Complete Idea-to-Venture Toolkit</h2>
                <p class="text-gray-400 text-lg sm:text-xl max-w-3xl mx-auto">From initial spark to strategic plan, Business Finder provides a comprehensive suite of AI-powered tools to guide your entrepreneurial journey.</p>
            </div>

            <!-- Section 1: Discover & Validate -->
            <div class="mb-16">
                <h3 class="text-2xl sm:text-3xl font-bold text-blue-400 mb-8 text-center">Discover & Validate</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Semantic Search</h4><p class="mt-1 text-sm text-gray-400">Go beyond keywords and search for concepts, problems, and solutions.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Advanced Filtering</h4><p class="mt-1 text-sm text-gray-400">Filter ideas by industry, market size, sentiment, required capital, and more.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Personalized Feed</h4><p class="mt-1 text-sm text-gray-400">An AI-curated feed of ideas based on your interests and interactions.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Real-time Trends</h4><p class="mt-1 text-sm text-gray-400">See which ideas are new and growing in popularity with a velocity score.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Sentiment Analysis</h4><p class="mt-1 text-sm text-gray-400">Gauge the emotional response to an idea with an AI-generated sentiment score.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Proactive Alerts</h4><p class="mt-1 text-sm text-gray-400">Get email notifications when new ideas matching your criteria start trending.</p></div></div>
                </div>
            </div>

            <!-- Section 2: Analyze & Strategize -->
            <div class="mb-16">
                <h3 class="text-2xl sm:text-3xl font-bold text-blue-400 mb-8 text-center">Analyze & Strategize</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Audience Personas</h4><p class="mt-1 text-sm text-gray-400">Get AI-generated personas of your target audience, including their key traits.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M12 12a2 2 0 11-4 0 2 2 0 014 0z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Competitor Deep Dive</h4><p class="mt-1 text-sm text-gray-400">Go beyond names to analyze competitor strategies and market positioning.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">AI-Powered SWOT Analysis</h4><p class="mt-1 text-sm text-gray-400">Automatically generate a SWOT analysis for any business idea.</p></div></div>
                </div>
            </div>

            <!-- Section 3: Develop & Plan -->
            <div class="mb-16">
                <h3 class="text-2xl sm:text-3xl font-bold text-blue-400 mb-8 text-center">Develop & Plan</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Interactive Plan Editor</h4><p class="mt-1 text-sm text-gray-400">Edit, customize, and expand on your business plans in real-time.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l-4 4-4-4M6 16l-4-4 4-4"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">AI Idea Fusion</h4><p class="mt-1 text-sm text-gray-400">Select multiple ideas and have our AI merge them into a novel hybrid concept.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Business Model Canvas</h4><p class="mt-1 text-sm text-gray-400">Automatically generate an interactive Business Model Canvas from your plan.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v.01M12 14v3m-3-3h6M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Basic Financial Projections</h4><p class="mt-1 text-sm text-gray-400">Generate simple revenue and cost forecasts based on market data.</p></div></div>
                    <div class="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-start"><div class="flex-shrink-0"><svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg></div><div class="ml-4"><h4 class="text-lg font-bold">Name & Slogan Generation</h4><p class="mt-1 text-sm text-gray-400">Let AI assist in brainstorming creative and available business names.</p></div></div>
                </div>
            </div>

        </div>

        <!-- Pricing Section -->
        <div class="w-full max-w-7xl mx-auto pt-16 pb-8 sm:pt-24 sm:pb-12 px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl sm:text-4xl font-bold mb-2">Find the Perfect Plan for Your Ambition</h2>
            <p class="text-gray-400 text-lg sm:text-xl mb-16">From casual exploration to deep market analysis, we have you covered.</p>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-8 items-start">

                <!-- Tier 1: Explorer -->
                <div class="bg-gray-800/50 p-8 rounded-xl border border-gray-700 flex flex-col h-full">
                    <h3 class="text-2xl font-semibold">Explorer</h3>
                    <p class="text-gray-400 mt-2 mb-6">For casual discovery.</p>
                    <p class="text-4xl font-bold">Free</p>
                    <a href="#" class="w-full text-center bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300 mt-6">Start Exploring</a>
                    <ul class="text-gray-300 space-y-3 text-left mt-8 flex-grow">
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>5 New Plans per Day</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Save up to 3 Plans</li>
                    </ul>
                </div>

                <!-- Tier 2: Founder -->
                <div class="bg-gray-800 p-8 rounded-xl border-2 border-blue-500 flex flex-col h-full relative transform scale-105 z-10">
                     <div class="absolute top-0 -translate-y-1/2 left-1/2 -translate-x-1/2"><span class="bg-blue-500 text-white text-xs font-semibold px-3 py-1 rounded-full uppercase">Most Popular</span></div>
                    <h3 class="text-2xl font-semibold text-blue-400">Founder</h3>
                    <p class="text-gray-400 mt-2 mb-6">For serious entrepreneurs.</p>
                    <p class="text-5xl font-bold">$29<span class="text-xl font-normal text-gray-400">/mo</span></p>
                    <a href="#" class="w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 mt-6">Start Founding</a>
                    <ul class="text-gray-300 space-y-3 text-left mt-8 flex-grow">
                        <li class="flex font-semibold"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Unlimited Plan Access</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Full Semantic Search</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Advanced Filtering & Sorting</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Sentiment Analysis Score</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>AI-Powered SWOT Analysis</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Business Name & Slogan Ideas</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Save & Organize Collections</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Export to PDF & Text</li>
                    </ul>
                </div>

                <!-- Tier 3: Innovator -->
                <div class="bg-gray-800/50 p-8 rounded-xl border border-gray-700 flex flex-col h-full">
                    <h3 class="text-2xl font-semibold">Innovator</h3>
                    <p class="text-gray-400 mt-2 mb-6">For dedicated power users.</p>
                    <p class="text-5xl font-bold">$99<span class="text-xl font-normal text-gray-400">/mo</span></p>
                    <a href="#" class="w-full text-center bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300 mt-6">Start Innovating</a>
                    <ul class="text-gray-300 space-y-3 text-left mt-8 flex-grow">
                        <li class="flex font-semibold"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Everything in Founder</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Trend Velocity Score</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Audience Insights & Personas</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Competitor Radar</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Suggested Monetization Strategies</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Interactive Plan Editor</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Business Model Canvas Generator</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Basic Financial Projections</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Alerts & Notifications</li>
                    </ul>
                </div>

                <!-- Tier 4: Enterprise -->
                <div class="bg-gray-800/50 p-8 rounded-xl border border-gray-700 flex flex-col h-full">
                    <h3 class="text-2xl font-semibold">Enterprise</h3>
                    <p class="text-gray-400 mt-2 mb-6">For teams and agencies.</p>
                    <p class="text-4xl font-bold">Custom</p>
                    <a href="#" class="w-full text-center bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition duration-300 mt-6">Contact Sales</a>
                    <ul class="text-gray-300 space-y-3 text-left mt-8 flex-grow">
                        <li class="flex font-semibold"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Everything in Innovator</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Team Accounts & Collaboration</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Full API Access</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Competitor Analysis Deep Dive</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Pitch Deck Generator</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>White-Label Reports</li>
                        <li class="flex"><svg class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Dedicated Support</li>
                    </ul>
                </div>

            </div>
        </div>

        <!-- Waitlist Section -->


    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function () {
            const modal = document.getElementById('waitlist-modal');
            const modalForm = modal.querySelector('form');
            const openModalButtons = document.querySelectorAll('a[href="#"]');

            openModalButtons.forEach(button => {
                button.addEventListener('click', function (e) {
                    e.preventDefault();
                    modal.classList.remove('hidden');
                });
            });

            modal.addEventListener('click', function (e) {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });

            modalForm.addEventListener('submit', function (e) {
                e.preventDefault();

                const email = modalForm.querySelector('input[name="email"]').value;
                const token = modalForm.querySelector('input[name="_token"]').value;

                fetch('{{ route('waitlist.store') }}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': token,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email })
                })
                .then(response => response.json())
                .then(data => {
                    const successMessage = document.createElement('p');
                    successMessage.classList.add('text-green-400', 'mt-4');

                    const errorMessage = document.createElement('p');
                    errorMessage.classList.add('text-red-400', 'mt-4');

                    if (data.success) {
                        modalForm.querySelector('input[name="email"]').value = '';
                        successMessage.textContent = data.success;
                        modalForm.parentNode.appendChild(successMessage);

                        setTimeout(() => {
                            modal.classList.add('hidden');
                            successMessage.remove();
                        }, 3000);
                    } else if (data.errors) {
                        errorMessage.textContent = data.errors.email[0];
                        modalForm.parentNode.appendChild(errorMessage);

                        setTimeout(() => {
                            errorMessage.remove();
                        }, 3000);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    </script>

    <div id="waitlist-modal" class="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50 hidden">
        <div class="bg-gray-800 rounded-lg p-8 max-w-md w-full">
            <h3 class="text-2xl font-semibold mb-3">Coming Soon!</h3>
            <p class="text-gray-400 mb-6">Paid plans are not yet available. Join the waitlist to be notified when they launch.</p>
            <form action="{{ route('waitlist.store') }}" method="POST" class="flex justify-center max-w-md mx-auto">
                @csrf
                <input type="email" name="email" placeholder="your.email@company.com" class="w-full px-4 py-3 border border-gray-700 bg-gray-800 rounded-l-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                <button type="submit" class="px-6 py-3 bg-blue-600 text-white font-semibold rounded-r-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">Join Waitlist</button>
            </form>
        </div>
    </div>
</body>
</html>