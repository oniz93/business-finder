<?php

namespace App\Http\Controllers;

use App\Models\BusinessPlan;
use Illuminate\Http\Request;

class BusinessPlanController extends Controller
{
    public function random()
    {
        $plan = \App\Models\BusinessPlan::search('')->raw()['hits']['hits'][0] ?? null;

        return view('welcome', ['plan' => $plan]);
    }
}
