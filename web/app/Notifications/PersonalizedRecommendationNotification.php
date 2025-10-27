<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class PersonalizedRecommendationNotification extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public BusinessPlan $businessPlan)
    {
        //
    }

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        return (new MailMessage)
            ->subject('Personalized Business Idea Recommendation: ' . $this->businessPlan->title)
            ->line('We thought you might be interested in this business idea: ' . $this->businessPlan->title)
            ->line($this->businessPlan->executive_summary)
            ->action('View Full Plan', route('business-plan', ['id' => $this->businessPlan->id]))
            ->line('Thank you for using our application!');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'business_plan_id' => $this->businessPlan->id,
            'title' => $this->businessPlan->title,
            'executive_summary' => $this->businessPlan->executive_summary,
        ];
    }
}
