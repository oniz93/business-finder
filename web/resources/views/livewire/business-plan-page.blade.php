<div>
    @if ($plan)
        <div class="max-w-2xl mx-auto">
            <div class="bg-gray-800 shadow-lg rounded-lg p-6">
                <h2 class="text-2xl font-bold mb-2">{{ $plan->name }}</h2>
                <p class="text-gray-400">{{ $plan->description }}</p>
                <div class="mt-4">
                    <h3 class="text-lg font-bold">Problem</h3>
                    <p class="text-gray-400">{{ $plan->problem }}</p>
                </div>
                <div class="mt-4">
                    <h3 class="text-lg font-bold">Solution</h3>
                    <p class="text-gray-400">{{ $plan->solution }}</p>
                </div>
                <div class="mt-4">
                    <h3 class="text-lg font-bold">Market Analysis</h3>
                    <p class="text-gray-400">{{ $plan->market_analysis }}</p>
                </div>
                <div class="mt-4">
                    <h3 class="text-lg font-bold">Financial Projections</h3>
                    <p class="text-gray-400">{{ $plan->financial_projections }}</p>
                </div>
                <div class="mt-4">
                    <h3 class="text-lg font-bold">Team</h3>
                    <p class="text-gray-400">{{ $plan->team }}</p>
                </div>
            </div>
        </div>
    @else
        <div class="text-center">
            <p class="text-lg">Business plan not found.</p>
        </div>
    @endif
</div>