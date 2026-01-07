<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use PragmaRX\Google2FALaravel\Support\Constants;
use PragmaRX\Google2FALaravel\Google2FA;

class Google2FAController extends Controller
{
    public function __construct(private Google2FA $google2fa)
    {
    }

    public function index(Request $request)
    {
        $user = $request->user();
        $qrCodeUrl = null;
        if (!$user->google2fa_secret) {
            $secret = $this->google2fa->generateSecretKey();
            $user->google2fa_secret = $secret;
            $user->save();
            $qrCodeUrl = $this->google2fa->getQRCodeUrl(
                config('app.name'),
                $user->email,
                $secret
            );
        }

        return view('2fa.index', ['user' => $user, 'qrCodeUrl' => $qrCodeUrl]);
    }

    public function enable(Request $request)
    {
        $request->validate([
            'otp' => 'required|digits:6',
        ]);

        $user = $request->user();

        if ($this->google2fa->verifyKey($user->google2fa_secret, $request->otp)) {
            $user->google2fa_enabled = true;
            $user->save();
            return redirect()->route('2fa.index')->with('status', '2fa-enabled');
        }

        return redirect()->route('2fa.index')->with('error', 'Invalid OTP');
    }

    public function disable(Request $request)
    {
        $user = $request->user();
        $user->google2fa_enabled = false;
        $user->save();

        return redirect()->route('2fa.index')->with('status', '2fa-disabled');
    }

    public function verify(Request $request)
    {
        if ($request->isMethod('get')) {
            return view('2fa.verify');
        }

        $request->validate([
            'otp' => 'required|digits:6',
        ]);

        if (session(Constants::SESSION_AUTH_PASSED)) {
            return redirect()->route('home');
        }

        if ($this->google2fa->verifyKey(auth()->user()->google2fa_secret, $request->otp)) {
            session([Constants::SESSION_AUTH_PASSED => true]);
            return redirect()->route('home');
        }

        return redirect()->route('2fa.verify')->with('error', 'Invalid OTP');
    }
}
