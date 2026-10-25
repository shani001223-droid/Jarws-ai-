package com.valtron.jarvis

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.os.Handler
import android.os.Looper
import android.view.accessibility.AccessibilityEvent

/**
 * Minimal opt-in actions only. No screen nodes or visible text are read or stored.
 * The dashboard exposes only Back, Home, and swipe gestures.
 */
class JarvisAccessibilityService : AccessibilityService() {
    companion object {
        @Volatile
        var instance: JarvisAccessibilityService? = null
            private set
    }

    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Intentionally do not inspect events or screen contents.
    }

    override fun onInterrupt() {
        // No continuous task is running to interrupt.
    }

    fun performBasicAction(action: String): Boolean {
        return when (action) {
            "back" -> performGlobalAction(GLOBAL_ACTION_BACK)
            "home" -> performGlobalAction(GLOBAL_ACTION_HOME)
            "swipe_up" -> dispatchSwipe(up = true)
            "swipe_down" -> dispatchSwipe(up = false)
            else -> false
        }
    }

    private fun dispatchSwipe(up: Boolean): Boolean {
        val metrics = resources.displayMetrics
        val x = metrics.widthPixels * 0.5f
        val startY = metrics.heightPixels * if (up) 0.78f else 0.28f
        val endY = metrics.heightPixels * if (up) 0.28f else 0.78f
        val path = Path().apply {
            moveTo(x, startY)
            lineTo(x, endY)
        }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 320))
            .build()
        return dispatchGesture(gesture, null, mainHandler)
    }

    override fun onDestroy() {
        if (instance === this) instance = null
        super.onDestroy()
    }
}
