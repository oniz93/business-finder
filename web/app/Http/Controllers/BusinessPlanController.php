<?php

namespace App\Http\Controllers;

use App\Models\BusinessPlan;
use Elastic\Elasticsearch\Client;

class BusinessPlanController extends Controller
{
    private $elasticsearch;

    public function __construct(Client $elasticsearch)
    {
        $this->elasticsearch = $elasticsearch;
    }

    public function random()
    {
        $params = [
            'index' => 'business_plans',
            'size' => 1,
            'body' => [
                'query' => [
                    'function_score' => [
                        'query' => ['match_all' => (object)[]],
                        'random_score' => (object) [],
                    ],
                ],
            ],
        ];

        $response = $this->elasticsearch->search($params);

        $planData = $response['hits']['hits'][0] ?? null;

        if ($planData) {
            $plan = new BusinessPlan($planData['_source']);
            $plan->id = $planData['_id']; // Set the ID from Elasticsearch
            $plan->exists = true; // Mark the model as existing
        } else {
            $plan = new BusinessPlan(); // Empty BusinessPlan object if no plan found
        }

        return view('welcome', ['plan' => $plan]);
    }
}
