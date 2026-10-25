package com.valtron.jarvis

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import org.json.JSONArray
import org.json.JSONObject

/**
 * One-shot reminders stored locally and rescheduled after reboot.
 * This intentionally uses inexact alarms so no special exact-alarm permission is needed.
 */
object ReminderScheduler {
    const val ACTION_FIRE = "com.valtron.jarvis.REMINDER_FIRE"
    private const val PREFS = "jarvis_local_reminders"
    private const val ITEMS = "items"

    fun schedule(context: Context, title: String, delayMinutes: Int): Long {
        require(title.isNotBlank()) { "Reminder title is required." }
        require(delayMinutes in 1..10080) { "Delay must be between 1 and 10080 minutes." }

        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val id = (System.currentTimeMillis() % 2_000_000_000L).toInt().coerceAtLeast(1)
        val fireAt = System.currentTimeMillis() + delayMinutes.toLong() * 60_000L
        val items = readItems(context)
        items.put(
            JSONObject()
                .put("id", id)
                .put("title", title.take(100))
                .put("fireAt", fireAt)
        )
        prefs.edit().putString(ITEMS, items.toString()).apply()
        scheduleOne(context, id, title.take(100), fireAt)
        return fireAt
    }

    fun rescheduleAll(context: Context) {
        val now = System.currentTimeMillis()
        val items = readItems(context)
        val remaining = JSONArray()
        for (i in 0 until items.length()) {
            val item = items.optJSONObject(i) ?: continue
            val id = item.optInt("id", 0)
            val title = item.optString("title", "JARVIS reminder")
            val fireAt = item.optLong("fireAt", 0L)
            if (id > 0 && fireAt > now) {
                remaining.put(item)
                scheduleOne(context, id, title, fireAt)
            }
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(ITEMS, remaining.toString()).apply()
    }

    fun remove(context: Context, id: Int) {
        val items = readItems(context)
        val remaining = JSONArray()
        for (i in 0 until items.length()) {
            val item = items.optJSONObject(i) ?: continue
            if (item.optInt("id", -1) != id) remaining.put(item)
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(ITEMS, remaining.toString()).apply()
    }

    private fun readItems(context: Context): JSONArray {
        val raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(ITEMS, "[]")
        return try {
            JSONArray(raw)
        } catch (_: Exception) {
            JSONArray()
        }
    }

    private fun scheduleOne(context: Context, id: Int, title: String, fireAt: Long) {
        val intent = Intent(context, ReminderReceiver::class.java).apply {
            action = ACTION_FIRE
            data = Uri.parse("jarvis-reminder://$id")
            putExtra("reminder_id", id)
            putExtra("reminder_title", title)
        }
        val pending = PendingIntent.getBroadcast(
            context,
            id,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val alarm = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, fireAt, pending)
        } else {
            alarm.set(AlarmManager.RTC_WAKEUP, fireAt, pending)
        }
    }
}
