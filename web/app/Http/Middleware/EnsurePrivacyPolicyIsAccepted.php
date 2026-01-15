<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsurePrivacyPolicyIsAccepted
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        if ($request->user() && 
            !$request->user()->privacy_policy_accepted_at && 
            !$request->routeIs('privacy.consent', 'privacy.accept', 'logout')) {
            return redirect()->route('privacy.consent');
        }

        return $next($request);
    }
}
