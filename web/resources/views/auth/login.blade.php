@extends('layouts.app')

@section('content')
<div class="flex justify-center">
    <div class="w-1/2 bg-gray-800 p-6 rounded-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
        <form method="POST" action="{{ route('login') }}">
            @csrf

            <div class="mb-4">
                <label for="email" class="sr-only">Email</label>
                <input id="email" type="email" class="bg-gray-700 border-2 w-full p-4 rounded-lg @error('email') border-red-500 @enderror" name="email" value="{{ old('email') }}" required autocomplete="email" autofocus placeholder="Email">

                @error('email')
                    <span class="text-red-500 mt-2 text-sm" role="alert">
                        <strong>{{ $message }}</strong>
                    </span>
                @enderror
            </div>

            <div class="mb-4">
                <label for="password" class="sr-only">Password</label>
                <input id="password" type="password" class="bg-gray-700 border-2 w-full p-4 rounded-lg @error('password') border-red-500 @enderror" name="password" required autocomplete="current-password" placeholder="Password">

                @error('password')
                    <span class="text-red-500 mt-2 text-sm" role="alert">
                        <strong>{{ $message }}</strong>
                    </span>
                @enderror
            </div>

            <div class="mb-4">
                <div class="flex items-center">
                    <input class="mr-2" type="checkbox" name="remember" id="remember" {{ old('remember') ? 'checked' : '' }}>
                    <label for="remember">
                        Remember Me
                    </label>
                </div>
            </div>

            <div>
                <button type="submit" class="bg-blue-500 text-white px-4 py-3 rounded font-medium w-full">Login</button>
            </div>
        </form>
    </div>
</div>
@endsection
