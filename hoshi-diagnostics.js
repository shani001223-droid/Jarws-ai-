/* Payload-free diagnostics stay in page memory until the user copies a report. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else { root.HoshiDiagnostics = api.create(); root.HoshiDiagnostics.install(root); }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const KINDS = new Set(['uncaught_error', 'unhandled_rejection', 'request_failed', 'request_cancelled']);
  const SCRIPTS = new Set(['index.html', 'hoshi-diagnostics.js', 'hoshi-product-ads.js', 'hoshi-task-router.js', 'assistant-commands.js', 'reminder-parser.js', 'memory-privacy.js']);
  function create(options = {}) {
    const now = typeof options.now === 'function' ? options.now : Date.now;
    const events = [], counts = Object.create(null), hosts = new WeakSet();
    let lastResponse = null, lastFailure = null;
    const time = () => { const n = now(); return Number.isFinite(n) ? Math.floor(n) : 0; };
    const position = n => Number.isInteger(n) && n > 0 && n <= 1000000 ? n : 0;
    function record(kind, event) {
      if (!KINDS.has(kind)) return false;
      let script = 'unknown', line = 0, column = 0;
      if (kind === 'uncaught_error' && event) {
        try {
          const filename = typeof event.filename === 'string' ? event.filename.slice(0, 2048) : '';
          const name = filename.split(/[?#]/)[0].split('/').pop();
          if (SCRIPTS.has(name)) script = name;
          line = position(event.lineno); column = position(event.colno);
        } catch (_) { /* Never inspect error.message, stack or rejection.reason. */ }
      }
      counts[kind] = Math.min(1000000, (counts[kind] || 0) + 1);
      events.push({ kind, script, line, column, at_ms: time() });
      if (events.length > 10) events.shift();
      return true;
    }
    function noteResponse(response) {
      try {
        const id = response.headers.get('X-Request-ID');
        if (typeof id !== 'string' || !UUID.test(id)) return false;
        const status = Number.isInteger(response.status) && response.status >= 100 && response.status <= 599 ? response.status : null;
        lastResponse = { request_id: id.toLowerCase(), status, at_ms: time() };
        if (status >= 400) lastFailure = { ...lastResponse };
        return true;
      } catch (_) { return false; }
    }
    function snapshot() {
      return { version: 1, scope: 'this_page_only', last_api_response: lastResponse && { ...lastResponse },
        last_failed_api_response: lastFailure && { ...lastFailure }, counts: { ...counts }, events: events.map(e => ({ ...e })) };
    }
    function clear() {
      events.length = 0; Object.keys(counts).forEach(k => delete counts[k]);
      lastResponse = null; lastFailure = null;
    }
    function install(host) {
      if (!host || typeof host.addEventListener !== 'function' || hosts.has(host)) return;
      hosts.add(host);
      host.addEventListener('error', event => record('uncaught_error', event));
      host.addEventListener('unhandledrejection', () => record('unhandled_rejection'));
    }
    return { record, noteResponse, snapshot, clear, install };
  }
  return { create };
});
