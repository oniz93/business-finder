<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Team Workspace: {{ $team->name }}</h1>

    <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Business Plans</h2>

        @forelse ($businessPlans as $plan)
            <div class="border border-gray-200 dark:border-gray-700 rounded-md p-4 mb-4">
                <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ $plan->title }}</h3>
                <p class="text-gray-600 dark:text-gray-400">{{ $plan->summary }}</p>
                <div class="mt-4 flex space-x-4">
                    <a href="{{ route('business-plan', $plan->id) }}" wire:navigate class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        View Details
                    </a>
                    <a href="{{ route('business-plans.edit', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Edit Plan
                    </a>
                </div>
            </div>
        @empty
            <p class="text-gray-600 dark:text-gray-400">No business plans found for this team.</p>
        @endforelse
    </div>
</div>