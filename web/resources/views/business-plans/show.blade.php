<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 dark:text-gray-200 leading-tight">
            {{ $plan->title }}
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 space-y-6">
            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Executive Summary</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ $plan->executive_summary }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Problem</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ $plan->problem }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Solution</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ $plan->solution }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Market Analysis</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ implode(', ', $plan->market_analysis) }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Competition</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ implode(', ', $plan->competition) }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Marketing Strategy</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ implode(', ', $plan->marketing_strategy) }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Management Team</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ implode(', ', $plan->management_team) }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Financial Projections</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ implode(', ', $plan->financial_projections) }}</p>
                </div>
            </div>

            <div class="p-4 sm:p-8 bg-white dark:bg-gray-800 shadow sm:rounded-lg">
                <div class="max-w-xl">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">Call to Action</h3>
                    <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">{{ $plan->call_to_action }}</p>
                </div>
            </div>
        </div>
    </div>
</x-app-layout>
