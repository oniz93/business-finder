<x-app-layout>
    <x-slot name="header">
        <div class="flex items-center justify-between">
            <div>
                <nav class="flex mb-2" aria-label="Breadcrumb">
                    <ol role="list" class="flex items-center space-x-2">
                        <li>
                            <div class="flex items-center">
                                <span class="text-sm font-medium text-gray-600 dark:text-gray-400">Business Plan</span>
                            </div>
                        </li>
                        @if($plan->subreddit)
                            <li>
                                <div class="flex items-center">
                                    <svg class="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-gray-600" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                                        <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
                                    </svg>
                                    <a href="https://reddit.com/r/{{ $plan->subreddit }}" target="_blank" class="ml-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors">r/{{ $plan->subreddit }}</a>
                                </div>
                            </li>
                        @endif
                    </ol>
                </nav>
                <h2 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
                    {{ $plan->title }}
                </h2>
            </div>
            <div class="hidden lg:flex items-center gap-3">
                <a href="{{ route('business-plan', ['businessPlan' => $plan->id, 'theme' => 'classic']) }}"

                   class="inline-flex items-center px-4 py-2.5 border border-gray-300 dark:border-gray-600 shadow-sm text-sm font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:ring-offset-gray-900 transition-all">
                    <svg class="-ml-1 mr-2 h-4 w-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Switch to Classic
                </a>
            </div>
        </div>
    </x-slot>

    <div class="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-white dark:from-gray-900 dark:via-gray-950 dark:to-gray-900">
        <main class="py-8 lg:py-12">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

                <!-- Top Meta & Score Card -->
                <div class="mb-10 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                    <div class="p-6 lg:p-8">
                        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                            <!-- Viability Score -->
                            <div class="flex items-center gap-5">
                                <div class="relative h-20 w-20 flex items-center justify-center">
                                    <svg class="h-20 w-20 transform -rotate-90" viewBox="0 0 36 36">
                                        <path class="stroke-current text-gray-200 dark:text-gray-700" fill="none" stroke-width="2.5" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    </svg>
                                    <svg class="absolute h-20 w-20 transform -rotate-90 {{ $plan->viability_score >= 7 ? 'text-emerald-500' : ($plan->viability_score >= 4 ? 'text-amber-500' : 'text-rose-500') }}" viewBox="0 0 36 36">
                                        <path class="stroke-current" stroke-dasharray="{{ $plan->viability_score * 10 }}, 100" fill="none" stroke-width="2.5" stroke-linecap="round" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    </svg>
                                    <span class="absolute text-xl font-bold text-gray-900 dark:text-white">{{ $plan->viability_score }}</span>
                                </div>
                                <div>
                                    <span class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Viability Score</span>
                                    <span class="block text-base font-semibold {{ $plan->viability_score >= 7 ? 'text-emerald-600 dark:text-emerald-400' : ($plan->viability_score >= 4 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400') }}">
                                        {{ $plan->viability_score >= 7 ? 'High Potential' : ($plan->viability_score >= 4 ? 'Moderate Potential' : 'Risky Venture') }}
                                    </span>
                                </div>
                            </div>

                            <!-- Quick Tags -->
                            <div class="flex flex-wrap gap-2">
                                @if($plan->is_saas)
                                    <span class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                                        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20"><path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z"/><path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z"/><path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z"/></svg>
                                        SaaS
                                    </span>
                                @endif
                                @if($plan->is_solo_entrepreneur_possible)
                                    <span class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                                        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/></svg>
                                        Solo Friendly
                                    </span>
                                @endif
                                @if($plan->is_viable_business)
                                    <span class="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                                        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
                                        Viable
                                    </span>
                                @endif
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Executive Summary -->
                <section class="mb-10">
                    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                        <div class="px-6 py-5 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-blue-100 dark:border-blue-900/30">
                            <h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
                                <svg class="w-6 h-6 mr-2 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                </svg>
                                Executive Summary
                            </h3>
                        </div>
                        <div class="p-6 lg:p-8">
                            <div class="prose prose-lg prose-gray dark:prose-invert max-w-none leading-relaxed">
                                {!! Str::markdown($plan->executive_summary ?? '') !!}
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Problem & Solution -->
                <section class="mb-10">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- The Problem -->
                        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border-l-4 border-rose-500 dark:border-rose-400 overflow-hidden backdrop-blur-sm hover:shadow-xl transition-shadow duration-300">
                            <div class="px-6 py-5 bg-gradient-to-r from-rose-50 to-red-50 dark:from-rose-900/20 dark:to-red-900/20 border-b border-rose-100 dark:border-rose-900/30">
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center">
                                    <svg class="w-5 h-5 mr-2 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                                    </svg>
                                    The Problem
                                </h3>
                            </div>
                            <div class="p-6">
                                <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">
                                    {!! Str::markdown($plan->problem ?? '') !!}
                                </div>
                            </div>
                        </div>

                        <!-- The Solution -->
                        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border-l-4 border-emerald-500 dark:border-emerald-400 overflow-hidden backdrop-blur-sm hover:shadow-xl transition-shadow duration-300">
                            <div class="px-6 py-5 bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 border-b border-emerald-100 dark:border-emerald-900/30">
                                <h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center">
                                    <svg class="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                    The Solution
                                </h3>
                            </div>
                            <div class="p-6">
                                <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">
                                    {!! Str::markdown($plan->solution ?? '') !!}
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                @auth
                    @if(in_array(auth()->user()->plan, ['founder', 'innovator', 'enterprise']))

                        <!-- Market Analysis -->
                        <section class="mb-10">
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                <div class="px-6 py-5 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border-b border-indigo-100 dark:border-indigo-900/30">
                                    <h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
                                        <svg class="w-6 h-6 mr-2 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                                        </svg>
                                        Market Analysis
                                    </h3>
                                </div>
                                <div class="p-6 lg:p-8 space-y-6">
                                    @foreach($plan->market_analysis as $key => $value)
                                        <div class="group">
                                            <h4 class="text-sm font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wide mb-3">
                                                {{ ucfirst(str_replace('_', ' ', $key)) }}
                                            </h4>
                                            <div class="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-5 border border-gray-200 dark:border-gray-700/50 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors duration-200">
                                                @if(is_array($value))
                                                    <ul class="space-y-3">
                                                        @foreach($value as $item)
                                                            <li class="flex items-start">
                                                                <svg class="h-5 w-5 text-indigo-500 dark:text-indigo-400 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                                                </svg>
                                                                <div class="prose prose-sm prose-gray dark:prose-invert max-w-none flex-1 leading-relaxed">{!! Str::markdown($item ?? '') !!}</div>
                                                            </li>
                                                        @endforeach
                                                    </ul>
                                                @else
                                                    <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                                @endif
                                            </div>
                                        </div>
                                    @endforeach
                                </div>
                            </div>
                        </section>

                        <!-- Competitive Landscape -->
                        <section class="mb-10">
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                <div class="px-6 py-5 bg-gradient-to-r from-amber-50 to-yellow-50 dark:from-amber-900/20 dark:to-yellow-900/20 border-b border-amber-100 dark:border-amber-900/30">
                                    <h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
                                        <svg class="w-6 h-6 mr-2 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                                        </svg>
                                        Competitive Landscape
                                    </h3>
                                </div>
                                <div class="p-6 lg:p-8 space-y-6">
                                    @foreach($plan->competition as $key => $value)
                                        <div>
                                            <h4 class="text-sm font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wide mb-3">
                                                {{ ucfirst(str_replace('_', ' ', $key)) }}
                                            </h4>
                                            @if(is_array($value))
                                                <ul class="space-y-3 pl-5 border-l-2 border-amber-200 dark:border-amber-800/50">
                                                    @foreach($value as $item)
                                                        <li class="pl-4">
                                                            <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">{!! Str::markdown($item ?? '') !!}</div>
                                                        </li>
                                                    @endforeach
                                                </ul>
                                            @else
                                                <div class="prose prose-gray dark:prose-invert max-w-none pl-5 border-l-2 border-amber-200 dark:border-amber-800/50 leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                            @endif
                                        </div>
                                    @endforeach
                                </div>
                            </div>
                        </section>

                        <!-- Marketing Strategy -->
                        <section class="mb-10">
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                <div class="px-6 py-5 bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20 border-b border-cyan-100 dark:border-cyan-900/30">
                                    <h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
                                        <svg class="w-6 h-6 mr-2 text-cyan-600 dark:text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/>
                                        </svg>
                                        Marketing Strategy
                                    </h3>
                                </div>
                                <div class="p-6 lg:p-8">
                                    <div class="grid grid-cols-1 gap-6">
                                        @foreach($plan->marketing_strategy as $key => $value)
                                            <div class="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700/50 hover:border-cyan-300 dark:hover:border-cyan-700 transition-colors duration-200">
                                                <h4 class="text-base font-bold text-gray-900 dark:text-white mb-4">
                                                    {{ ucfirst(str_replace('_', ' ', $key)) }}
                                                </h4>
                                                @if(is_array($value))
                                                    <ul class="space-y-3">
                                                        @foreach($value as $item)
                                                            <li class="flex items-start text-gray-700 dark:text-gray-300">
                                                                <span class="h-2 w-2 bg-cyan-500 dark:bg-cyan-400 rounded-full mr-3 mt-2 flex-shrink-0"></span>
                                                                <div class="prose prose-sm prose-gray dark:prose-invert max-w-none flex-1 leading-relaxed">{!! Str::markdown($item ?? '') !!}</div>
                                                            </li>
                                                        @endforeach
                                                    </ul>
                                                @else
                                                    <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                                @endif
                                            </div>
                                        @endforeach
                                    </div>
                                </div>
                            </div>
                        </section>

                        <!-- Financial Projections -->
                        <section class="mb-10">
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                <div class="px-6 py-5 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-b border-emerald-100 dark:border-emerald-900/30">
                                    <h3 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
                                        <svg class="w-6 h-6 mr-2 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                        </svg>
                                        Financial Projections
                                    </h3>
                                </div>
                                <div class="p-6 lg:p-8 space-y-6">
                                    @foreach($plan->financial_projections as $key => $value)
                                        <div>
                                            <h4 class="text-sm font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide mb-3">
                                                {{ ucfirst(str_replace('_', ' ', $key)) }}
                                            </h4>
                                            <div class="bg-emerald-50 dark:bg-emerald-900/20 border-l-4 border-emerald-500 dark:border-emerald-400 pl-5 py-3 rounded-r-lg">
                                                @if(is_array($value))
                                                    <ul class="space-y-2">
                                                        @foreach($value as $item)
                                                            <li class="text-gray-700 dark:text-gray-300">
                                                                <div class="prose prose-sm prose-gray dark:prose-invert max-w-none leading-relaxed">{!! Str::markdown($item ?? '') !!}</div>
                                                            </li>
                                                        @endforeach
                                                    </ul>
                                                @else
                                                    <div class="prose prose-gray dark:prose-invert max-w-none leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                                @endif
                                            </div>
                                        </div>
                                    @endforeach
                                </div>
                            </div>
                        </section>

                    @endif

                    @if(in_array(auth()->user()->plan, ['innovator', 'enterprise']))
                        <div class="mb-10" x-data="{ open: false }">
                            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                <button @click="open = !open" class="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                    <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">View Source Data & Insights</span>
                                    <svg :class="{ 'rotate-180': open }" class="h-5 w-5 text-gray-500 dark:text-gray-400 transform transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                <div x-show="open" x-collapse class="border-t border-gray-200 dark:border-gray-700/50">
                                    <div class="p-6 bg-gray-50 dark:bg-gray-900/50">
                                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-6 mb-6">
                                            <div>
                                                <span class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Cluster ID</span>
                                                <span class="block text-sm font-mono text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-700/50">{{ $plan->cluster_id }}</span>
                                            </div>
                                            <div>
                                                <span class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Messages</span>
                                                <span class="block text-lg font-bold text-gray-900 dark:text-white">{{ $plan->message_count }}</span>
                                            </div>
                                            <div class="col-span-2">
                                                <span class="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Sentiment</span>
                                                <div class="flex items-center gap-4">
                                                <span class="inline-flex items-center px-3 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 font-bold text-sm">
                                                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clip-rule="evenodd"/></svg>
                                                    {{ $plan->total_ups }}
                                                </span>
                                                    <span class="inline-flex items-center px-3 py-1 rounded-lg bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 font-bold text-sm">
                                                    <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd"/></svg>
                                                    {{ $plan->total_downs }}
                                                </span>
                                                </div>
                                            </div>
                                        </div>

                                        <div class="space-y-4 mt-6">
                                            <div>
                                                <h5 class="text-xs font-bold text-gray-900 dark:text-white uppercase mb-2">Original Context</h5>
                                                <div class="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700/50 max-h-60 overflow-y-auto">
                                                    <p class="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono leading-relaxed">{{ $plan->texts_combined }}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    @endif
                @endauth

                <!-- Action Footer -->
                <div class="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 rounded-2xl shadow-2xl border border-gray-700 dark:border-slate-700/50 overflow-hidden backdrop-blur-sm">
                    <div class="p-8 sm:p-12 text-center">
                        <div class="max-w-3xl mx-auto">
                            <h3 class="text-3xl font-bold text-white mb-4">Start This Business</h3>
                            <div class="prose prose-lg prose-invert mx-auto mb-8 text-gray-300 leading-relaxed">
                                {!! Str::markdown($plan->call_to_action ?? '') !!}
                            </div>

                            @auth
                                <div class="flex justify-center gap-4">
                                    <button onclick="Livewire.dispatchTo('save-to-collection-modal', 'openModal', { businessPlanId: {{ $plan->id }} })" class="inline-flex items-center px-8 py-4 border border-transparent text-base font-semibold rounded-lg shadow-lg text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:ring-offset-gray-900 transition-all transform hover:scale-105">
                                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
                                        </svg>
                                        Save to Collection
                                    </button>
                                </div>
                            @endauth
                        </div>
                    </div>
                </div>

            </div>
        </main>

        @auth
            @livewire('save-to-collection-modal', ['businessPlanId' => $plan->id])
            @livewire('business-plan-feedback', ['businessPlanId' => $plan->id])
        @endauth
    </div>
</x-app-layout>
