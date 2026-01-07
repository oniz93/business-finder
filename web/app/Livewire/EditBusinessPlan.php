<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use Illuminate\Validation\Rule;

class EditBusinessPlan extends Component
{
    public BusinessPlan $businessPlan;

    public $title;
    public $executive_summary;
    public $problem;
    public $solution;
    public $market_analysis;
    public $competition;
    public $marketing_strategy;
    public $management_team;
    public $financial_projections;
    public $call_to_action;
    public $cluster_summary;
    public $is_viable_business;
    public $viability_score;
    public $is_saas;
    public $is_solo_entrepreneur_possible;
    public $message_ids;
    public $texts_combined;
    public $total_ups;
    public $total_downs;
    public $message_count;
    public $generated_plan;
    public $generated_at;


    protected function rules()
    {
        return [
            'title' => 'required|string|max:255',
            'executive_summary' => 'required|string',
            'problem' => 'required|string',
            'solution' => 'required|string',
            'market_analysis' => 'nullable|array',
            'competition' => 'nullable|array',
            'marketing_strategy' => 'nullable|array',
            'management_team' => 'nullable|array',
            'financial_projections' => 'nullable|array',
            'call_to_action' => 'nullable|string',
            'cluster_summary' => 'nullable|string',
            'is_viable_business' => 'nullable|boolean',
            'viability_score' => 'nullable|integer',
            'is_saas' => 'nullable|boolean',
            'is_solo_entrepreneur_possible' => 'nullable|boolean',
            'message_ids' => 'nullable|array',
            'texts_combined' => 'nullable|string',
            'total_ups' => 'nullable|integer',
            'total_downs' => 'nullable|integer',
            'message_count' => 'nullable|integer',
            'generated_plan' => 'nullable|string',
            'generated_at' => 'nullable|date',
        ];
    }

    public function mount(BusinessPlan $businessPlan)
    {
        $this->businessPlan = $businessPlan;
        $this->title = $businessPlan->title;
        $this->executive_summary = $businessPlan->executive_summary;
        $this->problem = $businessPlan->problem;
        $this->solution = $businessPlan->solution;
        $this->market_analysis = $businessPlan->market_analysis;
        $this->competition = $businessPlan->competition;
        $this->marketing_strategy = $businessPlan->marketing_strategy;
        $this->management_team = $businessPlan->management_team;
        $this->financial_projections = $businessPlan->financial_projections;
        $this->call_to_action = $businessPlan->call_to_action;
        $this->cluster_summary = $businessPlan->cluster_summary;
        $this->is_viable_business = $businessPlan->is_viable_business;
        $this->viability_score = $businessPlan->viability_score;
        $this->is_saas = $businessPlan->is_saas;
        $this->is_solo_entrepreneur_possible = $businessPlan->is_solo_entrepreneur_possible;
        $this->message_ids = $businessPlan->message_ids;
        $this->texts_combined = $businessPlan->texts_combined;
        $this->total_ups = $businessPlan->total_ups;
        $this->total_downs = $businessPlan->total_downs;
        $this->message_count = $businessPlan->message_count;
        $this->generated_plan = $businessPlan->generated_plan;
        $this->generated_at = $businessPlan->generated_at;
    }

    public function save()
    {
        $this->validate();

        $this->businessPlan->update([
            'title' => $this->title,
            'executive_summary' => $this->executive_summary,
            'problem' => $this->problem,
            'solution' => $this->solution,
            'market_analysis' => $this->market_analysis,
            'competition' => $this->competition,
            'marketing_strategy' => $this->marketing_strategy,
            'management_team' => $this->management_team,
            'financial_projections' => $this->financial_projections,
            'call_to_action' => $this->call_to_action,
            'cluster_summary' => $this->cluster_summary,
            'is_viable_business' => $this->is_viable_business,
            'viability_score' => $this->viability_score,
            'is_saas' => $this->is_saas,
            'is_solo_entrepreneur_possible' => $this->is_solo_entrepreneur_possible,
            'message_ids' => $this->message_ids,
            'texts_combined' => $this->texts_combined,
            'total_ups' => $this->total_ups,
            'total_downs' => $this->total_downs,
            'message_count' => $this->message_count,
            'generated_plan' => $this->generated_plan,
            'generated_at' => $this->generated_at,
        ]);

        session()->flash('message', 'Business plan updated successfully!');
        return redirect()->to('/business-plans/' . $this->businessPlan->id);
    }

    public function render()
    {
        return view('livewire.edit-business-plan');
    }
}
