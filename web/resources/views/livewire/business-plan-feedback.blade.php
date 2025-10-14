<div class="mt-8 p-6 bg-white dark:bg-gray-800 shadow-xl sm:rounded-lg">
    <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Provide Feedback</h2>

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

    <form wire:submit.prevent="submitFeedback">
        <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Rating</label>
            <div class="mt-1 flex items-center space-x-2">
                @foreach (range(1, 5) as $i)
                    <label for="rating-{{ $i }}" class="cursor-pointer">
                        <input type="radio" id="rating-{{ $i }}" name="rating" wire:model.defer="rating" value="{{ $i }}" class="hidden">
                        <svg class="w-6 h-6 {{ $rating >= $i ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600' }} fill-current" viewBox="0 0 24 24">
                            <path d="M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279L12 18.896l-7.416 3.817 1.48-8.279L.001 9.306l8.332-1.151L12 .587z"/>
                        </svg>
                    </label>
                @endforeach
            </div>
            @error('rating') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4">
            <label for="comments" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Comments (Optional)</label>
            <textarea wire:model.defer="comments" id="comments" rows="4" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"></textarea>
            @error('comments') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="flex items-center justify-end">
            <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Submit Feedback
            </button>
        </div>
    </form>
</div>