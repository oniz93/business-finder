<?php

namespace App\Livewire;

use Livewire\Component;
use Illuminate\Support\Facades\Auth;

class UserCollections extends Component
{
    public $collections;

    public function mount()
    {
        if (Auth::check()) {
            $this->collections = Auth::user()->collections()->with('businessPlans')->get();
        } else {
            $this->collections = collect(); // Empty collection if not authenticated
        }
    }

    public function render()
    {
        return view('livewire.user-collections');
    }
}
