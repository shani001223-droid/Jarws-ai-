package com.valtron.jarvis

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
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
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    companion object {
        private const val REQUEST_OVERLAY = 4101
        private const val REQUEST_MICROPHONE = 4102
        private const val DASHBOARD_URL = "https://jarws-ai-1.onrender.com/?native=1"
    }

    private lateinit var overlayButton: Button
    private var startOverlayWhenPermissionReturns = false
    private var pendingWebPermission: PermissionRequest? = null

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

        val hint = TextView(this).apply {
            text = "Floating icon runs only after you enable it. Tap the orb to return to JARVIS."
            textSize = 12f
            setTextColor(Color.rgb(154, 178, 198))
            setPadding(dp(4), dp(5), dp(4), dp(7))
        }
        root.addView(hint)

        val webView = WebView(this)
        webView.setBackgroundColor(Color.rgb(7, 17, 30))
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
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
