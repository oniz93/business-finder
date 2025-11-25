<?php

namespace App\Livewire;

use Livewire\Component;
use Illuminate\Support\Facades\Auth;

class NotificationPreferences extends Component
{
    public $preferences = [];

    public $notificationTypes = [
        'new_business_idea' => 'New Business Idea Notifications',
        'trend_change' => 'Trend Change Notifications',
        'competitor_alert' => 'Competitor Alerts',
        'saved_plan_update' => 'Saved Plan Updates',
        'personalized_recommendation' => 'Personalized Recommendations',
        'digest_email' => 'Daily/Weekly Digest Emails',
    ];

    public function mount()
    {
        if (Auth::check()) {
            $userPreferences = Auth::user()->notification_preferences;
            // Initialize preferences with defaults if not set
            foreach ($this->notificationTypes as $key => $value) {
                $this->preferences[$key] = $userPreferences[$key] ?? true; // Default to true
            }
        }
    }

    public function updatePreferences()
    {
        if (Auth::check()) {
            Auth::user()->forceFill([
                'notification_preferences' => $this->preferences,
            ])->save();
            session()->flash('message', 'Notification preferences updated successfully!');
        } else {
            session()->flash('error', 'You must be logged in to update preferences.');
        }
    }

    public function render()
    {
        return view('livewire.notification-preferences');
    }
}
