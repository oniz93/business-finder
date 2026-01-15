<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" class="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Business Finder - AI-Curated SaaS Ideas for Builders</title>
    <meta name="description" content="Stop guessing what to build. Discover validated SaaS business ideas from millions of real Reddit conversations. Perfect for solopreneurs and AI-powered developers.">

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">

    @vite(['resources/css/app.css', 'resources/js/app.js'])

    <style>
        .gradient-text {
            background: linear-gradient(135deg, #34d399 0%, #3b82f6 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .glow-card {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            transition: all 0.3s ease;
        }
        .glow-card:hover {
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.15);
            transform: translateY(-4px);
        }
        .pulse-dot {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .stat-card {
            background: linear-gradient(145deg, rgba(31, 41, 55, 0.8) 0%, rgba(17, 24, 39, 0.9) 100%);
        }
    </style>
</head>
<body class="bg-gray-950 text-white font-sans antialiased">
    @include('layouts.navigation')

    <div class="min-h-screen">

        <!-- Hero Section -->
        <div class="relative overflow-hidden">
            <!-- Subtle gradient background -->
            <div class="absolute inset-0 bg-gradient-to-br from-blue-950/30 via-gray-950 to-purple-950/20"></div>

            <div class="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 sm:pt-24 pb-12 sm:pb-16">
                <div class="text-center">

                    <!-- Badge -->
                    <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800/80 border border-gray-700/50 mb-8">
                        <span class="w-2 h-2 rounded-full bg-green-400 pulse-dot"></span>
                        <span class="text-sm text-gray-300">50,000+ AI-analyzed ideas</span>
                    </div>

                    <!-- Main Headline -->
                    <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-6">
                        Find Your Next<br>
                        <span class="gradient-text">SaaS to Build</span>
                    </h1>

                    <!-- Subheadline -->
                    <p class="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        We scan millions of Reddit conversations to find real problems people pay to solve.
                        <span class="text-white font-medium">Perfect for solo founders using AI to ship fast.</span>
                    </p>

                    <!-- CTA Buttons -->
                    <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
                        <a href="{{ route('business-plan-search.index') }}" wire:navigate
                           class="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                            </svg>
                            Search Ideas
                        </a>
                        <a href="/"
                           class="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-4 px-8 rounded-xl border border-gray-700 hover:border-gray-600 transition-all duration-300">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                            </svg>
                            Random Idea
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <!-- Featured Idea Card -->
        @if ($plan && $plan->exists)
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
            <div class="glow-card rounded-2xl p-8 border border-gray-800">
                <!-- Header -->
                <div class="flex items-start justify-between gap-4 mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-3">
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                                💡 Featured Idea
                            </span>
                            @if($plan->subreddit)
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
                                r/{{ $plan->subreddit }}
                            </span>
                            @endif
                                💡 Featured Idea
                            </span>
                            @if($plan->is_saas)
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                SaaS
                            </span>
                            @endif
                            @if($plan->is_solo_entrepreneur_possible)
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30">
                                Solo Friendly
                            </span>
                            @endif
                        </div>
                        <h2 class="text-2xl sm:text-3xl font-bold text-white leading-tight">{{ $plan->title }}</h2>
                    </div>
                    @if($plan->viability_score)
                    <div class="flex-shrink-0 text-center">
                        <div class="w-16 h-16 rounded-full bg-gradient-to-br from-green-500/20 to-blue-500/20 border border-gray-700 flex items-center justify-center">
                            <span class="text-xl font-bold text-white">{{ $plan->viability_score }}</span>
                        </div>
                        <span class="text-xs text-gray-500 mt-1 block">Score</span>
                    </div>
                    @endif
                </div>

                <!-- Summary -->
                <p class="text-gray-400 mb-6 leading-relaxed">{{ Str::limit($plan->executive_summary, 200) }}</p>

                <!-- Actions -->
                <div class="flex flex-col sm:flex-row gap-3">
                    <a href="/business-plans/{{ $plan->id }}" wire:navigate
                       class="flex-1 inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300">
                        View Full Plan
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                        </svg>
                    </a>
                    <a href="/"
                       class="flex-1 inline-flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white font-medium py-3 px-6 rounded-xl border border-gray-700 hover:border-gray-600 transition-all duration-300">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Show Me Another
                    </a>
                </div>
            </div>
        </div>
        @else
        <div class="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
            <div class="glow-card rounded-2xl p-8 border border-gray-800 text-center">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-800 flex items-center justify-center">
                    <svg class="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                    </svg>
                </div>
                <p class="text-gray-400 mb-4">No business plans loaded yet. Our AI is analyzing data.</p>
                <a href="/" class="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white font-medium py-3 px-6 rounded-xl transition-all duration-300">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    Try Again
                </a>
            </div>
        </div>
        @endif

        <!-- Why This Works Section -->
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
            <div class="text-center mb-12">
                <h2 class="text-2xl sm:text-3xl font-bold mb-3">Built for Solo Builders</h2>
                <p class="text-gray-400 max-w-xl mx-auto">Skip the idea validation phase. Every idea comes from real people expressing real frustrations.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Card 1 -->
                <div class="stat-card rounded-2xl p-6 border border-gray-800">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Real Pain Points</h3>
                    <p class="text-gray-400 text-sm leading-relaxed">Every idea comes from Reddit threads where people are genuinely frustrated and asking for solutions.</p>
                </div>

                <!-- Card 2 -->
                <div class="stat-card rounded-2xl p-6 border border-gray-800">
                    <div class="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Solo-Friendly Ideas</h3>
                    <p class="text-gray-400 text-sm leading-relaxed">Filtered for ideas a single developer can realistically build and launch using modern AI tools.</p>
                </div>

                <!-- Card 3 -->
                <div class="stat-card rounded-2xl p-6 border border-gray-800">
                    <div class="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold mb-2">SaaS-First Filter</h3>
                    <p class="text-gray-400 text-sm leading-relaxed">Pre-filtered for recurring revenue opportunities. Build products, not one-time gigs.</p>
                </div>
            </div>
        </div>

        <!-- Pricing Section -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
            <div class="text-center mb-16">
                <h2 class="text-3xl sm:text-4xl font-bold mb-4">Beta Access Pricing</h2>
                <p class="text-gray-400 text-lg max-w-2xl mx-auto">
                    During our Beta period, the <span class="text-white font-semibold">Founder Plan</span> is completely free. 
                    Monitor our roadmap as we roll out advanced features.
                </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-8">
                
                <!-- Tier 1: Explorer -->
                <div class="glow-card rounded-2xl p-6 border border-gray-800 opacity-60 grayscale hover:grayscale-0 transition-all duration-300 relative overflow-hidden">
                    <div class="absolute top-0 right-0 bg-gray-800 text-xs font-bold px-2 py-1 rounded-bl-lg text-gray-400">CLOSED</div>
                    <h3 class="text-xl font-semibold mb-2 text-gray-300">Explorer</h3>
                    <p class="text-sm text-gray-500 mb-6">For casual discovery.</p>
                    <div class="mb-6">
                        <span class="text-3xl font-bold text-gray-400">$0</span>
                    </div>
                    <button disabled class="w-full py-2 px-4 bg-gray-800 text-gray-500 font-medium rounded-lg cursor-not-allowed mb-8 text-sm border border-gray-700">
                        Not Available in Beta
                    </button>
                    <ul class="space-y-3 text-sm text-gray-500">
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>5 New Plans per Day</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Save up to 3 Plans</li>
                    </ul>
                </div>

                <!-- Tier 2: Founder (Highlighted) -->
                <div class="glow-card rounded-2xl p-6 border-2 border-blue-500/50 bg-gray-800/40 relative transform hover:-translate-y-1 transition-transform duration-300">
                    <div class="absolute top-0 right-0 left-0 bg-blue-500/10 text-blue-400 text-xs font-bold px-2 py-1 text-center border-b border-blue-500/20">FREE DURING BETA</div>
                    <h3 class="text-xl font-semibold mb-2 text-blue-400 mt-4">Founder</h3>
                    <p class="text-sm text-gray-400 mb-6">For serious entrepreneurs.</p>
                    <div class="mb-6 flex items-baseline gap-2">
                        <span class="text-4xl font-bold text-white">$0</span>
                        <span class="text-lg text-gray-500 line-through Decoration-gray-500">$29</span>
                        <span class="text-sm text-gray-500">/mo</span>
                    </div>
                    <a href="{{ route('register') }}" class="block w-full text-center py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg mb-8 shadow-lg shadow-blue-900/50 transition-colors">
                        Join Beta
                    </a>
                    <ul class="space-y-3 text-sm text-gray-300">
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Unlimited Plan Access</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Full Semantic Search</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Filtering & Sorting</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Viability Scores</li>
                        <li class="flex items-center gap-2 opacity-60"><svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>SWOT Analysis <span class="text-[10px] ml-auto border border-gray-600 px-1 rounded text-gray-400">SOON</span></li>
                        <li class="flex items-center gap-2 opacity-60"><svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Name & Slogan Gen <span class="text-[10px] ml-auto border border-gray-600 px-1 rounded text-gray-400">SOON</span></li>
                    </ul>
                </div>

                <!-- Tier 3: Innovator -->
                <div class="glow-card rounded-2xl p-6 border border-gray-800 opacity-60 grayscale hover:grayscale-0 transition-all duration-300 relative overflow-hidden">
                    <div class="absolute top-0 right-0 bg-gray-800 text-xs font-bold px-2 py-1 rounded-bl-lg text-gray-400">CLOSED</div>
                    <h3 class="text-xl font-semibold mb-2 text-green-400">Innovator</h3>
                    <p class="text-sm text-gray-500 mb-6">Full power for builders.</p>
                    <div class="mb-6">
                        <span class="text-3xl font-bold text-gray-400">$99</span><span class="text-gray-600">/mo</span>
                    </div>
                    <button disabled class="w-full py-2 px-4 bg-gray-800 text-gray-500 font-medium rounded-lg cursor-not-allowed mb-8 text-sm border border-gray-700">
                        Not Available in Beta
                    </button>
                    <ul class="space-y-3 text-sm text-gray-500">
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg><span class="font-semibold text-gray-400">Everything in Founder</span></li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Interactive Plan Editor</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Pitch Deck Generator</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Business Model Canvas</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Collections & export</li>
                        <li class="flex items-center gap-2 opacity-60"><svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Trend Velocity <span class="text-[10px] ml-auto border border-gray-600 px-1 rounded">SOON</span></li>
                        <li class="flex items-center gap-2 opacity-60"><svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Audience Personas <span class="text-[10px] ml-auto border border-gray-600 px-1 rounded">SOON</span></li>
                        <li class="flex items-center gap-2 opacity-60"><svg class="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>Competitor Radar <span class="text-[10px] ml-auto border border-gray-600 px-1 rounded">SOON</span></li>
                    </ul>
                </div>

                <!-- Tier 4: Enterprise -->
                <div class="glow-card rounded-2xl p-6 border border-gray-800 opacity-60 grayscale hover:grayscale-0 transition-all duration-300 relative overflow-hidden">
                    <div class="absolute top-0 right-0 bg-gray-800 text-xs font-bold px-2 py-1 rounded-bl-lg text-gray-400">CLOSED</div>
                    <h3 class="text-xl font-semibold mb-2 text-purple-400">Enterprise</h3>
                    <p class="text-sm text-gray-500 mb-6">For teams & agencies.</p>
                    <div class="mb-6">
                        <span class="text-3xl font-bold text-gray-400">Custom</span>
                    </div>
                    <button disabled class="w-full py-2 px-4 bg-gray-800 text-gray-500 font-medium rounded-lg cursor-not-allowed mb-8 text-sm border border-gray-700">
                        Not Available in Beta
                    </button>
                    <ul class="space-y-3 text-sm text-gray-500">
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Team Accounts</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>API Access</li>
                        <li class="flex items-center gap-2"><svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>White-Label Reports</li>
                    </ul>
                </div>

            </div>
        </div>

        <!-- Simple CTA -->
        <div class="border-t border-gray-800">
            <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
                <h2 class="text-2xl sm:text-3xl font-bold mb-4">Ready to find your next project?</h2>
                <p class="text-gray-400 mb-8">Stop scrolling Reddit for ideas. We already did the work.</p>
                <a href="{{ route('business-plan-search.index') }}" wire:navigate
                   class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold py-4 px-10 rounded-xl transition-all duration-300 shadow-lg shadow-blue-500/25">
                    Browse All Ideas
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                    </svg>
                </a>
            </div>
        </div>

        <!-- Footer -->
        <footer class="border-t border-gray-800 py-8">
            <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
                    <p>© {{ date('Y') }} Business Finder. Built with AI, for AI builders.</p>
                    <div class="flex items-center gap-6">
                        <a href="{{ route('business-plan-search.index') }}" class="hover:text-gray-300 transition-colors">Search</a>
                        @guest
                            <a href="{{ route('login') }}" class="hover:text-gray-300 transition-colors">Sign In</a>
                            <a href="{{ route('register') }}" class="hover:text-gray-300 transition-colors">Register</a>
                        @endguest
                    </div>
                </div>
            </div>
        </footer>

    </div>

</body>
</html>
