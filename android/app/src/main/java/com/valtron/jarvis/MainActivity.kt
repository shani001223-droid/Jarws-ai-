package com.valtron.jarvis

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
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
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale

class MainActivity : Activity() {
    private data class NativeSpeech(val text: String, val language: String, val pitch: Float, val rate: Float)

    companion object {
        private const val REQUEST_MICROPHONE = 4102
        private const val REQUEST_NOTIFICATIONS = 4103
        private const val DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?native=1"
    }

    private var textToSpeech: TextToSpeech? = null
    private var dashboardWebView: WebView? = null
    private var ttsReady = false
    private var pendingSpeech: NativeSpeech? = null
    private var pendingWebPermission: PermissionRequest? = null
    private var pendingReminder: Pair<String, Int>? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(7, 17, 30)
        window.navigationBarColor = Color.rgb(7, 17, 30)

        textToSpeech = TextToSpeech(applicationContext) { result ->
            runOnUiThread {
                if (result == TextToSpeech.SUCCESS) {
                    ttsReady = true
                    textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                        override fun onStart(utteranceId: String?) = notifyHoshiSpeaking(true)
                        override fun onDone(utteranceId: String?) = notifyHoshiSpeaking(false)
                        override fun onError(utteranceId: String?) = notifyHoshiVoiceError()
                        override fun onError(utteranceId: String?, errorCode: Int) = notifyHoshiVoiceError()
                    })
                    textToSpeech?.setPitch(1.12f)
                    val queued = pendingSpeech
                    pendingSpeech = null
                    if (queued != null) speakNativeOnUiThread(queued)
                }
            }
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(7, 17, 30))
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }

        val title = TextView(this).apply {
            text = "H O S H I"
            textSize = 22f
            setTextColor(Color.rgb(93, 225, 255))
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(4), dp(5), dp(4), dp(5))
        }
        root.addView(title, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ))

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

        val webView = WebView(this)
        dashboardWebView = webView
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
                "HOSHI only performs a Back, Home, swipe, or screenshot action when you tap that button. " +
                    "Screenshots use Android system capture and are not read or uploaded by HOSHI. " +
                    "You can disable the service anytime in Android Accessibility settings."
            )
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Open settings") { _, _ ->
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
            .show()
    }

    fun speakNative(text: String, language: String, pitch: Float, rate: Float): Boolean {
        val safeText = text.trim().take(3000)
        if (safeText.isBlank()) return false
        val request = NativeSpeech(
            safeText, language.take(20),
            pitch.coerceIn(0.8f, 1.6f), rate.coerceIn(0.75f, 1.15f)
        )
        runOnUiThread {
            if (!ttsReady || textToSpeech == null) pendingSpeech = request
            else speakNativeOnUiThread(request)
        }
        return true
    }

    private fun notifyHoshiSpeaking(speaking: Boolean) {
        runOnUiThread {
            dashboardWebView?.evaluateJavascript(
                "window.hoshiSetSpeaking && window.hoshiSetSpeaking($speaking)", null
            )
        }
    }

    private fun notifyHoshiVoiceError() {
        runOnUiThread {
            dashboardWebView?.evaluateJavascript(
                "window.hoshiVoiceError && window.hoshiVoiceError()", null
            )
        }
    }

    private fun speakNativeOnUiThread(request: NativeSpeech) {
        val engine = textToSpeech ?: run { pendingSpeech = request; return }
        if (!ttsReady) { pendingSpeech = request; return }
        engine.stop()
        engine.setPitch(request.pitch)
        engine.setSpeechRate(request.rate)
        val lang = request.language.substringBefore('-').lowercase(Locale.ROOT)
        val candidates = when (lang) {
            "ur" -> listOf(Locale("ur", "PK"), Locale("hi", "IN"), Locale("en", "IN"), Locale.US)
            "hi" -> listOf(Locale("hi", "IN"), Locale("en", "IN"), Locale.US)
            else -> listOf(Locale("en", "IN"), Locale.US, Locale.getDefault())
        }
        val available = candidates.distinct().firstOrNull {
            engine.isLanguageAvailable(it) >= TextToSpeech.LANG_AVAILABLE
        }
        if (available != null) engine.setLanguage(available)
        try {
            val voices = engine.voices.orEmpty().filter { available == null || it.locale.language == available.language }
            // Free-first voice selection: prefer an installed Pakistani Urdu voice,
            // then any installed Urdu voice, then a feminine-sounding fallback.
            // TTS engines expose inconsistent voice names; gender/accent cannot be guaranteed.
            val feminineVoiceHints = listOf(
                "female", "feminine", "sfg", "zira", "samantha", "aria",
                "jenny", "sara", "siri", "victoria", "sonia", "karen"
            )
            val isFeminineHint: (android.speech.tts.Voice) -> Boolean = { voice ->
                feminineVoiceHints.any { hint -> voice.name.contains(hint, ignoreCase = true) }
            }
            val preferred = if (lang == "ur") {
                voices.firstOrNull { it.locale.language == "ur" && it.locale.country == "PK" && isFeminineHint(it) }
                    ?: voices.firstOrNull { it.locale.language == "ur" && isFeminineHint(it) }
                    ?: voices.firstOrNull { it.locale.language == "ur" && it.locale.country == "PK" }
                    ?: voices.firstOrNull { it.locale.language == "ur" }
                    ?: voices.firstOrNull(isFeminineHint)
            } else {
                voices.firstOrNull(isFeminineHint)
            }
            if (preferred != null) engine.voice = preferred
        } catch (_: Exception) {
            // Some Android speech engines do not expose selectable voices.
        }
        val result = engine.speak(
            request.text, TextToSpeech.QUEUE_FLUSH, Bundle(),
            "jarvis-" + System.currentTimeMillis()
        )
        if (result == TextToSpeech.ERROR) {
            engine.setLanguage(Locale.getDefault())
            engine.speak(
                request.text, TextToSpeech.QUEUE_FLUSH, Bundle(),
                "jarvis-fallback-" + System.currentTimeMillis()
            )
        }
    }

    fun stopNativeSpeech(): Boolean {
        runOnUiThread { textToSpeech?.stop(); pendingSpeech = null; notifyHoshiSpeaking(false) }
        return true
    }

    override fun onDestroy() {
        try { textToSpeech?.stop(); textToSpeech?.shutdown() } catch (_: Exception) {}
        textToSpeech = null
        ttsReady = false
        super.onDestroy()
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
