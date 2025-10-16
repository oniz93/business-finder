<?php

use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Auth\ConfirmablePasswordController;
use App\Http\Controllers\Auth\EmailVerificationNotificationController;
use App\Http\Controllers\Auth\EmailVerificationPromptController;
use App\Http\Controllers\Auth\PasswordController;
use App\Http\Controllers\Auth\VerifyEmailController;
use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth')->group(function () {
    Route::get('verify-email', EmailVerificationPromptController::class)
        ->name('verification.notice');

    Route::get('verify-email/{id}/{hash}', VerifyEmailController::class)
        ->middleware(['signed', 'throttle:6,1'])
        ->name('verification.verify');

    Route::post('email/verification-notification', [EmailVerificationNotificationController::class, 'store'])
        ->middleware('throttle:6,1')
        ->name('verification.send');

    Route::get('confirm-password', [ConfirmablePasswordController::class, 'show'])
        ->name('password.confirm');

    Route::post('confirm-password', [ConfirmablePasswordController::class, 'store']);

    Route::put('password', [PasswordController::class, 'update'])->name('password.update');

    Route::post('logout', [AuthenticatedSessionController::class, 'destroy'])
        ->name('logout');
});

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');

    Route::get('/2fa', [App\Http\Controllers\Google2FAController::class, 'index'])->name('2fa.index');
    Route::post('/2fa/enable', [App\Http\Controllers\Google2FAController::class, 'enable'])->name('2fa.enable');
    Route::post('/2fa/disable', [App\Http\Controllers\Google2FAController::class, 'disable'])->name('2fa.disable');
    Route::get('/2fa/verify', [App\Http\Controllers\Google2FAController::class, 'verify'])->name('2fa.verify');
    Route::post('/2fa/verify', [App\Http\Controllers\Google2FAController::class, 'verify'])->name('2fa.verify.post');

    Route::middleware(['auth', 'subscription:founder'])->group(function () {
        Route::get('/business-plan-search', App\Livewire\BusinessPlanSearch::class)->name('business-plan-search');
        Route::get('/collections', App\Livewire\UserCollections::class)->name('collections.index');
        Route::get('/resources', App\Livewire\ResourceList::class)->name('resources.index');
        Route::get('/collections/share/{shareableLink}', App\Livewire\SharedCollectionPage::class)->name('collections.share');
    });

    Route::middleware(['auth', 'subscription:innovator'])->group(function () {
        Route::get('/business-plans/{businessPlan}/canvas', App\Livewire\BusinessModelCanvasDisplay::class)->name('business-plans.canvas');
        Route::get('/business-plans/{businessPlan}/financial-projections', App\Livewire\FinancialProjections::class)->name('business-plans.financial-projections');
        Route::get('/business-plans/{businessPlan}/edit', App\Livewire\EditBusinessPlan::class)->name('business-plans.edit');
        Route::get('/scoring-criteria', App\Livewire\ScoringCriteriaManagement::class)->name('scoring-criteria.index');
    });

    Route::middleware(['auth', 'subscription:enterprise'])->group(function () {
        Route::get('/business-plans/{businessPlan}/pitch-deck', App\Livewire\PitchDeckDisplay::class)->name('business-plans.pitch-deck');
        Route::get('/teams', App\Livewire\TeamManagement::class)->name('teams.index');
        Route::get('/teams/{team}/workspace', App\Livewire\TeamWorkspace::class)->name('teams.workspace');
    });
    Route::get('/marketplace', App\Livewire\ProductListings::class)->name('marketplace.index');
    Route::get('/marketplace/{product}', App\Livewire\ProductPurchase::class)->name('marketplace.show');

    Route::get('/auth/{provider}/redirect', [App\Http\Controllers\SocialiteController::class, 'redirect']);
    Route::get('/auth/{provider}/callback', [App\Http\Controllers\SocialiteController::class, 'callback']);

});
