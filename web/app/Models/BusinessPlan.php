<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Laravel\Scout\Searchable;

class BusinessPlan extends Model
{
    use HasFactory, Searchable;

    /**
     * Get the index name for the model.
     */
    public function searchableAs(): string
    {
        return 'business_plans';
    }
}
