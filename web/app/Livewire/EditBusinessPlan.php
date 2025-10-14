<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use Illuminate\Validation\Rule;

class EditBusinessPlan extends Component
{
    public BusinessPlan $businessPlan;

    public $title;
    public $summary;
    public $executive_summary;
    public $problem;
    public $solution;
    public $viability_score;
    public $viability_reasoning;
    public $market_analysis_target_market;
    public $market_analysis_market_size;
    public $market_analysis_trends;
    public $competition_competitors;
    public $competition_direct_competitors;
    public $competition_indirect_competitors;
    public $competition_competitive_advantages;
    public $marketing_strategy;
    public $management_team_description;
    public $management_team_roles;
    public $financial_projections_potential_monthly_revenue;
    public $financial_projections_revenue_streams;
    public $financial_projections_cost_structure;
    public $call_to_action;

    protected $rules = [
        'title' => 'required|string|max:255',
        'summary' => 'required|string|max:500',
        'executive_summary' => 'required|string',
        'problem' => 'required|string',
        'solution' => 'required|string',
        'viability_score' => 'nullable|numeric',
        'viability_reasoning' => 'nullable|string',
        'market_analysis_target_market' => 'nullable|array',
        'market_analysis_market_size' => 'nullable|string',
        'market_analysis_trends' => 'nullable|array',
        'competition_competitors' => 'nullable|array',
        'competition_direct_competitors' => 'nullable|array',
        'competition_indirect_competitors' => 'nullable|array',
        'competition_competitive_advantages' => 'nullable|array',
        'marketing_strategy' => 'nullable|array',
        'management_team_description' => 'nullable|string',
        'management_team_roles' => 'nullable|array',
        'financial_projections_potential_monthly_revenue' => 'nullable|string',
        'financial_projections_revenue_streams' => 'nullable|array',
        'financial_projections_cost_structure' => 'nullable|array',
        'call_to_action' => 'nullable|string',
    ];

    public function mount(BusinessPlan $businessPlan)
    {
        $this->businessPlan = $businessPlan;
        $this->title = $businessPlan->title;
        $this->summary = $businessPlan->summary;
        $this->executive_summary = $businessPlan->executive_summary;
        $this->problem = $businessPlan->problem;
        $this->solution = $businessPlan->solution;
        $this->viability_score = $businessPlan->viability_score;
        $this->viability_reasoning = $businessPlan->viability_reasoning;

        // Handle JSON fields
        $this->market_analysis_target_market = $businessPlan->market_analysis['target_market'] ?? [];
        $this->market_analysis_market_size = $businessPlan->market_analysis['market_size'] ?? '';
        $this->market_analysis_trends = $businessPlan->market_analysis['trends'] ?? [];

        $this->competition_competitors = $businessPlan->competition['competitors'] ?? [];
        $this->competition_direct_competitors = $businessPlan->competition['direct_competitors'] ?? [];
        $this->competition_indirect_competitors = $businessPlan->competition['indirect_competitors'] ?? [];
        $this->competition_competitive_advantages = $businessPlan->competition['competitive_advantages'] ?? [];

        $this->marketing_strategy = $businessPlan->marketing_strategy ?? [];

        $this->management_team_description = $businessPlan->management_team['description'] ?? '';
        $this->management_team_roles = $businessPlan->management_team['roles'] ?? [];

        $this->financial_projections_potential_monthly_revenue = $businessPlan->financial_projections['potential_monthly_revenue'] ?? '';
        $this->financial_projections_revenue_streams = $businessPlan->financial_projections['revenue_streams'] ?? [];
        $this->financial_projections_cost_structure = $businessPlan->financial_projections['cost_structure'] ?? [];

        $this->call_to_action = $businessPlan->call_to_action;
    }

    public function save()
    {
        $this->validate();

        $this->businessPlan->update([
            'title' => $this->title,
            'summary' => $this->summary,
            'executive_summary' => $this->executive_summary,
            'problem' => $this->problem,
            'solution' => $this->solution,
            'viability_score' => $this->viability_score,
            'viability_reasoning' => $this->viability_reasoning,
            'market_analysis' => [
                'target_market' => $this->market_analysis_target_market,
                'market_size' => $this->market_analysis_market_size,
                'trends' => $this->market_analysis_trends,
            ],
            'competition' => [
                'competitors' => $this->competition_competitors,
                'direct_competitors' => $this->competition_direct_competitors,
                'indirect_competitors' => $this->competition_indirect_competitors,
                'competitive_advantages' => $this->competition_competitive_advantages,
            ],
            'marketing_strategy' => $this->marketing_strategy,
            'management_team' => [
                'description' => $this->management_team_description,
                'roles' => $this->management_team_roles,
            ],
            'financial_projections' => [
                'potential_monthly_revenue' => $this->financial_projections_potential_monthly_revenue,
                'revenue_streams' => $this->financial_projections_revenue_streams,
                'cost_structure' => $this->financial_projections_cost_structure,
            ],
            'call_to_action' => $this->call_to_action,
        ]);

        session()->flash('message', 'Business plan updated successfully!');
        return redirect()->route('business-plan', $this->businessPlan->id);
    }

    public function render()
    {
        return view('livewire.edit-business-plan');
    }
}
