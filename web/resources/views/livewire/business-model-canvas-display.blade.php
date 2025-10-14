<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Business Model Canvas</h1>
        <button wire:click="exportToPdf" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
            Export to PDF
        </button>
    </div>

    @if ($canvasData)
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-gray-900 dark:text-gray-100">
                <!-- Key Partners -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Key Partners</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['key_partners'] ?? 'N/A' }}</p>
                </div>

                <!-- Key Activities -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Key Activities</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['key_activities'] ?? 'N/A' }}</p>
                </div>

                <!-- Key Resources -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Key Resources</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['key_resources'] ?? 'N/A' }}</p>
                </div>

                <!-- Value Propositions -->
                <div class="col-span-1 md:col-span-3 border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Value Propositions</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['value_propositions'] ?? 'N/A' }}</p>
                </div>

                <!-- Customer Relationships -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Customer Relationships</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['customer_relationships'] ?? 'N/A' }}</p>
                </div>

                <!-- Channels -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Channels</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['channels'] ?? 'N/A' }}</p>
                </div>

                <!-- Customer Segments -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Customer Segments</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['customer_segments'] ?? 'N/A' }}</p>
                </div>

                <!-- Cost Structure -->
                <div class="col-span-1 md:col-span-2 border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Cost Structure</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['cost_structure'] ?? 'N/A' }}</p>
                </div>

                <!-- Revenue Streams -->
                <div class="border border-gray-300 dark:border-gray-700 p-4 rounded-md">
                    <h2 class="text-xl font-semibold mb-2">Revenue Streams</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $canvasData['revenue_streams'] ?? 'N/A' }}</p>
                </div>
            </div>
        </div>
    @else
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <p class="text-gray-600 dark:text-gray-400">Business Model Canvas data not found.</p>
            </div>
        </div>
    @endif
</div>