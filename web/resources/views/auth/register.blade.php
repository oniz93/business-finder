@extends('layouts.app')

@section('content')
<div class="flex justify-center">
    <div class="w-1/2 bg-gray-800 p-6 rounded-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">Register</h2>
        <form method="POST" action="{{ route('register') }}">
            @csrf

            <div class="mb-4">
                <label for="name" class="sr-only">Name</label>
                <input id="name" type="text" class="bg-gray-700 border-2 w-full p-4 rounded-lg @error('name') border-red-500 @enderror" name="name" value="{{ old('name') }}" required autocomplete="name" autofocus placeholder="Name">

                @error('name')
                    <span class="text-red-500 mt-2 text-sm" role="alert">
                        <strong>{{ $message }}</strong>
                    </span>
                @enderror
            </div>

            <div class="mb-4">
                <label for="email" class="sr-only">Email</label>
                <input id="email" type="email" class="bg-gray-700 border-2 w-full p-4 rounded-lg @error('email') border-red-500 @enderror" name="email" value="{{ old('email') }}" required autocomplete="email" placeholder="Email">

                @error('email')
                    <span class="text-red-500 mt-2 text-sm" role="alert">
                        <strong>{{ $message }}</strong>
                    </span>
                @enderror
            </div>

            <div class="mb-4">
                <label for="password" class="sr-only">Password</label>
                <input id="password" type="password" class="bg-gray-700 border-2 w-full p-4 rounded-lg @error('password') border-red-500 @enderror" name="password" required autocomplete="new-password" placeholder="Password">

                @error('password')
                    <span class="text-red-500 mt-2 text-sm" role="alert">
                        <strong>{{ $message }}</strong>
                    </span>
                @enderror
            </div>

            <div class="mb-4">
                <label for="password-confirm" class="sr-only">Confirm Password</label>
                <input id="password-confirm" type="password" class="bg-gray-700 border-2 w-full p-4 rounded-lg" name="password_confirmation" required autocomplete="new-password" placeholder="Confirm Password">
            </div>

            <div>
                <button type="submit" class="bg-blue-500 text-white px-4 py-3 rounded font-medium w-full">Register</button>
            </div>
        </form>
    </div>
</div>
@endsection
