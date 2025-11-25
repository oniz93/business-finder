<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Services\FinancialProjectionService;
use Illuminate\Http\Request;

class FinancialProjectionController extends Controller
{
    public function __construct(private FinancialProjectionService $service)
    {
    }

    public function calculate(Request $request)
    {
        $request->validate([
            'revenue' => 'required|numeric',
            'cogs' => 'required|numeric',
            'opex' => 'required|numeric',
        ]);

        return response()->json($this->service->calculate(
            $request->revenue,
            $request->cogs,
            $request->opex
        ));
    }

    public function scenario(Request $request)
    {
        $request->validate([
            'revenue' => 'required|numeric',
            'cogs' => 'required|numeric',
            'opex' => 'required|numeric',
            'assumptions' => 'required|array',
        ]);

        return response()->json($this->service->scenarioPlanning(
            $request->revenue,
            $request->cogs,
            $request->opex,
            $request->assumptions
        ));
    }

    public function sensitivity(Request $request)
    {
        $request->validate([
            'revenue' => 'required|numeric',
            'cogs' => 'required|numeric',
            'opex' => 'required|numeric',
            'variable' => 'required|string',
            'change' => 'required|numeric',
        ]);

        return response()->json($this->service->sensitivityAnalysis(
            $request->revenue,
            $request->cogs,
            $request->opex,
            $request->variable,
            $request->change
        ));
    }
}
