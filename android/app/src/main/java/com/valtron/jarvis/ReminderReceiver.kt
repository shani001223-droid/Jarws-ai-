package com.valtron.jarvis

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

class ReminderReceiver : BroadcastReceiver() {
    companion object {
        private const val CHANNEL_ID = "jarvis_local_reminders"
    }

    override fun onReceive(context: Context, intent: Intent?) {
        when (intent?.action) {
            Intent.ACTION_BOOT_COMPLETED -> ReminderScheduler.rescheduleAll(context)
            ReminderScheduler.ACTION_FIRE -> showReminder(
                context,
                intent.getIntExtra("reminder_id", 1),
                intent.getStringExtra("reminder_title") ?: "HOSHI reminder"
            )
        }
    }

    private fun showReminder(context: Context, id: Int, title: String) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_ID,
                    "HOSHI reminders",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Reminders created locally in HOSHI."
                }
            )
        }

        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openPending = PendingIntent.getActivity(
            context,
            id xor 0x40000000,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(context, CHANNEL_ID)
        } else {
            Notification.Builder(context)
        }
        val notification = builder
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("HOSHI reminder")
            .setContentText(title)
            .setStyle(Notification.BigTextStyle().bigText(title))
            .setContentIntent(openPending)
            .setAutoCancel(true)
            .build()

        manager.notify(id, notification)
        ReminderScheduler.remove(context, id)
    }
}
