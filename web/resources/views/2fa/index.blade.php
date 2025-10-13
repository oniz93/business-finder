<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 dark:text-gray-200 leading-tight">
            {{ __('Two Factor Authentication') }}
        </h2>
    </x-slot>

    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6 text-gray-900 dark:text-gray-100">
                    @if (session('status') == '2fa-enabled')
                        <div class="mb-4 font-medium text-sm text-green-600">
                            Two factor authentication has been enabled.
                        </div>
                    @endif

                    @if (session('status') == '2fa-disabled')
                        <div class="mb-4 font-medium text-sm text-green-600">
                            Two factor authentication has been disabled.
                        </div>
                    @endif

                    @if ($user->google2fa_enabled)
                        <p>Two factor authentication is enabled.</p>
                        <form method="POST" action="{{ route('2fa.disable') }}">
                            @csrf
                            <button type="submit" class="btn btn-danger">Disable 2FA</button>
                        </form>
                    @else
                        <p>Two factor authentication is disabled.</p>
                        <p>Scan the QR code below to enable it.</p>
                        <div>
                            {!! $qrCodeUrl !!}
                        </div>
                        <form method="POST" action="{{ route('2fa.enable') }}">
                            @csrf
                            <div>
                                <x-input-label for="otp" :value="__('One Time Password')" />
                                <x-text-input id="otp" name="otp" type="text" class="mt-1 block w-full" required autofocus />
                            </div>
                            <div class="flex items-center justify-end mt-4">
                                <x-primary-button>
                                    {{ __('Enable 2FA') }}
                                </x-primary-button>
                            </div>
                        </form>
                    @endif
                </div>
            </div>
        </div>
    </div>
</x-app-layout>
