"""Task 31: bounded, citation-first public-source browsing for Hoshi.

This is a fixed-feed read-only research tool, NOT an arbitrary URL fetcher or
a general web browser. Feed text is untrusted DATA, never executable guidance.
No provider keys, cookies, local files, search proxies or redirects are used.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from threading import BoundedSemaphore, Lock
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from xml.etree import ElementTree as ET
import re
import time


# Only fixed public HTTPS feeds. A user cannot supply or influence fetch URLs.
SOURCES = {
    "world": ("BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml",
              frozenset({"www.bbc.com", "www.bbc.co.uk"}), 72),
    "technology": ("BBC News", "https://feeds.bbci.co.uk/news/technology/rss.xml",
                   frozenset({"www.bbc.com", "www.bbc.co.uk"}), 168),
    "science": ("BBC News", "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                frozenset({"www.bbc.com", "www.bbc.co.uk"}), 168),
    "space": ("NASA", "https://www.nasa.gov/feed/",
              frozenset({"www.nasa.gov", "science.nasa.gov"}), 336),
}
MAX_FEED_BYTES = 196_608
CACHE_SECONDS = 120
_FETCH_SLOTS = BoundedSemaphore(2)
_CACHE_LOCK = Lock()
_CACHE = {}
_ATOM = "{http://www.w3.org/2005/Atom}"


class SourceUnavailable(Exception):
    """Fixed source unreachable, malformed or over the resource budget."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # Never let a compromised feed endpoint redirect to internal networks.
        raise SourceUnavailable("redirect_blocked")


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.blocked += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.blocked:
            self.blocked -= 1

    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(data)


def _plain(value, max_chars):
    reader = _PlainText()
    try:
        reader.feed(str(value or "")[:4000])
        text = " ".join(reader.parts)
    except (ValueError, TypeError):
        text = ""
    # Keep text inert, printable and short; don't pass feed markup to a UI.
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


def _canonical_article_url(raw, allowed_hosts):
    try:
        url = urlsplit(str(raw or "").strip())
        if (url.scheme != "https" or url.hostname not in allowed_hosts
                or url.username is not None or url.password is not None
                or url.port not in (None, 443) or not url.path.startswith("/")):
            return None
        # Strip tracking queries and fragments; links are citations, not fetched.
        return urlunsplit(("https", url.hostname, url.path, "", ""))
    except (ValueError, TypeError):
        return None


def _published(raw):
    try:
        stamp = parsedate_to_datetime(raw)
    except (ValueError, TypeError, IndexError):
        try:
            stamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(timezone.utc)


def _matches(query, title, summary):
    if not query:
        return True
    words = re.findall(r"\w+", query.casefold(), flags=re.UNICODE)
    if not words:
        return False
    haystack = (title + " " + summary).casefold()
    return all(re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", haystack)
               for word in words)


def _parse_items(data, topic, query, now):
    publisher, feed_url, hosts, max_age_hours = SOURCES[topic]
    if len(data) > MAX_FEED_BYTES or b"<!doctype" in data.lower():
        raise SourceUnavailable("unsafe_feed")
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, ValueError):
        raise SourceUnavailable("invalid_feed") from None
    entries = root.findall(".//item")[:60]
    atom = False
    if not entries:
        entries = root.findall(".//" + _ATOM + "entry")[:60]
        atom = True
    found = {}
    for entry in entries:
        if atom:
            title = entry.findtext(_ATOM + "title")
            description = entry.findtext(_ATOM + "summary") or entry.findtext(_ATOM + "content")
            date = entry.findtext(_ATOM + "published") or entry.findtext(_ATOM + "updated")
            links = [x.attrib.get("href", "") for x in entry.findall(_ATOM + "link")
                     if x.attrib.get("rel", "alternate") == "alternate"]
            link = links[0] if links else ""
        else:
            title = entry.findtext("title")
            description = entry.findtext("description")
            date = entry.findtext("pubDate") or entry.findtext("{http://purl.org/dc/elements/1.1/}date")
            link = entry.findtext("link")
        title, summary = _plain(title, 180), _plain(description, 260)
        url = _canonical_article_url(link, hosts)
        published = _published(date)
        if not title or not url or not published:
            continue
        age = (now - published).total_seconds()
        if age < -600 or age > max_age_hours * 3600:
            continue
        if not _matches(query, title, summary):
            continue
        found[url] = {
            "title": title, "summary": summary, "publisher": publisher,
            "published_at": published.isoformat(), "age_minutes": max(0, int(age // 60)),
            "url": url, "citation_url": url,
        }
    return sorted(found.values(), key=lambda x: x["published_at"], reverse=True)


def _download(url):
    """Fetch only the hard-coded source URL; disable redirects and bound bytes."""
    request = Request(url, headers={
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        "User-Agent": "HoshiPrivateResearch/1.0 (read-only fixed feeds)",
    })
    try:
        with build_opener(_NoRedirect()).open(request, timeout=5) as response:
            data = response.read(MAX_FEED_BYTES + 1)
            if len(data) > MAX_FEED_BYTES:
                raise SourceUnavailable("feed_too_large")
            return data
    except SourceUnavailable:
        raise
    except Exception:
        # Never echo provider response bodies, URLs or transport diagnostics.
        raise SourceUnavailable("source_unavailable") from None


def browse_sources(topic, query="", limit=5, *, now=None):
    """Return fresh, directly linked headlines, never an ungrounded AI answer.

    Empty results are explicit. Source publication time and retrieval time are
    distinct; articles are NOT independently fact-checked. No LLM is called.
    """
    if topic not in SOURCES or not isinstance(query, str) or len(query) > 80:
        raise ValueError("invalid_research_request")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 5:
        raise ValueError("invalid_research_request")
    if query and not query.strip():
        raise ValueError("invalid_research_request")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("invalid_research_time")
    now = now.astimezone(timezone.utc)
    publisher, feed_url, _hosts, max_age_hours = SOURCES[topic]
    with _CACHE_LOCK:
        cached = _CACHE.get(topic)
        data = cached[1] if cached and time.monotonic() - cached[0] < CACHE_SECONDS else None
    if data is None:
        if not _FETCH_SLOTS.acquire(blocking=False):
            raise SourceUnavailable("source_busy")
        try:
            data = _download(feed_url)
            # Validate BEFORE caching so bad or oversized XML never gets cached.
            _parse_items(data, topic, "", now)
            with _CACHE_LOCK:
                _CACHE[topic] = (time.monotonic(), data)
        finally:
            _FETCH_SLOTS.release()
    items = _parse_items(data, topic, query.strip(), now)[:limit]
    return {
        "mode": "read_only_fixed_sources", "topic": topic,
        "publisher": publisher, "feed_url": feed_url,
        "retrieved_at": now.isoformat(), "freshness_hours": max_age_hours,
        "items": items, "count": len(items),
        "status": "fresh_results" if items else "no_matching_fresh_items",
        "notice": "Headlines are source claims, not independently verified facts. Cite each article URL and its publication time. No general web browsing or publishing.",
    }
