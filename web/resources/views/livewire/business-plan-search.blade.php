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

            <input type="hidden" name="sortBy" value="{{ old('sortBy', $sortBy) }}" id="sortBy">
            <input type="hidden" name="sortDirection" value="{{ old('sortDirection', $sortDirection) }}" id="sortDirection">

            <div class="mt-6 flex items-center space-x-4">
                <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Search
                </button>
                <span class="text-gray-700 dark:text-gray-300">Sort By:</span>
                <button type="button" onclick="document.getElementById('sortBy').value='created_at'; document.getElementById('sortDirection').value='{{ $sortBy === 'created_at' && $sortDirection === 'asc' ? 'desc' : 'asc' }}'; this.form.submit();" class="px-3 py-1 text-sm font-medium rounded-md {{ $sortBy === 'created_at' ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300' }}">
                    Date Created
                    @if ($sortBy === 'created_at')
                        @if ($sortDirection === 'asc') &uarr; @else &darr; @endif
                    @endif
                </button>
                <button type="button" onclick="document.getElementById('sortBy').value='total_ups'; document.getElementById('sortDirection').value='{{ $sortBy === 'total_ups' && $sortDirection === 'asc' ? 'desc' : 'asc' }}'; this.form.submit();" class="px-3 py-1 text-sm font-medium rounded-md {{ $sortBy === 'total_ups' ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300' }}">
                    Popularity
                    @if ($sortBy === 'total_ups')
                        @if ($sortDirection === 'asc') &uarr; @else &darr; @endif
                    @endif
                </button>
            </div>
        </div>
    </form>

    <div class="mt-8">
        @forelse ($businessPlans as $plan)
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-6">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ $plan->title }}</h2>
                    <p class="text-gray-600 dark:text-gray-400">{{ $plan->summary }}</p>
                    <div class="mt-4 flex justify-end">
                        <a href="/business-plans/{{ $plan->id }}" wire:navigate class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
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