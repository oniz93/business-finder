<div class="relative ml-3" x-data="{ open: @entangle('showNotifications') }" @click.outside="open = false">
    <div>
        <button type="button" class="relative flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800" id="user-menu-button" aria-expanded="false" aria-haspopup="true" @click="open = ! open">
            <span class="sr-only">View notifications</span>
            <!-- Bell Icon -->
            <svg class="h-6 w-6 text-gray-400 hover:text-white" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.248 24.248 0 01-7.224 0m7.224 0d3.47 4.756 4.99 1.407m-4.99-1.407H12c-4.985 0-9.33-1.278-10.125-3.75M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            @if ($unreadNotifications->count() > 0)
                <span class="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-red-100 bg-red-600 rounded-full">{{ $unreadNotifications->count() }}</span>
            @endif
        </button>
    </div>

    <!-- Dropdown menu -->
    <div x-show="open" x-transition:enter="transition ease-out duration-100" x-transition:enter-start="transform opacity-0 scale-95" x-transition:enter-end="transform opacity-100 scale-100" x-transition:leave="transition ease-in duration-75" x-transition:leave-start="transform opacity-100 scale-100" x-transition:leave-end="transform opacity-0 scale-95" class="absolute right-0 z-10 mt-2 w-80 origin-top-right rounded-md bg-white dark:bg-gray-700 py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
        <div class="px-4 py-2 text-sm text-gray-700 dark:text-gray-200 flex justify-between items-center">
            <span>Notifications</span>
            @if ($unreadNotifications->count() > 0)
                <button wire:click="markAllAsRead" class="text-xs text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300">Mark all as read</button>
            @endif
        </div>
        @forelse ($unreadNotifications as $notification)
            <a href="#" wire:click="markAsRead('{{ $notification->id }}')" class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600" role="menuitem" tabindex="-1" id="user-menu-item-0">
                {{ $notification->data['message'] ?? 'New notification' }}
                <span class="block text-xs text-gray-500">{{ $notification->created_at->diffForHumans() }}</span>
            </a>
        @empty
            <span class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200">No new notifications.</span>
        @endforelse
    </div>
</div>