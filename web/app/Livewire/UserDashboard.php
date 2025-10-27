<?php

namespace App\Livewire;

use Livewire\Component;
use Illuminate\Support\Facades\Auth;
use App\Models\Widget;

class UserDashboard extends Component
{
    public $widgets;

    public function mount()
    {
        if (Auth::check()) {
            $this->widgets = Auth::user()->widgets()->orderBy('order')->get();
        } else {
            $this->widgets = collect();
        }
    }

    public function updateWidgetOrder($order)
    {
        foreach ($order as $index => $widgetId) {
            Widget::find($widgetId)->update(['order' => $index]);
        }
        $this->mount(); // Refresh widgets after reordering
    }

    public function render()
    {
        return view('livewire.user-dashboard');
    }
}
