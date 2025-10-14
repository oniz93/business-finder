<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use App\Services\FinancialProjectionService;
use Maatwebsite\Excel\Facades\Excel;
use App\Exports\FinancialProjectionsExport;

class FinancialProjections extends Component
{
    public $businessPlanId;
    public $initialInvestment = 0;
    public $monthlyRevenue = 0;
    public $monthlyExpenses = 0;
    public $growthRate = 0; // Percentage
    public $projections = [];
    public $scenario = 'base'; // base, optimistic, pessimistic

    protected $rules = [
        'initialInvestment' => 'required|numeric|min:0',
        'monthlyRevenue' => 'required|numeric|min:0',
        'monthlyExpenses' => 'required|numeric|min:0',
        'growthRate' => 'required|numeric|min:0|max:100',
        'scenario' => 'required|in:base,optimistic,pessimistic',
    ];

    public function mount($businessPlanId)
    {
        $this->businessPlanId = $businessPlanId;
        // Optionally load initial data from business plan or user preferences
    }

    public function calculateProjections(FinancialProjectionService $service)
    {
        $this->validate();

        $businessPlan = BusinessPlan::find($this->businessPlanId);

        if (!$businessPlan) {
            session()->flash('error', 'Business plan not found.');
            return;
        }

        $data = [
            'initial_investment' => $this->initialInvestment,
            'monthly_revenue' => $this->monthlyRevenue,
            'monthly_expenses' => $this->monthlyExpenses,
            'growth_rate' => $this->growthRate / 100, // Convert percentage to decimal
        ];

        switch ($this->scenario) {
            case 'optimistic':
                $this->projections = $service->scenarioPlanning($businessPlan, $data, 'optimistic');
                break;
            case 'pessimistic':
                $this->projections = $service->scenarioPlanning($businessPlan, $data, 'pessimistic');
                break;
            default: // base
                $this->projections = $service->calculate($businessPlan, $data);
                break;
        }

        session()->flash('message', 'Projections calculated successfully!');
    }

    public function exportToExcel()
    {
        if (empty($this->projections)) {
            session()->flash('error', 'No projections to export. Please calculate projections first.');
            return;
        }
        return Excel::download(new FinancialProjectionsExport($this->projections), 'financial_projections_' . $this->businessPlanId . '.xlsx');
    }

    public function render()
    {
        return view('livewire.financial-projections');
    }
}
