package com.valtron.jarvis

import android.content.ComponentName
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.webkit.JavascriptInterface

/**
 * A deliberately small JavaScript bridge. Unknown action strings are rejected.
 */
class JarvisBridge(private val activity: MainActivity) {
    private val mainHandler = Handler(Looper.getMainLooper())
    private val allowedActions = setOf("back", "home", "swipe_up", "swipe_down", "screenshot")
    private val localUiActions = setOf("tap_chat", "tap_settings", "type_draft", "scroll_up", "scroll_down")

    @JavascriptInterface
    fun speakNative(text: String, language: String, pitch: Float, rate: Float): Boolean {
        return activity.speakNative(text, language, pitch, rate)
    }

    /** Android's own one-shot recognizer avoids WebView start/stop beep loops. */
    @JavascriptInterface
    fun startNativeListening(language: String): Boolean = activity.startNativeListening(language)

    @JavascriptInterface
    fun stopNativeListening(): Boolean = activity.stopNativeListening()

    @JavascriptInterface
    fun openKnownApp(action: String): Boolean = activity.openKnownApp(action)

    @JavascriptInterface
    fun saveAdZip(base64Zip: String, filename: String): Boolean = activity.saveAdZip(base64Zip, filename)

    /** Opens Android's document picker; cannot silently inspect other apps. */
    @JavascriptInterface
    fun chooseScreenshotForLocalOcr(): Boolean = activity.chooseScreenshotForLocalOcr()

    @JavascriptInterface
    fun copyUserText(text: String): Boolean = activity.copyUserText(text)

    @JavascriptInterface
    fun shareUserDraft(text: String): Boolean = activity.shareUserDraft(text)

    @JavascriptInterface
    fun showReminders() { activity.runOnUiThread { if (!activity.isFinishing) activity.showReminders() } }

    @JavascriptInterface
    fun supportsUrduSpeech(): Boolean = activity.supportsUrduSpeech()

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

    /**
     * Bounded Hoshi-only UI action with a caller-generated request ID.
     * The immediate Boolean only acknowledges queuing. Actual DOM evidence
     * is delivered asynchronously by MainActivity without leaking draft text.
     */
    @JavascriptInterface
    fun performLocalUiAction(action: String, payload: String, requestId: Int): Boolean {
        if (requestId !in 1..1_000_000_000 || action !in localUiActions || !isEnabled() ||
            JarvisAccessibilityService.instance == null) return false
        if (action == "type_draft") {
            if (payload.length !in 1..240 || payload.isBlank() ||
                payload.any { it.code < 32 || it.code == 127 }) return false
        } else if (payload.isNotEmpty()) return false
        return mainHandler.post {
            if (isEnabled() && JarvisAccessibilityService.instance != null) {
                activity.dispatchLocalUiAction(action, payload, requestId)
            } else {
                activity.reportLocalUiActionResult(requestId, false)
            }
        }
    }

    @JavascriptInterface
    fun performAction(action: String): Boolean {
        // The Android accessibility toggle alone does not prove the service
        // is connected. Fail closed rather than reporting a fake queued action.
        if (action !in allowedActions || !isEnabled()) return false
        if (action == "screenshot" && Build.VERSION.SDK_INT < Build.VERSION_CODES.P) return false
        if (JarvisAccessibilityService.instance == null) return false
        // Returning true means only that the request was queued on the UI
        // thread, NOT that Android completed the gesture or took a screenshot.
        return mainHandler.post {
            val liveService = JarvisAccessibilityService.instance
            if (isEnabled() && liveService != null) {
                liveService.performBasicAction(action)
            }
        }
    }
}
