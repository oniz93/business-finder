<?php

namespace App\Livewire;

use Livewire\Component;
use Livewire\WithPagination;
use App\Models\Product;

class ProductListings extends Component
{
    use WithPagination;

    public $search = '';
    public $category = '';

    protected $queryString = [
        'search' => ['except' => ''],
        'category' => ['except' => ''],
    ];

    public function updatingSearch()
    {
        $this->resetPage();
    }

    public function updatingCategory()
    {
        $this->resetPage();
    }

    public function render()
    {
        $query = Product::query();

        if ($this->search) {
            $query->where('name', 'like', '%' . $this->search . '%')
                  ->orWhere('description', 'like', '%' . $this->search . '%');
        }

        if ($this->category) {
            $query->where('category', $this->category);
        }

        $products = $query->paginate(10);

        return view('livewire.product-listings', [
            'products' => $products,
            'availableCategories' => Product::select('category')->distinct()->pluck('category'),
        ]);
    }
}
