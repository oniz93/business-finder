<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Casts\Attribute;
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
            'cluster_summary' => $this->cluster_summary,
            'texts_combined' => $this->texts_combined,
        ];
    }

    protected $fillable = [
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
        'plan_id',
        'cluster_id',
        'subreddit',
        'cluster_summary',
        'is_viable_business',
        'viability_score',
        'is_saas',
        'is_solo_entrepreneur_possible',
        'message_ids',
        'texts_combined',
        'total_ups',
        'total_downs',
        'message_count',
        'generated_plan',
        'generated_at',
    ];

    protected $casts = [
        'market_analysis' => 'array',
        'competition' => 'array',
        'management_team' => 'array',
        'financial_projections' => 'array',
        'generated_at' => 'datetime',
        'cluster_id' => 'integer',
        'viability_score' => 'integer',
        'is_viable_business' => 'boolean',
        'is_saas' => 'boolean',
        'is_solo_entrepreneur_possible' => 'boolean',
        'message_ids' => 'array',
        'total_ups' => 'integer',
        'total_downs' => 'integer',
        'message_count' => 'integer',
    ];

    protected function marketingStrategy(): Attribute
    {
        return Attribute::make(
            get: function ($value) {
                $decodedValue = is_string($value) ? json_decode($value, true) : $value;

                if (isset($decodedValue['retention']) && is_string($decodedValue['retention'])) {
                    $retentionArray = json_decode($decodedValue['retention'], true);
                    if (json_last_error() === JSON_ERROR_NONE) {
                        $decodedValue['retention'] = $retentionArray;
                    }
                }
                return $decodedValue;
            },
        );
    }

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
