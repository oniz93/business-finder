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

    public function search(Request $request)
    {
        $params = [
            'index' => 'business_plans',
            'body' => [
                'query' => [
                    'bool' => [
                        'must' => [],
                    ],
                ],
            ],
        ];

        if ($request->has('industry')) {
            $params['body']['query']['bool']['must'][] = ['match' => ['industry' => $request->industry]];
        }

        if ($request->has('market_size')) {
            $params['body']['query']['bool']['must'][] = ['range' => ['market_size' => ['gte' => $request->market_size]]];
        }

        if ($request->has('sentiment')) {
            $params['body']['query']['bool']['must'][] = ['match' => ['sentiment' => $request->sentiment]];
        }

        if ($request->has('required_capital')) {
            $params['body']['query']['bool']['must'][] = ['range' => ['required_capital' => ['lte' => $request->required_capital]]];
        }

        if ($request->has('time_to_market')) {
            $params['body']['query']['bool']['must'][] = ['range' => ['time_to_market' => ['lte' => $request->time_to_market]]];
        }

        if ($request->has('technology_stack')) {
            $params['body']['query']['bool']['must'][] = ['match' => ['technology_stack' => $request->technology_stack]];
        }

        if ($request->has('geographic_relevance')) {
            $params['body']['query']['bool']['must'][] = ['match' => ['geographic_relevance' => $request->geographic_relevance]];
        }

        if ($request->has('sort')) {
            $sort = explode('_', $request->sort);
            $field = $sort[0];
            $order = $sort[1];

            if ($field === 'date') {
                $field = 'created_at';
            }

            if ($field === 'popularity') {
                $field = 'total_ups';
            }

            $params['body']['sort'] = [
                [$field => $order],
            ];
        }

        $response = $this->elasticsearch->search($params);

        return response()->json($response['hits']['hits']);
    }

    public function show(BusinessPlan $businessPlan)
    {
        return view('business-plans.show', ['plan' => $businessPlan]);
    }
}
