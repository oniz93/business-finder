<div class="max-w-4xl mx-auto py-10 sm:px-6 lg:px-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Pitch Deck</h1>
        <button onclick="enterPresentationMode()" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
            Presentation Mode
        </button>
    </div>

    @if ($deckData)
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
            <div class="space-y-8 text-gray-900 dark:text-gray-100">
                <!-- Problem -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Problem</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['problem'] ?? 'N/A' }}</p>
                </div>

                <!-- Solution -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Solution</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['solution'] ?? 'N/A' }}</p>
                </div>

                <!-- Market Size -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Market Size</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['market_size'] ?? 'N/A' }}</p>
                </div>

                <!-- Competition -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Competition</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['competition'] ?? 'N/A' }}</p>
                </div>

                <!-- Team -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Team</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['team'] ?? 'N/A' }}</p>
                </div>

                <!-- Financial Projections -->
                <div>
                    <h2 class="text-2xl font-semibold mb-2">Financial Projections</h2>
                    <p class="text-gray-700 dark:text-gray-300">{{ $deckData['financial_projections'] ?? 'N/A' }}</p>
                </div>
            </div>
        </div>
    @else
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg">
            <div class="p-6 sm:px-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <p class="text-gray-600 dark:text-gray-400">Pitch Deck data not found.</p>
            </div>
        </div>
    @endif
</div>