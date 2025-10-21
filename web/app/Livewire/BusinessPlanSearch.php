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
    public $sortBy = 'popularity';
    public $sortDirection = 'desc';

    protected $queryString = [
        'search' => ['except' => ''],
        'subreddit' => ['except' => ''],
        'viability_score_min' => ['except' => ''],
        'viability_score_max' => ['except' => ''],
        'sortBy' => [
            'except' => 'popularity',
            'as' => 'sort_by' // Alias for URL parameter
        ],
        'sortDirection' => [
            'except' => 'desc',
            'as' => 'sort_dir' // Alias for URL parameter
        ],
        'page' => ['except' => 1],
    ];

    public function mount(Request $request)
    {
        // Populate properties from old input (after POST redirect) or GET request
        $this->search = old('search', $request->input('search', ''));
        $this->subreddit = old('subreddit', $request->input('subreddit', ''));
        $this->viability_score_min = old('viability_score_min', $request->input('viability_score_min'));
        $this->viability_score_max = old('viability_score_max', $request->input('viability_score_max'));
        $this->sortBy = old('sortBy', $request->input('sortBy', 'popularity'));
        $this->sortDirection = old('sortDirection', $request->input('sortDirection', 'desc'));

        $this->resetPage();
    }

    public function render(BusinessPlanDao $businessPlanDao)
    {
        $page = $this->getPage();
        $perPage = 10;

        $searchParams = [
            'search' => $this->search,
            'subreddit' => $this->subreddit,
            'viability_score_min' => $this->viability_score_min,
            'viability_score_max' => $this->viability_score_max,
            'sort' => $this->sortBy . '_' . $this->sortDirection,
            'from' => ($page - 1) * $perPage,
            'size' => $perPage,
        ];

        Log::info('BusinessPlanSearch: Search Params', $searchParams);

        $result = $businessPlanDao->search($searchParams);

        Log::info('BusinessPlanSearch: Search Result', ['total' => $result['total'], 'plans_count' => count($result['plans'])]);

        $businessPlans = new LengthAwarePaginator(
            $result['plans'],
            $result['total'],
            $perPage,
            $page,
            ['path' => request()->url(), 'query' => request()->query()]
        );

        return view('livewire.business-plan-search', [
            'businessPlans' => $businessPlans,
        ]);
    }
}
