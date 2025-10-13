<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Services\PaymentService;
use Illuminate\Http\Request;

class PaymentController extends Controller
{
    public function __construct(private PaymentService $paymentService)
    {
    }

    public function store(Request $request)
    {
        $request->validate([
            'token' => 'required|string',
            'amount' => 'required|numeric|min:0',
            'currency' => 'required|string|size:3',
        ]);

        if ($this->paymentService->processPayment($request->all())) {
            return response()->json(['message' => 'Payment successful']);
        }

        return response()->json(['message' => 'Payment failed'], 400);
    }
}
