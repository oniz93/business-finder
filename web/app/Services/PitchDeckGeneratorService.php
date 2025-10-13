<?php

namespace App\Services;

use App\Models\BusinessPlan;

class PitchDeckGeneratorService
{
    public function generate(BusinessPlan $businessPlan): array
    {
        return [
            'problem' => $businessPlan->problem,
            'solution' => $businessPlan->solution,
            'market_size' => $businessPlan->market_analysis['market_size'] ?? null,
            'competition' => $businessPlan->competition,
            'team' => $businessPlan->management_team,
            'financial_projections' => $businessPlan->financial_projections,
        ];
    }
}
