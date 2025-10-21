<div>
    @if ($plan && $plan->exists)
        <div class="max-w-4xl mx-auto py-8">
            <div class="bg-gray-800 shadow-lg rounded-lg p-8 text-white">
                <h1 class="text-4xl font-bold mb-4">{{ $plan->title }}</h1>
                <p class="text-gray-400 text-lg mb-6">{{ $plan->summary }}</p>

                <div class="mb-6 flex justify-end space-x-4">
                    <a href="{{ route('business-plans.canvas', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                        View Canvas
                    </a>
                    <a href="{{ route('business-plans.pitch-deck', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                        View Pitch Deck
                    </a>
                    <a href="{{ route('business-plans.financial-projections', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                        Financial Projections
                    </a>
                    <a href="{{ route('business-plans.edit', $plan->id) }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Edit Business Plan
                    </a>
                    <button wire:click="$dispatchTo('save-to-collection-modal', 'openModal', { businessPlanId: {{ $plan->id }} })" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        Save to Collection
                    </button>
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Executive Summary</h2>
                    <p class="text-gray-300">{{ $plan->executive_summary }}</p>
                </div>

                @livewire('save-to-collection-modal', ['businessPlanId' => $plan->id])

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Problem</h2>
                    <p class="text-gray-300">{{ $plan->problem }}</p>
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Solution</h2>
                    <p class="text-gray-300">{{ $plan->solution }}</p>
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Viability</h2>
                    <p class="text-gray-300"><strong>Score:</strong> {{ $plan->viability_score }}</p>
                    <p class="text-gray-300"><strong>Reasoning:</strong> {{ $plan->viability_reasoning }}</p>
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Market Analysis</h2>
                    @if (isset($plan->market_analysis['target_market']) && is_array($plan->market_analysis['target_market']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Target Market</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->market_analysis['target_market'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                    @if (isset($plan->market_analysis['market_size']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Market Size</h3>
                        <p class="text-gray-300">{{ $plan->market_analysis['market_size'] }}</p>
                    @endif
                    @if (isset($plan->market_analysis['trends']) && is_array($plan->market_analysis['trends']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Trends</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->market_analysis['trends'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Competition</h2>
                    @if (isset($plan->competition['competitors']) && is_array($plan->competition['competitors']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Competitors</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->competition['competitors'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                    @if (isset($plan->competition['direct_competitors']) && is_array($plan->competition['direct_competitors']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Direct Competitors</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->competition['direct_competitors'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                    @if (isset($plan->competition['indirect_competitors']) && is_array($plan->competition['indirect_competitors']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Indirect Competitors</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->competition['indirect_competitors'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                    @if (isset($plan->competition['competitive_advantages']) && is_array($plan->competition['competitive_advantages']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Competitive Advantages</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->competition['competitive_advantages'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Marketing Strategy</h2>
                    @if (isset($plan->marketing_strategy) && is_array($plan->marketing_strategy))
                        @foreach ($plan->marketing_strategy as $key => $value)
                            @if (is_string($value))
                                <h3 class="text-xl font-semibold mt-4 mb-2">{{ Str::title(str_replace('_', ' ', $key)) }}</h3>
                                <p class="text-gray-300">{{ $value }}</p>
                            @elseif (is_array($value))
                                <h3 class="text-xl font-semibold mt-4 mb-2">{{ Str::title(str_replace('_', ' ', $key)) }}</h3>
                                <ul class="list-disc list-inside text-gray-300 ml-4">
                                    @foreach ($value as $item)
                                        <li>{{ $item }}</li>
                                    @endforeach
                                </ul>
                            @endif
                        @endforeach
                    @endif
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Management Team</h2>
                    @if (isset($plan->management_team['description']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Description</h3>
                        <p class="text-gray-300">{{ $plan->management_team['description'] }}</p>
                    @endif
                    @if (isset($plan->management_team['roles']) && is_array($plan->management_team['roles']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Roles</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                            @foreach ($plan->management_team['roles'] as $role)
                                <div class="bg-gray-700 p-4 rounded-lg">
                                    <p class="font-medium text-lg">{{ $role['role'] }}</p>
                                    <p class="text-gray-400 text-sm">{{ $role['description'] }}</p>
                                </div>
                            @endforeach
                        </div>
                    @endif
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Financial Projections</h2>
                    @if (isset($plan->financial_projections['potential_monthly_revenue']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Potential Monthly Revenue</h3>
                        <p class="text-gray-300">{{ $plan->financial_projections['potential_monthly_revenue'] }}</p>
                    @endif
                    @if (isset($plan->financial_projections['revenue_streams']) && is_array($plan->financial_projections['revenue_streams']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Revenue Streams</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->financial_projections['revenue_streams'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                    @if (isset($plan->financial_projections['cost_structure']) && is_array($plan->financial_projections['cost_structure']))
                        <h3 class="text-xl font-semibold mt-4 mb-2">Cost Structure</h3>
                        <ul class="list-disc list-inside text-gray-300 ml-4">
                            @foreach ($plan->financial_projections['cost_structure'] as $item)
                                <li>{{ $item }}</li>
                            @endforeach
                        </ul>
                    @endif
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Call to Action</h2>
                    <p class="text-gray-300">{{ $plan->call_to_action }}</p>
                </div>

                <div class="mb-6">
                    <h2 class="text-2xl font-semibold border-b-2 border-gray-700 pb-2 mb-4">Additional Details</h2>
                    <p class="text-gray-300"><strong>Subreddit:</strong> {{ $plan->subreddit }}</p>
                    <p class="text-gray-300"><strong>Total Upvotes:</strong> {{ $plan->total_ups }}</p>
                    <p class="text-gray-300"><strong>Total Downvotes:</strong> {{ $plan->total_downs }}</p>
                    <p class="text-gray-300"><strong>Cluster ID:</strong> {{ $plan->cluster_id }}</p>
                </div>

                <div x-data="{ open: false }" class="mb-6">
                    <button @click="open = !open" class="text-blue-400 hover:text-blue-300 focus:outline-none">
                        <span x-show="!open">Show Raw Data (IDs in Cluster, Texts)</span>
                        <span x-show="open">Hide Raw Data (IDs in Cluster, Texts)</span>
                    </button>
                    <div x-show="open" x-transition:enter="transition ease-out duration-300" x-transition:enter-start="opacity-0 transform scale-90" x-transition:enter-end="opacity-100 transform scale-100" x-transition:leave="transition ease-in duration-300" x-transition:leave-start="opacity-100 transform scale-100" x-transition:leave-end="opacity-0 transform scale-90" class="mt-4 p-4 bg-gray-700 rounded-lg">
                        @if (isset($plan->ids_in_cluster) && is_array($plan->ids_in_cluster))
                            <h3 class="text-xl font-semibold mb-2">IDs in Cluster</h3>
                            <pre class="text-gray-300 text-sm overflow-auto">{{ json_encode($plan->ids_in_cluster, JSON_PRETTY_PRINT) }}</pre>
                        @endif
                        @if (isset($plan->texts) && is_array($plan->texts))
                            <h3 class="text-xl font-semibold mt-4 mb-2">Texts (Markdown Rendered)</h3>
                            <div class="text-gray-300 text-sm overflow-auto prose prose-invert max-w-none">
                                @foreach ($plan->texts as $text)
                                    <div class="mb-8">
                                        {!! Str::markdown($text) !!}
                                    </div>
                                @endforeach
                            </div>
                        @endif
                    </div>
                </div>

            </div>
            @livewire('business-plan-feedback', ['businessPlanId' => $plan->id])
        </div>
    @else
        <div class="text-center py-12">
            <p class="text-lg text-gray-400">Business plan not found.</p>
        </div>
    @endif
</div>