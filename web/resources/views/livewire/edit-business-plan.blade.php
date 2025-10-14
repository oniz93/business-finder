<div class="max-w-7xl mx-auto py-10 sm:px-6 lg:px-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Edit Business Plan: {{ $title }}</h1>

    <form wire:submit.prevent="save" class="bg-white dark:bg-gray-800 overflow-hidden shadow-xl sm:rounded-lg p-6">
        @if (session()->has('message'))
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
                <span class="block sm:inline">{{ session('message') }}</span>
            </div>
        @endif

        <div class="mb-4">
            <label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Title</label>
            <input type="text" wire:model.defer="title" id="title" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('title') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4">
            <label for="summary" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Summary</label>
            <textarea wire:model.defer="summary" id="summary" rows="3" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"></textarea>
            @error('summary') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4" wire:ignore>
            <label for="executive_summary" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Executive Summary</label>
            <textarea wire:model.defer="executive_summary" id="executive_summary" class="mt-1"></textarea>
            @error('executive_summary') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4" wire:ignore>
            <label for="problem" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Problem</label>
            <textarea wire:model.defer="problem" id="problem" class="mt-1"></textarea>
            @error('problem') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4" wire:ignore>
            <label for="solution" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Solution</label>
            <textarea wire:model.defer="solution" id="solution" class="mt-1"></textarea>
            @error('solution') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4">
            <label for="viability_score" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Viability Score</label>
            <input type="number" wire:model.defer="viability_score" id="viability_score" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('viability_score') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4" wire:ignore>
            <label for="viability_reasoning" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Viability Reasoning</label>
            <textarea wire:model.defer="viability_reasoning" id="viability_reasoning" class="mt-1"></textarea>
            @error('viability_reasoning') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        {{-- Market Analysis --}}
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-6 mb-4">Market Analysis</h2>
        <div class="mb-4">
            <label for="market_analysis_target_market" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Target Market (comma separated)</label>
            <input type="text" wire:model.defer="market_analysis_target_market" id="market_analysis_target_market" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('market_analysis_target_market') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4">
            <label for="market_analysis_market_size" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Market Size</label>
            <input type="text" wire:model.defer="market_analysis_market_size" id="market_analysis_market_size" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('market_analysis_market_size') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4">
            <label for="market_analysis_trends" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Trends (comma separated)</label>
            <input type="text" wire:model.defer="market_analysis_trends" id="market_analysis_trends" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('market_analysis_trends') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        {{-- Competition --}}
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-6 mb-4">Competition</h2>
        <div class="mb-4">
            <label for="competition_competitors" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Competitors (comma separated)</label>
            <input type="text" wire:model.defer="competition_competitors" id="competition_competitors" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('competition_competitors') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4">
            <label for="competition_direct_competitors" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Direct Competitors (comma separated)</label>
            <input type="text" wire:model.defer="competition_direct_competitors" id="competition_direct_competitors" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('competition_direct_competitors') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4">
            <label for="competition_indirect_competitors" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Indirect Competitors (comma separated)</label>
            <input type="text" wire:model.defer="competition_indirect_competitors" id="competition_indirect_competitors" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('competition_indirect_competitors') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4">
            <label for="competition_competitive_advantages" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Competitive Advantages (comma separated)</label>
            <input type="text" wire:model.defer="competition_competitive_advantages" id="competition_competitive_advantages" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('competition_competitive_advantages') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        {{-- Marketing Strategy --}}
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-6 mb-4">Marketing Strategy</h2>
        <div class="mb-4" wire:ignore>
            <label for="marketing_strategy" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Marketing Strategy (JSON)</label>
            <textarea wire:model.defer="marketing_strategy" id="marketing_strategy" class="mt-1"></textarea>
            @error('marketing_strategy') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        {{-- Management Team --}}
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-6 mb-4">Management Team</h2>
        <div class="mb-4" wire:ignore>
            <label for="management_team_description" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
            <textarea wire:model.defer="management_team_description" id="management_team_description" class="mt-1"></textarea>
            @error('management_team_description') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4" wire:ignore>
            <label for="management_team_roles" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Roles (JSON Array)</label>
            <textarea wire:model.defer="management_team_roles" id="management_team_roles" class="mt-1"></textarea>
            @error('management_team_roles') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        {{-- Financial Projections --}}
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-6 mb-4">Financial Projections</h2>
        <div class="mb-4">
            <label for="financial_projections_potential_monthly_revenue" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Potential Monthly Revenue</label>
            <input type="text" wire:model.defer="financial_projections_potential_monthly_revenue" id="financial_projections_potential_monthly_revenue" class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100">
            @error('financial_projections_potential_monthly_revenue') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4" wire:ignore>
            <label for="financial_projections_revenue_streams" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Revenue Streams (JSON Array)</label>
            <textarea wire:model.defer="financial_projections_revenue_streams" id="financial_projections_revenue_streams" class="mt-1"></textarea>
            @error('financial_projections_revenue_streams') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>
        <div class="mb-4" wire:ignore>
            <label for="financial_projections_cost_structure" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Cost Structure (JSON Array)</label>
            <textarea wire:model.defer="financial_projections_cost_structure" id="financial_projections_cost_structure" class="mt-1"></textarea>
            @error('financial_projections_cost_structure') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="mb-4" wire:ignore>
            <label for="call_to_action" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Call to Action</label>
            <textarea wire:model.defer="call_to_action" id="call_to_action" class="mt-1"></textarea>
            @error('call_to_action') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
        </div>

        <div class="flex items-center justify-end mt-6">
            <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Save Changes
            </button>
        </div>
    </form>
</div>

@push('scripts')
    <script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js" referrerpolicy="origin"></script>
    <script>
        function initializeTinyMCE(id) {
            tinymce.init({
                selector: '#' + id,
                plugins: 'advlist autolink lists link image charmap preview anchor',
                toolbar_mode: 'floating',
                tinycomments_mode: 'embedded',
                tinycomments_author: 'Author name',
                setup: function (editor) {
                    editor.on('change', function () {
                        @this.set(id, editor.getContent());
                    });
                    editor.on('init', function () {
                        editor.setContent(@this.get(id) || '');
                    });
                }
            });
        }

        document.addEventListener('livewire:navigated', () => {
            initializeTinyMCE('executive_summary');
            initializeTinyMCE('problem');
            initializeTinyMCE('solution');
            initializeTinyMCE('viability_reasoning');
            initializeTinyMCE('marketing_strategy');
            initializeTinyMCE('management_team_description');
            initializeTinyMCE('management_team_roles');
            initializeTinyMCE('financial_projections_revenue_streams');
            initializeTinyMCE('financial_projections_cost_structure');
            initializeTinyMCE('call_to_action');
        });
    </script>
@endpush