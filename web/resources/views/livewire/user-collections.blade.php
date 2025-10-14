<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">My Collections</h1>

    @forelse ($collections as $collection)
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ $collection->name }}</h2>
                <p class="mt-2 text-gray-600 dark:text-gray-400">{{ $collection->description }}</p>

                @if ($collection->shareable_link)
                    <div class="mt-4 flex items-center">
                        <p class="text-gray-600 dark:text-gray-400 mr-2">Shareable Link:</p>
                        <input type="text" value="{{ route('collections.share', $collection->shareable_link) }}" readonly
                               class="flex-grow px-2 py-1 text-sm border border-gray-300 dark:border-gray-700 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                               id="shareableLink-{{ $collection->id }}">
                        <button onclick="copyToClipboard('shareableLink-{{ $collection->id }}')"
                                class="ml-2 px-3 py-1 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Copy
                        </button>
                    </div>
                @endif

                <div class="mt-4">
                    <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Business Plans:</h3>
                    @forelse ($collection->businessPlans as $plan)
                        <div class="flex items-center justify-between py-2 border-t border-gray-200 dark:border-gray-700">
                            <a href="{{ route('business-plans.show', $plan->id) }}" class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300">{{ $plan->title }}</a>
                            {{-- Add actions like remove from collection if needed --}}
                        </div>
                    @empty
                        <p class="text-gray-600 dark:text-gray-400">No business plans in this collection yet.</p>
                    @endforelse
                </div>
            </div>
        </div>
    @empty
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <p class="text-gray-600 dark:text-gray-400">You haven't created any collections yet.</p>
            </div>
        </div>
    @endforelse
</div>