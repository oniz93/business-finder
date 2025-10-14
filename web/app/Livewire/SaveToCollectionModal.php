<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\Collection;
use App\Models\BusinessPlan;
use Illuminate\Support\Facades\Auth;

class SaveToCollectionModal extends Component
{
    public $businessPlanId;
    public $showModal = false;
    public $collections = [];
    public $selectedCollections = [];
    public $newCollectionName = '';
    public $newCollectionDescription = '';

    protected $listeners = ['openModal'];

    protected $rules = [
        'newCollectionName' => 'required_if:selectedCollections,null|min:3',
        'newCollectionDescription' => 'nullable|max:255',
    ];

    public function mount($businessPlanId)
    {
        $this->businessPlanId = $businessPlanId;
        $this->loadUserCollections();
    }

    public function loadUserCollections()
    {
        if (Auth::check()) {
            $this->collections = Auth::user()->collections()->get();
        }
    }

    public function openModal($businessPlanId = null)
    {
        if ($businessPlanId) {
            $this->businessPlanId = $businessPlanId;
        }
        $this->loadUserCollections();
        $this->showModal = true;
    }

    public function closeModal()
    {
        $this->showModal = false;
        $this->reset(['selectedCollections', 'newCollectionName', 'newCollectionDescription']);
        $this->resetValidation();
    }

    public function saveToCollections()
    {
        $this->validate();

        $businessPlan = BusinessPlan::find($this->businessPlanId);

        if (!$businessPlan) {
            session()->flash('error', 'Business plan not found.');
            $this->closeModal();
            return;
        }

        // Attach to existing collections
        foreach ($this->selectedCollections as $collectionId) {
            $collection = Collection::find($collectionId);
            if ($collection && $collection->user_id === Auth::id()) {
                $businessPlan->collections()->syncWithoutDetaching([$collectionId]);
            }
        }

        session()->flash('message', 'Business plan saved to selected collections!');
        $this->closeModal();
    }

    public function createAndSaveToCollection()
    {
        $this->validate();

        $businessPlan = BusinessPlan::find($this->businessPlanId);

        if (!$businessPlan) {
            session()->flash('error', 'Business plan not found.');
            $this->closeModal();
            return;
        }

        if (Auth::check()) {
            $newCollection = Auth::user()->collections()->create([
                'name' => $this->newCollectionName,
                'description' => $this->newCollectionDescription,
            ]);

            $businessPlan->collections()->attach($newCollection->id);
            session()->flash('message', 'New collection created and business plan saved!');
            $this->closeModal();
        } else {
            session()->flash('error', 'You must be logged in to create a collection.');
        }
    }

    public function render()
    {
        return view('livewire.save-to-collection-modal');
    }
}
