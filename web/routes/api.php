<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

Route::middleware(['auth:sanctum', 'throttle:api'])->group(function () {
    Route::post('/collections/{collection}/business-plans/{businessPlan}', [App\Http\Controllers\CollectionController::class, 'addBusinessPlan']);
    Route::delete('/collections/{collection}/business-plans/{businessPlan}', [App\Http\Controllers\CollectionController::class, 'removeBusinessPlan']);
    Route::post('/collections/{collection}/tags', [App\Http\Controllers\CollectionController::class, 'syncTags']);
    Route::get('/collections/search', [App\Http\Controllers\CollectionController::class, 'search']);
    Route::get('/business-plans/search', [App\Http\Controllers\BusinessPlanController::class, 'search']);

    Route::get('/business-plans/{businessPlan}/comments', [App\Http\Controllers\CommentController::class, 'index']);
    Route::post('/business-plans/{businessPlan}/comments', [App\Http\Controllers\CommentController::class, 'store']);
    Route::delete('/comments/{comment}', [App\Http\Controllers\CommentController::class, 'destroy']);

    Route::post('/business-plans/{businessPlan}/feedback', [App\Http\Controllers\FeedbackController::class, 'store']);

    Route::apiResource('teams', App\Http\Controllers\TeamController::class);
    Route::post('/teams/{team}/members', [App\Http\Controllers\TeamController::class, 'addMember']);
    Route::delete('/teams/{team}/members/{user}', [App\Http\Controllers\TeamController::class, 'removeMember']);

    Route::get('/business-plans/{businessPlan}/canvas', [App\Http\Controllers\BusinessModelCanvasController::class, 'show']);
    Route::get('/business-plans/{businessPlan}/pitch-deck', [App\Http\Controllers\PitchDeckController::class, 'show']);

    Route::post('/financial-projections/calculate', [App\Http\Controllers\FinancialProjectionController::class, 'calculate']);
    Route::post('/financial-projections/scenario', [App\Http\Controllers\FinancialProjectionController::class, 'scenario']);
    Route::post('/financial-projections/sensitivity', [App\Http\Controllers\FinancialProjectionController::class, 'sensitivity']);

    Route::get('/resources', [App\Http\Controllers\ResourceController::class, 'index']);

    Route::apiResource('widgets', App\Http\Controllers\WidgetController::class);

    Route::apiResource('scoring-criteria', App\Http\Controllers\ScoringCriteriaController::class);

    Route::apiResource('products', App\Http\Controllers\ProductController::class);

    Route::post('/payments', [App\Http\Controllers\PaymentController::class, 'store']);

    Route::apiResource('reviews', App\Http\Controllers\ReviewController::class)->except(['index', 'store']);
    Route::get('/products/{product}/reviews', [App\Http\Controllers\ReviewController::class, 'index']);
    Route::post('/products/{product}/reviews', [App\Http\Controllers\ReviewController::class, 'store']);
});
