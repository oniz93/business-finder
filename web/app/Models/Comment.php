<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Comment extends Model
{
    use HasFactory;

    protected $fillable = ['user_id', 'business_plan_id', 'body'];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function businessPlan()
    {
        return $this->belongsTo(BusinessPlan::class);
    }
}
