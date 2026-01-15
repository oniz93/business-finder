<?php

namespace App\Models;

use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Spatie\Activitylog\Traits\LogsActivity;
use Spatie\Activitylog\LogOptions;

class User extends Authenticatable implements MustVerifyEmail
{
    /** @use HasFactory<\Database\Factories\UserFactory> */
    use HasFactory, Notifiable; //, LogsActivity;

    protected static $logAttributes = ['name', 'email'];

    public function getActivitylogOptions(): LogOptions
    {
        return LogOptions::defaults()
            ->logOnly(['name', 'email'])
            ->setDescriptionForEvent(fn(string $eventName) => "This model has been {$eventName}");
    }

    /**
     * The attributes that are mass assignable.
     *
     * @var list<string>
     */
    protected $fillable = [
        'name',
        'email',
        'password',
        'provider',
        'provider_id',
        'provider_token',
        'provider_refresh_token',
        'notification_preferences',
        'plan',
        'privacy_policy_accepted_at',
        'receives_product_updates',
        'product_updates_consent_at',
    ];

    public function profile()
    {
        return $this->hasOne(Profile::class);
    }

    public function collections()
    {
        return $this->hasMany(Collection::class);
    }

    public function comments()
    {
        return $this->hasMany(Comment::class);
    }

    public function feedback()
    {
        return $this->hasMany(Feedback::class);
    }

    public function teams()
    {
        return $this->belongsToMany(Team::class, 'team_user');
    }

    public function ownedTeams()
    {
        return $this->hasMany(Team::class, 'user_id');
    }

    public function isMemberOfTeam(Team $team)
    {
        return $this->ownedTeams->contains($team) || $this->teams->contains($team);
    }

    public function widgets()
    {
        return $this->hasMany(Widget::class);
    }

    public function scoringCriterias()
    {
        return $this->hasMany(ScoringCriteria::class);
    }

    public function products()
    {
        return $this->hasMany(Product::class);
    }

    public function reviews()
    {
        return $this->hasMany(Review::class);
    }

    public function subscription()
    {
        return $this->hasOne(Subscription::class);
    }

    public function hasSubscribed()
    {
        return $this->subscription && $this->subscription->stripe_status === 'active';
    }

    public function onTrial()
    {
        return $this->subscription && $this->subscription->onTrial();
    }

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var list<string>
     */
    protected $hidden = [
        'password',
        'remember_token',
    ];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'notification_preferences' => 'array',
            'privacy_policy_accepted_at' => 'datetime',
            'receives_product_updates' => 'boolean',
            'product_updates_consent_at' => 'datetime',
        ];
    }
}
