<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Team Management</h1>

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

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg mb-8 p-6">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Create New Team</h2>
        <form wire:submit.prevent="createTeam">
            <div class="flex items-center">
                <input type="text" wire:model.defer="newTeamName" placeholder="Team Name" class="flex-grow px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm dark:bg-gray-900 dark:text-gray-100">
                <button type="submit" class="ml-4 px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Create Team
                </button>
            </div>
            @error('newTeamName') <span class="text-red-500 text-xs mt-2 block">{{ $message }}</span> @enderror
        </form>
    </div>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Your Teams</h2>
        @forelse ($teams as $team)
            <div class="border border-gray-200 dark:border-gray-700 rounded-md p-4 mb-4">
                <div class="flex justify-between items-center">
                    <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100">{{ $team->name }}</h3>
                    <div class="flex space-x-2">
                        <a href="{{ route('teams.workspace', $team->id) }}" class="px-3 py-1 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                            View Workspace
                        </a>
                        <button wire:click="editTeam({{ $team->id }})" class="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                            Manage Members
                        </button>
                    </div>
                </div>

                @if ($editingTeamId === $team->id)
                    <div class="mt-4 p-4 border border-gray-300 dark:border-gray-700 rounded-md">
                        <h4 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Members</h4>
                        @forelse ($team->members as $member)
                            <div class="flex justify-between items-center py-1">
                                <span class="text-gray-700 dark:text-gray-300">{{ $member->name }} ({{ $member->email }})</span>
                                @if ($member->id !== Auth::id())
                                    <button wire:click="removeMember({{ $team->id }}, {{ $member->id }})" class="text-red-600 hover:text-red-900 text-sm">
                                        Remove
                                    </button>
                                @endif
                            </div>
                        @empty
                            <p class="text-gray-600 dark:text-gray-400">No members in this team yet.</p>
                        @endforelse

                        <h4 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-4 mb-2">Add Member</h4>
                        <form wire:submit.prevent="addMember({{ $team->id }})">
                            <div class="flex items-center">
                                <input type="email" wire:model.defer="newMemberEmail" placeholder="Member Email" class="flex-grow px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm dark:bg-gray-900 dark:text-gray-100">
                                <button type="submit" class="ml-4 px-4 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                                    Add
                                </button>
                            </div>
                            @error('newMemberEmail') <span class="text-red-500 text-xs mt-2 block">{{ $message }}</span> @enderror
                        </form>
                    </div>
                @endif
            </div>
        @empty
            <p class="text-gray-600 dark:text-gray-400">You haven't created any teams yet.</p>
        @endforelse
    </div>
</div>