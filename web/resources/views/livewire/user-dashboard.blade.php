<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">My Dashboard</h1>

    <div wire:sortable="updateWidgetOrder" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        @forelse ($widgets as $widget)
            <div wire:sortable.item="{{ $widget->id }}" wire:key="widget-{{ $widget->id }}" class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6 cursor-grab">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $widget->name }}</h2>
                {{-- Render widget content based on type --}}
                @if ($widget->type === 'text')
                    <p class="text-gray-700 dark:text-gray-300">{{ $widget->settings['content'] ?? 'No content' }}</p>
                @elseif ($widget->type === 'link')
                    <a href="{{ $widget->settings['url'] ?? '#' }}" class="text-indigo-600 dark:text-indigo-400 hover:underline">{{ $widget->settings['text'] ?? 'Link' }}</a>
                @else
                    <p class="text-gray-700 dark:text-gray-300">Unknown widget type: {{ $widget->type }}</p>
                @endif
            </div>
        @empty
            <div class="col-span-full bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
                <p class="text-gray-600 dark:text-gray-400">You haven't added any widgets to your dashboard yet.</p>
            </div>
        @endforelse
    </div>

    @push('scripts')
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js"></script>
        <script>
            document.addEventListener('livewire:navigated', () => {
                const sortable = new Sortable(document.querySelector('[wire\\:sortable="updateWidgetOrder"]'), {
                    animation: 150,
                    onEnd: function (evt) {
                        const newOrder = Array.from(evt.from.children).map(item => item.getAttribute('wire:sortable.item'));
                        @this.call('updateWidgetOrder', newOrder);
                    },
                });
            });
        </script>
    @endpush
</div>