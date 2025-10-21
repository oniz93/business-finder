<?php

namespace App\Services;

class FinancialProjectionService
{
    public function calculate(float $revenue, float $cogs, float $opex): array
    {
        $grossMargin = $revenue - $cogs;
        $netProfit = $grossMargin - $opex;

        // Simple break-even point calculation (assuming fixed costs are part of opex)
        $breakEvenPoint = $cogs + $opex > 0 ? ($cogs + $opex) / ($revenue > 0 ? $revenue : 1) : 0;

        return [
            'gross_margin' => $grossMargin,
            'net_profit' => $netProfit,
            'break_even_point' => $breakEvenPoint,
        ];
    }

    public function scenarioPlanning(float $revenue, float $cogs, float $opex, array $assumptions): array
    {
        // Implement scenario planning logic here
        return $this->calculate($revenue * ($assumptions['revenue_growth'] ?? 1), $cogs * ($assumptions['cogs_change'] ?? 1), $opex * ($assumptions['opex_change'] ?? 1));
    }

    public function sensitivityAnalysis(float $revenue, float $cogs, float $opex, string $variable, float $change): array
    {
        // Implement sensitivity analysis logic here
        $newRevenue = $revenue;
        $newCogs = $cogs;
        $newOpex = $opex;

        if ($variable === 'revenue') {
            $newRevenue *= (1 + $change);
        } elseif ($variable === 'cogs') {
            $newCogs *= (1 + $change);
        } elseif ($variable === 'opex') {
            $newOpex *= (1 + $change);
        }

        return $this->calculate($newRevenue, $newCogs, $newOpex);
    }
}
