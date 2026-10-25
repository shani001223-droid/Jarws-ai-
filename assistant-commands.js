(function (root) {
  "use strict";
  function normalize(input) {
    return String(input == null ? "" : input).toLowerCase()
      .replace(/[!?.,،۔]/g, " ").replace(/\s+/g, " ").trim();
  }
  function isTimeCommand(input) {
    const c = normalize(input);
    if (!c) return false;
    return [
      "time", "what time is it", "what is the time", "tell me the time",
      "current time", "time now", "waqt", "waqt batao", "time batao",
      "abhi waqt kya hai", "abhi kya waqt hai", "abhi kya time hai",
      "kitne bajay", "kitne bajay hain", "kitna bajay", "kitna bajay hain",
      "baj rahe hain"
    ].includes(c) ||
      /\b(what time|current time|time batao|kitne bajay|kitna bajay)\b/.test(c) ||
      /وقت|کتنے بجے|کیا وقت/.test(c);
  }
  function isDateCommand(input) {
    const c = normalize(input);
    if (!c) return false;
    return [
      "date", "today date", "today's date", "todays date", "what is the date",
      "what's the date", "what is today's date", "tell me the date",
      "tareekh", "tarikh", "aaj ki date", "aaj ki tareekh", "aaj ki tarikh",
      "aj ki tareekh", "aj ki date"
    ].includes(c) ||
      /\b(date|tareekh|tarikh)\b/.test(c) || /تاریخ|آج کی تاریخ/.test(c);
  }
  const api = { normalize, isTimeCommand, isDateCommand };
  if (root) root.JarvisCommandUtils = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
