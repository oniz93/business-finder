<?php

namespace App\Http\Controllers;

use App\Models\WaitlistEntry;
use Illuminate\Http\Request;

class WaitlistController extends Controller
{
    public function store(Request $request)
    {
        $request->validate([
            'email' => 'required|email|unique:waitlist_entries',
        ]);

        WaitlistEntry::create($request->only('email'));

        return back()->with('success', 'You have been added to the waitlist!');
    }
}
