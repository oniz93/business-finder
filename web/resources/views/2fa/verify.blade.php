<x-guest-layout>
    <div class="mb-4 text-sm text-gray-600">
        {{ __('Please enter the one-time password from your authenticator app.') }}
    </div>

    <!-- Session Status -->
    <x-auth-session-status class="mb-4" :status="session('status')" />

    <form method="POST" action="{{ route('2fa.verify.post') }}">
        @csrf

        <!-- OTP -->
        <div>
            <x-input-label for="otp" :value="__('One Time Password')" />
            <x-text-input id="otp" class="block mt-1 w-full" type="text" name="otp" required autofocus />
            <x-input-error :messages="$errors->get('otp')" class="mt-2" />
        </div>

        <div class="flex items-center justify-end mt-4">
            <x-primary-button>
                {{ __('Verify') }}
            </x-primary-button>
        </div>
    </form>
</x-guest-layout>
