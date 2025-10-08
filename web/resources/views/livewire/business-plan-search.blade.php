<div>
    <div class="flex justify-center">
        <input wire:model.live="search" type="text" placeholder="Search for business plans..." class="w-1/2 px-4 py-2 border border-gray-300 rounded-lg">
        <button wire:click="search" class="ml-2 px-4 py-2 bg-blue-500 text-white rounded-lg">Search</button>
    </div>

    <div class="mt-8">
        @if ($plans)
            @foreach ($plans as $plan)
                <div class="max-w-2xl mx-auto mb-4">
                    <div class="bg-gray-800 shadow-lg rounded-lg p-6">
                        <h2 class="text-2xl font-bold mb-2">{{ $plan->name }}</h2>
                        <p class="text-gray-400">{{ $plan->description }}</p>
                    </div>
                </div>
            @endforeach
        @endif
    </div>
</div>