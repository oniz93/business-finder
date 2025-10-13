<?php

namespace App\Services;

use App\Models\BusinessPlan;

class BusinessModelCanvasGeneratorService
{
    public function generate(BusinessPlan $businessPlan): array
    {
        return [
            'key_partners' => $businessPlan->market_analysis['key_partners'] ?? [],
            'key_activities' => $businessPlan->marketing_strategy['key_activities'] ?? [],
            'key_resources' => $businessPlan->management_team['key_resources'] ?? [],
            'value_propositions' => $businessPlan->solution,
            'customer_relationships' => $businessPlan->marketing_strategy['customer_relationships'] ?? [],
            'channels' => $businessPlan->marketing_strategy['channels'] ?? [],
            'customer_segments' => $businessPlan->market_analysis['customer_segments'] ?? [],
            'cost_structure' => $businessPlan->financial_projections['cost_structure'] ?? [],
            'revenue_streams' => $businessPlan->financial_projections['revenue_streams'] ?? [],
        ];
    }
}
