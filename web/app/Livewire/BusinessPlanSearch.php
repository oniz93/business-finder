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
    public $industry = '';
    public $marketSize = '';
    public $sentiment = '';
    public $requiredCapital = '';
    public $timeToMarket = '';
    public $technologyStack = '';
    public $geographicRelevance = '';
    public $sortBy = 'popularity';
    public $sortDirection = 'desc';

    protected $queryString = [
        'search' => ['except' => ''],
        'industry' => ['except' => ''],
        'marketSize' => ['except' => ''],
        'sentiment' => ['except' => ''],
        'requiredCapital' => ['except' => ''],
        'timeToMarket' => ['except' => ''],
        'technologyStack' => ['except' => ''],
        'geographicRelevance' => ['except' => ''],
        'sortBy' => [
            'except' => 'popularity',
            'as' => 'sort_by' // Alias for URL parameter
        ],
        'sortDirection' => [
            'except' => 'desc',
            'as' => 'sort_dir' // Alias for URL parameter
        ],
    ];

    public function mount(Request $request)
    {
        // Populate properties from old input (after POST redirect) or GET request
        $this->search = old('search', $request->input('search', ''));
        $this->industry = old('industry', $request->input('industry', ''));
        $this->marketSize = old('marketSize', $request->input('marketSize', ''));
        $this->sentiment = old('sentiment', $request->input('sentiment', ''));
        $this->requiredCapital = old('requiredCapital', $request->input('requiredCapital', ''));
        $this->timeToMarket = old('timeToMarket', $request->input('timeToMarket', ''));
        $this->technologyStack = old('technologyStack', $request->input('technologyStack', ''));
        $this->geographicRelevance = old('geographicRelevance', $request->input('geographicRelevance', ''));
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
            'industry' => $this->industry,
            'market_size' => $this->marketSize,
            'sentiment' => $this->sentiment,
            'required_capital' => $this->requiredCapital,
            'time_to_market' => $this->timeToMarket,
            'technology_stack' => $this->technologyStack,
            'geographic_relevance' => $this->geographicRelevance,
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
