<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class CollectionController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index()
    {
        return auth()->user()->collections;
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
        ]);

        $collection = auth()->user()->collections()->create($request->all());

        return $collection;
    }

    /**
     * Display the specified resource.
     */
    public function show(Collection $collection)
    {
        $this->authorize('view', $collection);
        return $collection->load('businessPlans');
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, Collection $collection)
    {
        $this->authorize('update', $collection);

        $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
        ]);

        $collection->update($request->all());

        return $collection;
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(Collection $collection)
    {
        $this->authorize('delete', $collection);

        $collection->delete();

        return response()->noContent();
    }

    public function addBusinessPlan(Collection $collection, BusinessPlan $businessPlan)
    {
        $this->authorize('update', $collection);

        $collection->businessPlans()->attach($businessPlan);

        return response()->noContent();
    }

    public function removeBusinessPlan(Collection $collection, BusinessPlan $businessPlan)
    {
        $this->authorize('update', $collection);

        $collection->businessPlans()->detach($businessPlan);

        return response()->noContent();
    }

    public function syncTags(Request $request, Collection $collection)
    {
        $this->authorize('update', $collection);

        $collection->syncTags($request->tags);

        return response()->noContent();
    }

    public function search(Request $request)
    {
        $query = auth()->user()->collections()->getQuery();

        if ($request->has('keyword')) {
            $query->where(function ($q) use ($request) {
                $q->where('name', 'like', '%' . $request->keyword . '%')
                    ->orWhere('description', 'like', '%' . $request->keyword . '%');
            });
        }

        if ($request->has('tags')) {
            $query->withAnyTags($request->tags);
        }

        return $query->get();
    }
}
