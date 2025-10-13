<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class TrendChangeNotification extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public BusinessPlan $businessPlan, public string $trend)
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
            ->subject('Trend Change for ' . $this->businessPlan->title)
            ->line('There has been a significant trend change for the business idea: ' . $this->businessPlan->title)
            ->line('Trend: ' . $this->trend)
            ->action('View Full Plan', route('business-plan', ['id' => $this->businessPlan->id]))
            ->line('Thank you for using our application!');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'business_plan_id' => $this->businessPlan->id,
            'title' => $this->businessPlan->title,
            'trend' => $this->trend,
        ];
    }
}
