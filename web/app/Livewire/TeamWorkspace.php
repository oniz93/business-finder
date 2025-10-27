<?php

namespace App\Livewire;

use Livewire\Component;

class TeamWorkspace extends Component
{
    public function mount()
    {
        $memberIds = $team->members->pluck('id')->toArray();
        $this->businessPlans = \App\Models\BusinessPlan::whereIn('user_id', $memberIds)->get();
    }

    public function render()
    {
        return view('livewire.team-workspace');
    }
}
