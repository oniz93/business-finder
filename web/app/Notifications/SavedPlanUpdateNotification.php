<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class SavedPlanUpdateNotification extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public BusinessPlan $businessPlan, public string $change)
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
            ->subject('Update for Saved Business Plan: ' . $this->businessPlan->title)
            ->line('There has been an update to your saved business plan: ' . $this->businessPlan->title)
            ->line('Change: ' . $this->change)
            ->action('View Full Plan', route('business-plan', ['id' => $this->businessPlan->id]))
            ->line('Thank you for using our application!');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'business_plan_id' => $this->businessPlan->id,
            'title' => $this->businessPlan->title,
            'change' => $this->change,
        ];
    }
}
