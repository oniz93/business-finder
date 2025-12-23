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
            $table->renameColumn('summary', 'original_summary');
            $table->renameColumn('ids_in_cluster', 'message_ids');
            $table->renameColumn('texts', 'texts_combined');

            $table->text('cluster_summary')->nullable();
            $table->boolean('is_viable_business')->nullable();
            $table->boolean('is_saas')->nullable();
            $table->boolean('is_solo_entrepreneur_possible')->nullable();
            $table->integer('message_count')->nullable();
            $table->string('generated_plan')->nullable();
            $table->timestamp('generated_at')->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('business_plans', function (Blueprint $table) {
            $table->renameColumn('original_summary', 'summary');
            $table->renameColumn('message_ids', 'ids_in_cluster');
            $table->renameColumn('texts_combined', 'texts');

            $table->dropColumn([
                'cluster_summary',
                'is_viable_business',
                'is_saas',
                'is_solo_entrepreneur_possible',
                'message_count',
                'generated_plan',
                'generated_at',
            ]);
        });
    }
};