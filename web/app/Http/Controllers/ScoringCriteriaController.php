<?php

namespace App\Http\Controllers;

use App\Models\ScoringCriteria;
use Illuminate\Http\Request;

class ScoringCriteriaController extends Controller
{
    public function index()
    {
        return auth()->user()->scoringCriterias;
    }

    public function store(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'criteria' => 'required|array',
            'weight' => 'required|integer|min:1',
        ]);

        $scoringCriteria = auth()->user()->scoringCriterias()->create($request->all());

        return $scoringCriteria;
    }

    public function show(ScoringCriteria $scoringCriteria)
    {
        $this->authorize('view', $scoringCriteria);

        return $scoringCriteria;
    }

    public function update(Request $request, ScoringCriteria $scoringCriteria)
    {
        $this->authorize('update', $scoringCriteria);

        $request->validate([
            'name' => 'required|string|max:255',
            'criteria' => 'required|array',
            'weight' => 'required|integer|min:1',
        ]);

        $scoringCriteria->update($request->all());

        return $scoringCriteria;
    }

    public function destroy(ScoringCriteria $scoringCriteria)
    {
        $this->authorize('delete', $scoringCriteria);

        $scoringCriteria->delete();

        return response()->noContent();
    }
}
