import feedparser
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# RSS feed sources
# ---------------------------------------------------------------------------

VENEZUELA_FEEDS = [
    "https://news.google.com/rss/search?q=venezuela&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://efectococuyo.com/feed/",
    "https://talcualdigital.com/feed/",
    "https://venezuelanalysis.com/feed",
    "https://prodavinci.com/feed",
    "https://runrun.es/feed",
    "https://www.elnacional.com/feed",
    "https://dialogo-americas.com/feed/",
    "https://www.infobae.com/arc/outboundfeeds/rss/",
    "https://www.noticierodigital.com.ar/categoria/judiciales/feed/",
    "https://www.noticierodigital.com.ar/categoria/sociales/feed/",
    "https://www.noticierodigital.com.ar/categoria/sociedad/feed/",
    "http://feeds.bbci.co.uk/news/world/latin_america/rss.xml",
    "https://bastidoresdopoder.com.br/feed/",
]

GLOBAL_FEEDS = [
    "https://feeds.reuters.com/reuters/topNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.crisisgroup.org/rss.xml",
    "https://www.hrw.org/rss/news",
]

OG_NEWS_FEEDS = [
    "https://oilprice.com/rss/main",
    "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
    "https://www.energyvoice.com/feed/",
    "https://news.google.com/rss/search?q=oil+gas+energy+petroleum&hl=en&gl=US&ceid=US:en",
    "https://www.worldoil.com/rss?feed=news",
    "https://www.ogj.com/__rss/website-scheduled-content.xml?input=%7B%22sectionAlias%22%3A%22general-interest%22%7D",
    "https://feeder.co/discover/073d51739a/opec-org-opec_web-en-pressreleases-rss",
    "https://megawhat.energy/feed/",
    "https://www.iogp.org/feed/",
    "https://boereport.com/feed/",
    "https://www.worldenergytrade.com/feed",
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
    {"name": "International Energy Summit 2026", "date": "Jun/2026", "location": "New Orleans, LA, USA", "url": "https://www.theenergysummit.org/"},
    {"name": "Gas, LNG & The Future of Energy 2026", "date": "Jun/2026", "location": "London, UK", "url": "https://www.woodmac.com/events/gas-lng-future-of-energy-conference/"},
    {"name": "URTeC 2026", "date": "Jun/2026", "location": "Houston, TX, USA", "url": "https://www.urtec.org/"},
    {"name": "ONS 2026", "date": "Aug/2026", "location": "Stavanger, Norway", "url": "https://www.ons.no/"},
    {"name": "Oil & Gas Asia (OGA) 2026", "date": "Sep/2026", "location": "Kuala Lumpur, Malaysia", "url": "https://www.oilandgas-asia.com/"},
    {"name": "APPEC 2026", "date": "Sep/2026", "location": "Singapore", "url": "https://www.spglobal.com/commodityinsights/en/events/appec"},
    {"name": "Gastech 2026", "date": "Sep/2026", "location": "Bangkok, Thailand", "url": "https://www.gastechevent.com/"},
    {"name": "Subsea Pipeline Technology Congress 2026", "date": "Sep/2026", "location": "London, UK", "url": "https://www.subpipeline.com/"},
    {"name": "SPE ATCE 2026", "date": "Oct/2026", "location": "Houston, TX, USA", "url": "https://www.atce.org/"},
    {"name": "ADIPEC 2026", "date": "Nov/2026", "location": "Abu Dhabi, UAE", "url": "https://www.adipec.com/"},
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


def _fetch_price_yfinance(ticker: str):
    df = yf.download(ticker, period="35d", interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError("Empty dataframe")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    return close


def _fetch_price_requests(ticker: str):
    """Fallback: fetch price via Yahoo Finance v8 JSON API."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=35d"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    dates = pd.to_datetime(timestamps, unit="s", utc=True).normalize()
    close = pd.Series(closes, index=dates, dtype=float).dropna()
    return close


def _fetch_single(ticker: str):
    """Returns (close_series, current_price, pct_change_1d)."""
    close = pd.Series(dtype=float)
    for fn in (_fetch_price_yfinance, _fetch_price_requests):
        try:
            close = fn(ticker)
            if not close.empty:
                break
        except Exception as exc:
            print(f"[fetchers] {ticker} attempt failed ({fn.__name__}): {exc}")

    if close.empty:
        return close, 0.0, 0.0

    current = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else current
    pct = (current - prev) / prev * 100
    return close, current, pct


def fetch_brent():
    """Returns (close_series, current_price, pct_change_1d)."""
    return _fetch_single("BZ=F")


def fetch_oil_prices():
    """Returns (brent_series, brent_price, brent_pct, wti_series, wti_price, wti_pct)."""
    brent_close, brent_price, brent_pct = _fetch_single("BZ=F")
    wti_close, wti_price, wti_pct = _fetch_single("CL=F")
    return brent_close, brent_price, brent_pct, wti_close, wti_price, wti_pct


def fetch_og_events():
    """Returns (static_events, news_events)."""
    news = fetch_news(OG_EVENTS_FEEDS, max_items=5)
    return STATIC_EVENTS, news


def fetch_producao(days: int = 60):
    try:
        import db
        return db.fetch_producao(days)
    except Exception as exc:
        print(f"[fetchers] producao error: {exc}")
        return []
