from datetime import timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_news_headlines(symbol: str):
    try:
        import feedparser
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "feedparser is required for Google News RSS sentiment"
        ) from exc

    query = quote_plus(f"{symbol} stock NSE")
    feed = feedparser.parse(GOOGLE_NEWS_RSS_URL.format(query=query))

    if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
        error = getattr(feed, "bozo_exception", None)
        if error:
            raise RuntimeError(f"Unable to fetch Google News RSS: {error}") from error

        raise RuntimeError("Unable to fetch Google News RSS")

    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        published = parse_entry_date(entry)

        if title and published:
            articles.append(
                {
                    "headline": title,
                    "published_date": published.isoformat(),
                }
            )

    return articles


def parse_entry_date(entry):
    published = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not published:
        return None

    try:
        parsed = parsedate_to_datetime(published)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)
