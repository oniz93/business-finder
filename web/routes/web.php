<?php

use App\Http\Controllers\BusinessPlanController;
use App\Livewire\BusinessPlanSearch;
use App\Livewire\BusinessPlanPage;
use App\Http\Controllers\WaitlistController;

Route::get('/', [BusinessPlanController::class, 'random'])->name('home');
Route::get('/business-plans', BusinessPlanSearch::class)->name('business-plans');
Route::get('/business-plans/{id}', BusinessPlanPage::class)->name('business-plan');
Route::post('/waitlist', [WaitlistController::class, 'store'])->name('waitlist.store');

Route::view('dashboard', 'dashboard')
    ->middleware(['auth', 'verified'])
    ->name('dashboard');

Route::middleware(['auth'])->group(function () {
    Route::redirect('settings', 'settings/profile');

    // Volt::route('settings/profile', 'settings.profile')->name('profile.edit');
    // Volt::route('settings/password', 'settings.password')->name('password.edit');
    // Volt::route('settings/appearance', 'settings.appearance')->name('appearance.edit');

    // Volt::route('settings/two-factor', 'settings.two-factor')
    //     ->middleware(
    //         when(
    //             Features::canManageTwoFactorAuthentication()
    //                 && Features::optionEnabled(Features::twoFactorAuthentication(), 'confirmPassword'),
    //             ['password.confirm'],
    //             [],
    //         ),
    //     )
    //     ->name('two-factor.show');
});

require __DIR__.'/auth.php';
