"""Headlines from Google News RSS searches + a few publisher RSS feeds."""
import calendar
import html
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

from . import config

log = logging.getLogger("news")
GNEWS = "https://news.google.com/rss/search?q={q}+when:2d&hl=en-IN&gl=IN&ceid=IN:en"


def _norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def _clean_title(title):
    """Google News appends ' - Publisher'. Split it out."""
    title = html.unescape(title)
    if " - " in title:
        head, tail = title.rsplit(" - ", 1)
        return head.strip(), tail.strip()
    return title.strip(), None


def _tags_for(title):
    t = f" {_norm(title)} "
    tags = [s["name"] for s in config.STOCKS
            if any(f" {_norm(a)} " in t for a in s["aliases"])]
    if any(k in t for k in ("palm oil", "sugar", "coffee", "brent", "crude", "hdpe", "polymer", "wheat", "cocoa")):
        tags.append("Commodities")
    if any(k in t for k in ("fmcg", "consumer goods", "rural demand", "volume growth")):
        tags.append("FMCG sector")
    if any(k in t for k in ("quick commerce", "food delivery", "instamart", "blinkit", "zepto")):
        tags.append("Quick commerce")
    return sorted(set(tags))


def _collect(feed_url, default_source, queue, keyword_filter):
    import feedparser
    parsed = feedparser.parse(feed_url, agent="Mozilla/5.0 (fmcg-desk)")
    for e in parsed.entries:
        title, src = _clean_title(e.get("title", ""))
        if not title:
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        if not ts:
            continue
        epoch = calendar.timegm(ts)
        if keyword_filter and not any(k in _norm(title) for k in config.KEYWORDS):
            continue
        queue.append({"title": title, "link": e.get("link"), "source": src or default_source, "epoch": epoch})


def fetch_news():
    items = []
    queries = list(config.SECTOR_QUERIES)
    for s in config.STOCKS:
        queries.append(f'"{s["aliases"][0]}" shares OR results OR stock')
    for q in queries:
        try:
            _collect(GNEWS.format(q=quote_plus(q)), "Google News", items, keyword_filter=False)
        except Exception as e:
            log.warning("gnews '%s' failed: %s", q, e)
        time.sleep(0.4)  # be polite
    for name, url in config.DIRECT_FEEDS:
        try:
            _collect(url, name, items, keyword_filter=True)
        except Exception as e:
            log.warning("%s failed: %s", name, e)

    cutoff = time.time() - config.NEWS_HOURS * 3600
    seen, out = set(), []
    for it in sorted(items, key=lambda x: -x["epoch"]):
        key = _norm(it["title"])[:80]
        if it["epoch"] < cutoff or key in seen:
            continue
        seen.add(key)
        it["published"] = datetime.fromtimestamp(it["epoch"], timezone.utc).isoformat(timespec="minutes")
        it["tags"] = _tags_for(it["title"])
        del it["epoch"]
        out.append(it)
    # keep tagged items first when trimming
    out.sort(key=lambda x: (not x["tags"], ), reverse=False)
    out = sorted(out[: config.NEWS_MAX * 2], key=lambda x: x["published"], reverse=True)[: config.NEWS_MAX]
    return out
