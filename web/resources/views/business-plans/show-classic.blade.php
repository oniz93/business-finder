<x-app-layout>
    <x-slot name="header">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="font-bold text-3xl text-gray-900 dark:text-white leading-tight">
                    {{ $plan->title }}
                </h2>
                <div class="mt-2 flex flex-wrap items-center gap-2">
                    @if($plan->subreddit)
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                             r/{{ $plan->subreddit }}
                        </span>
                    @endif
                    <p class="text-sm text-gray-600 dark:text-gray-400 flex items-center">
                        Viability Score: <span class="ml-1 inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">{{ $plan->viability_score > 10 ? $plan->viability_score / 10 : $plan->viability_score }}/10</span>
                    </p>
                </div>
            </div>
        </div>
    </x-slot>

    <div class="py-8 sm:py-12 bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 min-h-screen">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 space-y-8">
            @auth
                @if(in_array(auth()->user()->plan, ['innovator', 'enterprise']))
                    {{--<div class="mb-6 flex justify-end space-x-4">
                        <a href="/business-plans/{{ $plan->id }}/canvas" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                            View Canvas
                        </a>
                        <a href="/business-plans/{{ $plan->id }}/pitch-deck" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                            View Pitch Deck
                        </a>
                        <a href="/business-plans/{{ $plan->id }}/financial-projections" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                            Financial Projections
                        </a>
                        <a href="/business-plans/{{ $plan->id }}/edit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Edit Business Plan
                        </a>
                        <button onclick="Livewire.dispatchTo('save-to-collection-modal', 'openModal', { businessPlanId: {{ $plan->id }} })" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Save to Collection
                        </button>
                    </div>--}}
                @endif
            @endauth

            <!-- Hero Section - Executive Summary -->
            <div class="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-blue-700 dark:to-indigo-800 rounded-2xl shadow-2xl overflow-hidden border border-blue-500/20 dark:border-blue-400/20 transform transition hover:scale-[1.01] duration-300">
                <div class="p-8 sm:p-12">
                    <div class="flex items-center mb-6">
                        <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-4">
                            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <h3 class="text-2xl sm:text-3xl font-bold text-white">Executive Summary</h3>
                    </div>
                    <div class="prose prose-invert prose-lg max-w-none text-blue-50 dark:text-blue-100 leading-relaxed">{!! Str::markdown($plan->executive_summary ?? '') !!}</div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">

                <!-- Problem Card -->
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden hover:shadow-2xl dark:hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-200 dark:border-gray-700">
                    <div class="bg-gradient-to-r from-red-500 to-pink-600 dark:from-red-600 dark:to-pink-700 p-6">
                        <div class="flex items-center">
                            <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                </svg>
                            </div>
                            <h3 class="text-xl font-bold text-white">The Problem</h3>
                        </div>
                    </div>
                    <div class="p-6">
                        <div class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed">{!! Str::markdown($plan->problem ?? '') !!}</div>
                    </div>
                </div>

                <!-- Solution Card -->
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden hover:shadow-2xl dark:hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-200 dark:border-gray-700">
                    <div class="bg-gradient-to-r from-green-500 to-emerald-600 dark:from-green-600 dark:to-emerald-700 p-6">
                        <div class="flex items-center">
                            <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                                </svg>
                            </div>
                            <h3 class="text-xl font-bold text-white">Our Solution</h3>
                        </div>
                    </div>
                    <div class="p-6">
                        <div class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed">{!! Str::markdown($plan->solution ?? '') !!}</div>
                    </div>
                </div>
            </div>
            @auth
                @if(in_array(auth()->user()->plan, ['founder', 'innovator', 'enterprise']))
                    <!-- Market Analysis -->
                    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                        <div class="bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-700 dark:to-indigo-700 p-6">
                            <div class="flex items-center">
                                <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-2xl font-bold text-white">Market Analysis</h3>
                            </div>
                        </div>
                        <div class="p-8">
                            @foreach($plan->market_analysis as $key => $value)
                                <div class="mb-6 last:mb-0 pb-6 last:pb-0 border-b last:border-b-0 border-gray-200 dark:border-gray-700">
                                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                        <span class="w-2 h-2 bg-purple-500 dark:bg-purple-400 rounded-full mr-2"></span>
                                        {{ ucfirst(str_replace('_', ' ', $key)) }}
                                    </h4>
                                    @if(is_array($value))
                                        <ul class="space-y-2">
                                            @foreach($value as $item)
                                                <li class="flex items-start text-gray-700 dark:text-gray-300 prose prose-invert max-w-none">
                                                    <svg class="w-5 h-5 text-purple-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                                    </svg>
                                                    <span>{!! Str::markdown($item ?? '') !!}</span>
                                                </li>
                                            @endforeach
                                        </ul>
                                    @else
                                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 pl-4 leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                    @endif
                                </div>
                            @endforeach
                        </div>
                    </div>

                    <!-- Competition -->
                    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                        <div class="bg-gradient-to-r from-orange-500 to-red-600 dark:from-orange-600 dark:to-red-700 p-6">
                            <div class="flex items-center">
                                <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-2xl font-bold text-white">Competitive Landscape</h3>
                            </div>
                        </div>
                        <div class="p-8">
                            @foreach($plan->competition as $key => $value)
                                <div class="mb-6 last:mb-0 pb-6 last:pb-0 border-b last:border-b-0 border-gray-200 dark:border-gray-700">
                                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                        <span class="w-2 h-2 bg-orange-500 dark:bg-orange-400 rounded-full mr-2"></span>
                                        {{ ucfirst(str_replace('_', ' ', $key)) }}
                                    </h4>
                                    @if(is_array($value))
                                        <ul class="space-y-2">
                                            @foreach($value as $item)
                                                <li class="flex items-start text-gray-700 dark:text-gray-300 prose prose-invert max-w-none">
                                                    <svg class="w-5 h-5 text-orange-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
                                                    </svg>
                                                    <span>{!! Str::markdown($item ?? '') !!}</span>
                                                </li>
                                            @endforeach
                                        </ul>
                                    @else
                                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 pl-4 leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                    @endif
                                </div>
                            @endforeach
                        </div>
                    </div>

                    <!-- Marketing Strategy -->
                    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                        <div class="bg-gradient-to-r from-cyan-500 to-blue-600 dark:from-cyan-600 dark:to-blue-700 p-6">
                            <div class="flex items-center">
                                <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-2xl font-bold text-white">Marketing Strategy</h3>
                            </div>
                        </div>
                        <div class="p-8">
                            @foreach($plan->marketing_strategy as $key => $value)
                                <div class="mb-6 last:mb-0 pb-6 last:pb-0 border-b last:border-b-0 border-gray-200 dark:border-gray-700">
                                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                        <span class="w-2 h-2 bg-cyan-500 dark:bg-cyan-400 rounded-full mr-2"></span>
                                        {{ ucfirst(str_replace('_', ' ', $key)) }}
                                    </h4>
                                    @if(is_array($value))
                                        <ul class="space-y-2">
                                            @foreach($value as $item)
                                                <li class="flex items-start text-gray-700 dark:text-gray-300 prose prose-invert max-w-none">
                                                    <svg class="w-5 h-5 text-cyan-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                                    </svg>
                                                    <span>{!! Str::markdown($item ?? '') !!}</span>
                                                </li>
                                            @endforeach
                                        </ul>
                                    @else
                                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 pl-4 leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                    @endif
                                </div>
                            @endforeach
                        </div>
                    </div>



                    <!-- Financial Projections -->
                    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                        <div class="bg-gradient-to-r from-emerald-500 to-teal-600 dark:from-emerald-600 dark:to-teal-700 p-6">
                            <div class="flex items-center">
                                <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                                <h3 class="text-2xl font-bold text-white">Financial Projections</h3>
                            </div>
                        </div>
                        <div class="p-8">
                            @foreach($plan->financial_projections as $key => $value)
                                <div class="mb-6 last:mb-0 pb-6 last:pb-0 border-b last:border-b-0 border-gray-200 dark:border-gray-700">
                                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                        <span class="w-2 h-2 bg-emerald-500 dark:bg-emerald-400 rounded-full mr-2"></span>
                                        {{ ucfirst(str_replace('_', ' ', $key)) }}
                                    </h4>
                                    @if(is_array($value))
                                        <ul class="space-y-2">
                                            @foreach($value as $item)
                                                <li class="flex items-start text-gray-700 dark:text-gray-300 prose prose-invert max-w-none">
                                                    <svg class="w-5 h-5 text-emerald-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                                    </svg>
                                                    <span>{!! Str::markdown($item ?? '') !!}</span>
                                                </li>
                                            @endforeach
                                        </ul>
                                    @else
                                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 pl-4 leading-relaxed">{!! Str::markdown($value ?? '') !!}</div>
                                    @endif
                                </div>
                            @endforeach
                        </div>
                    </div>

                @endif

                @if(in_array(auth()->user()->plan, ['innovator', 'enterprise']))
                    <div x-data="{ open: false }">
                        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg dark:shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                            <div @click="open = !open" class="bg-gradient-to-r from-gray-500 to-gray-600 dark:from-gray-600 dark:to-gray-700 p-6 cursor-pointer flex justify-between items-center hover:from-gray-600 hover:to-gray-700 dark:hover:from-gray-700 dark:hover:to-gray-800 transition-colors">
                                <div class="flex items-center">
                                    <div class="p-2 bg-white/10 dark:bg-white/5 rounded-lg mr-3">
                                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
                                        </svg>
                                    </div>
                                    <h3 class="text-2xl font-bold text-white">Raw Data Insights</h3>
                                </div>
                                <svg x-show="!open" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                <svg x-show="open" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
                            </div>
                            <div x-show="open" x-transition:enter="transition ease-out duration-300" x-transition:enter-start="opacity-0 transform scale-90" x-transition:enter-end="opacity-100 transform scale-100" x-transition:leave="transition ease-in duration-300" x-transition:leave-start="opacity-100 transform scale-100" x-transition:leave-end="opacity-0 transform scale-90" class="p-6 bg-gray-700 dark:bg-gray-700 rounded-lg border border-gray-600 dark:border-gray-600">
                                <dl class="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-6">
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Subreddit</dt>
                                        <dd class="text-lg font-semibold text-white dark:text-gray-100">{{ $plan->subreddit }}</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Cluster ID</dt>
                                        <dd class="text-lg font-semibold text-white dark:text-gray-100">{{ $plan->cluster_id }}</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Message Count</dt>
                                        <dd class="text-lg font-semibold text-white dark:text-gray-100">{{ $plan->message_count }}</dd>
                                    </div>

                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Viable Business?</dt>
                                        <dd class="text-lg font-semibold {{ $plan->is_viable_business ? 'text-green-400 dark:text-green-300' : 'text-red-400 dark:text-red-300' }}">
                                            {{ $plan->is_viable_business ? 'Yes' : 'No' }}
                                        </dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Viability Score</dt>
                                        <dd class="text-lg font-semibold text-white dark:text-gray-100">{{ $plan->viability_score > 10 ? $plan->viability_score / 10 : $plan->viability_score }}/10</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">SaaS?</dt>
                                        <dd class="text-lg font-semibold {{ $plan->is_saas ? 'text-blue-400 dark:text-blue-300' : 'text-gray-400 dark:text-gray-500' }}">
                                            {{ $plan->is_saas ? 'Yes' : 'No' }}
                                        </dd>
                                    </div>

                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Solo Entrepreneur?</dt>
                                        <dd class="text-lg font-semibold {{ $plan->is_solo_entrepreneur_possible ? 'text-green-400 dark:text-green-300' : 'text-yellow-400 dark:text-yellow-300' }}">
                                            {{ $plan->is_solo_entrepreneur_possible ? 'Yes' : 'No' }}
                                        </dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Total Ups</dt>
                                        <dd class="text-lg font-semibold text-green-400 dark:text-green-300">{{ $plan->total_ups }}</dd>
                                    </div>
                                    <div class="sm:col-span-1">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-1">Total Downs</dt>
                                        <dd class="text-lg font-semibold text-red-400 dark:text-red-300">{{ $plan->total_downs }}</dd>
                                    </div>

                                    <div class="sm:col-span-3">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">Cluster Summary</dt>
                                        <dd class="text-base text-gray-100 dark:text-gray-200 prose prose-invert max-w-none bg-gray-600 dark:bg-gray-700 rounded-lg p-4 border border-gray-500 dark:border-gray-600">
                                            {!! Str::markdown($plan->cluster_summary ?? 'No summary available.') !!}
                                        </dd>
                                    </div>

                                    <div class="sm:col-span-3">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">Original Cluster Texts (Combined)</dt>
                                        <dd class="text-xs text-gray-200 dark:text-gray-300 font-mono bg-gray-800 dark:bg-gray-900 p-4 rounded-lg max-h-64 overflow-y-auto whitespace-pre-wrap border border-gray-700 dark:border-gray-800">
                                            {{ $plan->texts_combined }}
                                        </dd>
                                    </div>

                                    <div class="sm:col-span-3">
                                        <dt class="text-sm font-medium text-gray-300 dark:text-gray-400 mb-2">Message IDs</dt>
                                        <dd class="text-xs text-gray-300 dark:text-gray-400 break-all font-mono bg-gray-800 dark:bg-gray-900 p-3 rounded border border-gray-700 dark:border-gray-800">
                                            {{ is_array($plan->message_ids) ? implode(', ', $plan->message_ids) : $plan->message_ids }}
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                            @endif

                            @endauth

                            <!-- Call to Action -->
                            <div class="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-2xl overflow-hidden border border-indigo-500/20 dark:border-indigo-400/20">
                                <div class="p-8 sm:p-12 text-center">
                                    <svg class="w-16 h-16 text-white mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                    </svg>
                                    <h3 class="text-3xl font-bold text-white mb-4">Ready to Take Action?</h3>
                                    <div class="prose prose-invert max-w-none text-xl text-purple-50 leading-relaxed mx-auto">{!! Str::markdown($plan->call_to_action ?? '') !!}</div>
                                </div>
                            </div>

                        </div>
                        @auth
                            <div class="space-y-8">
                                @livewire('save-to-collection-modal', ['businessPlanId' => $plan->id])
                                @livewire('business-plan-feedback', ['businessPlanId' => $plan->id])
                            </div>
                        @endauth
                    </div>
</x-app-layout>
