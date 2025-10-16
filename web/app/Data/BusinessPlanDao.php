<?php

namespace App\Data;

use App\Models\BusinessPlan;
use Elastic\Elasticsearch\Client;
use Elastic\Common\Exceptions\Missing404Exception;

class BusinessPlanDao
{
    private Client $elasticsearch;
    private string $index = 'business_plans';

    public function __construct(Client $elasticsearch)
    {
        $this->elasticsearch = $elasticsearch;
    }

    /**
     * Find a business plan by its ID.
     *
     * @param string $id
     * @return BusinessPlan|null
     */
    public function find(string $id): ?BusinessPlan
    {
        $params = [
            'index' => $this->index,
            'id'    => $id
        ];

        try {
            $response = $this->elasticsearch->get($params);
        } catch (\Exception $e) {
            return null;
        }

        $plan = new BusinessPlan($response['_source']);
        $plan->id = $response['_id'];
        $plan->exists = true;

        return $plan;
    }

    /**
     * Retrieve a random business plan.
     *
     * @return BusinessPlan|null
     */
    public function getRandom(): ?BusinessPlan
    {
        $params = [
            'index' => $this->index,
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
            $plan->id = $planData['_id'];
            $plan->exists = true;
            return $plan;
        }

        return null;
    }

    /**
     * Save a business plan (create or update).
     * To create a new plan, instantiate a new BusinessPlan object, set its id and properties, then pass it to this method.
     *
     * @param BusinessPlan $plan
     * @return void
     */
    public function save(BusinessPlan $plan): void
    {
        $body = $plan->toArray();

        $params = [
            'index' => $this->index,
            'id'    => $plan->id,
            'body'  => $body
        ];

        $this->elasticsearch->index($params);
    }

    /**
     * Search for business plans.
     *
     * @param array $searchParams
     * @return BusinessPlan[]
     */
    public function search(array $searchParams): array
    {
        $boolQuery = [];

        if (!empty($searchParams['search'])) {
            $boolQuery['must'][] = [
                            'query_string' => [
                                'query' => $searchParams['search'],
                                'fields' => ['*'], // Search across all fields
                                'default_operator' => 'OR', // Default operator if not specified in query string
                            ],

            ];
        }

        $filters = [];
        if (!empty($searchParams['industry'])) {
            $filters[] = ['match' => ['industry' => $searchParams['industry']]];
        }

        if (!empty($searchParams['market_size'])) {
            $filters[] = ['range' => ['market_size' => ['gte' => $searchParams['market_size']]]];
        }

        if (!empty($searchParams['sentiment'])) {
            $filters[] = ['match' => ['sentiment' => $searchParams['sentiment']]];
        }

        if (!empty($searchParams['required_capital'])) {
            $filters[] = ['range' => ['required_capital' => ['lte' => $searchParams['required_capital']]]];
        }

        if (!empty($searchParams['time_to_market'])) {
            $filters[] = ['range' => ['time_to_market' => ['lte' => $searchParams['time_to_market']]]];
        }

        if (!empty($searchParams['technology_stack'])) {
            $filters[] = ['match' => ['technology_stack' => $searchParams['technology_stack']]];
        }

        if (!empty($searchParams['geographic_relevance'])) {
            $filters[] = ['match' => ['geographic_relevance' => $searchParams['geographic_relevance']]];
        }

        if (!empty($filters)) {
            $boolQuery['filter'] = $filters;
        }

        $query = empty($boolQuery) ? ['match_all' => (object)[]] : ['bool' => $boolQuery];

        $params = [
            'index' => $this->index,
            'body' => [
                'query' => $query,
            ],
            'from' => $searchParams['from'] ?? 0,
            'size' => $searchParams['size'] ?? 10,
        ];

        if (isset($searchParams['sort'])) {
            $sort = explode('_', $searchParams['sort']);
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
//        dd($searchParams, $params);
        $response = $this->elasticsearch->search($params);

        $plans = [];
        foreach ($response['hits']['hits'] as $hit) {
            $plan = new BusinessPlan($hit['_source']);
            $plan->id = $hit['_id'];
            $plan->exists = true;
            $plans[] = $plan;
        }

        return [
            'plans' => $plans,
            'total' => $response['hits']['total']['value'],
        ];
    }
}
