"""Read-only production probe: tracing works and anonymous metrics stay closed."""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid

BASE = 'https://jarws-ai-2.onrender.com'


def fetch(path):
    request = Request(BASE + path + '?trace_probe=' + uuid.uuid4().hex,
                      headers={'Cache-Control': 'no-cache', 'User-Agent': 'Hoshi-ReadOnly-Trace-Smoke/1'})
    try:
        with urlopen(request, timeout=12) as response:
            return response.status, response.headers, json.loads(response.read(16384))
    except HTTPError as response:
        return response.code, response.headers, json.loads(response.read(16384))


def main():
    ready = False
    for attempt in range(18):
        try:
            status, headers, data = fetch('/health')
            if status == 200 and data.get('service') == 'hoshi-cloud-api':
                uuid.UUID(headers.get('X-Request-ID', ''))
                ready = True
                break
        except (URLError, TimeoutError, ValueError, OSError):
            pass
        if attempt < 17:
            time.sleep(5)
    if not ready:
        raise SystemExit('FAIL: production health never exposed a valid request ID for the new revision.')
    first = headers['X-Request-ID']
    status, headers, data = fetch('/health')
    assert status == 200 and data.get('service') == 'hoshi-cloud-api', 'Health payload regressed'
    uuid.UUID(headers.get('X-Request-ID', ''))
    assert headers['X-Request-ID'] != first, 'Distinct requests must not reuse trace IDs'
    status, headers, data = fetch('/api/diagnostics')
    assert status in (401, 503), 'Anonymous diagnostics must be denied'
    assert headers.get('Cache-Control') == 'no-store', 'Private diagnostics must not be cached'
    assert 'routes' not in data and 'detail' in data, 'Anonymous metrics must not leak'
    uuid.UUID(headers.get('X-Request-ID', ''))
    print('PASS: health unchanged; unique request IDs; anonymous diagnostics denied with no-store. '
          'Authorized metrics and real-phone behavior are not tested by this probe.')


if __name__ == '__main__':
    main()
