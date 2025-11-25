<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\BusinessPlan;
use App\Services\PitchDeckGeneratorService;
use Illuminate\Http\Request;

class PitchDeckController extends Controller
{
    public function __construct(private PitchDeckGeneratorService $service)
    {
    }

    public function show(BusinessPlan $businessPlan)
    {
        return response()->json($this->service->generate($businessPlan));
    }
}
