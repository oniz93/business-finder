<x-app-layout>
    <x-slot name="header">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="font-bold text-3xl text-gray-900 dark:text-white leading-tight">
                    {{ $plan->title }}
                </h2>
                <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Viability Score: <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">{{ $plan->viability_score }}/10</span>
                </p>
            </div>
        </div>
    </x-slot>

    <div class="py-12 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 min-h-screen">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">

            @auth
                <div class="mb-6 flex justify-end space-x-4">
                    <a href="{{ route('business-plans.canvas', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                        View Canvas
                    </a>
                    <a href="{{ route('business-plans.pitch-deck', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                        View Pitch Deck
                    </a>
                    <a href="{{ route('business-plans.financial-projections', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                        Financial Projections
                    </a>
                    <a href="{{ route('business-plans.edit', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Edit Business Plan
                    </a>
                    <button onclick="Livewire.dispatchTo('save-to-collection-modal', 'openModal', { businessPlanId: {{ $plan->id }} })" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Save to Collection
                    </button>
                </div>
            @endauth

            <!-- Hero Section - Executive Summary -->
            <div class="mb-8 bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl shadow-2xl overflow-hidden">
                <div class="p-8 sm:p-12">
                    <div class="flex items-center mb-4">
                        <svg class="w-8 h-8 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Executive Summary</h3>
                    </div>
                    <div class="prose prose-invert max-w-none text-lg text-blue-50 leading-relaxed">{!! Str::markdown($plan->executive_summary ?? '') !!}</div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">

                <!-- Problem Card -->
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-shadow duration-300">
                    <div class="bg-gradient-to-r from-red-500 to-pink-600 p-6">
                        <div class="flex items-center">
                            <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                            </svg>
                            <h3 class="text-xl font-bold text-white">The Problem</h3>
                        </div>
                    </div>
                    <div class="p-6">
                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed">{!! Str::markdown($plan->problem ?? '') !!}</div>
                    </div>
                </div>

                <!-- Solution Card -->
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-shadow duration-300">
                    <div class="bg-gradient-to-r from-green-500 to-emerald-600 p-6">
                        <div class="flex items-center">
                            <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                            </svg>
                            <h3 class="text-xl font-bold text-white">Our Solution</h3>
                        </div>
                    </div>
                    <div class="p-6">
                        <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed">{!! Str::markdown($plan->solution ?? '') !!}</div>
                    </div>
                </div>
            </div>
            @auth
            @if(in_array(auth()->user()->plan, ['founder', 'innovator', 'enterprise']))
            <!-- Market Analysis -->
            <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-purple-600 to-indigo-600 p-6">
                    <div class="flex items-center">
                        <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Market Analysis</h3>
                    </div>
                </div>
                <div class="p-8">
                    @foreach($plan->market_analysis as $key => $value)
                        <div class="mb-6 last:mb-0">
                            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                <span class="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
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
            <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-orange-500 to-red-600 p-6">
                    <div class="flex items-center">
                        <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Competitive Landscape</h3>
                    </div>
                </div>
                <div class="p-8">
                    @foreach($plan->competition as $key => $value)
                        <div class="mb-6 last:mb-0">
                            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                <span class="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
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
            <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-cyan-500 to-blue-600 p-6">
                    <div class="flex items-center">
                        <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Marketing Strategy</h3>
                    </div>
                </div>
                <div class="p-8">
                    @foreach($plan->marketing_strategy as $key => $value)
                        <div class="mb-6 last:mb-0">
                            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                <span class="w-2 h-2 bg-cyan-500 rounded-full mr-2"></span>
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

            <!-- Management Team -->
            <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-teal-500 to-green-600 p-6">
                    <div class="flex items-center">
                        <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Management Team</h3>
                    </div>
                </div>
                <div class="p-8">
                    <div class="prose prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed mb-6">{!! Str::markdown($plan->management_team['description'] ?? '') !!}</div>

                    <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                        <span class="w-2 h-2 bg-teal-500 rounded-full mr-2"></span>
                        Key Roles
                    </h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        @foreach($plan->management_team['roles'] as $role)
                            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border-l-4 border-teal-500">
                                <h5 class="font-bold text-gray-900 dark:text-white mb-2 prose prose-invert max-w-none">{!! Str::markdown($role['role'] ?? '') !!}</h5>
                                <div class="prose prose-invert max-w-none text-sm text-gray-600 dark:text-gray-400">{!! Str::markdown($role['description'] ?? '') !!}</div>
                            </div>
                        @endforeach
                    </div>
                </div>
            </div>

            <!-- Financial Projections -->
            <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                <div class="bg-gradient-to-r from-emerald-500 to-teal-600 p-6">
                    <div class="flex items-center">
                        <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 class="text-2xl font-bold text-white">Financial Projections</h3>
                    </div>
                </div>
                <div class="p-8">
                    @foreach($plan->financial_projections as $key => $value)
                        <div class="mb-6 last:mb-0">
                            <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                                <span class="w-2 h-2 bg-emerald-500 rounded-full mr-2"></span>
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
                <div class="mb-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
                    <div @click="open = !open" class="bg-gradient-to-r from-gray-500 to-gray-600 p-6 cursor-pointer flex justify-between items-center">
                        <div class="flex items-center">
                            <svg class="w-7 h-7 text-white mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path>
                            </svg>
                            <h3 class="text-2xl font-bold text-white">Raw Data Insights</h3>
                        </div>
                        <svg x-show="!open" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        <svg x-show="open" class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
                    </div>
                    <div x-show="open" x-transition:enter="transition ease-out duration-300" x-transition:enter-start="opacity-0 transform scale-90" x-transition:enter-end="opacity-100 transform scale-100" x-transition:leave="transition ease-in duration-300" x-transition:leave-start="opacity-100 transform scale-100" x-transition:leave-end="opacity-0 transform scale-90" class="mt-4 p-4 bg-gray-700 rounded-lg">
                        <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-8">
                            <div class="sm:col-span-1">
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Subreddit</dt>
                                <dd class="mt-1 text-lg font-semibold text-gray-900 dark:text-white">{{ $plan->subreddit }}</dd>
                            </div>
                            <div class="sm:col-span-1">
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Cluster ID</dt>
                                <dd class="mt-1 text-lg font-semibold text-gray-900 dark:text-white">{{ $plan->cluster_id }}</dd>
                            </div>
                            <div class="sm:col-span-2">
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Original Summary</dt>
                                <dd class="mt-1 text-base text-gray-900 dark:text-white prose prose-invert max-w-none">{!! Str::markdown($plan->original_summary ?? '') !!}</dd>
                            </div>
                        </div>
                    </div>
                @endif

            @endauth

            <!-- Call to Action -->
            <div class="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-2xl overflow-hidden">
                <div class="p-8 sm:p-12 text-center">
                    <svg class="w-16 h-16 text-white mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                    <h3 class="text-3xl font-bold text-white mb-4">Ready to Take Action?</h3>
                    <div class="prose prose-invert max-w-none text-xl text-purple-50 leading-relaxed">{!! Str::markdown($plan->call_to_action ?? '') !!}</div>
                    <div class="prose prose-invert max-w-none text-xl text-purple-50 leading-relaxed">{!! Str::markdown($plan->call_to_action ?? '') !!}</div>
                </div>
            </div>

        </div>
        @auth
            @livewire('save-to-collection-modal', ['businessPlanId' => $plan->id])
            @livewire('business-plan-feedback', ['businessPlanId' => $plan->id])
        @endauth
    </div>
</x-app-layout>
