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

        <div class="flex items-center justify-between mt-8">
            <form method="POST" action="{{ route('logout') }}">
                @csrf
                <button type="submit" class="underline text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-800">
                    {{ __('Log Out') }}
                </button>
            </form>

            <x-primary-button class="ms-4">
                {{ __('Accept and Continue') }}
            </x-primary-button>
        </div>
    </form>
</x-guest-layout>
