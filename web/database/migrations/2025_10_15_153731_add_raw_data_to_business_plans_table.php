<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('business_plans', function (Blueprint $table) {
            $table->string('subreddit')->nullable();
            $table->json('ids_in_cluster')->nullable();
            $table->json('texts')->nullable();
            $table->integer('total_ups')->nullable();
            $table->integer('total_downs')->nullable();
            $table->text('summary')->nullable();
            $table->integer('cluster_id')->nullable();
            $table->integer('viability_score')->nullable();
            $table->text('viability_reasoning')->nullable();
            $table->json('management_team')->nullable();
            $table->json('financial_projections')->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('business_plans', function (Blueprint $table) {
            $table->dropColumn([
                'subreddit',
                'ids_in_cluster',
                'texts',
                'total_ups',
                'total_downs',
                'summary',
                'cluster_id',
                'viability_score',
                'viability_reasoning',
                'management_team',
                'financial_projections',
            ]);
        });
    }
};
