<?php

use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Auth\ConfirmablePasswordController;
use App\Http\Controllers\Auth\EmailVerificationNotificationController;
use App\Http\Controllers\Auth\EmailVerificationPromptController;
use App\Http\Controllers\Auth\NewPasswordController;
use App\Http\Controllers\Auth\PasswordController;
use App\Http\Controllers\Auth\PasswordResetLinkController;
use App\Http\Controllers\Auth\RegisteredUserController;
use App\Http\Controllers\Auth\VerifyEmailController;
use App\Http\Controllers\BusinessPlanController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\SocialiteController;
use App\Http\Controllers\WaitlistController;
use App\Livewire\BusinessPlanSearch;
use App\Livewire\UserCollections;
use App\Livewire\ResourceList;
use App\Livewire\SharedCollectionPage;
use App\Livewire\BusinessModelCanvasDisplay;
use App\Livewire\FinancialProjections;
use App\Livewire\EditBusinessPlan;
use App\Livewire\ScoringCriteriaManagement;
use App\Livewire\PitchDeckDisplay;
use App\Livewire\TeamManagement;
use App\Livewire\TeamWorkspace;
use App\Livewire\ProductListings;
use App\Livewire\ProductPurchase;
use Illuminate\Support\Facades\Route;

Route::get('/', [BusinessPlanController::class, 'random'])->middleware('throttle:guests')->name('home');
Route::get('/business-plans/{businessPlan}', [BusinessPlanController::class, 'show'])->name('business-plan');
Route::get('/business-plans/{businessPlan}/canvas', BusinessModelCanvasDisplay::class)->name('business-plans.canvas');
Route::get('/business-plans/{businessPlan}/pitch-deck', PitchDeckDisplay::class)->name('business-plans.pitch-deck');
Route::get('/business-plans/{businessPlan}/financial-projections', FinancialProjections::class)->name('business-plans.financial-projections');
Route::post('/waitlist', [WaitlistController::class, 'store'])->name('waitlist.store');

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

Route::get('/business-plan-search', BusinessPlanSearch::class)->name('business-plan-search.index');

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
        Route::get('/collections', UserCollections::class)->name('collections.index');
        Route::get('/resources', ResourceList::class)->name('resources.index');
        Route::get('/collections/share/{shareableLink}', SharedCollectionPage::class)->name('collections.share');
    });

    Route::middleware(['auth', 'subscription:innovator'])->group(function () {
        Route::get('/business-plans/{businessPlan}/edit', EditBusinessPlan::class)->name('business-plans.edit');
        Route::get('/scoring-criteria', ScoringCriteriaManagement::class)->name('scoring-criteria.index');
    });

    Route::middleware(['auth', 'subscription:enterprise'])->group(function () {
        Route::get('/teams', TeamManagement::class)->name('teams.index');
        Route::get('/teams/{team}/workspace', TeamWorkspace::class)->name('teams.workspace');
    });
    Route::get('/marketplace', ProductListings::class)->name('marketplace.index');
    Route::get('/marketplace/{product}', ProductPurchase::class)->name('marketplace.show');

    Route::get('/auth/{provider}/redirect', [SocialiteController::class, 'redirect']);
    Route::get('/auth/{provider}/callback', [SocialiteController::class, 'callback']);

});

