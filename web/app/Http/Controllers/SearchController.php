<?php

namespace App\Http\Controllers;

use App\Data\BusinessPlanDao;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class SearchController extends Controller
{
    public function handlePostSearch(Request $request)
    {
        // Validate request if needed
        $validated = $request->validate([
            'search' => 'nullable|string',
            'industry' => 'nullable|string',
            'marketSize' => 'nullable|string',
            'sentiment' => 'nullable|string',
            'requiredCapital' => 'nullable|string',
            'timeToMarket' => 'nullable|string',
            'technologyStack' => 'nullable|string',
            'geographicRelevance' => 'nullable|string',
            'sortBy' => 'nullable|string',
            'sortDirection' => 'nullable|string
        ']);

        // Redirect back to the GET route with input flashed to session
        // The Livewire component will pick up these old inputs.
        return redirect()->route('business-plan-search.index')->withInput($request->except(['_token']));
    }
}
