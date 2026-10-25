package com.valtron.jarvis

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.text.InputType
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import android.widget.SeekBar

class MainActivity : Activity() {
    companion object {
        private const val REQUEST_OVERLAY = 4101
        private const val REQUEST_MICROPHONE = 4102
        private const val REQUEST_NOTIFICATIONS = 4103
        private const val DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?native=1"
    }

    private lateinit var overlayButton: Button
    private var startOverlayWhenPermissionReturns = false
    private var pendingWebPermission: PermissionRequest? = null
    private var pendingReminder: Pair<String, Int>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(7, 17, 30)
        window.navigationBarColor = Color.rgb(7, 17, 30)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(7, 17, 30))
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }

        val title = TextView(this).apply {
            text = "J A R V I S"
            textSize = 22f
            setTextColor(Color.rgb(93, 225, 255))
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(4), dp(5), dp(4), dp(5))
        }
        root.addView(title, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ))

        val sizeRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val initialIconSize = getSharedPreferences(
            FloatingAssistantService.PREFS_NAME, MODE_PRIVATE
        ).getInt(FloatingAssistantService.PREFS_SIZE_KEY, 62).coerceIn(44, 100)
        val sizeLabel = TextView(this).apply {
            text = "Icon size: ${initialIconSize} dp"
            textSize = 12f
            setTextColor(Color.rgb(154, 178, 198))
        }
        val sizeSlider = SeekBar(this).apply {
            min = 44
            max = 100
            progress = initialIconSize
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                    val size = progress.coerceIn(44, 100)
                    sizeLabel.text = "Icon size: ${size} dp"
                    getSharedPreferences(
                        FloatingAssistantService.PREFS_NAME, MODE_PRIVATE
                    ).edit().putInt(FloatingAssistantService.PREFS_SIZE_KEY, size).apply()
                    if (fromUser && FloatingAssistantService.isRunning) {
                        val resize = Intent(this@MainActivity, FloatingAssistantService::class.java).apply {
                            action = FloatingAssistantService.ACTION_RESIZE
                            putExtra(FloatingAssistantService.EXTRA_SIZE_DP, size)
                        }
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            startForegroundService(resize)
                        } else {
                            startService(resize)
                        }
                    }
                }

                override fun onStartTrackingTouch(seekBar: SeekBar?) = Unit
                override fun onStopTrackingTouch(seekBar: SeekBar?) = Unit
            })
        }
        sizeRow.addView(sizeLabel, LinearLayout.LayoutParams(dp(105), ViewGroup.LayoutParams.WRAP_CONTENT))
        sizeRow.addView(sizeSlider, LinearLayout.LayoutParams(0, dp(40), 1f))
        root.addView(sizeRow)

        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        overlayButton = makeButton("Enable floating icon") { enableOverlay() }
        controls.addView(overlayButton, LinearLayout.LayoutParams(0, dp(44), 1f))
        val stopButton = makeButton("Stop icon") {
            stopService(Intent(this, FloatingAssistantService::class.java))
            updateOverlayButton()
        }
        controls.addView(stopButton, LinearLayout.LayoutParams(0, dp(44), 1f))
        root.addView(controls)

        val featureButtons = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        val screenPermissionButton = makeButton("Screen controls") {
            promptScreenControls()
        }
        featureButtons.addView(screenPermissionButton, LinearLayout.LayoutParams(0, dp(42), 1f))
        val reminderButton = makeButton("Set reminder") {
            promptReminder()
        }
        featureButtons.addView(reminderButton, LinearLayout.LayoutParams(0, dp(42), 1f))
        root.addView(featureButtons)
        val listRemindersButton = makeButton("View / cancel reminders") {
            showReminders()
        }
        root.addView(listRemindersButton, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(40)
        ))

        val hint = TextView(this).apply {
            text = "Floating icon runs only after you enable it. Tap the orb to return to JARVIS."
            textSize = 12f
            setTextColor(Color.rgb(154, 178, 198))
            setPadding(dp(4), dp(5), dp(4), dp(7))
        }
        root.addView(hint)

        val webView = WebView(this)
        webView.setBackgroundColor(Color.rgb(7, 17, 30))
        webView.addJavascriptInterface(JarvisBridge(this), "JarvisBridge")
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadsImagesAutomatically = true
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            allowFileAccess = false
            allowContentAccess = false
            javaScriptCanOpenWindowsAutomatically = true
            setSupportMultipleWindows(false)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                safeBrowsingEnabled = true
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest
            ): Boolean {
                val uri = request.url
                val host = uri.host.orEmpty()
                val trusted = uri.scheme == "https" &&
                    (host == "jarws-ai-1.onrender.com" || host == "jarws-ai-2.onrender.com")
                if (trusted) return false

                if (uri.scheme == "https" || uri.scheme == "http") {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                    return true
                }
                return true
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    val isTrustedDashboard = request.origin.scheme == "https" &&
                        request.origin.host == "jarws-ai-1.onrender.com"
                    val asksOnlyForAudio = request.resources.isNotEmpty() &&
                        request.resources.all { it == PermissionRequest.RESOURCE_AUDIO_CAPTURE }
                    if (!isTrustedDashboard || !asksOnlyForAudio) {
                        request.deny()
                        return@runOnUiThread
                    }

                    if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
                        PackageManager.PERMISSION_GRANTED) {
                        request.grant(request.resources)
                    } else {
                        pendingWebPermission = request
                        requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_MICROPHONE)
                    }
                }
            }
        }

        root.addView(webView, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f
        ))
        setContentView(root)
        updateOverlayButton()
        webView.loadUrl(DASHBOARD_URL)
    }

    private fun makeButton(label: String, action: () -> Unit): Button {
        return Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 12f
            setTextColor(Color.WHITE)
            setOnClickListener { action() }
        }
    }

    private fun showReminders() {
        val items = ReminderScheduler.list(this)
        if (items.isEmpty()) {
            Toast.makeText(this, "No scheduled reminders.", Toast.LENGTH_SHORT).show()
            return
        }
        val formatter = java.text.DateFormat.getDateTimeInstance(
            java.text.DateFormat.SHORT,
            java.text.DateFormat.SHORT
        )
        val labels = items.map { reminder ->
            reminder.title + " — " + formatter.format(java.util.Date(reminder.fireAt))
        }.toTypedArray()

        AlertDialog.Builder(this)
            .setTitle("Scheduled reminders")
            .setItems(labels) { _, which ->
                val selected = items[which]
                AlertDialog.Builder(this)
                    .setTitle("Cancel this reminder?")
                    .setMessage(selected.title + "\n" + formatter.format(java.util.Date(selected.fireAt)))
                    .setNegativeButton("Keep", null)
                    .setPositiveButton("Cancel reminder") { _, _ ->
                        ReminderScheduler.cancel(this, selected.id)
                        Toast.makeText(this, "Reminder cancelled.", Toast.LENGTH_SHORT).show()
                    }
                    .show()
            }
            .setPositiveButton("Close", null)
            .show()
    }

    private fun promptReminder() {
        val titleInput = EditText(this).apply {
            hint = "Reminder title"
            setText("Take a short break")
            setSingleLine(true)
        }
        val minutesInput = EditText(this).apply {
            hint = "Minutes from now (1–10080)"
            inputType = InputType.TYPE_CLASS_NUMBER
            setText("30")
            setSingleLine(true)
        }
        val dialogContent = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(8), dp(20), 0)
            addView(titleInput)
            addView(minutesInput)
        }

        AlertDialog.Builder(this)
            .setTitle("Set a local reminder")
            .setMessage("Choose a title and a delay. The reminder is stored on this phone.")
            .setView(dialogContent)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Schedule") { _, _ ->
                val title = titleInput.text.toString().trim().take(100)
                val delay = minutesInput.text.toString().toIntOrNull()
                if (title.isBlank() || delay == null || delay !in 1..10080) {
                    Toast.makeText(
                        this,
                        "Enter a title and a delay from 1 to 10080 minutes.",
                        Toast.LENGTH_LONG
                    ).show()
                } else {
                    requestNotificationsThenSchedule(title, delay)
                }
            }
            .show()
    }

    private fun requestNotificationsThenSchedule(title: String, delayMinutes: Int) {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            pendingReminder = title to delayMinutes
            requestPermissions(
                arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                REQUEST_NOTIFICATIONS
            )
            return
        }
        scheduleLocalReminder(title, delayMinutes)
    }

    fun scheduleReminderFromAssistant(title: String, delayMinutes: Int) {
        val safeTitle = title.trim().take(100)
        if (safeTitle.isBlank() || delayMinutes !in 1..10080) {
            Toast.makeText(this, "Reminder must have a title and be within 7 days.", Toast.LENGTH_LONG).show()
            return
        }
        requestNotificationsThenSchedule(safeTitle, delayMinutes)
    }

    private fun scheduleLocalReminder(title: String, delayMinutes: Int) {
        val at = ReminderScheduler.schedule(this, title, delayMinutes)
        val minutesText = if (delayMinutes == 1) "1 minute" else "$delayMinutes minutes"
        Toast.makeText(
            this,
            "Reminder set for $minutesText from now.",
            Toast.LENGTH_LONG
        ).show()
    }

    fun promptScreenControls() {
        AlertDialog.Builder(this)
            .setTitle("Enable basic screen controls?")
            .setMessage(
                "JARVIS will only perform Back, Home, and swipe gestures when you tap those buttons. " +
                    "It will not read screen text or send screen contents to the cloud. " +
                    "You can disable the service anytime in Android Accessibility settings."
            )
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Open settings") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .show()
    }

    private fun enableOverlay() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            startOverlayWhenPermissionReturns = true
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            startActivityForResult(intent, REQUEST_OVERLAY)
            return
        }
        startFloatingService()
    }

    private fun startFloatingService() {
        val intent = Intent(this, FloatingAssistantService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
        updateOverlayButton()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_OVERLAY) {
            if (Settings.canDrawOverlays(this) && startOverlayWhenPermissionReturns) {
                startOverlayWhenPermissionReturns = false
                startFloatingService()
            } else {
                startOverlayWhenPermissionReturns = false
                updateOverlayButton()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        updateOverlayButton()
    }

    private fun updateOverlayButton() {
        if (::overlayButton.isInitialized) {
            overlayButton.text = if (Settings.canDrawOverlays(this)) {
                "Start / show floating icon"
            } else {
                "Grant overlay permission"
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_MICROPHONE) {
            val request = pendingWebPermission
            pendingWebPermission = null
            if (request != null) {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    request.grant(request.resources)
                } else {
                    request.deny()
                }
            }
        } else if (requestCode == REQUEST_NOTIFICATIONS) {
            val reminder = pendingReminder
            pendingReminder = null
            if (grantResults.isNotEmpty() &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED &&
                reminder != null
            ) {
                scheduleLocalReminder(reminder.first, reminder.second)
            } else {
                Toast.makeText(
                    this,
                    "Notifications are off. Enable them to receive reminders.",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
