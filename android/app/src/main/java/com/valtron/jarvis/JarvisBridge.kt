package com.valtron.jarvis

import android.content.ComponentName
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.webkit.JavascriptInterface

/**
 * A deliberately small JavaScript bridge. Unknown action strings are rejected.
 */
class JarvisBridge(private val activity: MainActivity) {
    private val mainHandler = Handler(Looper.getMainLooper())
    private val allowedActions = setOf("back", "home", "swipe_up", "swipe_down")

    @JavascriptInterface
    fun speakNative(text: String, language: String, pitch: Float, rate: Float): Boolean {
        return activity.speakNative(text, language, pitch, rate)
    }

    @JavascriptInterface
    fun stopNativeSpeech(): Boolean {
        return activity.stopNativeSpeech()
    }

    @JavascriptInterface
    fun isEnabled(): Boolean {
        val expected = ComponentName(activity, JarvisAccessibilityService::class.java)
            .flattenToString()
        val enabled = Settings.Secure.getString(
            activity.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ).orEmpty()
        return Settings.Secure.getInt(
            activity.contentResolver,
            Settings.Secure.ACCESSIBILITY_ENABLED,
            0
        ) == 1 && enabled.split(':').any { it.equals(expected, ignoreCase = true) }
    }

    @JavascriptInterface
    fun requestSettings() {
        activity.runOnUiThread {
            if (!activity.isFinishing) activity.promptScreenControls()
        }
    }

    @JavascriptInterface
    fun scheduleReminder(title: String, delayMinutes: Int): Boolean {
        val safeTitle = title.trim().take(100)
        if (safeTitle.isBlank() || delayMinutes !in 1..10080) return false
        activity.runOnUiThread {
            if (!activity.isFinishing) {
                activity.scheduleReminderFromAssistant(safeTitle, delayMinutes)
            }
        }
        return true
    }

    @JavascriptInterface
    fun performAction(action: String): Boolean {
        if (action !in allowedActions || !isEnabled()) return false
        val queued = mainHandler.post {
            JarvisAccessibilityService.instance?.performBasicAction(action)
        }
        return queued
    }
}
