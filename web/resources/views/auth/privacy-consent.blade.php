<x-guest-layout>
    <div class="mb-4 text-sm text-gray-600 dark:text-gray-400">
        {{ __('Before continuing, please review and accept our Privacy Policy. You can also choose to receive product updates.') }}
    </div>

    <!-- Session Status -->
    <x-auth-session-status class="mb-4" :status="session('status')" />

    <form method="POST" action="{{ route('privacy.accept') }}">
        @csrf

        <!-- Privacy Policy -->
        <div>
            <label for="privacy_policy" class="inline-flex items-center">
                <input id="privacy_policy" type="checkbox" class="rounded dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-indigo-600 shadow-sm focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:focus:ring-offset-gray-800" name="privacy_policy" required>
                <span class="ms-2 text-sm text-gray-600 dark:text-gray-400">
                    {{ __('I accept the') }} 
                    <a href="https://www.iubenda.com/privacy-policy/22933065" class="iubenda-black iubenda-noiframe iubenda-embed iubenda-noiframe underline" title="Privacy Policy ">Privacy Policy</a>
                    <script type="text/javascript">(function (w,d) {var loader = function () {var s = d.createElement("script"), tag = d.getElementsByTagName("script")[0]; s.src="https://cdn.iubenda.com/iubenda.js"; tag.parentNode.insertBefore(s,tag);}; if(w.addEventListener){w.addEventListener("load", loader, false);}else if(w.attachEvent){w.attachEvent("onload", loader);}else{w.onload = loader;}})(window, document);</script>
                </span>
            </label>
            <x-input-error :messages="$errors->get('privacy_policy')" class="mt-2" />
        </div>

        <!-- Product Updates -->
        <div class="mt-4">
            <label for="receives_product_updates" class="inline-flex items-center">
                <input id="receives_product_updates" type="checkbox" class="rounded dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-indigo-600 shadow-sm focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:focus:ring-offset-gray-800" name="receives_product_updates" value="1" {{ Auth::user()->receives_product_updates ? 'checked' : '' }}>
                <span class="ms-2 text-sm text-gray-600 dark:text-gray-400">{{ __('I would like to receive product updates and new features via email (no marketing/spam)') }}</span>
            </label>
            <x-input-error :messages="$errors->get('receives_product_updates')" class="mt-2" />
        </div>

        <div class="flex items-center justify-end mt-8">
            <x-primary-button>
                {{ __('Accept and Continue') }}
            </x-primary-button>
        </div>
    </form>

    <div class="mt-10 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
            <form method="POST" action="{{ route('logout') }}">
                @csrf
                <button type="submit" class="underline text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-800">
                    {{ __('Log Out') }}
                </button>
            </form>

            <button 
                x-data=""
                x-on:click.prevent="$dispatch('open-modal', 'confirm-user-deletion')"
                class="text-sm text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 underline font-medium"
            >
                {{ __('Delete Account') }}
            </button>
        </div>
    </div>

    <x-modal name="confirm-user-deletion" :show="$errors->userDeletion->isNotEmpty()" focusable>
        <form method="post" action="{{ route('profile.destroy') }}" class="p-6">
            @csrf
            @method('delete')

            <h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">
                {{ __('Are you sure you want to delete your account?') }}
            </h2>

            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {{ __('If you do not accept the Privacy Policy, you can delete your account. All of your resources and data will be permanently deleted. Please enter your password to confirm.') }}
            </p>

            <div class="mt-6">
                <x-input-label for="delete_password" value="{{ __('Password') }}" class="sr-only" />

                <x-text-input
                    id="delete_password"
                    name="password"
                    type="password"
                    class="mt-1 block w-3/4"
                    placeholder="{{ __('Password') }}"
                />

                <x-input-error :messages="$errors->userDeletion->get('password')" class="mt-2" />
            </div>

            <div class="mt-6 flex justify-end">
                <x-secondary-button x-on:click="$dispatch('close')">
                    {{ __('Cancel') }}
                </x-secondary-button>

                <x-danger-button class="ms-3">
                    {{ __('Delete Account') }}
                </x-danger-button>
            </div>
        </form>
    </x-modal>
</x-guest-layout>
