<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\ScoringCriteria;
use Illuminate\Support\Facades\Auth;

class ScoringCriteriaManagement extends Component
{
    public $criterias;
    public $name = '';
    public $criteriaJson = ''; // For JSON input of criteria details
    public $weight = 1;
    public $editingCriteriaId = null;

    protected $rules = [
        'name' => 'required|string|min:3|max:255',
        'criteriaJson' => 'nullable|json',
        'weight' => 'required|integer|min:1|max:10',
    ];

    public function mount()
    {
        $this->loadCriterias();
    }

    public function loadCriterias()
    {
        if (Auth::check()) {
            $this->criterias = Auth::user()->scoringCriterias()->get();
        } else {
            $this->criterias = collect();
        }
    }

    public function createCriteria()
    {
        $this->validate();

        if (Auth::check()) {
            Auth::user()->scoringCriterias()->create([
                'name' => $this->name,
                'criteria' => json_decode($this->criteriaJson, true) ?? [],
                'weight' => $this->weight,
            ]);
            $this->reset(['name', 'criteriaJson', 'weight']);
            $this->loadCriterias();
            session()->flash('message', 'Scoring criteria created successfully!');
        } else {
            session()->flash('error', 'You must be logged in to create criteria.');
        }
    }

    public function editCriteria($criteriaId)
    {
        $criteria = ScoringCriteria::find($criteriaId);
        if ($criteria && $criteria->user_id === Auth::id()) {
            $this->editingCriteriaId = $criteria->id;
            $this->name = $criteria->name;
            $this->criteriaJson = json_encode($criteria->criteria);
            $this->weight = $criteria->weight;
        }
    }

    public function updateCriteria()
    {
        $this->validate();

        $criteria = ScoringCriteria::find($this->editingCriteriaId);
        if ($criteria && $criteria->user_id === Auth::id()) {
            $criteria->update([
                'name' => $this->name,
                'criteria' => json_decode($this->criteriaJson, true) ?? [],
                'weight' => $this->weight,
            ]);
            $this->reset(['name', 'criteriaJson', 'weight', 'editingCriteriaId']);
            $this->loadCriterias();
            session()->flash('message', 'Scoring criteria updated successfully!');
        } else {
            session()->flash('error', 'Failed to update criteria. Check permissions.');
        }
    }

    public function deleteCriteria($criteriaId)
    {
        $criteria = ScoringCriteria::find($criteriaId);
        if ($criteria && $criteria->user_id === Auth::id()) {
            $criteria->delete();
            $this->loadCriterias();
            session()->flash('message', 'Scoring criteria deleted successfully!');
        } else {
            session()->flash('error', 'Failed to delete criteria. Check permissions.');
        }
    }

    public function render()
    {
        return view('livewire.scoring-criteria-management');
    }
}
