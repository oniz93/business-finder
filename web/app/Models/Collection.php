<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Spatie\Tags\HasTags;

class Collection extends Model
{
    use HasFactory, HasTags;

    protected $fillable = ['user_id', 'name', 'description', 'shareable_link'];

    protected static function boot()
    {
        parent::boot();

        static::creating(function ($collection) {
            $collection->shareable_link = \Illuminate\Support\Str::random(32);
        });
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function businessPlans()
    {
        return $this->belongsToMany(BusinessPlan::class, 'business_plan_collection');
    }
}
