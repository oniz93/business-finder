<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends \Illuminate\Database\Eloquent\Factories\Factory<\App\Models\BusinessPlan>
 */
class BusinessPlanFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'title' => $this->faker->company,
            'executive_summary' => $this->faker->paragraph,
            'problem' => $this->faker->paragraph,
            'solution' => $this->faker->paragraph,
            'market_analysis' => json_encode(['size' => $this->faker->numberBetween(100000, 1000000), 'growth_rate' => $this->faker->randomFloat(2, 0, 1)]),
            'competition' => json_encode(['competitor_1' => $this->faker->company, 'competitor_2' => $this->faker->company]),
            'marketing_strategy' => json_encode(['online' => $this->faker->sentence, 'offline' => $this->faker->sentence]),
            'call_to_action' => $this->faker->sentence,
        ];
    }
}
