<?php

namespace App\Livewire;

use Livewire\Component;
use Illuminate\Support\Facades\Auth;
use Illuminate\Notifications\DatabaseNotification;

class InAppNotifications extends Component
{
    public $unreadNotifications;
    public $showNotifications = false;

    protected $listeners = ['refreshNotifications' => 'mount'];

    public function mount()
    {
        if (Auth::check()) {
            $this->unreadNotifications = Auth::user()->unreadNotifications;
        } else {
            $this->unreadNotifications = collect();
        }
    }

    public function markAsRead($notificationId)
    {
        if (Auth::check()) {
            Auth::user()->notifications()->where('id', $notificationId)->first()->markAsRead();
            $this->mount(); // Refresh notifications
        }
    }

    public function markAllAsRead()
    {
        if (Auth::check()) {
            Auth::user()->unreadNotifications->markAsRead();
            $this->mount(); // Refresh notifications
        }
    }

    public function toggleNotifications()
    {
        $this->showNotifications = !$this->showNotifications;
    }

    public function render()
    {
        return view('livewire.in-app-notifications');
    }
}
