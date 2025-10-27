<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use App\Services\PitchDeckGeneratorService;

class PitchDeckDisplay extends Component
{
    public $businessPlanId;
    public $deckData;

    public function mount($businessPlanId, PitchDeckGeneratorService $service)
    {
        $this->businessPlanId = $businessPlanId;
        $businessPlan = BusinessPlan::find($businessPlanId);

        if (!$businessPlan) {
            abort(404);
        }

        $this->deckData = $service->generate($businessPlan);
    }

    public function render()
    {
        return view('livewire.pitch-deck-display');
    }
}
