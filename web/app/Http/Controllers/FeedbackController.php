<?php

namespace App\Http\Controllers;

use App\Models\BusinessPlan;
use App\Models\Feedback;
use Illuminate\Http\Request;

class FeedbackController extends Controller
{
    public function store(Request $request, BusinessPlan $businessPlan)
    {
        $request->validate([
            'rating' => 'required|integer|min:1|max:5',
            'comments' => 'nullable|string',
        ]);

        $feedback = $businessPlan->feedback()->create([
            'user_id' => auth()->id(),
            'rating' => $request->rating,
            'comments' => $request->comments,
        ]);

        return $feedback;
    }
}
