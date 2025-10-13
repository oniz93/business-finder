<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class CompetitorNotification extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public BusinessPlan $businessPlan, public string $competitor)
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
            ->subject('New Competitor for ' . $this->businessPlan->title)
            ->line('A new competitor has been identified for the business idea: ' . $this->businessPlan->title)
            ->line('Competitor: ' . $this->competitor)
            ->action('View Full Plan', route('business-plan', ['id' => $this->businessPlan->id]))
            ->line('Thank you for using our application!');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'business_plan_id' => $this->businessPlan->id,
            'title' => $this->businessPlan->title,
            'competitor' => $this->competitor,
        ];
    }
}
