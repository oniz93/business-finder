<?php

use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Auth\NewPasswordController;
use App\Http\Controllers\Auth\PasswordResetLinkController;
use App\Http\Controllers\Auth\RegisteredUserController;
use App\Http\Controllers\BusinessPlanController;
use App\Http\Controllers\WaitlistController;
use Illuminate\Support\Facades\Route;

Route::get('/', [BusinessPlanController::class, 'random'])->middleware('throttle:guests')->name('home');
Route::get('/business-plans/{businessPlan}', [BusinessPlanController::class, 'show'])->name('business-plan');
Route::get('/business-plans/{businessPlan}/canvas', App\Livewire\BusinessModelCanvasDisplay::class)->name('business-plans.canvas');
Route::get('/business-plans/{businessPlan}/pitch-deck', App\Livewire\PitchDeckDisplay::class)->name('business-plans.pitch-deck');
Route::get('/business-plans/{businessPlan}/financial-projections', App\Livewire\FinancialProjections::class)->name('business-plans.financial-projections');
Route::post('/waitlist', [WaitlistController::class, 'store'])->name('waitlist.store');

Route::get('/dashboard', App\Livewire\UserDashboard::class)->middleware(['auth', 'verified'])->name('dashboard');

Route::middleware('guest')->group(function () {
    Route::get('register', [RegisteredUserController::class, 'create'])
        ->name('register');

    Route::post('register', [RegisteredUserController::class, 'store']);

    Route::get('login', [AuthenticatedSessionController::class, 'create'])
        ->name('login');

    Route::post('login', [AuthenticatedSessionController::class, 'store']);

    Route::get('forgot-password', [PasswordResetLinkController::class, 'create'])
        ->name('password.request');

    Route::post('forgot-password', [PasswordResetLinkController::class, 'store'])
        ->name('password.email');

    Route::get('reset-password/{token}', [NewPasswordController::class, 'create'])
        ->name('password.reset');

    Route::post('reset-password', [NewPasswordController::class, 'store'])
        ->name('password.store');
});

use App\Http\Controllers\SearchController;
use App\Livewire\BusinessPlanSearch;

Route::get('/business-plan-search', BusinessPlanSearch::class)->name('business-plan-search.index');
Route::post('/business-plan-search', [SearchController::class, 'handlePostSearch'])->name('business-plan-search.post');

require __DIR__ . '/auth.php';

