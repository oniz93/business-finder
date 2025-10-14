<div class="max-w-4xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">{{ $product->name }}</h1>

    @if (session()->has('message'))
        <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
            <span class="block sm:inline">{{ session('message') }}</span>
        </div>
    @endif
    @if (session()->has('error'))
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <span class="block sm:inline">{{ session('error') }}</span>
        </div>
    @endif

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
        <div class="flex flex-col md:flex-row">
            <div class="md:w-1/2">
                <img class="w-full h-auto object-cover rounded-lg" src="{{ $product->image ?? 'https://via.placeholder.com/400x300' }}" alt="{{ $product->name }}">
            </div>
            <div class="md:w-1/2 md:ml-6 mt-4 md:mt-0">
                <p class="text-gray-600 dark:text-gray-400 text-lg mb-4">{{ $product->description }}</p>
                <p class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">${{ number_format($product->price, 2) }}</p>

                <button wire:click="purchase" class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Buy Now
                </button>
            </div>
        </div>
    </div>

    @livewire('product-reviews', ['productId' => $product->id])
</div>