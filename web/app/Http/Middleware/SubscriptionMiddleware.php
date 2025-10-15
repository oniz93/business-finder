<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class SubscriptionMiddleware
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    protected $plans = [
        'free',
        'founder',
        'innovator',
        'enterprise',
    ];

    public function handle(Request $request, Closure $next, $plan): Response
    {
        if (! $request->user()) {
            return redirect('login');
        }

        $userPlanIndex = array_search($request->user()->plan, $this->plans);
        $requiredPlanIndex = array_search($plan, $this->plans);

        if ($userPlanIndex < $requiredPlanIndex) {
            return redirect()->route('upgrade-plan');
        }

        return $next($request);
    }
}
