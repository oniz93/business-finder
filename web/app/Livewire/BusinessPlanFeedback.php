<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use App\Models\Feedback;
use Illuminate\Support\Facades\Auth;

class BusinessPlanFeedback extends Component
{
    public $businessPlanId;
    public $rating;
    public $comments;

    protected $rules = [
        'rating' => 'required|integer|min:1|max:5',
        'comments' => 'nullable|string|max:1000',
    ];

    public function mount($businessPlanId)
    {
        $this->businessPlanId = $businessPlanId;
    }

    public function submitFeedback()
    {
        $this->validate();

        if (!Auth::check()) {
            session()->flash('error', 'You must be logged in to submit feedback.');
            return;
        }

        Feedback::create([
            'user_id' => Auth::id(),
            'business_plan_id' => $this->businessPlanId,
            'rating' => $this->rating,
            'comments' => $this->comments,
        ]);

        $this->reset(['rating', 'comments']);
        session()->flash('message', 'Feedback submitted successfully!');
    }

    public function render()
    {
        return view('livewire.business-plan-feedback');
    }
}
