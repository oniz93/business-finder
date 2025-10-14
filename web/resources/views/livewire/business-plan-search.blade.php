<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Advanced Business Plan Search</h1>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8 p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
                <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Industry</label>
                <input type="text" wire:model.live="industry" id="industry" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="marketSize" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Market Size</label>
                <input type="text" wire:model.live="marketSize" id="marketSize" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="sentiment" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Sentiment</label>
                <input type="text" wire:model.live="sentiment" id="sentiment" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="requiredCapital" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Required Capital</label>
                <input type="text" wire:model.live="requiredCapital" id="requiredCapital" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="timeToMarket" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Time to Market</label>
                <input type="text" wire:model.live="timeToMarket" id="timeToMarket" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="technologyStack" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Technology Stack</label>
                <input type="text" wire:model.live="technologyStack" id="technologyStack" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div>
                <label for="geographicRelevance" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Geographic Relevance</label>
                <input type="text" wire:model.live="geographicRelevance" id="geographicRelevance" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
        </div>

        <div class="mt-6 flex items-center space-x-4">
            <span class="text-gray-700 dark:text-gray-300">Sort By:</span>
            <button wire:click="sortBy('created_at')" class="px-3 py-1 text-sm font-medium rounded-md {{ $sortBy === 'created_at' ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300' }}">
                Date Created
                @if ($sortBy === 'created_at')
                    @if ($sortDirection === 'asc') &uarr; @else &darr; @endif
                @endif
            </button>
            <button wire:click="sortBy('total_ups')" class="px-3 py-1 text-sm font-medium rounded-md {{ $sortBy === 'total_ups' ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300' }}">
                Popularity
                @if ($sortBy === 'total_ups')
                    @if ($sortDirection === 'asc') &uarr; @else &darr; @endif
                @endif
            </button>
        </div>
    </div>

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