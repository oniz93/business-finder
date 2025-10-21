<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\BusinessPlan;
use App\Services\BusinessModelCanvasGeneratorService;

use Barryvdh\DomPDF\Facade\Pdf;

class BusinessModelCanvasDisplay extends Component
{
    public $businessPlanId;
    public $canvasData;

    public function mount($businessPlanId, BusinessModelCanvasGeneratorService $service)
    {
        $this->businessPlanId = $businessPlanId;
        $businessPlan = BusinessPlan::find($businessPlanId);

        if (!$businessPlan) {
            abort(404);
        }

        $this->canvasData = $service->generate($businessPlan);
    }

    public function exportToPdf()
    {
        $pdf = Pdf::loadView('pdfs.business-model-canvas', ['canvasData' => $this->canvasData, 'businessPlanId' => $this->businessPlanId]);
        return response()->streamDownload(function () use ($pdf) {
            echo $pdf->output();
        }, 'business_model_canvas_' . $this->businessPlanId . '.pdf');
    }

    public function render()
    {
        return view('livewire.business-model-canvas-display');
    }
}
