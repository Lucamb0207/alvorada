import feedparser
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# RSS feed sources
# ---------------------------------------------------------------------------

VENEZUELA_FEEDS = [
    "https://news.google.com/rss/search?q=venezuela&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://efectococuyo.com/feed/",
    "https://talcualdigital.com/feed/",
]

GLOBAL_FEEDS = [
    "https://feeds.reuters.com/reuters/topNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
]

OG_NEWS_FEEDS = [
    "https://oilprice.com/rss/main",
    "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
    "https://www.energyvoice.com/feed/",
    "https://news.google.com/rss/search?q=oil+gas+energy+petroleum&hl=en&gl=US&ceid=US:en",
]

OG_EVENTS_FEEDS = [
    "https://news.google.com/rss/search?q=%22oil+gas%22+%22conference%22+OR+%22summit%22+OR+%22forum%22+2025+2026&hl=en&gl=US&ceid=US:en",
]

OFAC_FEEDS = [
    "https://news.google.com/rss/search?q=OFAC+Venezuela+sanctions+license&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=OFAC+Venezuela+licencia+petroleo&hl=es&gl=US&ceid=US:es",
    "https://home.treasury.gov/system/files/126/ofac-recent-actions.xml",
]

# Curated upcoming O&G industry conferences
STATIC_EVENTS = [
    {"name": "Gastech 2025", "date": "Set/2025", "location": "Houston, TX", "url": "https://www.gastechevent.com"},
    {"name": "SPE ATCE 2025", "date": "Set/2025", "location": "Houston, TX", "url": "https://www.spe.org/en/atce/"},
    {"name": "Africa Oil Week 2025", "date": "Out/2025", "location": "Cape Town, ZA", "url": "https://africa-oilweek.com"},
    {"name": "ADIPEC 2025", "date": "Nov/2025", "location": "Abu Dhabi, UAE", "url": "https://adipec.com"},
    {"name": "IP Week 2026", "date": "Fev/2026", "location": "London, UK", "url": "https://www.energyinst.org/ipweek"},
    {"name": "CERAWeek 2026", "date": "Mar/2026", "location": "Houston, TX", "url": "https://ceraweek.com"},
    {"name": "OTC 2026", "date": "Mai/2026", "location": "Houston, TX", "url": "https://www.otcnet.org"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_ago(dt: datetime | None) -> str:
    if not dt:
        return ""
    now = datetime.now(timezone.utc)
    diff = (now - dt).total_seconds()
    if diff < 3600:
        return f"{int(diff // 60)}min"
    if diff < 86400:
        return f"{int(diff // 3600)}h"
    return f"{int(diff // 86400)}d"


def _parse_entry(entry, source_name: str) -> dict:
    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass

    title = entry.get("title", "Sem título")
    # Google News wraps titles like "Title - Source", strip the source suffix
    if " - " in title:
        parts = title.rsplit(" - ", 1)
        title = parts[0]

    summary = ""
    if hasattr(entry, "summary"):
        import re
        summary = re.sub(r"<[^>]+>", "", entry.summary)[:180]

    return {
        "title": title,
        "link": entry.get("link", "#"),
        "source": source_name,
        "published": published,
        "time_ago": _time_ago(published),
        "summary": summary,
    }


def fetch_news(feeds, max_items: int = 8):
    items = []
    seen_titles: set[str] = set()

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.get("title", url)
            for entry in feed.entries:
                parsed = _parse_entry(entry, source_name)
                key = parsed["title"].lower()[:60]
                if key not in seen_titles:
                    seen_titles.add(key)
                    items.append(parsed)
        except Exception as exc:
            print(f"[fetchers] Error parsing {url}: {exc}")

    items.sort(
        key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items[:max_items]


def fetch_brent():
    """Returns (close_series, current_price, pct_change_1d)."""
    try:
        df = yf.download("BZ=F", period="35d", interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError("Empty dataframe")
        # yfinance >=0.2.x returns MultiIndex columns — flatten to get Close series
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        current = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else current
        pct = (current - prev) / prev * 100
        return close, current, pct
    except Exception as exc:
        print(f"[fetchers] Brent error: {exc}")
        return pd.Series(dtype=float), 0.0, 0.0


def fetch_og_events():
    """Returns (static_events, news_events)."""
    news = fetch_news(OG_EVENTS_FEEDS, max_items=5)
    return STATIC_EVENTS, news
