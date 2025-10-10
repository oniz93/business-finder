<?php

namespace App\Livewire;

use App\Models\BusinessPlan;
use Elastic\Elasticsearch\Client;
use Livewire\Component;

class BusinessPlanPage extends Component
{
    public BusinessPlan $plan;

    public function mount(Client $elasticsearch, $id)
    {
        $params = [
            'index' => 'business_plans',
            'id'    => $id
        ];

        try {
            $response = $elasticsearch->get($params);
            $this->plan = new BusinessPlan($response['_source']);
            $this->plan->id = $response['_id'];
            $this->plan->exists = true;
        } catch (\Exception $e) {
            $this->plan = new BusinessPlan(); // Initialize with an empty model or handle as appropriate
        }
    }

    public function render()
    {
        return view('livewire.business-plan-page')->layout('layouts.app');
    }
}
