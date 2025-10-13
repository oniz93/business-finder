<?php

namespace App\Http\Controllers;

use App\Models\BusinessPlan;
use App\Models\Comment;
use Illuminate\Http\Request;

class CommentController extends Controller
{
    public function index(BusinessPlan $businessPlan)
    {
        return $businessPlan->comments()->with('user')->latest()->get();
    }

    public function store(Request $request, BusinessPlan $businessPlan)
    {
        $request->validate([
            'body' => 'required|string',
        ]);

        $comment = $businessPlan->comments()->create([
            'user_id' => auth()->id(),
            'body' => $request->body,
        ]);

        return $comment->load('user');
    }

    public function destroy(Comment $comment)
    {
        $this->authorize('delete', $comment);

        $comment->delete();

        return response()->noContent();
    }
}
