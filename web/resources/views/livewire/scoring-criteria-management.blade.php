<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Scoring Criteria Management</h1>

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

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6 mb-8">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $editingCriteriaId ? 'Edit Criteria' : 'Create New Criteria' }}</h2>
        <form wire:submit.prevent="{{ $editingCriteriaId ? 'updateCriteria' : 'createCriteria' }}">
            <div class="mb-4">
                <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
                <input type="text" wire:model.defer="name" id="name" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                @error('name') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
            </div>

            <div class="mb-4">
                <label for="criteriaJson" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Criteria Details (JSON)</label>
                <textarea wire:model.defer="criteriaJson" id="criteriaJson" rows="5" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"></textarea>
                @error('criteriaJson') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
            </div>

            <div class="mb-4">
                <label for="weight" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Weight (1-10)</label>
                <input type="number" wire:model.defer="weight" id="weight" min="1" max="10" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
                @error('weight') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
            </div>

            <div class="flex items-center justify-end mt-6">
                <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    {{ $editingCriteriaId ? 'Update Criteria' : 'Create Criteria' }}
                </button>
                @if ($editingCriteriaId)
                    <button type="button" wire:click="resetForm" class="ml-4 inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md shadow-sm text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Cancel Edit
                    </button>
                @endif
            </div>
        </form>
    </div>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Your Scoring Criteria</h2>
        @forelse ($criterias as $criteria)
            <div class="border border-gray-200 dark:border-gray-700 rounded-md p-4 mb-4">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100">{{ $criteria->name }}</h3>
                        <p class="text-gray-600 dark:text-gray-400">Weight: {{ $criteria->weight }}</p>
                        <p class="text-gray-600 dark:text-gray-400 text-sm">Details: {{ json_encode($criteria->criteria) }}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button wire:click="editCriteria({{ $criteria->id }})" class="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Edit
                        </button>
                        <button wire:click="deleteCriteria({{ $criteria->id }})" class="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        @empty
            <p class="text-gray-600 dark:text-gray-400">You haven't defined any scoring criteria yet.</p>
        @endforelse
    </div>
</div>