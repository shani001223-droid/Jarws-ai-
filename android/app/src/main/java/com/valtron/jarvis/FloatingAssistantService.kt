package com.valtron.jarvis

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.IBinder
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowManager
import android.widget.ImageView
import kotlin.math.abs

class FloatingAssistantService : Service() {
    companion object {
        const val PREFS_NAME = "jarvis_assistant"
        const val PREFS_SIZE_KEY = "overlay_icon_size_dp"
        const val ACTION_RESIZE = "com.valtron.jarvis.RESIZE_FLOATING"
        const val EXTRA_SIZE_DP = "size_dp"
        private const val CHANNEL_ID = "jarvis_floating_assistant"
        private const val NOTIFICATION_ID = 1701
        private const val ACTION_STOP = "com.valtron.jarvis.STOP_FLOATING"
        @Volatile var isRunning: Boolean = false
    }

    private lateinit var windowManager: WindowManager
    private var bubble: ImageView? = null
    private var layoutParams: WindowManager.LayoutParams? = null

    override fun onCreate() {
        super.onCreate()
        isRunning = true
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        showBubble()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopSelf()
            return START_NOT_STICKY
        }
        if (intent?.action == ACTION_RESIZE) {
            val requestedSize = intent.getIntExtra(EXTRA_SIZE_DP, 62).coerceIn(44, 100)
            getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit().putInt(PREFS_SIZE_KEY, requestedSize).apply()
            resizeBubble(requestedSize)
            return START_STICKY
        }
        if (bubble == null) showBubble()
        return START_STICKY
    }

    private fun showBubble() {
        if (bubble != null) return
        val sizeDp = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .getInt(PREFS_SIZE_KEY, 62).coerceIn(44, 100)
        val size = dp(sizeDp)
        val view = ImageView(this).apply {
            setImageResource(R.drawable.jarvis_anime_avatar)
            scaleType = ImageView.ScaleType.CENTER_CROP
            contentDescription = "Open JARVIS anime assistant"
            elevation = dp(8).toFloat()
            background = GradientDrawable().apply {
                shape = GradientDrawable.OVAL
                setColor(Color.rgb(8, 25, 39))
                setStroke(dp(2), Color.rgb(93, 225, 255))
            }
            clipToOutline = true
            setOnClickListener {
                val launch = Intent(this@FloatingAssistantService, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                }
                startActivity(launch)
            }
        }
        val params = WindowManager.LayoutParams(
            size,
            size,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = dp(12)
            y = dp(190)
        }

        val touchSlop = ViewConfiguration.get(this).scaledTouchSlop
        var downX = 0f
        var downY = 0f
        var startX = 0
        var startY = 0
        var dragged = false
        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    downX = event.rawX
                    downY = event.rawY
                    startX = params.x
                    startY = params.y
                    dragged = false
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val dx = event.rawX - downX
                    val dy = event.rawY - downY
                    if (abs(dx) > touchSlop || abs(dy) > touchSlop) dragged = true
                    if (dragged) {
                        params.x = startX + dx.toInt()
                        params.y = startY + dy.toInt()
                        try {
                            windowManager.updateViewLayout(view, params)
                        } catch (_: IllegalArgumentException) {
                        }
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (!dragged) view.performClick()
                    true
                }
                MotionEvent.ACTION_CANCEL -> true
                else -> false
            }
        }

        try {
            windowManager.addView(view, params)
            bubble = view
            layoutParams = params
        } catch (_: SecurityException) {
            stopSelf()
        }
    }

    private fun resizeBubble(sizeDp: Int) {
        val view = bubble ?: return
        val params = layoutParams ?: return
        val px = dp(sizeDp.coerceIn(44, 100))
        params.width = px
        params.height = px
        try {
            windowManager.updateViewLayout(view, params)
        } catch (_: IllegalArgumentException) {
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "JARVIS floating assistant",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows a notification while the floating JARVIS icon is active."
            }
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(channel)
        }
    }

    private fun buildNotification(): Notification {
        val openIntent = Intent(this, MainActivity::class.java)
        val openPending = PendingIntent.getActivity(
            this, 1, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val stopIntent = Intent(this, FloatingAssistantService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPending = PendingIntent.getService(
            this, 2, stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, CHANNEL_ID)
        } else {
            Notification.Builder(this)
        }
        return builder
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("JARVIS floating icon is active")
            .setContentText("Tap to open the assistant, or Stop to hide the icon.")
            .setContentIntent(openPending)
            .setOngoing(true)
            .addAction(0, "Stop", stopPending)
            .build()
    }

    override fun onDestroy() {
        isRunning = false
        bubble?.let {
            try {
                windowManager.removeView(it)
            } catch (_: Exception) {
            }
        }
        bubble = null
        layoutParams = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
