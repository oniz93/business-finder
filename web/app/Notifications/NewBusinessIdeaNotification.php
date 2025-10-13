<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class NewBusinessIdeaNotification extends Notification implements ShouldQueue
{
    use Queueable;

    /**
     * Create a new notification instance.
     */
    public function __construct(public BusinessPlan $businessPlan)
    {
        //
    }

    /**
     * Get the notification's delivery channels.
     *
     * @return array<int, string>
     */
    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    /**
     * Get the mail representation of the notification.
     */
    public function toMail(object $notifiable): MailMessage
    {
        return (new MailMessage)
            ->subject('New Business Idea: ' . $this->businessPlan->title)
            ->line($this->businessPlan->executive_summary)
            ->action('View Full Plan', route('business-plan', ['id' => $this->businessPlan->id]))
            ->line('Thank you for using our application!');
    }

    /**
     * Get the array representation of the notification.
     *
     * @return array<string, mixed>
     */
    public function toArray(object $notifiable): array
    {
        return [
            'business_plan_id' => $this->businessPlan->id,
            'title' => $this->businessPlan->title,
            'executive_summary' => $this->businessPlan->executive_summary,
        ];
    }
}
