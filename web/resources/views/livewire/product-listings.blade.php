<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Product Marketplace</h1>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6 mb-8">
        <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 md:space-x-4">
            <div class="w-full md:w-1/2">
                <label for="search" class="sr-only">Search Products</label>
                <input type="text" wire:model.live="search" id="search" placeholder="Search by product name or description..." class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            </div>
            <div class="w-full md:w-1/4">
                <label for="category" class="sr-only">Filter by Category</label>
                <select wire:model.live="category" id="category" class="mt-1 block w-full py-2 px-3 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:text-gray-100">
                    <option value="">All Categories</option>
                    @foreach ($availableCategories as $availableCategory)
                        <option value="{{ $availableCategory }}">{{ Str::title($availableCategory) }}</option>
                    @endforeach
                </select>
            </div>
        </div>
    </div>

    <div class="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        @forelse ($products as $product)
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
                <img class="w-full h-48 object-cover" src="{{ $product->image ?? 'https://via.placeholder.com/300x200' }}" alt="{{ $product->name }}">
                <div class="p-6">
                    <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ $product->name }}</h2>
                    <p class="text-gray-600 dark:text-gray-400 mb-4">{{ $product->description }}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-xl font-bold text-gray-900 dark:text-gray-100">${{ number_format($product->price, 2) }}</span>
                        <a href="{{ route('marketplace.show', $product->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            View Product
                        </a>
                    </div>
                </div>
            </div>
        @empty
            <div class="col-span-full bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
                <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <p class="text-gray-600 dark:text-gray-400">No products found in the marketplace.</p>
                </div>
            </div>
        @endforelse
    </div>

    <div class="mt-8">
        {{ $products->links() }}
    </div>
</div>