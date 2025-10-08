<?php

namespace App\Livewire;

use Livewire\Component;

class BusinessPlanPage extends Component
{
    public $plan;

    public function mount($id)
    {
        $this->plan = \App\Models\BusinessPlan::find($id);
    }

    public function render()
    {
        return view('livewire.business-plan-page');
    }
}
