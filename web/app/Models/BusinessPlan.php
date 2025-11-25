<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Laravel\Scout\Searchable;
use Venturecraft\Revisionable\RevisionableTrait;

class BusinessPlan extends Model
{
    use HasFactory, RevisionableTrait, Searchable;

    public $incrementing = false; // Disable auto-incrementing for the primary key
    protected $keyType = 'string'; // Set the primary key type to string

    protected static function boot()
    {
        parent::boot();

        static::creating(function ($model) {
            $model->{$model->getKeyName()} = (string) \Illuminate\Support\Str::uuid();
        });
    }

    public function toSearchableArray()
    {
        return [
            'title' => $this->title,
            'executive_summary' => $this->executive_summary,
            'problem' => $this->problem,
            'solution' => $this->solution,
            'market_analysis' => $this->market_analysis,
            'competition' => $this->competition,
            'marketing_strategy' => $this->marketing_strategy,
            'call_to_action' => $this->call_to_action,
        ];
    }

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
    public function collections()
    {
        return $this->belongsToMany(Collection::class, 'business_plan_collection');
    }

    public function comments()
    {
        return $this->hasMany(Comment::class);
    }

    public function feedback()
    {
        return $this->hasMany(Feedback::class);
    }
}
