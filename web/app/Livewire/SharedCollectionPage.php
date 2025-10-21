<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\Collection;

class SharedCollectionPage extends Component
{
    public $collection;

    public function mount($shareableLink)
    {
        $this->collection = Collection::where('shareable_link', $shareableLink)->with('businessPlans')->first();

        if (!$this->collection) {
            abort(404); // Or redirect to an error page
        }
    }

    public function render()
    {
        return view('livewire.shared-collection-page');
    }
}
