"""Behavioral coverage for private, bounded, payload-free request diagnostics."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from cloud_backend.observability import (
    RequestMetrics, RequestObservabilityMiddleware, current_request_id, install_observability,
)


class ObservabilityTests(unittest.TestCase):
    def make_app(self):
        app = FastAPI()
        app.add_middleware(CORSMiddleware, allow_origins=['https://hoshi.test'],
                           allow_methods=['GET'], expose_headers=['X-Request-ID'])
        metrics = install_observability(app)

        @app.get('/sync')
        def sync_route():
            return {'request_id': current_request_id(), 'ok': True}

        @app.get('/async')
        async def async_route():
            await asyncio.sleep(0)
            return {'request_id': current_request_id()}

        @app.get('/items/{item_id}')
        def item(item_id: str):
            return {'ok': True}

        @app.get('/fail')
        def failure():
            raise RuntimeError('provider-secret-SENTINEL must never be recorded')

        @app.get('/status/{code}')
        def status(code: int):
            raise HTTPException(code, 'Request rejected')

        @app.get('/replace-header')
        def header():
            return JSONResponse({'ok': True}, headers={'X-Request-ID': 'handler-supplied'})

        return app, metrics

    def test_generated_ids_are_unique_and_match_sync_async_context(self):
        app, _ = self.make_app()
        with TestClient(app) as client:
            ids = []
            for path in ['/sync', '/async', '/sync']:
                response = client.get(path, headers={'X-Request-ID': 'untrusted-secret'})
                identity = response.headers['x-request-id']
                uuid.UUID(identity)
                self.assertEqual(identity, response.json()['request_id'])
                ids.append(identity)
            self.assertEqual(len(set(ids)), 3)
        self.assertIsNone(current_request_id())

    def test_generated_id_replaces_handler_header(self):
        app, _ = self.make_app()
        with TestClient(app) as client:
            response = client.get('/replace-header')
            uuid.UUID(response.headers['x-request-id'])
            self.assertEqual(len(response.headers.get_list('x-request-id')), 1)

    def test_cors_and_preflight_expose_trace_without_response_rewrite(self):
        app, _ = self.make_app()
        with TestClient(app) as client:
            response = client.get('/sync', headers={'Origin': 'https://hoshi.test'})
            self.assertEqual(response.headers['access-control-expose-headers'], 'X-Request-ID')
            self.assertTrue(response.json()['ok'])
            response = client.options('/sync', headers={'Origin': 'https://hoshi.test', 'Access-Control-Request-Method': 'GET'})
            self.assertEqual(response.status_code, 200)
            uuid.UUID(response.headers['x-request-id'])

    def test_exception_response_and_logs_have_no_sensitive_content(self):
        app, metrics = self.make_app()
        with self.assertLogs('hoshi.requests', level='INFO') as logs, TestClient(app) as client:
            response = client.get('/fail?api_key=query-secret', headers={'Authorization': 'Bearer auth-secret'})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['request_id'], response.headers['x-request-id'])
        records = [json.loads(r.message) for r in logs.records]
        record = records[0]
        self.assertEqual(record['route'], '/fail')
        self.assertEqual(record['error_class'], 'internal_error')
        evidence = response.text + json.dumps(records) + json.dumps(metrics.snapshot())
        for secret in ['provider-secret-SENTINEL', 'query-secret', 'auth-secret', 'api_key', 'Authorization']:
            self.assertNotIn(secret, evidence)
        self.assertEqual(metrics.snapshot()['active_requests'], 0)

    def test_unmatched_raw_paths_and_dynamic_ids_do_not_enter_logs(self):
        app, metrics = self.make_app()
        with self.assertLogs('hoshi.requests', level='INFO') as logs, TestClient(app) as client:
            client.get('/items/private-customer-id?email=person-secret')
            client.get('/secret-unknown-path')
        evidence = '\n'.join(r.message for r in logs.records) + json.dumps(metrics.snapshot())
        for value in ['private-customer-id', 'person-secret', 'secret-unknown-path']:
            self.assertNotIn(value, evidence)
        self.assertIn('/items/{item_id}', evidence)
        self.assertIn('unmatched', evidence)

    def test_post_body_is_not_consumed_or_logged(self):
        app, _ = self.make_app()
        from fastapi import Request

        @app.post('/echo-size')
        async def echo(request: Request):
            return {'length': len(await request.body())}

        with self.assertLogs('hoshi.requests', level='INFO') as logs, TestClient(app) as client:
            response = client.post('/echo-size', content=b'body-secret' * 5000)
        self.assertEqual(response.json()['length'], 55000)
        self.assertNotIn('body-secret', '\n'.join(r.message for r in logs.records))

    def test_handled_http_failures_are_classified(self):
        app, metrics = self.make_app()
        with TestClient(app) as client:
            for status in [401, 429, 504, 502, 422]:
                response = client.get('/status/' + str(status))
                self.assertEqual(response.status_code, status)
                self.assertIn('x-request-id', response.headers)
        bucket = next(r for r in metrics.snapshot()['routes'] if r['route'] == '/status/{code}')
        self.assertEqual(bucket['requests'], 5)
        self.assertEqual(bucket['errors']['timeout'], 1)
        self.assertEqual(bucket['errors']['access_denied'], 1)
        self.assertEqual(bucket['errors']['rate_limited'], 1)
        self.assertEqual(bucket['errors']['invalid_request'], 1)
        self.assertEqual(bucket['errors']['upstream_unavailable'], 1)

    def test_private_diagnostics_are_disabled_without_a_strong_token(self):
        app, _ = self.make_app()
        with patch.dict(os.environ, {'DIAGNOSTICS_TOKEN': 'short'}), TestClient(app) as client:
            response = client.get('/api/diagnostics')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertNotIn('routes', response.json())

    def test_private_diagnostics_require_matching_bearer_token(self):
        app, _ = self.make_app()
        secret = 'diagnostics-token-' * 4
        with patch.dict(os.environ, {'DIAGNOSTICS_TOKEN': secret}), TestClient(app) as client:
            for auth in ['', 'Basic ' + secret, 'Bearer wrong-value']:
                response = client.get('/api/diagnostics', headers={'Authorization': auth})
                self.assertEqual(response.status_code, 401)
            response = client.get('/api/diagnostics', headers={'Authorization': 'Bearer ' + secret})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        data = response.json()
        self.assertEqual(data['scope'], 'current_process')
        self.assertFalse(data['persistent'])
        self.assertIsNone(data['queue_depth'])
        self.assertNotIn(secret, response.text)

    def test_health_payload_and_business_behavior_are_preserved(self):
        from cloud_backend.main import app
        with TestClient(app) as client:
            response = client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['service'], 'hoshi-cloud-api')
        self.assertEqual(response.json()['version'], '0.9.1')
        uuid.UUID(response.headers['x-request-id'])


class MetricsBehaviorTests(unittest.TestCase):
    def test_percentiles_use_real_bounded_recent_samples(self):
        metrics = RequestMetrics(sample_limit=5)
        for value in [999, 10, 20, 30, 40, 50]:
            metrics.begin()
            metrics.end('GET', '/health', 200, value, None)
        data = metrics.snapshot()
        self.assertEqual(data['requests_completed'], 6)
        self.assertEqual(data['active_requests'], 0)
        bucket = data['routes'][0]
        self.assertEqual(bucket['recent_samples'], 5)
        self.assertEqual(bucket['p50_ms'], 30)
        self.assertEqual(bucket['p95_ms'], 50)

    def test_route_and_sample_cardinality_are_bounded(self):
        metrics = RequestMetrics(max_routes=3, sample_limit=4)
        for i in range(1000):
            metrics.begin()
            metrics.end('GET', '/route-' + str(i), 200, i, None)
        data = metrics.snapshot()
        self.assertLessEqual(len(data['routes']), 3)
        self.assertTrue(all(r['recent_samples'] <= 4 for r in data['routes']))
        self.assertEqual(sum(r['requests'] for r in data['routes']), 1000)

    def test_concurrent_requests_do_not_lose_counts(self):
        metrics = RequestMetrics()
        def record(_):
            metrics.begin()
            metrics.end('GET', '/health', 200, 1, None)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(record, range(2000)))
        self.assertEqual(metrics.snapshot()['requests_completed'], 2000)
        self.assertEqual(metrics.snapshot()['active_requests'], 0)

    def test_invalid_bounds_are_rejected(self):
        with self.assertRaises(ValueError):
            RequestMetrics(max_routes=0)
        with self.assertRaises(ValueError):
            RequestMetrics(sample_limit=0)


class ASGILifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_frames_are_forwarded_without_buffering(self):
        seen = []
        async def app(scope, receive, send):
            scope['route'] = SimpleNamespace(path='/stream')
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'first', 'more_body': True})
            self.assertEqual(seen[-1]['body'], b'first')
            await send({'type': 'http.response.body', 'body': b'last', 'more_body': False})
        async def send(message):
            seen.append(message)
        async def receive():
            raise AssertionError('Middleware must not read the body')
        metrics = RequestMetrics()
        await RequestObservabilityMiddleware(app, metrics)({'type': 'http', 'method': 'GET'}, receive, send)
        self.assertEqual([m.get('body') for m in seen[1:]], [b'first', b'last'])
        self.assertEqual(metrics.snapshot()['active_requests'], 0)
        self.assertIsNone(current_request_id())

    async def test_client_cancellation_cleans_up_and_propagates(self):
        async def app(scope, receive, send):
            raise asyncio.CancelledError()
        async def sink(*args):
            pass
        metrics = RequestMetrics()
        with self.assertRaises(asyncio.CancelledError):
            await RequestObservabilityMiddleware(app, metrics)({'type': 'http', 'method': 'GET'}, sink, sink)
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot['active_requests'], 0)
        self.assertEqual(snapshot['routes'][0]['errors'], {'client_cancelled': 1})
        self.assertIsNone(current_request_id())

    async def test_late_stream_errors_keep_wire_status_and_hide_exception_detail(self):
        frames = []
        async def app(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
            await send({'type': 'http.response.body', 'body': b'chunk', 'more_body': True})
            raise ValueError('sensitive-provider-detail')
        async def send(frame):
            frames.append(frame)
        async def receive():
            pass
        metrics = RequestMetrics()
        with self.assertRaisesRegex(RuntimeError, '^Response interrupted; consult the request ID.$'):
            await RequestObservabilityMiddleware(app, metrics)({'type': 'http', 'method': 'GET'}, receive, send)
        self.assertEqual(len(frames), 2)
        bucket = metrics.snapshot()['routes'][0]
        self.assertEqual(bucket['status_classes'], {'2xx': 1})
        self.assertEqual(bucket['errors'], {'stream_error': 1})
        self.assertEqual(metrics.snapshot()['active_requests'], 0)

    async def test_simultaneous_request_contexts_do_not_leak_between_requests(self):
        import httpx
        app = FastAPI()
        install_observability(app)

        @app.get('/context')
        async def context():
            before = current_request_id()
            await asyncio.sleep(0)
            return {'before': before, 'after': current_request_id()}

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            responses = await asyncio.gather(*(client.get('/context') for _ in range(20)))
        identities = []
        for response in responses:
            identity = response.headers['x-request-id']
            self.assertEqual(response.json(), {'before': identity, 'after': identity})
            identities.append(identity)
        self.assertEqual(len(set(identities)), 20)
        self.assertIsNone(current_request_id())

    async def test_non_http_scope_is_forwarded_unchanged(self):
        scopes = []
        async def app(scope, receive, send):
            scopes.append(scope)
        async def sink(*args):
            pass
        metrics = RequestMetrics()
        scope = {'type': 'lifespan'}
        await RequestObservabilityMiddleware(app, metrics)(scope, sink, sink)
        self.assertIs(scopes[0], scope)
        self.assertEqual(metrics.snapshot()['requests_completed'], 0)
