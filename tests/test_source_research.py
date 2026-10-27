"""Task 31: fixed-source, freshness and citation security regression tests."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch
from xml.sax.saxutils import escape
import unittest

from fastapi import HTTPException, Response
from cloud_backend import main, source_research as sr


NOW = datetime(2026, 10, 27, 0, 0, tzinfo=timezone.utc)


def item(title="A verified headline", description="Latest public report",
         link="https://www.bbc.com/news/articles/example",
         published=None):
    published = NOW - timedelta(hours=2) if published is None else published
    return ("<item><title>" + escape(title) + "</title>"
            "<description>" + escape(description) + "</description>"
            "<link>" + escape(link) + "</link><pubDate>"
            + format_datetime(published) + "</pubDate></item>")


def feed(*entries):
    return ('<?xml version="1.0"?><rss version="2.0"><channel>'
            + "".join(entries) + "</channel></rss>").encode("utf-8")


class SourceResearchTests(unittest.TestCase):
    def setUp(self):
        with sr._CACHE_LOCK:
            sr._CACHE.clear()

    def test_returns_real_citation_urls_timestamps_and_sorted_fresh_results(self):
        xml = feed(item("AI research", "<b>Science</b> report",
                        "https://www.bbc.com/news/articles/old?utm=tracking",
                        NOW - timedelta(hours=6)),
                   item("AI new discovery", "Science update",
                        "https://www.bbc.com/news/articles/new#fragment",
                        NOW - timedelta(minutes=30)))
        with patch.object(sr, "_download", return_value=xml) as fetch:
            data = sr.browse_sources("technology", "AI", 2, now=NOW)
            cached = sr.browse_sources("technology", "AI", 1, now=NOW)
        fetch.assert_called_once_with(sr.SOURCES["technology"][1])
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["items"][0]["url"], "https://www.bbc.com/news/articles/new")
        self.assertEqual(data["items"][1]["url"], "https://www.bbc.com/news/articles/old")
        self.assertEqual(data["items"][0]["citation_url"], data["items"][0]["url"])
        self.assertEqual(data["items"][0]["age_minutes"], 30)
        self.assertEqual(data["items"][0]["published_at"], "2026-10-26T23:30:00+00:00")
        self.assertEqual(data["retrieved_at"], NOW.isoformat())
        self.assertEqual(data["mode"], "read_only_fixed_sources")
        self.assertEqual(cached["count"], 1)
        self.assertNotIn("utm=", str(data))

    def test_filters_stale_future_missing_date_and_malicious_citation_urls(self):
        xml = feed(
            item("Valid", "story", "https://www.bbc.co.uk/news/valid"),
            item("Stale", "story", "https://www.bbc.com/news/stale", NOW - timedelta(days=5)),
            item("Future", "story", "https://www.bbc.com/news/future", NOW + timedelta(hours=2)),
            item("Impersonator", "story", "https://www.bbc.com.evil.test/news/x"),
            item("Userinfo", "story", "https://www.bbc.com@127.0.0.1/internal"),
            item("Local", "story", "http://www.bbc.com/news/local"),
            item("Script", "story", "javascript:alert(1)"),
        )
        xml = xml.replace(b"</channel>", b"<item><title>Undated</title>"
                          b"<link>https://www.bbc.com/news/undated</link></item></channel>")
        with patch.object(sr, "_download", return_value=xml):
            result = sr.browse_sources("world", now=NOW)
        self.assertEqual([x["title"] for x in result["items"]], ["Valid"])
        self.assertEqual(result["freshness_hours"], 72)

    def test_search_is_word_bounded_and_no_match_is_not_fabricated(self):
        xml = feed(item("A major aid agreement", "Regional update"),
                   item("AI breakthroughs", "Science research",
                        "https://www.bbc.com/news/ai"))
        with patch.object(sr, "_download", return_value=xml):
            result = sr.browse_sources("world", "AI", now=NOW)
            absent = sr.browse_sources("world", "quantum weather", now=NOW)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["items"][0]["title"], "AI breakthroughs")
        self.assertEqual(absent["status"], "no_matching_fresh_items")
        self.assertEqual(absent["items"], [])

    def test_markup_is_inert_and_scripts_not_part_of_summary(self):
        xml = feed(item("Hello <b>World</b>",
                        "<p>Safe text</p><script>STEAL SECRET</script>"))
        with patch.object(sr, "_download", return_value=xml):
            result = sr.browse_sources("world", now=NOW)
        self.assertEqual(result["items"][0]["title"], "Hello World")
        self.assertIn("Safe text", result["items"][0]["summary"])
        self.assertNotIn("STEAL SECRET", result["items"][0]["summary"])

    def test_doctype_and_oversize_and_invalid_xml_fail_closed(self):
        for data in (b'<!DOCTYPE rss [<!ENTITY x SYSTEM "file:///etc/passwd">]><rss/>',
                     b"x" * (sr.MAX_FEED_BYTES + 1),
                     b"<rss><channel><item>"):
            with self.subTest(data=data[:20]), patch.object(sr, "_download", return_value=data):
                with self.assertRaises(sr.SourceUnavailable):
                    sr.browse_sources("world", now=NOW)

    def test_fixed_feed_only_and_bounded_query_limit(self):
        for topic, query, limit in (
            ("http://localhost:8000/private", "", 2),
            ("world", "x" * 81, 2),
            ("world", "   ", 2),
            ("world", "", 0),
            ("world", "", 6),
            ("world", "", True),
        ):
            with self.subTest(topic=topic, query=query[:8], limit=limit):
                with self.assertRaises(ValueError):
                    sr.browse_sources(topic, query, limit, now=NOW)

    def test_source_network_failure_is_sanitized_and_not_cached_as_success(self):
        with patch.object(sr, "_download", side_effect=sr.SourceUnavailable("transport")) as fetch:
            with self.assertRaises(sr.SourceUnavailable):
                sr.browse_sources("world", now=NOW)
        fetch.assert_called_once()
        self.assertNotIn("world", sr._CACHE)

    def test_nasa_source_is_separate_allowlist_and_freshness_window(self):
        xml = feed(item("NASA update", "Moon science",
                        "https://www.nasa.gov/mission/real", NOW - timedelta(days=10)),
                   item("Wrong publisher", "NASA",
                        "https://www.bbc.com/news/not-nasa"))
        with patch.object(sr, "_download", return_value=xml):
            result = sr.browse_sources("space", now=NOW)
        self.assertEqual(result["publisher"], "NASA")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["freshness_hours"], 336)

    def test_api_is_get_only_read_only_no_store_and_safe_failure(self):
        paths = {(route.path, method) for route in main.app.routes
                 for method in getattr(route, "methods", set())}
        self.assertIn(("/api/research/sources", "GET"), paths)
        self.assertNotIn(("/api/research/sources", "POST"), paths)
        expected = {"topic": "world", "items": [], "count": 0}
        with patch.object(main, "browse_sources", return_value=expected) as mock:
            response = Response()
            actual = main.research_sources(response, "world", "", 2)
            self.assertEqual(actual, expected)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            mock.assert_called_once_with("world", "", 2)
        with patch.object(main, "browse_sources", side_effect=sr.SourceUnavailable("SECRET")):
            with self.assertRaises(HTTPException) as error:
                main.research_sources(Response(), "world", "", 2)
            self.assertEqual(error.exception.status_code, 503)
            self.assertNotIn("SECRET", error.exception.detail)
        with patch.object(main, "browse_sources", side_effect=ValueError("invalid")):
            with self.assertRaises(HTTPException) as error:
                main.research_sources(Response(), "world", "", 2)
            self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
