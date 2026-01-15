<?php

namespace App\Http\Controllers;

use App\Data\BusinessPlanDao;
use App\Models\BusinessPlan;
use Illuminate\Http\Request;

class BusinessPlanController extends Controller
{
    private BusinessPlanDao $businessPlanDao;

    public function __construct(BusinessPlanDao $businessPlanDao)
    {
        $this->businessPlanDao = $businessPlanDao;
    }

    public function random()
    {
        $result = $this->businessPlanDao->getRandom(1);
        $plan = $result['plans'][0] ?? null;

        if (!$plan) {
            // If no plan is found, create an empty BusinessPlan object
            $plan = new BusinessPlan();
        }

        return view('welcome', ['plan' => $plan]);
    }

    public function search(Request $request)
    {
        $plans = $this->businessPlanDao->search($request->all());

        return response()->json($plans);
    }

    public function show(string $id)
    {
        $plan = $this->businessPlanDao->find($id);

        if (!$plan) {
            abort(404);
        }
        
        return view('business-plans.show', ['plan' => $plan]);
    }
}
