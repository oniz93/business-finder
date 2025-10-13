<?php

namespace App\Http\Controllers;

use App\Models\Widget;
use Illuminate\Http\Request;

class WidgetController extends Controller
{
    public function index()
    {
        return auth()->user()->widgets()->orderBy('order')->get();
    }

    public function store(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'type' => 'required|string|max:255',
            'settings' => 'nullable|array',
            'order' => 'nullable|integer',
        ]);

        $widget = auth()->user()->widgets()->create($request->all());

        return $widget;
    }

    public function update(Request $request, Widget $widget)
    {
        $this->authorize('update', $widget);

        $request->validate([
            'name' => 'required|string|max:255',
            'type' => 'required|string|max:255',
            'settings' => 'nullable|array',
            'order' => 'nullable|integer',
        ]);

        $widget->update($request->all());

        return $widget;
    }

    public function destroy(Widget $widget)
    {
        $this->authorize('delete', $widget);

        $widget->delete();

        return response()->noContent();
    }
}
