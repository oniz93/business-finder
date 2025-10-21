<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ScoringCriteria extends Model
{
    use HasFactory;

    protected $fillable = ['user_id', 'name', 'criteria', 'weight'];

    protected $casts = [
        'criteria' => 'array',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
