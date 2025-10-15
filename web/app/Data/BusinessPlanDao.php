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
        $params = [
            'index' => $this->index,
            'body' => [
                'query' => [
                    'bool' => [
                        'must' => [],
                    ],
                ],
            ],
        ];

        if (isset($searchParams['industry'])) {
            $params['body']['query']['bool']['must'][] = ['match' => ['industry' => $searchParams['industry']]];
        }

        if (isset($searchParams['market_size'])) {
            $params['body']['query']['bool']['must'][] = ['range' => ['market_size' => ['gte' => $searchParams['market_size']]]];
        }

        if (isset($searchParams['sentiment'])) {
            $params['body']['query']['bool']['must'][] = ['match' => ['sentiment' => $searchParams['sentiment']]];
        }

        if (isset($searchParams['required_capital'])) {
            $params['body']['query']['bool']['must'][] = ['range' => ['required_capital' => ['lte' => $searchParams['required_capital']]]];
        }

        if (isset($searchParams['time_to_market'])) {
            $params['body']['query']['bool']['must'][] = ['range' => ['time_to_market' => ['lte' => $searchParams['time_to_market']]]];
        }

        if (isset($searchParams['technology_stack'])) {
            $params['body']['query']['bool']['must'][] = ['match' => ['technology_stack' => $searchParams['technology_stack']]];
        }

        if (isset($searchParams['geographic_relevance'])) {
            $params['body']['query']['bool']['must'][] = ['match' => ['geographic_relevance' => $searchParams['geographic_relevance']]];
        }

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

        $response = $this->elasticsearch->search($params);

        $plans = [];
        foreach ($response['hits']['hits'] as $hit) {
            $plan = new BusinessPlan($hit['_source']);
            $plan->id = $hit['_id'];
            $plan->exists = true;
            $plans[] = $plan;
        }

        return $plans;
    }
}
