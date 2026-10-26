package com.valtron.jarvis

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.ContentValues
import android.provider.MediaStore
import android.os.Environment
import android.util.Base64
import android.net.Uri
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
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import org.json.JSONObject
import org.json.JSONArray
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : Activity() {
    private data class NativeSpeech(val text: String, val language: String, val pitch: Float, val rate: Float)

    companion object {
        private const val REQUEST_MICROPHONE = 4102
        private const val REQUEST_NOTIFICATIONS = 4103
        private const val REQUEST_NATIVE_MIC = 4104
        private const val REQUEST_LOCAL_SCREENSHOT_OCR = 4105
        private const val DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?native=1"
    }

    private var textToSpeech: TextToSpeech? = null
    private var dashboardWebView: WebView? = null
    private var ttsReady = false
    private var pendingSpeech: NativeSpeech? = null
    private var pendingWebPermission: PermissionRequest? = null
    private var pendingReminder: Pair<String, Int>? = null
    private var nativeRecognizer: SpeechRecognizer? = null
    private var nativeMicActive = false
    private var pendingNativeLanguage: String? = null
    // WebView @JavascriptInterface calls can arrive off the UI thread.
    // Reserve the picker synchronously to prevent duplicate picker launches.
    private val localOcrBusy = AtomicBoolean(false)

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
                    textToSpeech?.setPitch(1.04f)
                    val queued = pendingSpeech
                    pendingSpeech = null
                    if (queued != null) speakNativeOnUiThread(queued)
                }
            }
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(7, 17, 30))
            setPadding(0, 0, 0, 0)
        }

        val webView = WebView(this)
        dashboardWebView = webView
        webView.setBackgroundColor(Color.rgb(7, 17, 30))
        webView.addJavascriptInterface(JarvisBridge(this), "JarvisBridge")
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            // Audio is started after an async TTS response; do not block it due to a lost click gesture.
            mediaPlaybackRequiresUserGesture = false
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

    /** Start exactly one utterance. Never auto-restart when Android ends recognition. */
    fun startNativeListening(language: String): Boolean {
        val locale = if (language == "en-US") "en-US" else "ur-PK"
        runOnUiThread {
            if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                pendingNativeLanguage = locale
                requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_NATIVE_MIC)
            } else {
                beginNativeListening(locale)
            }
        }
        return true
    }

    private fun sendNativeSpeechEvent(function: String, value: String) {
        val argument = JSONObject.quote(value)
        dashboardWebView?.evaluateJavascript(
            "window.$function && window.$function($argument)", null
        )
    }

    private fun beginNativeListening(locale: String) {
        stopNativeListeningInternal()
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            sendNativeSpeechEvent("hoshiNativeSpeechError", "Android speech service unavailable")
            return
        }
        try {
            val recognizer = SpeechRecognizer.createSpeechRecognizer(this)
            nativeRecognizer = recognizer
            nativeMicActive = true
            recognizer.setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {
                    if (nativeMicActive && nativeRecognizer === recognizer)
                        dashboardWebView?.evaluateJavascript(
                            "window.hoshiNativeListeningState && window.hoshiNativeListeningState(true)", null
                        )
                }
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onPartialResults(partialResults: Bundle?) {}
                override fun onEvent(eventType: Int, params: Bundle?) {}
                override fun onResults(results: Bundle?) {
                    if (!nativeMicActive || nativeRecognizer !== recognizer) return
                    // Android recognizers frequently transcribe Roman Urdu with
                    // more than one plausible script/spelling. Let the local
                    // client choose a wake-bearing candidate when needed.
                    val alternatives = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        ?.asSequence()?.map { it.trim() }?.filter { it.isNotBlank() }
                        ?.take(3)?.toList().orEmpty()
                    stopNativeListeningInternal()
                    if (alternatives.isNotEmpty()) {
                        val encoded = JSONArray(alternatives).toString()
                        dashboardWebView?.evaluateJavascript(
                            "window.hoshiNativeSpeechResult && window.hoshiNativeSpeechResult($encoded)", null
                        )
                    } else sendNativeSpeechEvent("hoshiNativeSpeechError", "No speech recognized")
                }
                override fun onError(error: Int) {
                    if (!nativeMicActive || nativeRecognizer !== recognizer) return
                    stopNativeListeningInternal()
                    val reason = when (error) {
                        SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
                            "No speech recognized. Try again"
                        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission denied"
                        SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
                            "Speech service network unavailable"
                        SpeechRecognizer.ERROR_LANGUAGE_NOT_SUPPORTED,
                        SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE -> "Urdu speech pack unavailable"
                        SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech recognizer busy"
                        else -> "Android speech recognition error " + error
                    }
                    sendNativeSpeechEvent("hoshiNativeSpeechError", reason)
                }
            })
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, locale)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, locale)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            }
            recognizer.startListening(intent)
        } catch (_: Exception) {
            stopNativeListeningInternal()
            sendNativeSpeechEvent("hoshiNativeSpeechError", "Cannot start Android speech service")
        }
    }

    private fun stopNativeListeningInternal() {
        nativeMicActive = false
        try { nativeRecognizer?.cancel(); nativeRecognizer?.destroy() } catch (_: Exception) {}
        nativeRecognizer = null
    }

    fun stopNativeListening(): Boolean {
        runOnUiThread {
            pendingNativeLanguage = null
            stopNativeListeningInternal()
        }
        return true
    }

    /**
     * User-requested shortcuts only. Never silently send a message, post online
     * or interact with a trading account.
     */
    fun openKnownApp(action: String): Boolean {
        if (action !in setOf("youtube", "whatsapp", "telegram", "browser", "settings", "tradingview")) return false
        runOnUiThread {
            if (isFinishing) return@runOnUiThread
            try {
                val packageName = when (action) {
                    "youtube" -> "com.google.android.youtube"
                    "whatsapp" -> "com.whatsapp"
                    "telegram" -> "org.telegram.messenger"
                    else -> null
                }
                val app = packageName?.let { packageManager.getLaunchIntentForPackage(it) }
                if (app != null) {
                    startActivity(app)
                } else {
                    val fallback = when (action) {
                        "settings" -> Intent(Settings.ACTION_SETTINGS)
                        "browser" -> Intent(Intent.ACTION_VIEW, Uri.parse("https://www.google.com/"))
                        "tradingview" -> Intent(Intent.ACTION_VIEW, Uri.parse("https://www.tradingview.com/"))
                        "youtube" -> Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com/"))
                        "whatsapp" -> Intent(Intent.ACTION_VIEW, Uri.parse("https://www.whatsapp.com/"))
                        else -> Intent(Intent.ACTION_VIEW, Uri.parse("https://web.telegram.org/"))
                    }
                    startActivity(fallback)
                }
            } catch (_: Exception) {
                Toast.makeText(this, "App could not be opened.", Toast.LENGTH_SHORT).show()
            }
        }
        return true
    }

    /** Save only validated Hoshi-generated ZIP bytes to user-visible Downloads.
     * Decoding and disk IO happen on a worker thread, never the voice/UI thread.
     * Android 10+ MediaStore does not require a storage permission. */
    fun saveAdZip(encoded: String, suggestedFilename: String): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return false
        if (encoded.isEmpty() || encoded.length > 8_000_000) return false
        val safeName = suggestedFilename.replace(Regex("[^A-Za-z0-9_.-]"), "_").take(58)
        if (!safeName.endsWith(".zip") || safeName.startsWith(".")) return false
        Thread {
            var uri: Uri? = null
            try {
                val decoded = Base64.decode(encoded, Base64.DEFAULT)
                if (decoded.size !in 20..5_000_000 ||
                    decoded[0] != 0x50.toByte() || decoded[1] != 0x4b.toByte()) {
                    throw IllegalArgumentException("Invalid creative ZIP")
                }
                val values = ContentValues().apply {
                    put(MediaStore.MediaColumns.DISPLAY_NAME, safeName)
                    put(MediaStore.MediaColumns.MIME_TYPE, "application/zip")
                    put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/Hoshi")
                    put(MediaStore.MediaColumns.IS_PENDING, 1)
                }
                uri = contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                    ?: throw IllegalStateException("Cannot open Downloads")
                contentResolver.openOutputStream(uri!!)?.use { output ->
                    output.write(decoded)
                } ?: throw IllegalStateException("Cannot write ZIP")
                val completed = ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) }
                contentResolver.update(uri!!, completed, null, null)
                runOnUiThread {
                    if (!isFinishing) Toast.makeText(this, "Hoshi ads saved: Downloads/Hoshi", Toast.LENGTH_LONG).show()
                }
            } catch (_: Exception) {
                uri?.let { try { contentResolver.delete(it, null, null) } catch (_: Exception) {} }
                runOnUiThread {
                    if (!isFinishing) Toast.makeText(this, "Could not save ads. Try Chrome download.", Toast.LENGTH_LONG).show()
                }
            }
        }.start()
        return true
    }

    /**
     * Dispatch only allowlisted local Hoshi DOM actions, never other apps.
     * This method must run on the Android UI thread (JarvisBridge posts it).
     * WebView page-origin is rechecked at execution time to avoid navigation races.
     */
    fun dispatchLocalUiAction(action: String, payload: String, requestId: Int) {
        if (isFinishing || isDestroyed) return
        val view = dashboardWebView ?: return
        val originalUrl = view.url ?: return
        val page = Uri.parse(originalUrl)
        if (page.scheme != "https" || page.host != "jarws-ai-1.onrender.com") return
        if (requestId !in 1..1_000_000_000 ||
            action !in setOf("tap_chat", "tap_settings", "type_draft", "scroll_up", "scroll_down")) return
        if (action == "type_draft") {
            if (payload.length !in 1..240 || payload.isBlank() ||
                payload.any { it.code < 32 || it.code == 127 }) return
        } else if (payload.isNotEmpty()) return
        val script = "window.hoshiExecuteLocalUiAction && window.hoshiExecuteLocalUiAction(" +
            JSONObject.quote(action) + "," + JSONObject.quote(payload) + ")"
        try {
            view.evaluateJavascript(script) { raw ->
                // The JavaScript result is a Boolean, not a screenshot or draft.
                // Reject a stale callback after navigation or permission loss.
                val verified = raw == "true" && dashboardWebView === view &&
                    view.url == originalUrl && !isFinishing && !isDestroyed &&
                    JarvisAccessibilityService.instance != null && JarvisBridge(this).isEnabled()
                reportLocalUiActionResult(requestId, verified)
            }
        } catch (_: Exception) {
            reportLocalUiActionResult(requestId, false)
        }
    }

    /** A status-only callback to the trusted dashboard; never echoes user text. */
    fun reportLocalUiActionResult(requestId: Int, verified: Boolean) {
        if (requestId !in 1..1_000_000_000 || isFinishing || isDestroyed) return
        val view = dashboardWebView ?: return
        val page = Uri.parse(view.url ?: return)
        if (page.scheme != "https" || page.host != "jarws-ai-1.onrender.com") return
        val success = if (verified) "true" else "false"
        view.evaluateJavascript(
            "window.hoshiLocalUiActionResult && window.hoshiLocalUiActionResult($requestId,$success)",
            null
        )
    }

    /** User-selected screenshot only: no background capture or remote upload. */
    fun chooseScreenshotForLocalOcr(): Boolean {
        if (isFinishing || isDestroyed || !localOcrBusy.compareAndSet(false, true)) return false
        runOnUiThread {
            if (isFinishing || isDestroyed) {
                localOcrBusy.set(false)
                return@runOnUiThread
            }
            try {
                val picker = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE)
                    type = "image/*"
                }
                startActivityForResult(picker, REQUEST_LOCAL_SCREENSHOT_OCR)
            } catch (_: Exception) {
                localOcrBusy.set(false)
                sendLocalOcrError("Image picker unavailable")
            }
        }
        return true // Picker reserved; recognition result arrives asynchronously.
    }

    private fun sendLocalOcrError(reason: String) {
        dashboardWebView?.evaluateJavascript(
            "window.hoshiLocalOcrError && window.hoshiLocalOcrError(${JSONObject.quote(reason)})", null
        )
    }

    private fun sendLocalOcrResult(json: String) {
        dashboardWebView?.evaluateJavascript(
            "window.hoshiLocalOcrResult && window.hoshiLocalOcrResult(${JSONObject.quote(json)})", null
        )
    }

    @Deprecated("Uses Android document picker activity result.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQUEST_LOCAL_SCREENSHOT_OCR) return
        val uri = if (resultCode == RESULT_OK) data?.data else null
        if (uri == null) {
            localOcrBusy.set(false)
            sendLocalOcrError("No screenshot selected")
            return
        }
        LocalScreenshotOcr(this,
            onResult = { json ->
                localOcrBusy.set(false)
                if (!isFinishing && !isDestroyed) sendLocalOcrResult(json)
            },
            onError = { reason ->
                localOcrBusy.set(false)
                if (!isFinishing && !isDestroyed) sendLocalOcrError(reason)
            }
        ).analyze(uri)
    }

    fun copyUserText(text: String): Boolean {
        val safe = text.trim().take(2000)
        if (safe.isEmpty()) return false
        runOnUiThread {
            if (isFinishing) return@runOnUiThread
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            clipboard.setPrimaryClip(ClipData.newPlainText("Hoshi draft", safe))
            Toast.makeText(this, "Text copied. Paste it where you want.", Toast.LENGTH_SHORT).show()
        }
        return true
    }

    fun shareUserDraft(text: String): Boolean {
        val safe = text.trim().take(2000)
        if (safe.isEmpty()) return false
        runOnUiThread {
            if (isFinishing) return@runOnUiThread
            try {
                val share = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, safe)
                }
                startActivity(Intent.createChooser(share, "Share Hoshi draft"))
            } catch (_: Exception) {
                Toast.makeText(this, "No app available for sharing.", Toast.LENGTH_SHORT).show()
            }
        }
        return true
    }

    fun showReminders() {
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

    fun supportsUrduSpeech(): Boolean {
        val engine = textToSpeech ?: return false
        return ttsReady && engine.isLanguageAvailable(Locale("ur", "PK")) >= TextToSpeech.LANG_AVAILABLE
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
                "window.hoshiSetSpeaking && window.hoshiSetSpeaking($speaking);" +
                    (if (speaking) "window.hoshiNativeSpeechStarted && window.hoshiNativeSpeechStarted();" else ""), null
            )
        }
    }

    private fun notifyHoshiUrduUnavailable() {
        runOnUiThread {
            dashboardWebView?.evaluateJavascript("window.hoshiUrduUnavailable && window.hoshiUrduUnavailable()", null)
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
            "ur" -> listOf(Locale("ur", "PK"))
            "hi" -> listOf(Locale("hi", "IN"), Locale("en", "IN"), Locale.US)
            else -> listOf(Locale("en", "IN"), Locale.US, Locale.getDefault())
        }
        val available = candidates.distinct().firstOrNull {
            engine.isLanguageAvailable(it) >= TextToSpeech.LANG_AVAILABLE
        }
        if (lang == "ur" && available == null) {
            notifyHoshiUrduUnavailable()
            return
        }
        if (available != null && engine.setLanguage(available) < TextToSpeech.LANG_AVAILABLE) {
            if (lang == "ur") notifyHoshiUrduUnavailable() else notifyHoshiVoiceError()
            return
        }
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
        if (result == TextToSpeech.ERROR) notifyHoshiVoiceError()
    }

    fun stopNativeSpeech(): Boolean {
        runOnUiThread { textToSpeech?.stop(); pendingSpeech = null; notifyHoshiSpeaking(false) }
        return true
    }

    override fun onDestroy() {
        stopNativeListeningInternal()
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
        } else if (requestCode == REQUEST_NATIVE_MIC) {
            val language = pendingNativeLanguage
            pendingNativeLanguage = null
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED && language != null) {
                beginNativeListening(language)
            } else {
                sendNativeSpeechEvent("hoshiNativeSpeechError", "Microphone permission denied")
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
