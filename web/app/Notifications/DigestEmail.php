<?php

namespace App\Notifications;

use App\Models\BusinessPlan;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;
use Illuminate\Support\Collection;

class DigestEmail extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public Collection $businessPlans)
    {
        //
    }

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $mailMessage = (new MailMessage)
            ->subject('Your Daily Business Idea Digest')
            ->line('Here are some new business ideas you might be interested in:');

        foreach ($this->businessPlans as $plan) {
            $mailMessage->line('**' . $plan->title . '**')
                        ->line($plan->executive_summary)
                        ->action('View Plan', route('business-plan', ['id' => $plan->id]))
                        ->line('---');
        }

        return $mailMessage->line('Thank you for using our application!');
    }

    public function toArray(object $notifiable): array
    {
        return [
            'business_plans' => $this->businessPlans->map(function ($plan) {
                return [
                    'id' => $plan->id,
                    'title' => $plan->title,
                    'executive_summary' => $plan->executive_summary,
                ];
            })->toArray(),
        ];
    }
}
