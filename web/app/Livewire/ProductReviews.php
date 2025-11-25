<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\Product;
use App\Models\Review;
use Illuminate\Support\Facades\Auth;

class ProductReviews extends Component
{
    public $productId;
    public $reviews;
    public $rating;
    public $comment;

    protected $rules = [
        'rating' => 'required|integer|min:1|max:5',
        'comment' => 'nullable|string|max:1000',
    ];

    public function mount($productId)
    {
        $this->productId = $productId;
        $this->loadReviews();
    }

    public function loadReviews()
    {
        $this->reviews = Review::where('product_id', $this->productId)->latest()->get();
    }

    public function submitReview()
    {
        $this->validate();

        if (!Auth::check()) {
            session()->flash('error', 'You must be logged in to submit a review.');
            return;
        }

        Review::create([
            'user_id' => Auth::id(),
            'product_id' => $this->productId,
            'rating' => $this->rating,
            'comment' => $this->comment,
        ]);

        $this->reset(['rating', 'comment']);
        $this->loadReviews(); // Refresh reviews after submission
        session()->flash('message', 'Review submitted successfully!');
    }

    public function render()
    {
        return view('livewire.product-reviews');
    }
}
