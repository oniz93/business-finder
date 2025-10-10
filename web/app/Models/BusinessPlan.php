<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class BusinessPlan extends Model
{
    use HasFactory;

    public $incrementing = false; // Disable auto-incrementing for the primary key
    protected $keyType = 'string'; // Set the primary key type to string

    protected $fillable = [
        'subreddit',
        'ids_in_cluster',
        'texts',
        'total_ups',
        'total_downs',
        'summary',
        'cluster_id',
        'viability_score',
        'viability_reasoning',
        'title',
        'executive_summary',
        'problem',
        'solution',
        'market_analysis',
        'competition',
        'marketing_strategy',
        'management_team',
        'financial_projections',
        'call_to_action',
    ];

    protected $casts = [
        'ids_in_cluster' => 'array',
        'texts' => 'array',
        'total_ups' => 'integer',
        'total_downs' => 'integer',
        'cluster_id' => 'integer',
        'viability_score' => 'integer',
        'market_analysis' => 'array',
        'competition' => 'array',
        'marketing_strategy' => 'array',
        'management_team' => 'array',
        'financial_projections' => 'array',
    ];
}
