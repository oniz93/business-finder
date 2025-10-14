<?php

namespace App\Livewire;

use Livewire\Component;
use Livewire\WithPagination;
use App\Models\BusinessPlan;

class BusinessPlanSearch extends Component
{
    use WithPagination;

    public $industry = '';
    public $marketSize = '';
    public $sentiment = '';
    public $requiredCapital = '';
    public $timeToMarket = '';
    public $technologyStack = '';
    public $geographicRelevance = '';
    public $sortBy = 'created_at';
    public $sortDirection = 'desc';

    protected $queryString = [
        'industry' => ['except' => ''],
        'marketSize' => ['except' => ''],
        'sentiment' => ['except' => ''],
        'requiredCapital' => ['except' => ''],
        'timeToMarket' => ['except' => ''],
        'technologyStack' => ['except' => ''],
        'geographicRelevance' => ['except' => ''],
        'sortBy' => ['except' => 'created_at'],
        'sortDirection' => ['except' => 'desc'],
    ];

    public function mount()
    {
        $this->resetPage();
    }

    public function updating($name, $value)
    {
        $this->resetPage();
    }

    public function sortBy($field)
    {
        if ($this->sortBy === $field) {
            $this->sortDirection = $this->sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            $this->sortBy = $field;
            $this->sortDirection = 'asc';
        }
    }

    public function render()
    {
        $query = BusinessPlan::query();

        if ($this->industry) {
            $query->where('industry', 'like', '%' . $this->industry . '%');
        }
        if ($this->marketSize) {
            $query->where('market_size', 'like', '%' . $this->marketSize . '%');
        }
        if ($this->sentiment) {
            $query->where('sentiment', 'like', '%' . $this->sentiment . '%');
        }
        if ($this->requiredCapital) {
            $query->where('required_capital', 'like', '%' . $this->requiredCapital . '%');
        }
        if ($this->timeToMarket) {
            $query->where('time_to_market', 'like', '%' . $this->timeToMarket . '%');
        }
        if ($this->technologyStack) {
            $query->where('technology_stack', 'like', '%' . $this->technologyStack . '%');
        }
        if ($this->geographicRelevance) {
            $query->where('geographic_relevance', 'like', '%' . $this->geographicRelevance . '%');
        }

        $businessPlans = $query->orderBy($this->sortBy, $this->sortDirection)->paginate(10);

        return view('livewire.business-plan-search', [
            'businessPlans' => $businessPlans,
        ]);
    }
}
