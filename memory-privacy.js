(function (root) {
  "use strict";

  const patterns = [
    /\b(?:password|passcode|pin(?:\s+code)?|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|secret|otp|one[- ]time code|seed phrase|recovery phrase|mnemonic|private key)\b/i,
    /\b\d{6,}\b/,
    /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/,
    /(?:\+?\d[\d ()-]{7,}\d)/,
    /\b(?:bearer\s+[A-Za-z0-9._~+/-]+=*|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{15,}|sk-[A-Za-z0-9_-]{12,})\b/i,
    /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/i
  ];

  function looksSensitive(value) {
    const text = String(value == null ? "" : value);
    return patterns.some(pattern => pattern.test(text));
  }

  const api = { looksSensitive };
  if (root) root.HoshiPrivacy = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
