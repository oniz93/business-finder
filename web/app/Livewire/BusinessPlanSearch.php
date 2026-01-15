<?php

namespace App\Livewire;

use App\Data\BusinessPlanDao;
use Illuminate\Pagination\LengthAwarePaginator;
use Livewire\Component;
use Livewire\WithPagination;
use Illuminate\Support\Facades\Log;
use Illuminate\Http\Request;

class BusinessPlanSearch extends Component
{
    use WithPagination;

    public $search = '';
    public $subreddit = '';
    public $viability_score_min = null;
    public $viability_score_max = null;

    public function updatedSearch() { session()->forget('random_search_results'); $this->resetPage(); }
    public function updatedSubreddit() { session()->forget('random_search_results'); $this->resetPage(); }
    public function updatedViabilityScoreMin() { session()->forget('random_search_results'); $this->resetPage(); }
    public function updatedViabilityScoreMax() { session()->forget('random_search_results'); $this->resetPage(); }

    protected $queryString = [
        'search' => ['except' => ''],
        'subreddit' => ['except' => ''],
        'viability_score_min' => ['except' => ''],
        'viability_score_max' => ['except' => ''],
        'page' => ['except' => 1],
    ];

    public function mount(Request $request)
    {
        // Populate properties from old input (after POST redirect) or GET request
        $this->search = old('search', $request->input('search', ''));
        $this->subreddit = old('subreddit', $request->input('subreddit', ''));
        $this->viability_score_min = old('viability_score_min', $request->input('viability_score_min'));
        $this->viability_score_max = old('viability_score_max', $request->input('viability_score_max'));
        
        $this->resetPage();
    }

    public function render(BusinessPlanDao $businessPlanDao)
    {
        $page = $this->getPage();
        $perPage = 10;
        
        // Define filters
        $hasFilters = !empty($this->search) || 
                      !empty($this->subreddit) || 
                      !empty($this->viability_score_min) || 
                      !empty($this->viability_score_max);

        if (!$hasFilters) {
            // Check if we already have a random list in session
            if (session()->has('random_search_results')) {
                $result = session('random_search_results');
            } else {
                // Get 50 random items and cache them for the session (to support pagination of randomness)
                $result = $businessPlanDao->getRandom(50);
                session(['random_search_results' => $result]);
            }
            
            // Slice for pagination since getRandom doesn't support offset naturally here
            $plans = array_slice($result['plans'], ($page - 1) * $perPage, $perPage);
            $total = $result['total'];
        } else {
            // Normal search logic
            $searchParams = [
                'search' => $this->search,
                'subreddit' => $this->subreddit,
                'viability_score_min' => $this->viability_score_min,
                'viability_score_max' => $this->viability_score_max,
                'from' => ($page - 1) * $perPage,
                'size' => $perPage,
            ];

            Log::info('BusinessPlanSearch: Search Params', $searchParams);
            $result = $businessPlanDao->search($searchParams);
            $plans = $result['plans'];
            $total = $result['total'];
        }

        Log::info('BusinessPlanSearch: Result Info', ['total' => $total, 'plans_count' => count($plans)]);

        $businessPlans = new LengthAwarePaginator(
            $plans,
            $total,
            $perPage,
            $page,
            ['path' => request()->url(), 'query' => request()->query()]
        );

        return view('livewire.business-plan-search', [
            'businessPlans' => $businessPlans,
        ]);
    }
}
