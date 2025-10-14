<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\Product;
use App\Services\PaymentService;
use Illuminate\Support\Facades\Auth;

class ProductPurchase extends Component
{
    public Product $product;

    public function mount(Product $product)
    {
        $this->product = $product;
    }

    public function purchase(PaymentService $paymentService)
    {
        if (!Auth::check()) {
            session()->flash('error', 'You must be logged in to purchase a product.');
            return;
        }

        // In a real application, you would integrate with a payment gateway here.
        // For now, we'll simulate a successful payment.
        $result = $paymentService->processPayment(Auth::user(), $this->product->price);

        if ($result) {
            session()->flash('message', 'Purchase successful! Thank you for your order.');
            // Optionally, redirect to an order confirmation page or user's orders
            // return redirect()->route('orders.show', $order->id);
        } else {
            session()->flash('error', 'Payment failed. Please try again.');
        }
    }

    public function render()
    {
        return view('livewire.product-purchase');
    }
}
