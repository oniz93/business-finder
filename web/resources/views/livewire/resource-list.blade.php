<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Learning & Educational Resources</h1>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6 mb-8">
        <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 md:space-x-4">
            <div class="w-full md:w-1/2">
                <label for="search" class="sr-only">Search Resources</label>
                <input type="text" wire:model.live="search" id="search" placeholder="Search by title or description..." class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div class="w-full md:w-1/4">
                <label for="type" class="sr-only">Filter by Type</label>
                <select wire:model.live="type" id="type" class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:text-gray-100">
                    <option value="">All Types</option>
                    @foreach ($availableTypes as $availableType)
                        <option value="{{ $availableType }}">{{ Str::title($availableType) }}</option>
                    @endforeach
                </select>
            </div>
        </div>
    </div>

    <div class="mt-8">
        @forelse ($resources as $resource)
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-6">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ $resource->title }}</h2>
                    <p class="text-gray-600 dark:text-gray-400 mb-4">{{ $resource->description }}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-500 dark:text-gray-400">Type: {{ Str::title($resource->type) }}</span>
                        <a href="{{ $resource->url }}" target="_blank" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            View Resource
                        </a>
                    </div>
                </div>
            </div>
        @empty
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <p class="text-gray-600 dark:text-gray-400">No resources found matching your criteria.</p>
                </div>
            </div>
        @endforelse

        <div class="mt-8">
            {{ $resources->links() }}
        </div>
    </div>
</div>