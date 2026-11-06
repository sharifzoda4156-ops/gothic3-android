/*
 * Gothic 3: The Beginning - standalone MIDlet launch defaults.
 *
 * This code only applies when BuildConfig.FULL_EMULATOR is false.
 * Existing player-defined profiles are preserved.
 */
package ru.playsoftware.j2meloader.config;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.preference.PreferenceManager;

import java.io.File;

import ru.playsoftware.j2meloader.util.Constants;

public final class GothicProfileDefaults {
    private static final String SETTINGS_PREFS = "gothic_standalone_settings";
    private static final String PROFILE_PRESET_APPLIED = "profile_preset_v1";
    private static final String UI_PRESET_APPLIED = "ui_preset_v1";

    private GothicProfileDefaults() {
    }

    /**
     * Create the missing config before MicroLoader.init() decides to open ConfigActivity.
     * Migrate old, untouched 240x320 profiles once. Never reset user-customized settings.
     *
     * @return true only if the profile exists and is readable or was saved successfully.
     */
    public static boolean ensure(Context context, File configDir) {
        SharedPreferences applied = context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE);
        ProfileModel profile = ProfilesManager.loadConfig(configDir);
        boolean firstRun = !applied.getBoolean(PROFILE_PRESET_APPLIED, false);

        if (profile == null || (firstRun && isLegacyDefaultResolution(profile))) {
            if (!configDir.isDirectory() && !configDir.mkdirs()) {
                return false;
            }
            if (profile == null) {
                profile = new ProfileModel(configDir);
            }
            applyPreset(profile);
            if (!ProfilesManager.saveConfig(profile)) {
                return false;
            }
        }

        if (firstRun) {
            applied.edit().putBoolean(PROFILE_PRESET_APPLIED, true).apply();
        }
        prepareUiPreferences(context);
        return true;
    }

    static boolean isLegacyDefaultResolution(ProfileModel profile) {
        return profile.screenWidth == 240 && profile.screenHeight == 320;
    }

    static void applyPreset(ProfileModel profile) {
        profile.version = ProfileModel.VERSION;
        profile.screenWidth = 480;
        profile.screenHeight = 640;
        profile.orientation = 2;           // Portrait, per MicroActivity.setOrientation()
        profile.screenScaleType = 1;       // Fit with aspect ratio preserved
        profile.screenGravity = 1;         // Center
        profile.screenScaleRatio = 100;
        profile.screenScaleToFit = true;
        profile.screenKeepAspectRatio = true;
        profile.screenBackgroundColor = 0x160D0A;
        profile.screenFilter = false;      // Keep pixel art sharp
        profile.forceFullscreen = true;
        profile.showFps = false;
        profile.fpsLimit = 0;              // No artificial FPS cap
        profile.graphicsMode = 1;          // Upstream default; stable graphics mode
        profile.touchInput = true;
        profile.showKeyboard = true;
        profile.vkType = 3;                // NUM_ARR: numeric buttons + directional pad
        profile.vkAlpha = 112;
        profile.vkFeedback = true;
        profile.fontAA = true;
    }

    public static void prepareUiPreferences(Context context) {
        SharedPreferences applied = context.getSharedPreferences(SETTINGS_PREFS, Context.MODE_PRIVATE);
        if (applied.getBoolean(UI_PRESET_APPLIED, false)) {
            return;
        }
        SharedPreferences sp = PreferenceManager.getDefaultSharedPreferences(context);
        SharedPreferences.Editor editor = sp.edit();
        // Existing explicit choices must never be overwritten.
        if (!sp.contains(Constants.PREF_TOOLBAR)) {
            editor.putBoolean(Constants.PREF_TOOLBAR, false);
        }
        if (!sp.contains(Constants.PREF_STATUSBAR)) {
            editor.putBoolean(Constants.PREF_STATUSBAR, false);
        }
        if (!sp.contains(Constants.PREF_KEEP_SCREEN)) {
            editor.putBoolean(Constants.PREF_KEEP_SCREEN, true);
        }
        if (!sp.contains(Constants.PREF_BLACK_BACKGROUND)) {
            editor.putBoolean(Constants.PREF_BLACK_BACKGROUND, true);
        }
        editor.apply();
        applied.edit().putBoolean(UI_PRESET_APPLIED, true).apply();
    }
}
