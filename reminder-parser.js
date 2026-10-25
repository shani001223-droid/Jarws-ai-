(function (root) {
  "use strict";

  function toMinutes(amount, unit) {
    const count = Number(amount);
    const word = String(unit).toLowerCase();
    if (/hour|hr|ghant/.test(word)) return count * 60;
    if (/day|din/.test(word)) return count * 1440;
    return count;
  }

  function makeReminder(title, amount, unit) {
    const cleanTitle = String(title || "")
      .trim()
      .replace(/^[,:\s]+|[,.\s!?۔،]+$/g, "")
      .slice(0, 100);
    const minutes = toMinutes(amount, unit);
    if (!cleanTitle || !Number.isFinite(minutes) || minutes < 1 || minutes > 10080) {
      return null;
    }
    return { title: cleanTitle, minutes };
  }

  function parseReminderCommand(raw) {
    if (typeof raw !== "string") return null;
    const text = raw.trim();
    if (!text) return null;
    let match = text.match(/^(?:hey jarvis[, ]*)?(?:remind me|set a reminder)(?:\s+to)?\s+(.+?)\s+(?:in|after)\s+(\d+)\s*(minutes?|mins?|m|hours?|hrs?|days?)\s*[.!?۔،]?$/i);
    if (match) return makeReminder(match[1], match[2], match[3]);

    match = text.match(/^(?:hey jarvis[, ]*)?(?:remind me|set a reminder)\s+(?:in|after)\s+(\d+)\s*(minutes?|mins?|m|hours?|hrs?|days?)(?:\s+to\s+)?(.+?)\s*[.!?۔،]?$/i);
    if (match) return makeReminder(match[3], match[1], match[2]);

    match = text.match(/^(?:mujhe\s+)?(\d+)\s*(minutes?|mins?|m|ghanta|ghante|ghanton|hours?|hrs?|din|days?)\s+(?:baad|mein|me)\s+(.+?)\s+(?:ki\s+)?yaad\s+(?:dilao|dilana|dila\s+dena)\s*[.!?۔،]?$/i);
    if (match) return makeReminder(match[3], match[1], match[2]);

    match = text.match(/^(?:mujhe\s+)?(.+?)\s+(\d+)\s*(minutes?|mins?|m|ghanta|ghante|ghanton|hours?|hrs?|din|days?)\s+(?:baad|mein|me)\s+yaad\s+(?:dilao|dilana|dila\s+dena)\s*[.!?۔،]?$/i);
    if (match) return makeReminder(match[1], match[2], match[3]);

    return null;
  }

  if (root) root.JarvisReminderParser = parseReminderCommand;
  if (typeof module === "object" && module.exports) module.exports = parseReminderCommand;
})(typeof window !== "undefined" ? window : globalThis);
