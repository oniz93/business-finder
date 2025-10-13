<?php

use App\Http\Controllers\BusinessPlanController;
use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;

Route::get('/', [BusinessPlanController::class, 'random'])->middleware('throttle:guests')->name('home');
Route::get('/business-plans/{businessPlan}', [BusinessPlanController::class, 'show'])->name('business-plan');
Route::post('/waitlist', [WaitlistController::class, 'store'])->name('waitlist.store');

Route::get('/dashboard', function () {
    return view('dashboard');
})->middleware(['auth', 'verified'])->name('dashboard');

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');

    Route::get('/2fa', [App\Http\Controllers\Google2FAController::class, 'index'])->name('2fa.index');
    Route::post('/2fa/enable', [App\Http\Controllers\Google2FAController::class, 'enable'])->name('2fa.enable');
    Route::post('/2fa/disable', [App\Http\Controllers\Google2FAController::class, 'disable'])->name('2fa.disable');
    Route::get('/2fa/verify', [App\Http\Controllers\Google2FAController::class, 'verify'])->name('2fa.verify');
    Route::post('/2fa/verify', [App\Http\Controllers\Google2FAController::class, 'verify'])->name('2fa.verify.post');
});

require __DIR__.'/auth.php';

Route::get('/auth/{provider}/redirect', [App\Http\Controllers\SocialiteController::class, 'redirect']);
Route::get('/auth/{provider}/callback', [App\Http\Controllers\SocialiteController::class, 'callback']);
