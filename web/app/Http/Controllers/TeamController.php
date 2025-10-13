<?php

namespace App\Http\Controllers;

use App\Models\Team;
use App\Models\User;
use Illuminate\Http\Request;

class TeamController extends Controller
{
    public function index()
    {
        return auth()->user()->teams()->with('owner', 'members')->get();
    }

    public function store(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:255',
        ]);

        $team = auth()->user()->ownedTeams()->create($request->all());
        $team->members()->attach(auth()->id());

        return $team->load('owner', 'members');
    }

    public function show(Team $team)
    {
        $this->authorize('view', $team);

        return $team->load('owner', 'members');
    }

    public function update(Request $request, Team $team)
    {
        $this->authorize('update', $team);

        $request->validate([
            'name' => 'required|string|max:255',
        ]);

        $team->update($request->all());

        return $team->load('owner', 'members');
    }

    public function destroy(Team $team)
    {
        $this->authorize('delete', $team);

        $team->delete();

        return response()->noContent();
    }

    public function addMember(Request $request, Team $team)
    {
        $this->authorize('update', $team);

        $request->validate([
            'user_id' => 'required|exists:users,id',
        ]);

        $team->members()->attach($request->user_id);

        return $team->load('members');
    }

    public function removeMember(Team $team, User $user)
    {
        $this->authorize('update', $team);

        $team->members()->detach($user->id);

        return response()->noContent();
    }
}
