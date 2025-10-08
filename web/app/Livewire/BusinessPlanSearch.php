<?php

namespace App\Livewire;

use Livewire\Component;

class BusinessPlanSearch extends Component
{
    public string $search = '';

    public $plans;

    public function search()
    {
        $this->plans = \App\Models\BusinessPlan::search($this->search)->get();
    }

    public function render()
    {
        return view('livewire.business-plan-search');
    }
}
