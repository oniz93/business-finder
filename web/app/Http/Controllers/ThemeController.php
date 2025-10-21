<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class ThemeController extends Controller
{
    public function switchTheme(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'theme' => 'required|in:light,dark',
        ]);

        if ($validator->fails()) {
            return redirect()->back()->withErrors($validator);
        }

        $theme = $request->input('theme');

        session(['theme' => $theme]);

        return redirect()->back()->cookie('theme', $theme, 525600); // 1 year
    }
}
