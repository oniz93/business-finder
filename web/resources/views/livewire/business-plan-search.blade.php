<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Advanced Business Plan Search</h1>

    <form method="POST" action="{{ route('business-plan-search.post') }}">
        @csrf
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8 p-6">
            <div class="mb-4">
                <label for="search" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Search</label>
                <input type="text" name="search" value="{{ old('search', $search) }}" id="search" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                    <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Industry</label>
                    <input type="text" name="industry" value="{{ old('industry', $industry) }}" id="industry" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="marketSize" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Market Size</label>
                    <input type="text" name="marketSize" value="{{ old('marketSize', $marketSize) }}" id="marketSize" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="sentiment" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Sentiment</label>
                    <input type="text" name="sentiment" value="{{ old('sentiment', $sentiment) }}" id="sentiment" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="requiredCapital" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Required Capital</label>
                    <input type="text" name="requiredCapital" value="{{ old('requiredCapital', $requiredCapital) }}" id="requiredCapital" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="timeToMarket" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Time to Market</label>
                    <input type="text" name="timeToMarket" value="{{ old('timeToMarket', $timeToMarket) }}" id="timeToMarket" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="technologyStack" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Technology Stack</label>
                    <input type="text" name="technologyStack" value="{{ old('technologyStack', $technologyStack) }}" id="technologyStack" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                </div>
                <div>
                    <label for="geographicRelevance" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Geographic Relevance</label>
                    <input type="text" name="geographicRelevance" value="{{ old('geographicRelevance', $geographicRelevance) }}" id="geographicRelevance" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
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
                        <a href="{{ route('business-plan', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
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
</div>