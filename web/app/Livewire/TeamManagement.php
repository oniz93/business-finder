<?php

namespace App\Livewire;

use Livewire\Component;
use App\Models\Team;
use App\Models\User;
use Illuminate\Support\Facades\Auth;
use Illuminate\Validation\Rule;

class TeamManagement extends Component
{
    public $teams;
    public $newTeamName = '';
    public $editingTeamId = null;
    public $newMemberEmail = '';

    protected $rules = [
        'newTeamName' => 'required|string|min:3|max:255',
        'newMemberEmail' => 'required|email|exists:users,email',
    ];

    public function mount()
    {
        $this->loadTeams();
    }

    public function loadTeams()
    {
        if (Auth::check()) {
            $this->teams = Auth::user()->ownedTeams()->with('members')->get();
        } else {
            $this->teams = collect();
        }
    }

    public function createTeam()
    {
        $this->validateOnly('newTeamName');

        if (Auth::check()) {
            Auth::user()->ownedTeams()->create([
                'name' => $this->newTeamName,
            ]);
            $this->newTeamName = '';
            $this->loadTeams();
            session()->flash('message', 'Team created successfully!');
        } else {
            session()->flash('error', 'You must be logged in to create a team.');
        }
    }

    public function editTeam($teamId)
    {
        $this->editingTeamId = $teamId;
        $this->newMemberEmail = ''; // Clear previous email
    }

    public function addMember($teamId)
    {
        $this->validateOnly('newMemberEmail');

        $team = Team::find($teamId);
        $userToAdd = User::where('email', $this->newMemberEmail)->first();

        if ($team && $userToAdd && Auth::id() === $team->user_id) {
            $team->members()->attach($userToAdd->id);
            $this->newMemberEmail = '';
            $this->loadTeams();
            session()->flash('message', 'Member added successfully!');
        } else {
            session()->flash('error', 'Failed to add member. Check permissions or email.');
        }
    }

    public function removeMember($teamId, $userId)
    {
        $team = Team::find($teamId);

        if ($team && Auth::id() === $team->user_id) {
            $team->members()->detach($userId);
            $this->loadTeams();
            session()->flash('message', 'Member removed successfully!');
        } else {
            session()->flash('error', 'Failed to remove member. Check permissions.');
        }
    }

    public function render()
    {
        return view('livewire.team-management');
    }
}
