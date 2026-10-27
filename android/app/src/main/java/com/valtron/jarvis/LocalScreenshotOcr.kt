package com.valtron.jarvis

import android.app.Activity
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import org.json.JSONArray
import org.json.JSONObject

/** On-device OCR for a screenshot explicitly selected in the Android picker.
 * Never inspects arbitrary windows, persists images or uploads recognized text.
 * Bundled Latin model reads Roman Urdu/English, NOT Urdu script.
 */
internal class LocalScreenshotOcr(
    private val activity: Activity,
    private val onResult: (String) -> Unit,
    private val onError: (String) -> Unit
) {
    fun analyze(uri: Uri) {
        Thread {
            val bitmap = try {
                decodeBoundedScreenshot(uri)
            } catch (_: Exception) {
                activity.runOnUiThread { onError("Choose a local PNG, JPEG or WebP screenshot under 8 MB") }
                return@Thread
            }
            activity.runOnUiThread {
                if (activity.isFinishing || activity.isDestroyed) {
                    bitmap.recycle()
                    onError("Screenshot reading cancelled")
                    return@runOnUiThread
                }
                try {
                    val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
                    recognizer.process(InputImage.fromBitmap(bitmap, 0))
                        .addOnSuccessListener { recognized ->
                            val blocks = JSONArray()
                            var remaining = 2400
                            var truncated = false
                            for (block in recognized.textBlocks) {
                                if (blocks.length() >= 35 || remaining <= 0) {
                                    truncated = true
                                    break
                                }
                                val raw = block.text.trim()
                                if (raw.isEmpty()) continue
                                val safe = raw.take(minOf(180, remaining))
                                if (safe.length < raw.length) truncated = true
                                val item = JSONObject().put("text", safe)
                                block.boundingBox?.let { box ->
                                    item.put("box", JSONArray().put(box.left).put(box.top)
                                        .put(box.right).put(box.bottom))
                                }
                                blocks.put(item)
                                remaining -= safe.length
                            }
                            onResult(JSONObject().put("engine", "on-device-latin")
                                .put("width", bitmap.width).put("height", bitmap.height)
                                .put("blocks", blocks).put("truncated", truncated).toString())
                        }
                        .addOnFailureListener { onError("Could not read text from this screenshot") }
                        .addOnCompleteListener {
                            bitmap.recycle()
                            recognizer.close()
                        }
                } catch (_: Exception) {
                    bitmap.recycle()
                    onError("Screenshot OCR unavailable on this device")
                }
            }
        }.start()
    }

    private fun decodeBoundedScreenshot(uri: Uri): Bitmap {
        val resolver = activity.contentResolver
        require(resolver.getType(uri) in setOf("image/png", "image/jpeg", "image/webp"))
        val size = resolver.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)?.use {
            if (it.moveToFirst() && !it.isNull(0)) it.getLong(0) else null
        }
        // Reject unknown-size streams rather than fetching cloud content.
        require(size != null && size in 1L..8_000_000L)
        val probe = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        val stream = resolver.openInputStream(uri) ?: error("Image stream unavailable")
        stream.use { BitmapFactory.decodeStream(it, null, probe) }
        require(probe.outWidth in 1..12000 && probe.outHeight in 1..12000)
        var sample = 1
        while (maxOf(probe.outWidth, probe.outHeight) / sample > 2048) sample *= 2
        val options = BitmapFactory.Options().apply {
            inSampleSize = sample
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        val decoded = resolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it, null, options)
        } ?: error("Cannot decode screenshot")
        require(decoded.width.toLong() * decoded.height.toLong() <= 4_500_000L)
        return decoded
    }
}
