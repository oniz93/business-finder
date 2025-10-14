<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    @if ($collection)
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">{{ $collection->name }}</h1>
                <p class="mt-2 text-gray-600 dark:text-gray-400">{{ $collection->description }}</p>

                <div class="mt-6">
                    <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Business Plans:</h2>
                    @forelse ($collection->businessPlans as $plan)
                        <div class="flex items-center justify-between py-2 border-t border-gray-200 dark:border-gray-700">
                            <a href="{{ route('business-plans.show', $plan->id) }}" class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300">{{ $plan->title }}</a>
                        </div>
                    @empty
                        <p class="text-gray-600 dark:text-gray-400">No business plans in this collection yet.</p>
                    @endforelse
                </div>
            </div>
        </div>
    @else
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <p class="text-gray-600 dark:text-gray-400">Collection not found or invalid link.</p>
            </div>
        </div>
    @endif
</div>