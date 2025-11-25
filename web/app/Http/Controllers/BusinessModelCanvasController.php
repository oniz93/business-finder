<?php

namespace App\Http\Controllers;

use App\Http\Controllers\Controller;
use App\Models\BusinessPlan;
use App\Services\BusinessModelCanvasGeneratorService;
use Illuminate\Http\Request;

class BusinessModelCanvasController extends Controller
{
    public function __construct(private BusinessModelCanvasGeneratorService $service)
    {
    }

    public function show(BusinessPlan $businessPlan)
    {
        return response()->json($this->service->generate($businessPlan));
    }
}
