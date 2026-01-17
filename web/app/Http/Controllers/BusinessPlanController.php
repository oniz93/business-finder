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

    public function show(Request $request, string $id)
    {
        $plan = $this->businessPlanDao->find($id);

        if (!$plan) {
            abort(404);
        }

        // Theme support - allows switching between different view templates
        $theme = $request->query('theme');
        $validThemes = ['classic'];

        if ($theme && in_array($theme, $validThemes)) {
            $viewName = "business-plans.show-{$theme}";
        } else {
            $viewName = 'business-plans.show';
        }

        return view($viewName, ['plan' => $plan, 'currentTheme' => $theme]);
    }
}
