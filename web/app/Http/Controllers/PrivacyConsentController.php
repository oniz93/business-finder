<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class PrivacyConsentController extends Controller
{
    /**
     * Show the privacy consent form.
     */
    public function show()
    {
        return view('auth.privacy-consent');
    }

    /**
     * Handle the privacy consent submission.
     */
    public function accept(Request $request)
    {
        $request->validate([
            'privacy_policy' => ['required', 'accepted'],
            'receives_product_updates' => ['nullable', 'boolean'],
        ]);

        $user = Auth::user();
        
        $user->update([
            'privacy_policy_accepted_at' => now(),
            'receives_product_updates' => $request->boolean('receives_product_updates'),
            'product_updates_consent_at' => $request->boolean('receives_product_updates') ? now() : $user->product_updates_consent_at,
        ]);

        return redirect()->intended(route('home'));
    }
}
