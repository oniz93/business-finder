<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Advanced Business Plan Search</h1>

    @persist('business-plan-search-results')
    <form method="GET" action="{{ route('business-plan-search.index') }}">
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8 p-6">
            <div class="mb-4">
                <label for="search" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Search</label>
                <input type="text" name="search" value="{{ old('search', $search) }}" id="search" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                    <label for="subreddit" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Subreddit</label>
                    <input type="text" name="subreddit" value="{{ old('subreddit', $subreddit) }}" id="subreddit" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="viability_score_min" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Min Viability Score</label>
                    <input type="number" name="viability_score_min" value="{{ old('viability_score_min', $viability_score_min) }}" id="viability_score_min" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="viability_score_max" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Max Viability Score</label>
                    <input type="number" name="viability_score_max" value="{{ old('viability_score_max', $viability_score_max) }}" id="viability_score_max" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
            </div>

            <div class="mt-6 flex items-center space-x-4">
                <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Search
                </button>
            </div>
        </div>
    </form>

    <div class="mt-8">
        @forelse ($businessPlans as $plan)
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-6">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
                        <div>
                            <div class="flex items-center gap-2 mb-2">
                                @if($plan->subreddit)
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-500/20 dark:text-orange-400 border border-orange-200 dark:border-orange-500/30">
                                        r/{{ $plan->subreddit }}
                                    </span>
                                @endif
                                @if($plan->viability_score)
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400 border border-green-200 dark:border-green-500/30">
                                        Score: {{ $plan->viability_score > 10 ? $plan->viability_score / 10 : $plan->viability_score }}
                                    </span>
                                @endif
                            </div>
                            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $plan->title }}</h2>
                        </div>
                    </div>
                    
                    <div class="prose dark:prose-invert max-w-none text-gray-600 dark:text-gray-400 mb-6">
                        {{ Str::limit($plan->executive_summary ?? $plan->summary, 250) }}
                    </div>

                    <div class="flex justify-end">
                        <a href="/business-plans/{{ $plan->id }}" wire:navigate class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                            View Details
                        </a>
                    </div>
                </div>
            </div>
        @empty
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <p class="text-gray-600 dark:text-gray-400">No business plans found matching your criteria.</p>
                </div>
            </div>
        @endforelse

        <div class="mt-8">
            {{ $businessPlans->links() }}
        </div>
    </div>
    @endpersist
</div>