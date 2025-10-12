<?php

namespace App\Http\Controllers;

use App\Models\WaitlistEntry;
use Illuminate\Http\Request;

class WaitlistController extends Controller
{
    public function store(Request $request)
    {
        $validator = \Validator::make($request->all(), [
            'email' => 'required|email|unique:waitlist_entries',
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 422);
        }

        WaitlistEntry::create($request->only('email'));

        return response()->json(['success' => 'You have been added to the waitlist!']);
    }
}
